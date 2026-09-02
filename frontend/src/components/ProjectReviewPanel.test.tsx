import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { deleteProjectReview, getProjectReview, saveProjectReview } from "../api";
import ProjectReviewPanel from "./ProjectReviewPanel";

vi.mock("../api", () => ({
  getProjectReview: vi.fn(),
  saveProjectReview: vi.fn(),
  deleteProjectReview: vi.fn(),
}));

const getReview = vi.mocked(getProjectReview);
const saveReview = vi.mocked(saveProjectReview);
const deleteReview = vi.mocked(deleteProjectReview);

const approvedReview = {
  projectId: "team-foundation",
  reviewerUsername: "professor",
  status: "approved" as const,
  functionalityScore: 30,
  codeQualityScore: 18,
  documentationScore: 13,
  integrationScore: 19,
  contributionScore: 14,
  totalScore: 94,
  feedback: "Approved with strong integration work.",
  updatedAt: "2026-09-02 08:00:00",
};

describe("ProjectReviewPanel", () => {
  beforeEach(() => {
    getReview.mockReset();
    saveReview.mockReset();
    deleteReview.mockReset();
  });

  it("shows professor feedback read-only to a student", async () => {
    getReview.mockResolvedValue(approvedReview);

    render(<ProjectReviewPanel projectId="team-foundation" role="student" />);

    expect(await screen.findByRole("heading", { name: "Approved" })).toBeInTheDocument();
    expect(screen.getByText("94/100")).toBeInTheDocument();
    expect(screen.getByText("Approved with strong integration work.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save review" })).not.toBeInTheDocument();
  });

  it("lets a professor create a rubric review", async () => {
    getReview.mockResolvedValue(null);
    saveReview.mockResolvedValue({
      ...approvedReview,
      status: "in-review",
      functionalityScore: 25,
      codeQualityScore: 16,
      documentationScore: 11,
      integrationScore: 17,
      contributionScore: 12,
      totalScore: 81,
      feedback: "Good first review.",
    });

    render(<ProjectReviewPanel projectId="team-foundation" role="professor" />);

    expect(await screen.findByRole("heading", { name: "Start review" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Functionality"), { target: { value: "25" } });
    fireEvent.change(screen.getByLabelText("Code quality"), { target: { value: "16" } });
    fireEvent.change(screen.getByLabelText("Documentation"), { target: { value: "11" } });
    fireEvent.change(screen.getByLabelText("Integration"), { target: { value: "17" } });
    fireEvent.change(screen.getByLabelText("Contribution"), { target: { value: "12" } });
    fireEvent.change(screen.getByLabelText("Feedback"), {
      target: { value: "Good first review." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save review" }));

    expect(await screen.findByText("Review saved.")).toBeInTheDocument();
    expect(saveReview).toHaveBeenCalledWith("team-foundation", {
      status: "in-review",
      functionalityScore: 25,
      codeQualityScore: 16,
      documentationScore: 11,
      integrationScore: 17,
      contributionScore: 12,
      feedback: "Good first review.",
    });
    expect(screen.getByText("81/100")).toBeInTheDocument();
  });
});
