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
  refreshAINotifications,
  replanAIThread,
  streamAIMessage,
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
import { useI18n } from "../i18n";

interface AIAgentPanelProps {
  projectId: string | null;
}

export default function AIAgentPanel({ projectId }: AIAgentPanelProps) {
  const { t } = useI18n();
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
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [pendingMessage, setPendingMessage] = useState("");
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
      setStreamingText("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("ag.createError"));
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage() {
    if (!activeThread || !message.trim()) return;
    const sent = message.trim();
    setBusy(true);
    setStreaming(true);
    setStreamingText("");
    setPendingMessage(sent);
    setError("");
    try {
      const response = await streamAIMessage(activeThread.id, sent, (delta) =>
        setStreamingText((current) => current + delta),
      );
      setStreaming(false);
      setStreamingText("");
      setLastReply(response);
      setSnapshot(response.snapshot);
      setThreads((current) =>
        current.map((thread) => (thread.id === response.thread.id ? response.thread : thread)),
      );
      setMessage("");
    } catch (requestError) {
      // Keep any partially streamed reply visible when the stream fails.
      setStreaming(false);
      setError(requestError instanceof Error ? requestError.message : t("ag.requestError"));
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
      setError(requestError instanceof Error ? requestError.message : t("ag.replanError"));
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
      setError(requestError instanceof Error ? requestError.message : t("ag.indexError"));
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
        setError(t("ag.noStatusChange"));
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("ag.syncError"));
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
          <p className="eyebrow">{t("ag.eyebrow")}</p>
          <h3 id="ai-agent-title">{t("ag.cockpit")}</h3>
          <p>{t("ag.description")}</p>
        </div>
        <button type="button" className="secondary-button" onClick={startThread} disabled={busy}>
          {t("ag.newThread")}
        </button>
      </div>

      {health ? (
        <div className="ai-agent-brief">
          <strong>{t("ag.health", { score: health.overall })}</strong>
          <div className="ai-agent-snapshot">
            <span>{t("ag.delivery", { score: health.delivery })}</span>
            <span>{t("ag.code", { score: health.code })}</span>
            <span>{t("ag.security", { score: health.security })}</span>
            <span>{t("ag.tests", { score: health.tests })}</span>
            <span>{t("ag.schedule", { score: health.schedule })}</span>
            <span>{t("ag.docs", { score: health.documentation })}</span>
          </div>
          {health.reasons[0] ? <p>{health.reasons[0]}</p> : null}
        </div>
      ) : null}

      {brief ? (
        <div className="ai-agent-brief">
          <strong>{brief.headline}</strong>
          <div className="ai-agent-snapshot">
            <span>{t("ag.overdue", { count: brief.overdueCount })}</span>
            <span>{t("ag.githubSignals", { count: brief.githubSignalCount })}</span>
            <span>{t("ag.blockers", { count: brief.blockers.length })}</span>
          </div>
          {brief.priorities.length > 0 ? (
            <p>{t("ag.today", { items: brief.priorities.slice(0, 3).join(" · ") })}</p>
          ) : null}
        </div>
      ) : null}

      {weekly ? (
        <div className="ai-agent-brief">
          <strong>{t("ag.weeklyIntel")}</strong>
          <p>{weekly.headline}</p>
          <div className="ai-agent-snapshot">
            <span>{t("ag.completed", { count: weekly.completedTasks })}</span>
            <span>{t("ag.inProgress", { count: weekly.inProgressTasks })}</span>
            <span>{t("ag.overdue", { count: weekly.overdueTasks })}</span>
            <span>{t("ag.githubSignals", { count: weekly.githubSignals })}</span>
          </div>
        </div>
      ) : null}

      <div className="ai-agent-actions">
        <button type="button" className="secondary-button" onClick={buildRepoIndex} disabled={busy}>
          {t("ag.indexRepo")}
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={synchronizeProgress}
          disabled={busy}
        >
          {t("ag.syncProgress")}
        </button>
      </div>

      {repoIndex ? (
        <p className="ai-agent-provider">
          {t("ag.repoIndex", { files: repoIndex.filesIndexed, chunks: repoIndex.chunksIndexed })}
        </p>
      ) : null}

      {threads.length > 0 ? (
        <div className="ai-agent-thread-tabs" role="tablist" aria-label={t("ag.threads")}>
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
                setStreamingText("");
              }}
            >
              {thread.title}
            </button>
          ))}
        </div>
      ) : (
        <div className="ai-agent-empty">{t("ag.noThread")}</div>
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
              {t("ag.previewReplan")}
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={busy}
              onClick={() => runReplan(true)}
            >
              {t("ag.applyReplan")}
            </button>
          </div>

          <div className="ai-agent-messages">
            {activeThread.messages.length === 0 ? (
              <p className="ai-agent-empty">{t("ag.emptyMessages")}</p>
            ) : null}
            {activeThread.messages.map((item) => (
              <article className={`ai-agent-message ai-agent-${item.role}`} key={item.id}>
                <strong>{item.role === "assistant" ? t("ag.copilot") : t("ag.you")}</strong>
                <p>{item.content}</p>
              </article>
            ))}
          </div>

          {streaming ? (
            <div className="ai-agent-messages" aria-live="polite">
              <article className="ai-agent-message ai-agent-user">
                <strong>{t("ag.you")}</strong>
                <p>{pendingMessage}</p>
              </article>
              <article className="ai-agent-message ai-agent-assistant">
                <strong>{t("ag.copilot")}</strong>
                <p>{streamingText || t("ag.thinking")}</p>
              </article>
            </div>
          ) : null}

          {lastReply ? (
            <p className="ai-agent-provider">
              {t("ag.responseEngine", { provider: lastReply.provider })}
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
              <strong>{t("ag.replanSuggestions")}</strong>
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
                <p>{t("ag.addedToTracked", { count: replan.appliedActivities.length })}</p>
              ) : null}
            </div>
          ) : null}

          <div className="ai-agent-composer">
            <textarea
              rows={2}
              maxLength={4000}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder={t("ag.placeholder")}
            />
            <button
              type="button"
              className="primary-button"
              disabled={busy || !message.trim()}
              onClick={sendMessage}
            >
              {busy ? t("ag.thinking") : t("ag.send")}
            </button>
          </div>
          <button type="button" className="ai-agent-delete" onClick={removeThread} disabled={busy}>
            {t("ag.deleteThread")}
          </button>
        </>
      ) : null}

      {orchestration ? (
        <div className="ai-agent-review">
          <strong>{t("ag.coordinator")}</strong>
          <p>{orchestration.executiveSummary}</p>
          {orchestration.nextActions.slice(0, 4).map((action) => (
            <p key={action}>{t("ag.next", { action })}</p>
          ))}
        </div>
      ) : null}

      {review ? (
        <div className="ai-agent-review">
          <strong>{t("ag.review")}</strong>
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
