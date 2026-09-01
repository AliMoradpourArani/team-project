import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getProfessorGitHubDashboard } from "../api";
import GitHubContributionPanel from "./GitHubContributionPanel";

vi.mock("../api", () => ({
  getProfessorGitHubDashboard: vi.fn(),
}));

const getGitHub = vi.mocked(getProfessorGitHubDashboard);

describe("GitHubContributionPanel", () => {
  beforeEach(() => {
    getGitHub.mockReset();
  });

  it("renders linked contribution metrics and leaves unlinked members explicit", async () => {
    getGitHub.mockResolvedValue({
      status: "ok",
      message: null,
      repository: {
        fullName: "HoosseinRahimi/team-project",
        url: "https://github.com/HoosseinRahimi/team-project",
        defaultBranch: "main",
        openPullRequests: 1,
        lastPushedAt: "2026-09-01T20:00:00Z",
      },
      members: [
        {
          userId: "hossein",
          displayName: "Hossein",
          githubUsername: "HoosseinRahimi",
          linked: true,
          commits: 7,
          pullRequests: 3,
          openPullRequests: 1,
          mergedPullRequests: 2,
          latestContributionAt: "2026-09-01T20:00:00Z",
        },
        {
          userId: "ali",
          displayName: "Ali",
          githubUsername: null,
          linked: false,
          commits: 0,
          pullRequests: 0,
          openPullRequests: 0,
          mergedPullRequests: 0,
          latestContributionAt: null,
        },
      ],
      timeline: [
        {
          kind: "pull-request",
          userId: "hossein",
          githubUsername: "HoosseinRahimi",
          title: "#11 Add GitHub integration",
          url: "https://github.com/HoosseinRahimi/team-project/pull/11",
          occurredAt: "2026-09-01T20:00:00Z",
          detail: "merged PR",
        },
      ],
      generatedAt: "2026-09-01T20:01:00Z",
    });

    render(<GitHubContributionPanel />);

    expect(await screen.findByText("HoosseinRahimi/team-project")).toBeInTheDocument();
    expect(screen.getByText("@HoosseinRahimi")).toBeInTheDocument();
    expect(screen.getByText("GitHub not linked")).toBeInTheDocument();
    expect(screen.getByText("#11 Add GitHub integration")).toBeInTheDocument();
  });

  it("keeps the professor dashboard usable when GitHub is unavailable", async () => {
    getGitHub.mockResolvedValue({
      status: "unavailable",
      message: "GitHub integration is disabled for this environment.",
      repository: null,
      members: [],
      timeline: [],
      generatedAt: "2026-09-01T20:01:00Z",
    });

    render(<GitHubContributionPanel />);

    expect(
      await screen.findByText("GitHub integration is disabled for this environment."),
    ).toBeInTheDocument();
  });
});
