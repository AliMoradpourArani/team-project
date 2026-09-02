import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createSubmissionRelease,
  getProfessorSubmissionDashboard,
  getSubmissionReleases,
  saveSubmissionSettings,
} from "../api";
import type { ProfessorSubmissionDashboardData } from "../types";
import ProfessorSubmissionPanel from "./ProfessorSubmissionPanel";

vi.mock("../api", () => ({
  getProfessorSubmissionDashboard: vi.fn(),
  getSubmissionReleases: vi.fn(),
  saveSubmissionSettings: vi.fn(),
  createSubmissionRelease: vi.fn(),
}));

const getDashboard = vi.mocked(getProfessorSubmissionDashboard);
const getReleases = vi.mocked(getSubmissionReleases);
const saveSettings = vi.mocked(saveSubmissionSettings);
const createRelease = vi.mocked(createSubmissionRelease);

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
      project: {
        id: "team-foundation",
        userId: "hossein",
        name: "Team Project Foundation",
        description: "Shared platform project.",
        technology: ["python", "react"],
        status: "active",
      },
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

describe("ProfessorSubmissionPanel", () => {
  beforeEach(() => {
    getDashboard.mockReset();
    getReleases.mockReset();
    saveSettings.mockReset();
    createRelease.mockReset();
    getDashboard.mockResolvedValue(dashboard);
    getReleases.mockResolvedValue([]);
  });

  it("updates the submission window", async () => {
    saveSettings.mockResolvedValue({
      ...dashboard.settings,
      isOpen: false,
      acceptingSubmissions: false,
    });

    render(<ProfessorSubmissionPanel />);

    expect(
      await screen.findByRole("heading", { name: "Final delivery control" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Accept project submissions"));
    fireEvent.click(screen.getByRole("button", { name: "Save submission settings" }));

    expect(saveSettings).toHaveBeenCalledWith({ isOpen: false, deadlineAt: null });
    expect(await screen.findByText("Submission settings saved.")).toBeInTheDocument();
  });

  it("freezes a release when every project is submitted and approved", async () => {
    createRelease.mockResolvedValue({
      id: 7,
      label: "Final submission",
      manifestDigest: "b".repeat(64),
      projectCount: 1,
      createdByUsername: "professor",
      createdAt: "2026-09-02 11:00:00",
      manifest: {},
    });

    render(<ProfessorSubmissionPanel />);

    expect(await screen.findByText("Ready to freeze release")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Release label"), {
      target: { value: "Final submission" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Freeze final release" }));

    expect(createRelease).toHaveBeenCalledWith("Final submission");
    expect(await screen.findByText("Release “Final submission” frozen.")).toBeInTheDocument();
  });
});
