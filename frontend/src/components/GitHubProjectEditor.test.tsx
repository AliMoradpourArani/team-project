import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  commitProject,
  connectGitHub,
  createActivity,
  disconnectGitHub,
  getGitHubRepos,
  getGitHubStatus,
  getProjectFile,
  getProjectFiles,
  getProjects,
  importGitHubRepo,
  runProject,
  saveProjectFile,
} from "../api";
import GitHubProjectEditor from "./GitHubProjectEditor";

vi.mock("../api", () => ({
  commitProject: vi.fn(),
  connectGitHub: vi.fn(),
  createActivity: vi.fn(),
  disconnectGitHub: vi.fn(),
  getGitHubRepos: vi.fn(),
  getGitHubStatus: vi.fn(),
  getProjectFile: vi.fn(),
  getProjectFiles: vi.fn(),
  getProjects: vi.fn(),
  importGitHubRepo: vi.fn(),
  runProject: vi.fn(),
  saveProjectFile: vi.fn(),
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
});
