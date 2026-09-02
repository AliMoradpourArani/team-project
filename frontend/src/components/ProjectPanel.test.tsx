import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getProjectIntegrations, runProject } from "../api";
import ProjectPanel from "./ProjectPanel";

vi.mock("../api", () => ({
  getProjectIntegrations: vi.fn(),
  runProject: vi.fn(),
}));

const getIntegrations = vi.mocked(getProjectIntegrations);
const executeProject = vi.mocked(runProject);

const projects = [
  {
    id: "team-foundation",
    userId: "hossein",
    name: "Team Project Foundation",
    description: "Shared platform",
    technology: ["Python"],
    status: "active",
  },
];

describe("ProjectPanel", () => {
  beforeEach(() => {
    getIntegrations.mockReset();
    executeProject.mockReset();
  });

  it("shows an integrated project while keeping execution disabled by default", async () => {
    getIntegrations.mockResolvedValue([
      {
        projectId: "team-foundation",
        userId: "hossein",
        name: "Team Project Foundation",
        integrationStatus: "ready",
        runnerEnabled: false,
        runnable: false,
        projectType: "cli",
        runner: "python-script-v1",
        entryPoint: "main.py",
        repositoryPath: "projects/hossein/team-platform",
        reason: "Runner is disabled.",
      },
    ]);

    render(<ProjectPanel projects={projects} />);

    expect(await screen.findByText("python-script-v1 · main.py")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Runner disabled" })).toBeDisabled();
    expect(screen.getByText("Runner is disabled.")).toBeInTheDocument();
  });

  it("runs a ready project and renders structured output", async () => {
    getIntegrations.mockResolvedValue([
      {
        projectId: "team-foundation",
        userId: "hossein",
        name: "Team Project Foundation",
        integrationStatus: "ready",
        runnerEnabled: true,
        runnable: true,
        projectType: "cli",
        runner: "python-script-v1",
        entryPoint: "main.py",
        repositoryPath: "projects/hossein/team-platform",
        reason: null,
      },
    ]);
    executeProject.mockResolvedValue({
      projectId: "team-foundation",
      runner: "python-script-v1",
      exitCode: 0,
      timedOut: false,
      durationMs: 17,
      stdout: "runner-ok\n",
      stderr: "",
      outputTruncated: false,
    });

    render(<ProjectPanel projects={projects} />);

    fireEvent.click(await screen.findByRole("button", { name: "Run demo" }));

    expect(await screen.findByText("runner-ok")).toBeInTheDocument();
    expect(screen.getByText("Exit 0")).toBeInTheDocument();
    expect(executeProject).toHaveBeenCalledWith("team-foundation");
  });
});
