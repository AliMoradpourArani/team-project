import { afterEach, describe, expect, it, vi } from "vitest";

import type { AIAgentReply } from "./ai-agent-types";
import { login, streamAIMessage, UnauthorizedError } from "./api";

const reply: AIAgentReply = {
  thread: {
    id: "thread-1",
    projectId: "team-foundation",
    title: "Project copilot",
    memory: "",
    createdAt: "2026-09-03T10:00:00Z",
    updatedAt: "2026-09-03T10:05:00Z",
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
        content: "Hello world",
        createdAt: "2026-09-03T10:05:00Z",
      },
    ],
  },
  reply: {
    id: 2,
    role: "assistant",
    content: "Hello world",
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

function sseEvent(event: object): string {
  return `data: ${JSON.stringify(event)}\n\n`;
}

function sseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
  return { ok: true, status: 200, body: stream } as unknown as Response;
}

async function loginWithMockedSession(fetchMock: ReturnType<typeof vi.fn>): Promise<void> {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: async () => ({ username: "hossein", role: "student", csrfToken: "csrf-token" }),
  } as unknown as Response);
  await login("hossein", "student-pass-123");
}

describe("streamAIMessage", () => {
  const fetchMock = vi.fn();

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it("streams deltas to the callback and resolves the final reply", async () => {
    vi.stubGlobal("fetch", fetchMock);
    await loginWithMockedSession(fetchMock);
    fetchMock.mockResolvedValueOnce(
      sseResponse([
        sseEvent({ type: "start", threadId: "thread-1" }) +
          sseEvent({ type: "delta", value: "Hello " }),
        sseEvent({ type: "delta", value: "world" }) + sseEvent({ type: "done", reply }),
      ]),
    );

    const deltas: string[] = [];
    const result = await streamAIMessage("thread-1", "Hi", (delta) => deltas.push(delta));

    expect(deltas).toEqual(["Hello ", "world"]);
    expect(result).toEqual(reply);

    const [url, init] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(url).toContain("/api/ai/threads/thread-1/messages/stream");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    expect(init.body).toBe(JSON.stringify({ content: "Hi" }));
    expect((init.headers as Headers).get("X-CSRF-Token")).toBe("csrf-token");
  });

  it("reassembles a stream event that is split across chunk boundaries", async () => {
    vi.stubGlobal("fetch", fetchMock);
    await loginWithMockedSession(fetchMock);
    fetchMock.mockResolvedValueOnce(
      sseResponse([
        sseEvent({ type: "start", threadId: "thread-1" }) + 'data: {"type":"delta","value":"He',
        'llo"}\n\n' + sseEvent({ type: "done", reply }),
      ]),
    );

    const deltas: string[] = [];
    const result = await streamAIMessage("thread-1", "Hi", (delta) => deltas.push(delta));

    expect(deltas).toEqual(["Hello"]);
    expect(result).toEqual(reply);
  });

  it("throws the message of a mid-stream error event", async () => {
    vi.stubGlobal("fetch", fetchMock);
    await loginWithMockedSession(fetchMock);
    fetchMock.mockResolvedValueOnce(
      sseResponse([
        sseEvent({ type: "start", threadId: "thread-1" }),
        sseEvent({ type: "error", message: "The AI reply could not be persisted." }),
      ]),
    );

    await expect(streamAIMessage("thread-1", "Hi", () => undefined)).rejects.toThrow(
      "The AI reply could not be persisted.",
    );
  });

  it("throws when the stream ends without a final reply", async () => {
    vi.stubGlobal("fetch", fetchMock);
    await loginWithMockedSession(fetchMock);
    fetchMock.mockResolvedValueOnce(sseResponse([sseEvent({ type: "delta", value: "Partial" })]));

    await expect(streamAIMessage("thread-1", "Hi", () => undefined)).rejects.toThrow(
      "The AI stream ended without a final reply.",
    );
  });

  it("throws when the browser cannot expose a stream body", async () => {
    vi.stubGlobal("fetch", fetchMock);
    await loginWithMockedSession(fetchMock);
    fetchMock.mockResolvedValueOnce({ ok: true, status: 200, body: null } as unknown as Response);

    await expect(streamAIMessage("thread-1", "Hi", () => undefined)).rejects.toThrow(
      "The AI stream is not available in this browser.",
    );
  });

  it("surfaces HTTP errors before the stream opens", async () => {
    vi.stubGlobal("fetch", fetchMock);
    await loginWithMockedSession(fetchMock);
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Session expired" }),
    } as unknown as Response);

    await expect(streamAIMessage("thread-1", "Hi", () => undefined)).rejects.toThrow(
      UnauthorizedError,
    );
    await expect(streamAIMessage("thread-1", "Hi", () => undefined)).rejects.toThrow(
      "Session expired",
    );
  });
});
