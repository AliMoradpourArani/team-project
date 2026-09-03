"""Service-level tests for the in-page code editor (no real git invoked)."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest

from backend.schemas.api import ProjectResponse
from backend.services import code_editor, github_sync
from backend.services.github_sync import GithubConnection


def make_project(tmp_path, monkeypatch):
    projects_root = tmp_path / "projects"
    monkeypatch.setenv("PROJECTS_ROOT", str(projects_root))
    directory = projects_root / "ali" / "hello"
    directory.mkdir(parents=True)
    (directory / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (directory / "helpers").mkdir()
    (directory / "helpers" / "util.py").write_text("X = 1\n", encoding="utf-8")
    manifest = {
        "id": "hello",
        "name": "hello",
        "owner_id": "ali",
        "description": "demo",
        "technology": ["Python"],
        "project_type": "cli",
        "runner": "python-script-v1",
        "entry_point": "main.py",
        "repository_path": "projects/ali/hello",
    }
    (directory / "project.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    return ProjectResponse(
        id="hello", userId="ali", name="hello", description="demo",
        technology=["Python"], status="active",
    )


def fake_git(project_dir, *args):
    """Deterministic stand-in for code_editor._run_git (no real git calls)."""
    del project_dir
    stdout = ""
    returncode = 0
    if args == ("rev-parse", "--abbrev-ref", "HEAD"):
        stdout = "main"
    elif args == ("remote", "get-url", "origin"):
        stdout = "https://github.com/octocat/hello.git"
    elif args == ("diff", "--cached", "--quiet"):
        returncode = 1  # there are staged changes
    elif args == ("commit", "-m"):
        returncode = 0
    elif args == ("rev-parse", "HEAD"):
        stdout = "deadbeef"
    elif args[0] == "push":
        returncode = 0
    return subprocess.CompletedProcess(["git", *args], returncode, stdout=stdout, stderr="")


def test_safe_target_rejects_traversal_and_absolute_paths(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    for path in ["../escape", "a/../../escape", "/etc/passwd", ".", ".git/config", "a/../b"]:
        with pytest.raises(ValueError):
            code_editor._safe_target(project_dir, path)


def test_safe_target_allows_nested_file(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    target = code_editor._safe_target(project_dir, "src/main.py")
    assert target == (project_dir / "src" / "main.py").resolve()


def test_list_read_write_project_files(tmp_path, monkeypatch):
    project = make_project(tmp_path, monkeypatch)
    entries = code_editor.list_files(project)
    paths = {entry.path for entry in entries}
    assert "main.py" in paths
    assert "helpers" in paths
    helpers = next(entry for entry in entries if entry.path == "helpers")
    assert helpers.isDirectory is True

    read = code_editor.read_file(project, "main.py")
    assert read.content == "print('hi')\n"

    written = code_editor.write_file(project, "notes/todo.txt", "do it\n")
    assert written.content == "do it\n"
    content = code_editor.read_file(project, "notes/todo.txt")
    assert content.content == "do it\n"


def test_write_file_rejects_traversal(tmp_path, monkeypatch):
    project = make_project(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        code_editor.write_file(project, "../../evil.py", "x")


def test_commit_local_only_when_no_connection(tmp_path, monkeypatch):
    project = make_project(tmp_path, monkeypatch)
    monkeypatch.setattr(code_editor, "_run_git", fake_git)
    result = code_editor.commit_and_push(project, "wip", None)
    assert result.committed is True
    assert result.pushed is False
    assert result.sha == "deadbeef"


def test_commit_pushes_with_token_connection(tmp_path, monkeypatch):
    project = make_project(tmp_path, monkeypatch)
    connection = GithubConnection(
        user_id="ali",
        github_username="AliMoradpourArani",
        personal_token="tok",
        can_push=True,
        synced_at="now",
    )
    monkeypatch.setattr(code_editor, "_run_git", fake_git)
    result = code_editor.commit_and_push(project, "wip", connection)
    assert result.committed is True
    assert result.pushed is True


def test_commit_no_changes(tmp_path, monkeypatch):
    project = make_project(tmp_path, monkeypatch)

    def noop(project_dir, *args):
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(code_editor, "_run_git", noop)
    result = code_editor.commit_and_push(project, "wip", None)
    assert result.committed is False
    assert result.detail == "No changes to commit."


def test_credential_url_sanitizes_and_injects_token():
    # Clean URL
    clean = code_editor._credential_url("https://github.com/octocat/hello.git", "secret_token")
    assert clean == "https://x-access-token:secret_token@github.com/octocat/hello.git"

    # URL with existing embedded token
    with_token = code_editor._credential_url("https://old_token@github.com/octocat/hello.git", "secret_token")
    assert with_token == "https://x-access-token:secret_token@github.com/octocat/hello.git"

    # URL with existing x-access-token
    with_x_access = code_editor._credential_url("https://x-access-token:old_token@github.com/octocat/hello.git", "secret_token")
    assert with_x_access == "https://x-access-token:secret_token@github.com/octocat/hello.git"

    # Non-https
    ssh = code_editor._credential_url("git@github.com:octocat/hello.git", "secret_token")
    assert ssh == "git@github.com:octocat/hello.git"


def test_sanitize_git_origin(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    commands_run = []

    def fake_run(cmd, *args, **kwargs):
        commands_run.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        github_sync._sanitize_git_origin(repo_dir, "octocat/hello")

    assert len(commands_run) == 1
    assert commands_run[0] == [
        "git",
        "-C",
        str(repo_dir),
        "remote",
        "set-url",
        "origin",
        "https://github.com/octocat/hello.git",
    ]


def test_import_repository_cleans_up_on_entry_point_failure(tmp_path, monkeypatch):
    projects_root = tmp_path / "projects"
    monkeypatch.setenv("PROJECTS_ROOT", str(projects_root))

    connection = GithubConnection(
        user_id="ali",
        github_username="AliMoradpourArani",
        personal_token="secret_token",
        can_push=True,
        synced_at="now",
    )
    monkeypatch.setattr(github_sync, "get_connection", lambda user_id: connection)

    def fake_clone(url, dest):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "readme.md").write_text("No python files here\n", encoding="utf-8")

    monkeypatch.setattr(github_sync, "_clone_repository", fake_clone)
    monkeypatch.setattr(github_sync, "_sanitize_git_origin", lambda dest, full_name: None)

    with pytest.raises(ValueError, match=r"No Python \(\.py\) file found in the cloned repository"):
        github_sync.import_repository("ali", "AliMoradpourArani/no-python-repo")

    expected_dest = projects_root / "ali" / "no-python-repo"
    assert not expected_dest.exists()

