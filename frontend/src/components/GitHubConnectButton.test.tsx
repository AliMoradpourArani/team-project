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

  it("shows the linked GitHub id as non-clickable text in the professor view", () => {
    render(<GitHubConnectButton userId="ali" initialUsername="octocat" />);

    const badge = screen.getByRole("status");
    expect(screen.getByText("@octocat")).toBeInTheDocument();
    expect(badge.tagName).not.toBe("BUTTON");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows a not-connected note with no button in the professor view", () => {
    render(<GitHubConnectButton userId="ali" initialUsername={null} />);

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
    fireEvent.change(screen.getByPlaceholderText("octocat"), {
      target: { value: "octocat" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Connect" }));

    expect(await screen.findByText("@octocat")).toBeInTheDocument();
    expect(mockConnect).toHaveBeenCalledWith("octocat", null);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
