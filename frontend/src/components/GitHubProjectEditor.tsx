import { useCallback, useEffect, useState } from "react";

import {
  commitProject,
  connectGitHub,
  createActivity,
  disconnectGitHub,
  getActivities,
  getGitHubRepos,
  getGitHubStatus,
  getProjectFile,
  getProjectFiles,
  getProjects,
  importGitHubRepo,
  runProject,
  saveProjectFile,
  updateActivity,
} from "../api";
import "../github-editor.css";
import { useI18n } from "../i18n";
import type {
  Activity,
  GithubRepo,
  GithubStatus,
  Project,
  ProjectFile,
  ProjectFileEntry,
  ProjectRunResult,
} from "../types";
import FileTree from "./FileTree";
import StatusMessage from "./StatusMessage";

interface Props {
  userId: string;
  initialTarget?: { projectId: string; path: string | null } | null;
}

export default function GitHubProjectEditor({ userId, initialTarget = null }: Props) {
  const { t } = useI18n();

  const [status, setStatus] = useState<GithubStatus | null>(null);
  const [username, setUsername] = useState("");
  const [token, setToken] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const [repos, setRepos] = useState<GithubRepo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState("");
  const [importing, setImporting] = useState(false);

  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");

  const [files, setFiles] = useState<ProjectFileEntry[]>([]);
  const [selectedPath, setSelectedPath] = useState("");
  const [file, setFile] = useState<ProjectFile | null>(null);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);

  const [result, setResult] = useState<ProjectRunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [commitMessage, setCommitMessage] = useState("");
  const [committing, setCommitting] = useState(false);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [attachActivityId, setAttachActivityId] = useState("");
  const [attaching, setAttaching] = useState(false);
  const [reposError, setReposError] = useState("");

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadProjects = useCallback(async () => {
    const all = await getProjects();
    setProjects(all.filter((project) => project.userId === userId));
  }, [userId]);

  const loadActivities = useCallback(async () => {
    const all = await getActivities();
    setActivities(all.filter((activity) => activity.userId === userId));
  }, [userId]);

  const loadStatus = useCallback(async () => {
    const next = await getGitHubStatus();
    setStatus(next);
    if (!next.connected) {
      setRepos([]);
      setReposError("");
      return;
    }
    // A repositories failure must never take down the whole editor:
    // connecting, importing, editing, running and attaching keep working.
    try {
      setRepos(await getGitHubRepos());
      setReposError("");
    } catch (requestError) {
      setRepos([]);
      setReposError(requestError instanceof Error ? requestError.message : t("gh.noRepos"));
    }
  }, [t]);

  useEffect(() => {
    setNotice("");
    setError("");
    loadStatus()
      .then(loadProjects)
      .then(loadActivities)
      .catch((requestError: Error) => setError(requestError.message));
  }, [loadStatus, loadProjects, loadActivities]);

  // Deep-link target from the activity form ("Open in code editor").
  useEffect(() => {
    if (!initialTarget) return;
    setProjectId(initialTarget.projectId);
    if (initialTarget.path) {
      setSelectedPath(initialTarget.path);
      getProjectFile(initialTarget.projectId, initialTarget.path)
        .then((next) => {
          setFile(next);
          setContent(next.content);
        })
        .catch((requestError: Error) => setError(requestError.message));
    }
  }, [initialTarget]);

  useEffect(() => {
    setSelectedPath("");
    setFile(null);
    setContent("");
    setResult(null);
    setNotice("");
    setError("");
    if (!projectId) {
      setFiles([]);
      return;
    }
    getProjectFiles(projectId)
      .then(setFiles)
      .catch((requestError: Error) => setError(requestError.message));
  }, [projectId]);

  async function handleConnect() {
    if (!username.trim()) return;
    setError("");
    setNotice("");
    setConnecting(true);
    try {
      const next = await connectGitHub(username.trim(), token.trim() || null);
      setStatus(next);
      if (next.connected) setRepos(await getGitHubRepos());
      setUsername("");
      setToken("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("gh.connectError"));
    } finally {
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    setError("");
    setNotice("");
    setDisconnecting(true);
    try {
      await disconnectGitHub();
      setStatus({ connected: false, username: null, syncedAt: null, canPush: false });
      setRepos([]);
      setSelectedRepo("");
      setProjectId("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("gh.disconnectError"));
    } finally {
      setDisconnecting(false);
    }
  }

  async function handleImport() {
    if (!selectedRepo) return;
    setError("");
    setNotice("");
    setImporting(true);
    try {
      await importGitHubRepo(selectedRepo);
      await loadProjects();
      setNotice(t("gh.imported"));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("gh.importError"));
    } finally {
      setImporting(false);
    }
  }
  const selectFile = useCallback(
    async (entry: ProjectFileEntry) => {
      if (entry.isDirectory || !projectId) return;
      setError("");
      setNotice("");
      setSelectedPath(entry.path);
      try {
        const next = await getProjectFile(projectId, entry.path);
        setFile(next);
        setContent(next.content);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : t("gh.readError"));
      }
    },
    [projectId, t],
  );

  async function handleSave() {
    if (!projectId || !selectedPath) return;
    setError("");
    setNotice("");
    setSaving(true);
    try {
      const next = await saveProjectFile(projectId, selectedPath, content);
      setFile(next);
      setContent(next.content);
      setNotice(t("gh.saved", { path: selectedPath }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("gh.saveError"));
    } finally {
      setSaving(false);
    }
  }

  async function handleRun() {
    if (!projectId) return;
    setError("");
    setNotice("");
    setRunning(true);
    try {
      setResult(await runProject(projectId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("pp.runError"));
    } finally {
      setRunning(false);
    }
  }

  async function handleAttach() {
    if (!projectId || attaching) return;
    const project = projects.find((candidate) => candidate.id === projectId);
    if (!project) return;
    setError("");
    setNotice("");
    setAttaching(true);
    try {
      if (attachActivityId) {
        const target = activities.find((candidate) => candidate.id === attachActivityId);
        if (!target) {
          setError(t("gh.attachError"));
          return;
        }
        await updateActivity(target.id, {
          userId,
          date: target.date,
          title: target.title,
          status: target.status,
          projectId,
        });
      } else {
        await createActivity({
          userId,
          date: new Date().toISOString().slice(0, 10),
          title: project.name,
          projectId,
          status: "in-progress",
        });
        await loadActivities();
      }
      setNotice(t("gh.attachedToActivity"));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("gh.attachError"));
    } finally {
      setAttaching(false);
    }
  }

  async function handleCommit() {
    if (!projectId) return;
    if (!commitMessage.trim()) {
      setError(t("gh.commitMessageRequired"));
      return;
    }
    setError("");
    setNotice("");
    setCommitting(true);
    try {
      const response = await commitProject(projectId, commitMessage.trim());
      setNotice(
        response.detail ? t("gh.commitResult", { detail: response.detail }) : t("gh.committed"),
      );
      setCommitMessage("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("gh.commitError"));
    } finally {
      setCommitting(false);
    }
  }

  if (status === null) {
    return (
      <section className="dashboard-card github-editor-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("gh.editorEyebrow")}</p>
            <h2>{t("gh.editorTitle")}</h2>
          </div>
        </div>
        <StatusMessage>{t("gh.editorLoading")}</StatusMessage>
      </section>
    );
  }

  const connectedProject = projects.find((candidate) => candidate.id === projectId);
  return (
    <section className="dashboard-card github-editor-card" id="github-editor">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{t("gh.editorEyebrow")}</p>
          <h2>{t("gh.editorTitle")}</h2>
        </div>
        {status.connected ? (
          <span className="runner-badge runner-ready">{t("gh.connected")}</span>
        ) : null}
      </div>

      {error ? <StatusMessage error>{error}</StatusMessage> : null}
      {notice ? <StatusMessage>{notice}</StatusMessage> : null}

      {!status.connected ? (
        <div className="gh-editor-empty">
          <p className="runner-safety-note">{t("gh.connectFirst")}</p>
          <p>{t("gh.connectCaption")}</p>
          <div className="gh-connect-form">
            <label className="gh-field">
              <span>{t("gh.username")}</span>
              <input
                type="text"
                value={username}
                placeholder={t("gh.usernamePlaceholder")}
                autoComplete="username"
                onChange={(event) => setUsername(event.target.value)}
              />
            </label>
            <label className="gh-field">
              <span>{t("gh.token")}</span>
              <input
                type="password"
                value={token}
                placeholder={t("gh.tokenPlaceholder")}
                autoComplete="off"
                onChange={(event) => setToken(event.target.value)}
              />
            </label>
            <p className="runner-reason">{t("gh.tokenHint")}</p>
            <button
              className="primary-button runner-button"
              type="button"
              disabled={connecting || !username.trim()}
              onClick={() => void handleConnect()}
            >
              {connecting ? t("gh.connecting") : t("gh.connect")}
            </button>
          </div>
        </div>
      ) : (
        <div className="gh-editor-connected">
          <div className="gh-connected-header">
            <p>
              {t("gh.connectedAs", {
                username: status.username ?? t("gh.unknownUser"),
              })}
            </p>
            <button
              className="secondary-button runner-button"
              type="button"
              disabled={disconnecting}
              onClick={() => void handleDisconnect()}
            >
              {disconnecting ? t("gh.disconnecting") : t("gh.disconnect")}
            </button>
          </div>

          <div className="gh-import-row">
            <div className="gh-field">
              <span>{t("gh.repositories")}</span>
              <select
                className="gh-picker"
                value={selectedRepo}
                onChange={(event) => setSelectedRepo(event.target.value)}
              >
                <option value="">{t("gh.pickRepo")}</option>
                {repos.map((repo) => (
                  <option key={repo.fullName} value={repo.fullName}>
                    {repo.fullName}
                  </option>
                ))}
              </select>
            </div>
            <button
              className="secondary-button runner-button"
              type="button"
              disabled={importing || !selectedRepo}
              onClick={() => void handleImport()}
            >
              {importing ? t("gh.importing") : t("gh.import")}
            </button>
          </div>
          {reposError ? (
            <div className="gh-repos-error">
              <StatusMessage error>{reposError}</StatusMessage>
              <button
                className="secondary-button runner-button"
                type="button"
                onClick={() => void loadStatus().catch(() => undefined)}
              >
                {t("gh.retryRepos")}
              </button>
            </div>
          ) : null}

          <div className="gh-field">
            <span>{t("gh.pickProject")}</span>
            <select
              className="gh-picker"
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
            >
              <option value="">{t("gh.chooseProject")}</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
          {projectId ? (
            <div className="gh-editor-workspace">
              <aside className="gh-file-list" aria-label={t("gh.projectFiles")}>
                <h3>{t("gh.projectFiles")}</h3>
                {files.length > 0 ? (
                  <FileTree
                    entries={files}
                    selectedPath={selectedPath || null}
                    onSelectFile={(entry) => void selectFile(entry)}
                  />
                ) : (
                  <StatusMessage>{t("gh.noFiles")}</StatusMessage>
                )}
              </aside>

              <div className="gh-editor-pane">
                {selectedPath ? (
                  <>
                    <div className="gh-editor-toolbar">
                      <strong>{selectedPath}</strong>
                      <span className="runner-contract">{file ? `${file.size} B` : ""}</span>
                      <button
                        className="secondary-button runner-button"
                        type="button"
                        disabled={saving}
                        onClick={() => void handleSave()}
                      >
                        {saving ? t("gh.saving") : t("gh.save")}
                      </button>
                      <button
                        className="primary-button runner-button"
                        type="button"
                        disabled={running}
                        onClick={() => void handleRun()}
                      >
                        {running ? t("pp.running") : t("gh.run")}
                      </button>
                    </div>
                    <textarea
                      className="gh-code-textarea"
                      spellCheck={false}
                      value={content}
                      aria-label={selectedPath}
                      onChange={(event) => setContent(event.target.value)}
                    />

                    {result ? (
                      <div className="runner-result" aria-live="polite">
                        <div className="runner-result-meta">
                          <strong>
                            {result.timedOut
                              ? t("pp.timedOut")
                              : t("pp.exit", { code: result.exitCode ?? "—" })}
                          </strong>
                          <span>{result.durationMs} ms</span>
                          {result.outputTruncated ? <span>{t("pp.outputTruncated")}</span> : null}
                        </div>
                        {result.stdout ? <pre>{result.stdout}</pre> : null}
                        {result.stderr ? (
                          <pre className="runner-stderr">{result.stderr}</pre>
                        ) : null}
                        {!result.stdout && !result.stderr ? <p>{t("pp.noOutput")}</p> : null}
                      </div>
                    ) : null}
                  </>
                ) : (
                  <StatusMessage>{t("gh.selectFileHint")}</StatusMessage>
                )}
              </div>
            </div>
          ) : null}

          {projectId ? (
            <div className="gh-attach-row">
              <div className="gh-field">
                <span>{t("gh.attachActivity")}</span>
                <select
                  className="gh-picker"
                  value={attachActivityId}
                  aria-label={t("gh.attachActivity")}
                  onChange={(event) => setAttachActivityId(event.target.value)}
                >
                  <option value="">{t("gh.newActivity")}</option>
                  {activities.map((activity) => (
                    <option key={activity.id} value={activity.id}>
                      {activity.title}
                    </option>
                  ))}
                </select>
              </div>
              <button
                className="gh-run-button"
                type="button"
                disabled={attaching}
                onClick={() => void handleAttach()}
              >
                {attaching ? t("gh.attaching") : t("gh.attach")}
              </button>
            </div>
          ) : null}

          {projectId ? (
            <div className="gh-commit-row">
              <input
                className="gh-commit-input"
                type="text"
                value={commitMessage}
                placeholder={t("gh.commitMessagePlaceholder")}
                onChange={(event) => setCommitMessage(event.target.value)}
              />
              <button
                className="primary-button runner-button"
                type="button"
                disabled={committing || !connectedProject}
                onClick={() => void handleCommit()}
              >
                {committing ? t("gh.committing") : t("gh.commitPush")}
              </button>
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}
