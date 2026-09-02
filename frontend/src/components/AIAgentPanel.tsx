import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createAIThread,
  deleteAIThread,
  getAIAgentSnapshot,
  getAIDailyBrief,
  getAIHealth,
  getAIMultiAgentReview,
  getAIOrchestration,
  getAIThreads,
  getAIWeeklyBrief,
  indexAIRepository,
  postAIMessage,
  refreshAINotifications,
  replanAIThread,
  syncAIProgress,
} from "../api";
import "../ai-agent.css";
import type {
  AIAgentReply,
  AIAgentReplanResponse,
  AIAgentSnapshot,
  AIAgentThread,
  AIDailyBrief,
  AIHealthScore,
  AIMultiAgentReview,
  AIOrchestrationResult,
  AIRepoIndexResult,
  AIWeeklyBrief,
} from "../ai-agent-types";

interface AIAgentPanelProps {
  projectId: string | null;
}

export default function AIAgentPanel({ projectId }: AIAgentPanelProps) {
  const [threads, setThreads] = useState<AIAgentThread[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [message, setMessage] = useState("");
  const [lastReply, setLastReply] = useState<AIAgentReply | null>(null);
  const [snapshot, setSnapshot] = useState<AIAgentSnapshot | null>(null);
  const [brief, setBrief] = useState<AIDailyBrief | null>(null);
  const [weekly, setWeekly] = useState<AIWeeklyBrief | null>(null);
  const [health, setHealth] = useState<AIHealthScore | null>(null);
  const [replan, setReplan] = useState<AIAgentReplanResponse | null>(null);
  const [review, setReview] = useState<AIMultiAgentReview | null>(null);
  const [orchestration, setOrchestration] = useState<AIOrchestrationResult | null>(null);
  const [repoIndex, setRepoIndex] = useState<AIRepoIndexResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === activeId) ?? null,
    [activeId, threads],
  );

  const refresh = useCallback(async () => {
    const next = await getAIThreads();
    setThreads(next);
    setActiveId((current) =>
      next.some((thread) => thread.id === current) ? current : (next[0]?.id ?? ""),
    );
  }, []);

  const loadProjectIntelligence = useCallback(async () => {
    const [nextBrief, nextWeekly, nextHealth, nextReview, nextOrchestration] = await Promise.all([
      getAIDailyBrief(projectId),
      getAIWeeklyBrief(projectId),
      getAIHealth(projectId),
      getAIMultiAgentReview(projectId),
      getAIOrchestration(projectId),
    ]);
    setBrief(nextBrief);
    setWeekly(nextWeekly);
    setHealth(nextHealth);
    setReview(nextReview);
    setOrchestration(nextOrchestration);
  }, [projectId]);

  useEffect(() => {
    refresh().catch(() => setThreads([]));
    loadProjectIntelligence().catch(() => {
      setBrief(null);
      setWeekly(null);
      setHealth(null);
      setReview(null);
      setOrchestration(null);
    });
  }, [loadProjectIntelligence, refresh]);

  useEffect(() => {
    if (!activeId) {
      setSnapshot(null);
      return;
    }
    getAIAgentSnapshot(activeId)
      .then(setSnapshot)
      .catch(() => setSnapshot(null));
  }, [activeId]);

  async function startThread() {
    setBusy(true);
    setError("");
    try {
      const thread = await createAIThread(projectId);
      setThreads((current) => [thread, ...current]);
      setActiveId(thread.id);
      setLastReply(null);
      setReplan(null);
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Could not create AI thread.",
      );
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
      setSnapshot(response.snapshot);
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

  async function runReplan(applyTasks: boolean) {
    if (!activeThread) return;
    setBusy(true);
    setError("");
    try {
      const response = await replanAIThread(activeThread.id, applyTasks);
      setReplan(response);
      setSnapshot(response.snapshot);
      await loadProjectIntelligence();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Replanning failed.");
    } finally {
      setBusy(false);
    }
  }

  async function buildRepoIndex() {
    setBusy(true);
    setError("");
    try {
      const result = await indexAIRepository(projectId);
      setRepoIndex(result);
      await loadProjectIntelligence();
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Repository indexing failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function synchronizeProgress() {
    setBusy(true);
    setError("");
    try {
      const result = await syncAIProgress(projectId, true);
      await refreshAINotifications(projectId);
      await loadProjectIntelligence();
      if (result.changes.length === 0) {
        setError("No GitHub evidence required a task status change.");
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Progress sync failed.");
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
      setReplan(null);
    } finally {
      setBusy(false);
    }
  }

  const visibleSnapshot = lastReply?.snapshot ?? snapshot;

  return (
    <section className="ai-agent-panel" aria-labelledby="ai-agent-title">
      <div className="ai-agent-header">
        <div>
          <p className="eyebrow">AI project operating system</p>
          <h3 id="ai-agent-title">Project intelligence cockpit</h3>
          <p>
            Persistent context, repository RAG, GitHub evidence, governed actions, progress sync,
            debugging, health scoring, and specialist agents.
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={startThread} disabled={busy}>
          New thread
        </button>
      </div>

      {health ? (
        <div className="ai-agent-brief">
          <strong>Project health {health.overall}/100</strong>
          <div className="ai-agent-snapshot">
            <span>Delivery {health.delivery}</span>
            <span>Code {health.code}</span>
            <span>Security {health.security}</span>
            <span>Tests {health.tests}</span>
            <span>Schedule {health.schedule}</span>
            <span>Docs {health.documentation}</span>
          </div>
          {health.reasons[0] ? <p>{health.reasons[0]}</p> : null}
        </div>
      ) : null}

      {brief ? (
        <div className="ai-agent-brief">
          <strong>{brief.headline}</strong>
          <div className="ai-agent-snapshot">
            <span>{brief.overdueCount} overdue</span>
            <span>{brief.githubSignalCount} GitHub signals</span>
            <span>{brief.blockers.length} blockers</span>
          </div>
          {brief.priorities.length > 0 ? (
            <p>Today: {brief.priorities.slice(0, 3).join(" · ")}</p>
          ) : null}
        </div>
      ) : null}

      {weekly ? (
        <div className="ai-agent-brief">
          <strong>Weekly intelligence</strong>
          <p>{weekly.headline}</p>
          <div className="ai-agent-snapshot">
            <span>{weekly.completedTasks} completed</span>
            <span>{weekly.inProgressTasks} in progress</span>
            <span>{weekly.overdueTasks} overdue</span>
            <span>{weekly.githubSignals} GitHub signals</span>
          </div>
        </div>
      ) : null}

      <div className="ai-agent-actions">
        <button type="button" className="secondary-button" onClick={buildRepoIndex} disabled={busy}>
          Index repository
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={synchronizeProgress}
          disabled={busy}
        >
          Sync GitHub progress
        </button>
      </div>

      {repoIndex ? (
        <p className="ai-agent-provider">
          Repository index: {repoIndex.filesIndexed} files · {repoIndex.chunksIndexed} chunks
        </p>
      ) : null}

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
                setReplan(null);
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
          <div className="ai-agent-actions">
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={() => runReplan(false)}
            >
              Preview replan
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={() => runReplan(true)}
            >
              Apply replan tasks
            </button>
          </div>

          <div className="ai-agent-messages">
            {activeThread.messages.length === 0 ? (
              <p className="ai-agent-empty">
                Ask for a roadmap, blocker check, code review, debug pass, or next milestone.
              </p>
            ) : null}
            {activeThread.messages.map((item) => (
              <article className={`ai-agent-message ai-agent-${item.role}`} key={item.id}>
                <strong>{item.role === "assistant" ? "Copilot" : "You"}</strong>
                <p>{item.content}</p>
              </article>
            ))}
          </div>

          {lastReply ? (
            <p className="ai-agent-provider">
              Response engine: {lastReply.provider}
              {lastReply.model ? ` · ${lastReply.model}` : ""}
            </p>
          ) : null}

          {visibleSnapshot ? (
            <div className="ai-agent-snapshot">
              <span>{visibleSnapshot.progressPercent}% progress</span>
              <span>{visibleSnapshot.overdueTasks.length} overdue</span>
              <span>{visibleSnapshot.githubSignals.length} GitHub signals</span>
              <span>{visibleSnapshot.findings.length} checks</span>
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

          {replan ? (
            <div className="ai-agent-suggestions">
              <strong>{replan.summary}</strong>
              {replan.tasks.map((task) => (
                <p key={`${task.date}-${task.title}`}>
                  {task.date} · {task.title}
                </p>
              ))}
              {replan.appliedActivities.length > 0 ? (
                <p>{replan.appliedActivities.length} task(s) added to tracked work.</p>
              ) : null}
            </div>
          ) : null}

          <div className="ai-agent-composer">
            <textarea
              rows={2}
              maxLength={4000}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Replan my week, review the implementation, debug blockers…"
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

      {orchestration ? (
        <div className="ai-agent-review">
          <strong>Multi-agent coordinator</strong>
          <p>{orchestration.executiveSummary}</p>
          {orchestration.nextActions.slice(0, 4).map((action) => (
            <p key={action}>Next: {action}</p>
          ))}
        </div>
      ) : null}

      {review ? (
        <div className="ai-agent-review">
          <strong>7-agent review</strong>
          <p>{review.executiveSummary}</p>
          <div className="ai-agent-specialists">
            {review.results.map((result) => (
              <article key={result.specialist}>
                <strong>{result.specialist}</strong>
                <p>{result.summary}</p>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      {error ? <p className="ai-error">{error}</p> : null}
    </section>
  );
}
