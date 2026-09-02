import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { getProfessorReviewQueue } from "../api";
import ProfessorReviewQueue from "./ProfessorReviewQueue";

vi.mock("../api", () => ({
  getProfessorReviewQueue: vi.fn(),
}));

const getQueue = vi.mocked(getProfessorReviewQueue);

describe("ProfessorReviewQueue", () => {
  it("shows review counts and project links", async () => {
    getQueue.mockResolvedValue({
      totalProjects: 2,
      pending: 1,
      inReview: 0,
      changesRequested: 0,
      approved: 1,
      items: [
        {
          project: {
            id: "team-foundation",
            userId: "hossein",
            name: "Team Project Foundation",
            description: "Shared platform",
            technology: ["Python"],
            status: "active",
          },
          review: {
            projectId: "team-foundation",
            reviewerUsername: "professor",
            status: "approved",
            functionalityScore: 30,
            codeQualityScore: 18,
            documentationScore: 13,
            integrationScore: 19,
            contributionScore: 14,
            totalScore: 94,
            feedback: "Approved.",
            updatedAt: "2026-09-02 08:00:00",
          },
        },
        {
          project: {
            id: "ali-project",
            userId: "ali",
            name: "Ali Project",
            description: "Second project",
            technology: ["HTML"],
            status: "active",
          },
          review: null,
        },
      ],
    });

    render(<ProfessorReviewQueue />);

    expect(
      await screen.findByRole("heading", { name: "Project review queue" }),
    ).toBeInTheDocument();
    expect(screen.getByText("94/100")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Team Project Foundation/ })).toHaveAttribute(
      "href",
      "/projects/team-foundation",
    );
    expect(screen.getByRole("link", { name: /Ali Project/ })).toHaveAttribute(
      "href",
      "/projects/ali-project",
    );
  });
});
