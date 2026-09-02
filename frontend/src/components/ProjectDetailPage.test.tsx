import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getProjectDetail, runProject } from "../api";
import ProjectDetailPage from "./ProjectDetailPage";

vi.mock("../api", () => ({
  getProjectDetail: vi.fn(),
  runProject: vi.fn(),
}));

vi.mock("./ProjectOnboardingPanel", () => ({
  default: () => <div>Project onboarding panel</div>,
}));

vi.mock("./ProjectReviewPanel", () => ({
  default: () => <div>Professor review panel</div>,
}));

vi.mock("./ProjectSubmissionPanel", () => ({
  default: () => <div>Project submission panel</div>,
}));

const getDetail = vi.mocked(getProjectDetail);
const executeProject = vi.mocked(runProject);

const detail = {
  project: {
    id: "team-foundation",
    userId: "hossein",
    name: "Team Project Foundation",
    description: "Shared platform",
    technology: ["Python"],
    status: "active",
  },
  integration: {
    projectId: "team-foundation",
    userId: "hossein",
    name: "Team Project Foundation",
    integrationStatus: "ready" as const,
    runnerEnabled: true,
    runnable: true,
    projectType: "cli",
    runner: "python-script-v1",
    entryPoint: "main.py",
    repositoryPath: "projects/hossein/team-platform",
    reason: null,
  },
  health: [
    {
      key: "manifest",
      label: "Manifest",
      passed: true,
      detail: "Manifest is valid.",
    },
  ],
  healthPassed: 1,
  healthTotal: 1,
  readme: "# Team Project Foundation\n\nDemo documentation.",
  recentRuns: [
    {
      id: 1,
      projectId: "team-foundation",
      runner: "python-script-v1",
      exitCode: 0,
      timedOut: false,
      durationMs: 9,
      stdoutPreview: "history-ok\n",
      stderrPreview: "",
      outputTruncated: false,
      createdAt: "2026-09-02 00:00:00",
    },
  ],
};

describe("ProjectDetailPage", () => {
  beforeEach(() => {
    getDetail.mockReset();
    executeProject.mockReset();
    getDetail.mockResolvedValue(detail);
  });

  it("renders health, review panel, safe readme text, and runtime history", async () => {
    render(
      <ProjectDetailPage projectId="team-foundation" backHref="/users/hossein" role="student" />,
    );

    expect(
      await screen.findByRole("heading", { name: "Team Project Foundation" }),
    ).toBeInTheDocument();
    expect(screen.getByText("1/1 checks passing")).toBeInTheDocument();
    expect(screen.getByText("Manifest is valid.")).toBeInTheDocument();
    expect(screen.getByText("Project onboarding panel")).toBeInTheDocument();
    expect(screen.getByText("Professor review panel")).toBeInTheDocument();
    expect(screen.getByText("Project submission panel")).toBeInTheDocument();
    expect(screen.getByText(/Demo documentation/)).toBeInTheDocument();
    expect(screen.getByText("history-ok")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "← Back" })).toHaveAttribute("href", "/users/hossein");
  });

  it("runs a demo and refreshes detail history", async () => {
    executeProject.mockResolvedValue({
      projectId: "team-foundation",
      runner: "python-script-v1",
      exitCode: 0,
      timedOut: false,
      durationMs: 14,
      stdout: "fresh-run\n",
      stderr: "",
      outputTruncated: false,
    });

    render(
      <ProjectDetailPage projectId="team-foundation" backHref="/users/hossein" role="student" />,
    );

    fireEvent.click(await screen.findByRole("button", { name: "Run demo" }));

    expect(await screen.findByText("fresh-run")).toBeInTheDocument();
    expect(executeProject).toHaveBeenCalledWith("team-foundation");
    expect(getDetail).toHaveBeenCalledTimes(2);
  });
});
