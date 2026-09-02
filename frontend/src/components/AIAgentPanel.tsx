import { useEffect, useMemo, useState } from "react";

import { createAIThread, deleteAIThread, getAIThreads, postAIMessage } from "../api";
import "../ai-agent.css";
import type { AIAgentReply, AIAgentThread } from "../ai-agent-types";

interface AIAgentPanelProps {
  projectId: string | null;
}

export default function AIAgentPanel({ projectId }: AIAgentPanelProps) {
  const [threads, setThreads] = useState<AIAgentThread[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [message, setMessage] = useState("");
  const [lastReply, setLastReply] = useState<AIAgentReply | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === activeId) ?? null,
    [activeId, threads],
  );

  async function refresh() {
    const next = await getAIThreads();
    setThreads(next);
    if (!next.some((thread) => thread.id === activeId)) setActiveId(next[0]?.id ?? "");
  }

  useEffect(() => {
    refresh().catch(() => setThreads([]));
  }, []);

  async function startThread() {
    setBusy(true);
    setError("");
    try {
      const thread = await createAIThread(projectId);
      setThreads((current) => [thread, ...current]);
      setActiveId(thread.id);
      setLastReply(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not create AI thread.");
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage() {
    if (!activeThread || !message.trim()) return;
    setBusy(true);
    setError("");
    try {
      const response = await postAIMessage(activeThread.id, message.trim());
      setLastReply(response);
      setThreads((current) =>
        current.map((thread) => (thread.id === response.thread.id ? response.thread : thread)),
      );
      setMessage("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "AI agent request failed.");
    } finally {
      setBusy(false);
    }
  }

  async function removeThread() {
    if (!activeThread) return;
    setBusy(true);
    try {
      await deleteAIThread(activeThread.id);
      const remaining = threads.filter((thread) => thread.id !== activeThread.id);
      setThreads(remaining);
      setActiveId(remaining[0]?.id ?? "");
      setLastReply(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ai-agent-panel" aria-labelledby="ai-agent-title">
      <div className="ai-agent-header">
        <div>
          <p className="eyebrow">Persistent agent</p>
          <h3 id="ai-agent-title">Project memory & chat</h3>
          <p>Keep context between sessions and replan from tracked work, health checks, and GitHub.</p>
        </div>
        <button type="button" className="secondary-button" onClick={startThread} disabled={busy}>
          New thread
        </button>
      </div>

      {threads.length > 0 ? (
        <div className="ai-agent-thread-tabs" role="tablist" aria-label="AI threads">
          {threads.map((thread) => (
            <button
              type="button"
              role="tab"
              aria-selected={thread.id === activeId}
              className={thread.id === activeId ? "active" : ""}
              key={thread.id}
              onClick={() => {
                setActiveId(thread.id);
                setLastReply(null);
              }}
            >
              {thread.title}
            </button>
          ))}
        </div>
      ) : (
        <div className="ai-agent-empty">
          No persistent thread yet. Start one to give the copilot memory across visits.
        </div>
      )}

      {activeThread ? (
        <>
          <div className="ai-agent-messages">
            {activeThread.messages.length === 0 ? (
              <p className="ai-agent-empty">Ask for a replan, blocker check, review, or next milestone.</p>
            ) : null}
            {activeThread.messages.map((item) => (
              <article className={`ai-agent-message ai-agent-${item.role}`} key={item.id}>
                <strong>{item.role === "assistant" ? "Copilot" : "You"}</strong>
                <p>{item.content}</p>
              </article>
            ))}
          </div>

          {lastReply ? (
            <div className="ai-agent-snapshot">
              <span>{lastReply.snapshot.progressPercent}% progress</span>
              <span>{lastReply.snapshot.overdueTasks.length} overdue</span>
              <span>{lastReply.snapshot.githubSignals.length} GitHub signals</span>
              <span>{lastReply.snapshot.findings.length} checks</span>
            </div>
          ) : null}

          {lastReply?.suggestedTasks.length ? (
            <div className="ai-agent-suggestions">
              <strong>Replanning suggestions</strong>
              {lastReply.suggestedTasks.map((task) => (
                <p key={`${task.date}-${task.title}`}>
                  {task.date} · {task.title}
                </p>
              ))}
            </div>
          ) : null}

          <div className="ai-agent-composer">
            <textarea
              rows={2}
              maxLength={4000}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Replan my week, check blockers, review what I finished…"
            />
            <button
              type="button"
              className="primary-button"
              disabled={busy || !message.trim()}
              onClick={sendMessage}
            >
              {busy ? "Thinking…" : "Send"}
            </button>
          </div>
          <button type="button" className="ai-agent-delete" onClick={removeThread} disabled={busy}>
            Delete thread
          </button>
        </>
      ) : null}

      {error ? <p className="ai-error">{error}</p> : null}
    </section>
  );
}
