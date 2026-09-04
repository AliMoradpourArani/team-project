import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { connectGitHub, getGitHubStatus } from "../api";
import GitHubConnectButton from "./GitHubConnectButton";

vi.mock("../api", () => ({
  getGitHubStatus: vi.fn(),
  connectGitHub: vi.fn(),
}));

const mockStatus = vi.mocked(getGitHubStatus);
const mockConnect = vi.mocked(connectGitHub);

describe("GitHubConnectButton", () => {
  beforeEach(() => {
    mockStatus.mockReset();
    mockConnect.mockReset();
  });

  it("shows the linked GitHub id in a green box with a profile link in the professor view", () => {
    render(<GitHubConnectButton userId="ali" initialUsername="octocat" />);

    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("gh-status-box", "is-linked");
    expect(badge.tagName).not.toBe("BUTTON");
    const profileLink = screen.getByRole("link", { name: "@octocat" });
    expect(profileLink).toHaveAttribute("href", "https://github.com/octocat");
    expect(profileLink).toHaveAttribute("target", "_blank");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows a red not-connected box with no button in the professor view", () => {
    render(<GitHubConnectButton userId="ali" initialUsername={null} />);

    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("gh-status-box", "is-unlinked");
    expect(screen.getByText("Not connected yet")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(mockStatus).not.toHaveBeenCalled();
  });

  it("automatically loads the GitHub service status and shows only the id when connected", async () => {
    mockStatus.mockResolvedValue({
      connected: true,
      username: "octocat",
      syncedAt: "2026-09-01T00:00:00Z",
      canPush: false,
    });

    render(<GitHubConnectButton userId="ali" canConnect />);

    expect(await screen.findByText("@octocat")).toBeInTheDocument();
    expect(mockStatus).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("status")).toHaveClass("gh-status-box", "is-linked");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("connects through the GitHub service and then shows only the new id", async () => {
    mockStatus.mockResolvedValue({
      connected: false,
      username: null,
      syncedAt: null,
      canPush: false,
    });
    mockConnect.mockResolvedValue({
      connected: true,
      username: "octocat",
      syncedAt: "2026-09-01T00:00:00Z",
      canPush: false,
    });

    render(<GitHubConnectButton userId="ali" canConnect />);

    fireEvent.click(await screen.findByRole("button", { name: "Connect GitHub" }));
    const usernameInput = screen.getByPlaceholderText("octocat");
    expect(usernameInput).toHaveAttribute(
      "title",
      "Type your GitHub username, for example: octocat.",
    );
    expect(
      screen.getByText("Type your GitHub username, for example: octocat."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("A token lets you push commits and see private repositories."),
    ).toBeInTheDocument();
    fireEvent.change(usernameInput, { target: { value: "octocat" } });
    fireEvent.click(screen.getByRole("button", { name: "Connect" }));

    expect(await screen.findByText("@octocat")).toBeInTheDocument();
    expect(mockConnect).toHaveBeenCalledWith("octocat", null);
    expect(screen.getByRole("status")).toHaveClass("gh-status-box", "is-linked");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
