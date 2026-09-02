import { useEffect, useState } from "react";

import { getAIStatus, runAIWorkspace } from "../api";
import "../ai-workspace.css";
import type { AIAction, AIStatus, AIWorkspaceResult, Project } from "../types";

const actions: { value: AIAction; label: string; description: string }[] = [
  { value: "plan", label: "Plan", description: "Turn a goal into dated, actionable tasks." },
  { value: "roadmap", label: "Roadmap", description: "Build milestones from scope to delivery." },
  {
    value: "progress",
    label: "Progress",
    description: "Measure tracked work and suggest next steps.",
  },
  {
    value: "debug",
    label: "Debug",
    description: "Inspect project health and recent run failures.",
  },
  {
    value: "review",
    label: "Review",
    description: "Check completed work for errors and quality gaps.",
  },
];

interface AIWorkspaceProps {
  projects: Project[];
  onTasksApplied: () => Promise<void>;
}

export default function AIWorkspace({ projects, onTasksApplied }: AIWorkspaceProps) {
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
      setError(
        requestError instanceof Error ? requestError.message : "AI workspace request failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  const createsTasks = ["plan", "roadmap", "progress"].includes(action);

  return (
    <section className="ai-workspace" aria-labelledby="ai-workspace-title">
      <div className="ai-workspace-heading">
        <div>
          <p className="eyebrow">Project copilot</p>
          <h2 id="ai-workspace-title">AI workspace</h2>
          <p className="ai-workspace-intro">
            Plan work, create roadmaps, measure progress, inspect failures, and review what has
            already been built.
          </p>
        </div>
        <span className={`ai-mode-badge ai-mode-${status?.mode ?? "local"}`}>
          {status?.mode === "provider" ? `${status.model ?? "AI"} connected` : "Local engine ready"}
        </span>
      </div>

      <div className="ai-action-grid" role="group" aria-label="AI action">
        {actions.map((item) => (
          <button
            className={`ai-action ${action === item.value ? "ai-action-active" : ""}`}
            type="button"
            key={item.value}
            onClick={() => setAction(item.value)}
          >
            <strong>{item.label}</strong>
            <span>{item.description}</span>
          </button>
        ))}
      </div>

      <div className="ai-controls">
        <label>
          Project
          <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
            <option value="">Whole workspace</option>
            {projects.map((project) => (
              <option value={project.id} key={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Suggested task count
          <input
            type="number"
            min={1}
            max={12}
            value={taskCount}
            onChange={(event) => setTaskCount(Number(event.target.value))}
            disabled={!createsTasks}
          />
        </label>
      </div>

      <label className="ai-goal-field">
        Goal or question
        <textarea
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          rows={3}
          maxLength={2000}
          placeholder={
            action === "debug"
              ? "What is failing or behaving unexpectedly?"
              : "What outcome do you want the AI to plan or review?"
          }
        />
      </label>

      {createsTasks ? (
        <label className="ai-apply-toggle">
          <input
            type="checkbox"
            checked={applyTasks}
            onChange={(event) => setApplyTasks(event.target.checked)}
          />
          Add generated tasks to my tracked timeline
        </label>
      ) : null}

      <button
        className="primary-button ai-run-button"
        type="button"
        disabled={loading}
        onClick={generate}
      >
        {loading
          ? "Analyzing workspace…"
          : `Run ${actions.find((item) => item.value === action)?.label}`}
      </button>

      {error ? <p className="ai-error">{error}</p> : null}

      {result ? (
        <div className="ai-result" aria-live="polite">
          <div className="ai-result-summary">
            <div>
              <p className="eyebrow">AI result</p>
              <h3>{result.summary}</h3>
            </div>
            <div className="ai-progress-score" aria-label={`${result.progressPercent}% progress`}>
              <strong>{result.progressPercent}%</strong>
              <span>tracked progress</span>
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
              Added {result.appliedActivities.length} task
              {result.appliedActivities.length === 1 ? "" : "s"} to your timeline.
            </p>
          ) : null}

          {result.tasks.length > 0 ? (
            <div className="ai-result-section">
              <h4>Suggested tasks</h4>
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
              <h4>Roadmap</h4>
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
              <h4>Checks and findings</h4>
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
    </section>
  );
}
