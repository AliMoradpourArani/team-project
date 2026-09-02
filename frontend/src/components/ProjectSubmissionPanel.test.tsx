import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getProjectSubmissionStatus, submitProject } from "../api";
import type { ProjectSubmission, ProjectSubmissionStatus } from "../types";
import ProjectSubmissionPanel from "./ProjectSubmissionPanel";

vi.mock("../api", () => ({
  getProjectSubmissionStatus: vi.fn(),
  submitProject: vi.fn(),
}));

const getStatus = vi.mocked(getProjectSubmissionStatus);
const submit = vi.mocked(submitProject);

const settings = {
  isOpen: true,
  deadlineAt: null,
  acceptingSubmissions: true,
  updatedByUsername: null,
  updatedAt: "2026-09-02 09:00:00",
};

const frozen: ProjectSubmission = {
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
  submittedAt: "2026-09-02 10:00:00",
};

function status(latest: ProjectSubmission | null = null): ProjectSubmissionStatus {
  return {
    settings,
    latestSubmission: latest,
    historyCount: latest ? 1 : 0,
    canSubmit: true,
    blockedReason: null,
  };
}

describe("ProjectSubmissionPanel", () => {
  beforeEach(() => {
    getStatus.mockReset();
    submit.mockReset();
  });

  it("lets a student create a frozen submission", async () => {
    getStatus.mockResolvedValueOnce(status()).mockResolvedValueOnce(status(frozen));
    submit.mockResolvedValue(frozen);

    render(<ProjectSubmissionPanel projectId="team-foundation" role="student" />);

    const button = await screen.findByRole("button", { name: "Submit frozen snapshot" });
    fireEvent.click(button);

    expect(await screen.findByText("Submission v1 frozen successfully.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Frozen submission · v1" })).toBeInTheDocument();
    expect(screen.getByText("92/100", { exact: false })).toBeInTheDocument();
    expect(submit).toHaveBeenCalledWith("team-foundation");
  });

  it("keeps professor submission view read-only", async () => {
    getStatus.mockResolvedValue(status(frozen));

    render(<ProjectSubmissionPanel projectId="team-foundation" role="professor" />);

    expect(
      await screen.findByRole("heading", { name: "Frozen submission · v1" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Professor view · submission history is immutable."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Submit/ })).not.toBeInTheDocument();
  });
});
