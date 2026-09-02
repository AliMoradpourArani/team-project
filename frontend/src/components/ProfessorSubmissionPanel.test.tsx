import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createSubmissionRelease,
  getProfessorDeliveryPreflight,
  getProfessorSubmissionDashboard,
  getSubmissionRelease,
  getSubmissionReleases,
  saveSubmissionSettings,
} from "../api";
import type { DeliveryPreflightData, ProfessorSubmissionDashboardData } from "../types";
import ProfessorSubmissionPanel from "./ProfessorSubmissionPanel";

vi.mock("../api", () => ({
  getProfessorSubmissionDashboard: vi.fn(),
  getProfessorDeliveryPreflight: vi.fn(),
  getSubmissionReleases: vi.fn(),
  getSubmissionRelease: vi.fn(),
  saveSubmissionSettings: vi.fn(),
  createSubmissionRelease: vi.fn(),
}));

const getDashboard = vi.mocked(getProfessorSubmissionDashboard);
const getPreflight = vi.mocked(getProfessorDeliveryPreflight);
const getReleases = vi.mocked(getSubmissionReleases);
const getRelease = vi.mocked(getSubmissionRelease);
const saveSettings = vi.mocked(saveSubmissionSettings);
const createRelease = vi.mocked(createSubmissionRelease);

const project = {
  id: "team-foundation",
  userId: "hossein",
  name: "Team Project Foundation",
  description: "Shared platform project.",
  technology: ["python", "react"],
  status: "active",
};

const dashboard: ProfessorSubmissionDashboardData = {
  settings: {
    isOpen: true,
    deadlineAt: null,
    acceptingSubmissions: true,
    updatedByUsername: "professor",
    updatedAt: "2026-09-02 10:00:00",
  },
  totalProjects: 1,
  submittedProjects: 1,
  pendingProjects: 0,
  approvedProjects: 1,
  releaseReady: true,
  releaseBlockedReason: null,
  items: [
    {
      project,
      latestSubmission: {
        id: 1,
        projectId: "team-foundation",
        userId: "hossein",
        submittedByUsername: "hossein",
        version: 1,
        snapshotDigest: "a".repeat(64),
        sourceFileCount: 4,
        sourceTotalBytes: 2048,
        reviewStatus: "approved",
        reviewTotalScore: 92,
        submittedAt: "2026-09-02 09:00:00",
      },
      review: {
        projectId: "team-foundation",
        reviewerUsername: "professor",
        status: "approved",
        functionalityScore: 28,
        codeQualityScore: 18,
        documentationScore: 13,
        integrationScore: 19,
        contributionScore: 14,
        totalScore: 92,
        feedback: "Approved.",
        updatedAt: "2026-09-02 09:30:00",
      },
    },
  ],
};

const preflight: DeliveryPreflightData = {
  status: "ready",
  releaseCandidateReady: true,
  totalProjects: 1,
  readyProjects: 1,
  blockingProjects: 0,
  blockerCount: 0,
  generatedAt: "2026-09-02T10:00:00+00:00",
  localCheckCommand: "make delivery-preflight",
  summary: "READY TO FREEZE RELEASE CANDIDATE",
  globalGates: [
    {
      key: "final-approval-order",
      label: "Final approvals cover frozen submissions",
      passed: true,
      blocking: true,
      detail: "Every latest frozen submission was followed by an approved professor review.",
      remediation: "Review after freeze.",
    },
  ],
  projects: [
    {
      project,
      status: "ready",
      latestSubmissionVersion: 1,
      reviewStatus: "approved",
      reviewAfterSubmission: true,
      gates: [],
    },
  ],
};

describe("ProfessorSubmissionPanel", () => {
  beforeEach(() => {
    getDashboard.mockReset();
    getPreflight.mockReset();
    getReleases.mockReset();
    getRelease.mockReset();
    saveSettings.mockReset();
    createRelease.mockReset();
    getDashboard.mockResolvedValue(dashboard);
    getPreflight.mockResolvedValue(preflight);
    getReleases.mockResolvedValue([]);
  });

  it("updates the submission window and shows the shared preflight", async () => {
    saveSettings.mockResolvedValue({
      ...dashboard.settings,
      isOpen: false,
      acceptingSubmissions: false,
    });

    render(<ProfessorSubmissionPanel />);

    expect(
      await screen.findByRole("heading", { name: "Final delivery control" }),
    ).toBeInTheDocument();
    expect(screen.getByText("READY TO FREEZE RELEASE CANDIDATE")).toBeInTheDocument();
    expect(screen.getByText("make delivery-preflight")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Accept project submissions"));
    fireEvent.click(screen.getByRole("button", { name: "Save submission settings" }));

    expect(saveSettings).toHaveBeenCalledWith({ isOpen: false, deadlineAt: null });
    expect(await screen.findByText("Submission settings saved.")).toBeInTheDocument();
  });

  it("freezes a release candidate only when preflight is ready", async () => {
    createRelease.mockResolvedValue({
      id: 7,
      label: "RC1",
      manifestDigest: "b".repeat(64),
      projectCount: 1,
      createdByUsername: "professor",
      createdAt: "2026-09-02 11:00:00",
      manifest: {},
    });

    render(<ProfessorSubmissionPanel />);

    expect(await screen.findByText("Ready to freeze release candidate")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Release candidate label"), {
      target: { value: "RC1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Freeze release candidate" }));

    expect(createRelease).toHaveBeenCalledWith("RC1");
    expect(await screen.findByText("Release candidate “RC1” frozen.")).toBeInTheDocument();
  });

  it("disables release candidate freezing when preflight is blocked", async () => {
    getPreflight.mockResolvedValue({
      ...preflight,
      status: "blocked",
      releaseCandidateReady: false,
      readyProjects: 0,
      blockingProjects: 1,
      blockerCount: 2,
      summary: "BLOCKED: 2 final-delivery gate(s) still require attention",
      projects: [
        {
          ...preflight.projects[0],
          status: "blocked",
          reviewAfterSubmission: false,
          gates: [
            {
              key: "approval-sequence",
              label: "Approval covers frozen version",
              passed: false,
              blocking: true,
              detail: "Approval predates the frozen submission.",
              remediation: "Freeze first, then approve.",
            },
          ],
        },
      ],
    });

    render(<ProfessorSubmissionPanel />);

    expect(
      await screen.findByRole("heading", { name: /BLOCKED: 2 final-delivery gate/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Freeze release candidate" })).toBeDisabled();
    expect(screen.getByText("Freeze first, then approve.")).toBeInTheDocument();
  });
});
