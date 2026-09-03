import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AIAgentReply, AIAgentSnapshot, AIAgentThread } from "../ai-agent-types";
import AIAgentPanel from "./AIAgentPanel";

vi.mock("../api", () => ({
  createAIThread: vi.fn(),
  deleteAIThread: vi.fn(),
  getAIAgentSnapshot: vi.fn(),
  getAIDailyBrief: vi.fn(),
  getAIHealth: vi.fn(),
  getAIMultiAgentReview: vi.fn(),
  getAIOrchestration: vi.fn(),
  getAIThreads: vi.fn(),
  getAIWeeklyBrief: vi.fn(),
  indexAIRepository: vi.fn(),
  refreshAINotifications: vi.fn(),
  replanAIThread: vi.fn(),
  streamAIMessage: vi.fn(),
  syncAIProgress: vi.fn(),
}));

import { getAIAgentSnapshot, getAIThreads, streamAIMessage } from "../api";

const getThreads = vi.mocked(getAIThreads);
const getSnapshot = vi.mocked(getAIAgentSnapshot);
const streamMessage = vi.mocked(streamAIMessage);

const thread: AIAgentThread = {
  id: "thread-1",
  projectId: "team-foundation",
  title: "Release agent",
  memory: "",
  createdAt: "2026-09-03T10:00:00Z",
  updatedAt: "2026-09-03T10:05:00Z",
  messages: [],
};

const snapshot: AIAgentSnapshot = {
  progressPercent: 0,
  overdueTasks: [],
  githubSignals: [],
  findings: [],
};

const reply: AIAgentReply = {
  thread: {
    ...thread,
    messages: [
      {
        id: 1,
        role: "user",
        content: "What should I focus on next?",
        createdAt: "2026-09-03T10:04:00Z",
      },
      {
        id: 2,
        role: "assistant",
        content: "Working on it.",
        createdAt: "2026-09-03T10:05:00Z",
      },
    ],
  },
  reply: {
    id: 2,
    role: "assistant",
    content: "Working on it.",
    createdAt: "2026-09-03T10:05:00Z",
  },
  snapshot: {
    progressPercent: 42,
    overdueTasks: [],
    githubSignals: [],
    findings: [],
  },
  suggestedTasks: [],
  provider: "local",
  model: null,
  providerMessage: null,
};

async function typeAndSend(text: string): Promise<void> {
  const composer = await screen.findByPlaceholderText(
    "Replan my week, review the implementation, debug blockers…",
  );
  fireEvent.change(composer, { target: { value: text } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
  });
}

describe("AIAgentPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getThreads.mockResolvedValue([thread]);
    getSnapshot.mockResolvedValue(snapshot);
    streamMessage.mockResolvedValue(reply);
  });

  it("streams a reply and applies the final thread and snapshot", async () => {
    streamMessage.mockImplementation(async (_threadId, _content, onDelta) => {
      onDelta("Working ");
      onDelta("on it.");
      return reply;
    });

    render(<AIAgentPanel projectId="team-foundation" />);
    await typeAndSend("What should I focus on next?");

    expect(await screen.findByText("Response engine: local")).toBeInTheDocument();
    expect(screen.getByText("42% progress")).toBeInTheDocument();
    expect(screen.getByText("Working on it.")).toBeInTheDocument();
    expect(streamMessage).toHaveBeenCalledWith(
      "thread-1",
      "What should I focus on next?",
      expect.any(Function),
    );

    const composer = screen.getByPlaceholderText(
      "Replan my week, review the implementation, debug blockers…",
    );
    expect(composer).toHaveValue("");
  });

  it("keeps the draft and shows the error message when the stream fails", async () => {
    streamMessage.mockRejectedValue(new Error("The AI stream broke"));

    render(<AIAgentPanel projectId="team-foundation" />);
    await typeAndSend("What should I focus on next?");

    expect(await screen.findByText("The AI stream broke")).toBeInTheDocument();
    const composer = screen.getByPlaceholderText(
      "Replan my week, review the implementation, debug blockers…",
    );
    expect(composer).toHaveValue("What should I focus on next?");
  });

  it("offers thread creation when no threads exist yet", async () => {
    getThreads.mockResolvedValue([]);

    render(<AIAgentPanel projectId={null} />);
    await act(async () => {});

    expect(
      await screen.findByText(
        "No persistent thread yet. Start one to give the copilot memory across visits.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Send" })).not.toBeInTheDocument();
  });
});
