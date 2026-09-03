import { useEffect, useState } from "react";

import { getAIStatus, runAIWorkspace } from "../api";
import { useI18n } from "../i18n";
import type { TranslationKey } from "../i18n/translations";
import "../ai-workspace.css";
import type { AIAction, AIStatus, AIWorkspaceResult, Project } from "../types";
import AIAgentPanel from "./AIAgentPanel";

const actions: { value: AIAction; labelKey: TranslationKey; descKey: TranslationKey }[] = [
  { value: "plan", labelKey: "ai.action.plan", descKey: "ai.action.plan.desc" },
  { value: "roadmap", labelKey: "ai.action.roadmap", descKey: "ai.action.roadmap.desc" },
  { value: "progress", labelKey: "ai.action.progress", descKey: "ai.action.progress.desc" },
  { value: "debug", labelKey: "ai.action.debug", descKey: "ai.action.debug.desc" },
  { value: "review", labelKey: "ai.action.review", descKey: "ai.action.review.desc" },
];

interface AIWorkspaceProps {
  projects: Project[];
  onTasksApplied: () => Promise<void>;
}

export default function AIWorkspace({ projects, onTasksApplied }: AIWorkspaceProps) {
  const { t } = useI18n();
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [action, setAction] = useState<AIAction>("plan");
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [goal, setGoal] = useState("");
  const [taskCount, setTaskCount] = useState(5);
  const [applyTasks, setApplyTasks] = useState(false);
  const [result, setResult] = useState<AIWorkspaceResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getAIStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    if (projectId && !projects.some((project) => project.id === projectId)) {
      setProjectId(projects[0]?.id ?? "");
    } else if (!projectId && projects.length > 0) {
      setProjectId(projects[0].id);
    }
  }, [projectId, projects]);

  async function generate() {
    setLoading(true);
    setError("");
    try {
      const response = await runAIWorkspace({
        action,
        projectId: projectId || null,
        goal,
        taskCount,
        applyTasks: applyTasks && ["plan", "roadmap", "progress"].includes(action),
      });
      setResult(response);
      if (response.appliedActivities.length > 0) await onTasksApplied();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("ai.requestError"));
    } finally {
      setLoading(false);
    }
  }

  const createsTasks = ["plan", "roadmap", "progress"].includes(action);

  return (
    <section className="ai-workspace" aria-labelledby="ai-workspace-title">
      <div className="ai-workspace-heading">
        <div>
          <p className="eyebrow">{t("ai.copilot")}</p>
          <h2 id="ai-workspace-title">{t("ai.workspace")}</h2>
          <p className="ai-workspace-intro">{t("ai.intro")}</p>
        </div>
        <span className={`ai-mode-badge ai-mode-${status?.mode ?? "local"}`}>
          {status?.mode === "provider"
            ? t("ai.providerConnected", { model: status.model ?? "AI" })
            : t("ai.localReady")}
        </span>
      </div>

      <div className="ai-action-grid" role="group" aria-label={t("ai.action")}>
        {actions.map((item) => (
          <button
            className={`ai-action ${action === item.value ? "ai-action-active" : ""}`}
            type="button"
            key={item.value}
            aria-pressed={action === item.value}
            onClick={() => setAction(item.value)}
          >
            <strong>{t(item.labelKey)}</strong>
            <span>{t(item.descKey)}</span>
          </button>
        ))}
      </div>

      <div className="ai-controls">
        <label>
          {t("ai.project")}
          <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
            <option value="">{t("ai.wholeWorkspace")}</option>
            {projects.map((project) => (
              <option value={project.id} key={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          {t("ai.taskCount")}
          <input
            type="number"
            min={1}
            max={12}
            value={taskCount}
            onChange={(event) => {
              const parsed = Number(event.target.value);
              setTaskCount(Number.isFinite(parsed) ? Math.min(12, Math.max(1, parsed)) : 1);
            }}
            disabled={!createsTasks}
          />
        </label>
      </div>

      <label className="ai-goal-field">
        {t("ai.goal")}
        <textarea
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          rows={3}
          maxLength={2000}
          placeholder={action === "debug" ? t("ai.goalDebugPlaceholder") : t("ai.goalPlaceholder")}
        />
      </label>

      {createsTasks ? (
        <label className="ai-apply-toggle">
          <input
            type="checkbox"
            checked={applyTasks}
            onChange={(event) => setApplyTasks(event.target.checked)}
          />
          {t("ai.applyTasks")}
        </label>
      ) : null}

      <button
        className="primary-button ai-run-button"
        type="button"
        disabled={loading}
        onClick={generate}
      >
        {loading
          ? t("ai.analyzing")
          : t("ai.run", {
              action: t(
                actions.find((item) => item.value === action)?.labelKey ?? "ai.action.plan",
              ),
            })}
      </button>

      {error ? <p className="ai-error">{error}</p> : null}

      {result ? (
        <div className="ai-result" aria-live="polite">
          <div className="ai-result-summary">
            <div>
              <p className="eyebrow">{t("ai.result")}</p>
              <h3>{result.summary}</h3>
            </div>
            <div
              className="ai-progress-score"
              aria-label={t("prof.percentComplete", { rate: result.progressPercent })}
            >
              <strong>{result.progressPercent}%</strong>
              <span>{t("ai.trackedProgress")}</span>
            </div>
          </div>

          <div className="ai-progress-track" aria-hidden="true">
            <span style={{ width: `${result.progressPercent}%` }} />
          </div>

          {result.providerMessage ? (
            <p className="ai-provider-note">{result.providerMessage}</p>
          ) : null}
          {result.appliedActivities.length > 0 ? (
            <p className="ai-applied-note">
              {t("ai.addedTasks", { count: result.appliedActivities.length })}
            </p>
          ) : null}

          {result.tasks.length > 0 ? (
            <div className="ai-result-section">
              <h4>{t("ai.suggestedTasks")}</h4>
              <div className="ai-task-list">
                {result.tasks.map((task, index) => (
                  <article className="ai-task-card" key={`${task.date}-${task.title}-${index}`}>
                    <time>{task.date}</time>
                    <strong>{task.title}</strong>
                    <p>{task.rationale}</p>
                  </article>
                ))}
              </div>
            </div>
          ) : null}

          {result.roadmap.length > 0 ? (
            <div className="ai-result-section">
              <h4>{t("ai.roadmap")}</h4>
              <ol className="ai-roadmap-list">
                {result.roadmap.map((milestone) => (
                  <li key={`${milestone.targetDate}-${milestone.title}`}>
                    <div>
                      <strong>{milestone.title}</strong>
                      <time>{milestone.targetDate}</time>
                    </div>
                    <p>{milestone.objective}</p>
                    {milestone.tasks.length > 0 ? (
                      <small>{milestone.tasks.join(" · ")}</small>
                    ) : null}
                  </li>
                ))}
              </ol>
            </div>
          ) : null}

          {result.findings.length > 0 ? (
            <div className="ai-result-section">
              <h4>{t("ai.findings")}</h4>
              <div className="ai-finding-list">
                {result.findings.map((finding, index) => (
                  <article
                    className={`ai-finding ai-finding-${finding.severity}`}
                    key={`${finding.title}-${index}`}
                  >
                    <span>{finding.severity}</span>
                    <strong>{finding.title}</strong>
                    <p>{finding.detail}</p>
                    <small>{finding.recommendation}</small>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      <AIAgentPanel projectId={projectId || null} />
    </section>
  );
}
