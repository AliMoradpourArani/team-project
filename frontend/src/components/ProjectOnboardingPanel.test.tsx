import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getProjectOnboarding } from "../api";
import type { ProjectOnboarding } from "../types";
import ProjectOnboardingPanel from "./ProjectOnboardingPanel";

vi.mock("../api", () => ({
  getProjectOnboarding: vi.fn(),
}));

const getOnboarding = vi.mocked(getProjectOnboarding);

const ready: ProjectOnboarding = {
  projectId: "team-foundation",
  userId: "hossein",
  name: "Team Project Foundation",
  status: "ready",
  readyForSubmission: true,
  completedGates: 6,
  totalGates: 6,
  expectedMetadataPath: "data/projects/team-foundation.json",
  expectedRepositoryPath: "projects/hossein/team-platform",
  localCheckCommand: "make project-check PROJECT_ID=team-foundation",
  nextAction: "Integration gates are complete. Open a normal feature PR.",
  gates: [
    {
      key: "manifest",
      label: "Manifest",
      passed: true,
      blocking: true,
      detail: "project.json is valid.",
      remediation: "Add a valid project.json.",
    },
  ],
  supportedContracts: [
    {
      projectType: "cli",
      runner: "python-script-v1",
      demoMode: "execute",
      entryPointExample: "main.py",
    },
  ],
};

describe("ProjectOnboardingPanel", () => {
  beforeEach(() => getOnboarding.mockReset());

  it("shows a ready project and its local validation command", async () => {
    getOnboarding.mockResolvedValue(ready);

    render(<ProjectOnboardingPanel projectId="team-foundation" role="student" />);

    expect(await screen.findByText("ready")).toBeInTheDocument();
    expect(screen.getByText("6/6 blocking gates complete")).toBeInTheDocument();
    expect(screen.getByText("make project-check PROJECT_ID=team-foundation")).toBeInTheDocument();
    expect(
      screen.getByText(/Integration-ready for the Phase 9 submission flow/),
    ).toBeInTheDocument();
  });

  it("shows remediation and a read-only professor label for pending work", async () => {
    getOnboarding.mockResolvedValue({
      ...ready,
      status: "pending",
      readyForSubmission: false,
      completedGates: 5,
      gates: [
        {
          key: "readme",
          label: "README",
          passed: false,
          blocking: true,
          detail: "README.md is required.",
          remediation: "Add README.md with demo instructions.",
        },
      ],
      nextAction: "Add README.md with demo instructions.",
    });

    render(<ProjectOnboardingPanel projectId="team-foundation" role="professor" />);

    expect(await screen.findByText("pending")).toBeInTheDocument();
    expect(screen.getAllByText("Add README.md with demo instructions.")).toHaveLength(2);
    expect(screen.getByText("Read-only readiness")).toBeInTheDocument();
  });
});
