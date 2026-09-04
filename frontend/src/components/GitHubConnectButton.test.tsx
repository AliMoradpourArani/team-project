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

  it("shows the linked GitHub id in green in read-only members view", () => {
    render(<GitHubConnectButton userId="ali" initialUsername="octocat" />);

    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("connected");
    expect(screen.getByText("@octocat")).toBeInTheDocument();
  });

  it("shows a connect affordance when the member has no linked GitHub id", () => {
    render(<GitHubConnectButton userId="ali" initialUsername={null} />);

    expect(screen.getByText("Connect GitHub")).toBeInTheDocument();
  });

  it("automatically loads the GitHub service status and shows the id when connected", async () => {
    mockStatus.mockResolvedValue({
      connected: true,
      username: "octocat",
      syncedAt: "2026-09-01T00:00:00Z",
      canPush: false,
    });

    render(<GitHubConnectButton userId="ali" canConnect />);

    expect(await screen.findByText("@octocat")).toBeInTheDocument();
    expect(mockStatus).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("status")).toHaveClass("connected");
  });

  it("connects through the GitHub service and turns green with the new id", async () => {
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
    fireEvent.change(screen.getByPlaceholderText("octocat"), { target: { value: "octocat" } });
    fireEvent.click(screen.getByRole("button", { name: "Connect" }));

    expect(await screen.findByText("@octocat")).toBeInTheDocument();
    expect(mockConnect).toHaveBeenCalledWith("octocat", null);
  });
});
