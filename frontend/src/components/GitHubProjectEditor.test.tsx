import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  commitProject,
  connectGitHub,
  createActivity,
  deleteProject,
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
import type { Activity } from "../types";
import GitHubProjectEditor from "./GitHubProjectEditor";

vi.mock("../api", () => ({
  commitProject: vi.fn(),
  connectGitHub: vi.fn(),
  createActivity: vi.fn(),
  deleteProject: vi.fn(),
  disconnectGitHub: vi.fn(),
  getActivities: vi.fn(),
  getGitHubRepos: vi.fn(),
  getGitHubStatus: vi.fn(),
  getProjectFile: vi.fn(),
  getProjectFiles: vi.fn(),
  getProjects: vi.fn(),
  importGitHubRepo: vi.fn(),
  runProject: vi.fn(),
  saveProjectFile: vi.fn(),
  updateActivity: vi.fn(),
}));

const statusApi = vi.mocked(getGitHubStatus);
const reposApi = vi.mocked(getGitHubRepos);
const projectsApi = vi.mocked(getProjects);
const connectApi = vi.mocked(connectGitHub);
const disconnectApi = vi.mocked(disconnectGitHub);
const importApi = vi.mocked(importGitHubRepo);
const filesApi = vi.mocked(getProjectFiles);
const fileApi = vi.mocked(getProjectFile);
const saveApi = vi.mocked(saveProjectFile);
const runApi = vi.mocked(runProject);
const activityApi = vi.mocked(createActivity);
const commitApi = vi.mocked(commitProject);
const deleteApi = vi.mocked(deleteProject);

describe("GitHubProjectEditor", () => {
  beforeEach(() => {
    statusApi.mockReset();
    reposApi.mockReset();
    projectsApi.mockReset();
    connectApi.mockReset();
    disconnectApi.mockReset();
    importApi.mockReset();
    filesApi.mockReset();
    fileApi.mockReset();
    saveApi.mockReset();
    runApi.mockReset();
    activityApi.mockReset();
    commitApi.mockReset();
    deleteApi.mockReset();
    projectsApi.mockResolvedValue([]);
  });

  it("shows the connect-first empty state when GitHub is disconnected", async () => {
    statusApi.mockResolvedValue({
      connected: false,
      username: null,
      syncedAt: null,
      canPush: false,
    });

    render(<GitHubProjectEditor userId="ali" />);

    expect(await screen.findByText("Connect to the git first.")).toBeInTheDocument();
    expect(screen.getByLabelText("GitHub username")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Connect" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Disconnect" })).not.toBeInTheDocument();
  });

  it("renders connected state with the repository picker and disconnect button", async () => {
    statusApi.mockResolvedValue({
      connected: true,
      username: "octocat",
      syncedAt: "2026-09-03T00:00:00Z",
      canPush: false,
    });
    reposApi.mockResolvedValue([
      {
        fullName: "octocat/hello",
        name: "hello",
        owner: "octocat",
        htmlUrl: "https://github.com/octocat/hello",
        language: "Python",
        defaultBranch: "main",
        updatedAt: "2026-09-03T00:00:00Z",
        private: false,
      },
    ]);

    render(<GitHubProjectEditor userId="ali" />);

    expect(await screen.findByText("Connected as octocat")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Disconnect" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "octocat/hello" })).toBeInTheDocument();
    expect(statusApi).toHaveBeenCalled();
    expect(reposApi).toHaveBeenCalled();
    expect(screen.queryByText("Connect to the git first.")).not.toBeInTheDocument();
  });

  it("asks for confirmation and deletes the selected imported project", async () => {
    statusApi.mockResolvedValue({
      connected: true,
      username: "octocat",
      syncedAt: "2026-09-03T00:00:00Z",
      canPush: false,
    });
    reposApi.mockResolvedValue([]);
    projectsApi.mockResolvedValue([
      {
        id: "hello",
        userId: "ali",
        name: "hello",
        description: "demo",
        technology: ["Python"],
        status: "active",
      },
    ]);
    filesApi.mockResolvedValue([]);
    deleteApi.mockResolvedValue(undefined);
    // After delete, no projects remain
    projectsApi.mockResolvedValueOnce([
      {
        id: "hello",
        userId: "ali",
        name: "hello",
        description: "demo",
        technology: ["Python"],
        status: "active",
      },
    ]);
    projectsApi.mockResolvedValueOnce([]);

    render(<GitHubProjectEditor userId="ali" />);

    expect(await screen.findByText("Connected as octocat")).toBeInTheDocument();
    const select = screen.getByRole("combobox", { name: "Imported project" });
    const { fireEvent } = await import("@testing-library/react");
    fireEvent.change(select, { target: { value: "hello" } });

    expect(await screen.findByRole("button", { name: "Delete project" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete project" }));
    expect(await screen.findByText("Are you sure about delete hello?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yes, delete" }));

    // Wait a tick for the async delete to settle, then verify
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(deleteApi).toHaveBeenCalledWith("hello");
  });
});

const connectedStatus = {
  connected: true,
  username: "octocat",
  syncedAt: "2026-09-01T00:00:00Z",
  canPush: false,
};

const project = {
  id: "demo",
  userId: "ali",
  name: "demo",
  description: "demo project",
  technology: ["Python"],
  status: "active",
};

const activity: Activity = {
  id: "a1",
  userId: "ali",
  date: "2026-09-01",
  title: "some work",
  status: "in-progress",
  projectId: null,
};

describe("GitHubProjectEditor activity attach", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getGitHubStatus).mockResolvedValue(connectedStatus);
    vi.mocked(getGitHubRepos).mockResolvedValue([]);
    vi.mocked(getProjects).mockResolvedValue([project]);
    vi.mocked(getActivities).mockResolvedValue([activity]);
    vi.mocked(getProjectFiles).mockResolvedValue([
      { path: "main.py", name: "main.py", isDirectory: false, size: 10 },
    ]);
    vi.mocked(createActivity).mockResolvedValue({ ...activity, projectId: "demo" });
    vi.mocked(updateActivity).mockResolvedValue({ ...activity, projectId: "demo" });
  });

  it("attaches the current project to an existing activity", async () => {
    render(<GitHubProjectEditor userId="ali" />);

    const selects = await screen.findAllByRole("combobox");
    fireEvent.change(selects[1], { target: { value: "demo" } });

    const attachSelect = await screen.findByRole("combobox", {
      name: "Attach to activity",
    });
    fireEvent.change(attachSelect, { target: { value: "a1" } });
    fireEvent.click(screen.getByRole("button", { name: "Attach" }));

    expect(await screen.findByText("Attached to your tracked activities.")).toBeInTheDocument();
    expect(updateActivity).toHaveBeenCalledWith("a1", {
      userId: "ali",
      date: "2026-09-01",
      title: "some work",
      status: "in-progress",
      projectId: "demo",
    });
    expect(createActivity).not.toHaveBeenCalled();
  });

  it("creates a new activity when no existing one is picked", async () => {
    render(<GitHubProjectEditor userId="ali" />);

    const selects = await screen.findAllByRole("combobox");
    fireEvent.change(selects[1], { target: { value: "demo" } });

    await screen.findByRole("combobox", { name: "Attach to activity" });
    fireEvent.click(screen.getByRole("button", { name: "Attach" }));

    expect(await screen.findByText("Attached to your tracked activities.")).toBeInTheDocument();
    expect(createActivity).toHaveBeenCalledWith({
      userId: "ali",
      date: expect.any(String),
      title: "demo",
      projectId: "demo",
      status: "in-progress",
    });
  });

  it("keeps the editor usable when repositories cannot be listed", async () => {
    vi.mocked(getGitHubRepos).mockRejectedValue(
      new Error("GitHub rate limit reached. Try again later or connect with an access token."),
    );

    render(<GitHubProjectEditor userId="ali" />);

    expect(
      await screen.findByText(
        "GitHub rate limit reached. Try again later or connect with an access token.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Import repository" })).toBeInTheDocument();
  });
});
