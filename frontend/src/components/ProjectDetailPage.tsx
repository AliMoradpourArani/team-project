import { useCallback, useEffect, useState } from "react";

import { getProjectDetail, runProject } from "../api";
import "../project-runner.css";
import type { ProjectDetail, ProjectRunResult } from "../types";
import StatusMessage from "./StatusMessage";

interface Props {
  projectId: string;
  backHref: string;
}

export default function ProjectDetailPage({ projectId, backHref }: Props) {
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [result, setResult] = useState<ProjectRunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const loadDetail = useCallback(async () => {
    setDetail(await getProjectDetail(projectId));
  }, [projectId]);

  useEffect(() => {
    setDetail(null);
    setResult(null);
    setError("");
    loadDetail().catch((requestError: Error) => setError(requestError.message));
  }, [loadDetail]);

  async function execute() {
    setError("");
    setRunning(true);
    try {
      const nextResult = await runProject(projectId);
      setResult(nextResult);
      await loadDetail();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not run project.");
    } finally {
      setRunning(false);
    }
  }

  if (error && !detail) return <StatusMessage error>{error}</StatusMessage>;
  if (!detail) return <StatusMessage>Loading project details…</StatusMessage>;

  const { project, integration } = detail;

  return (
    <section className="project-detail-page">
      <a className="back-link" href={backHref} data-link>
        ← Back
      </a>

      <div className="project-detail-hero">
        <div>
          <p className="eyebrow">Member project</p>
          <h1>{project.name}</h1>
          <p>{project.description}</p>
          <div className="project-detail-meta">
            <span>Owner: {project.userId}</span>
            <span>Status: {project.status}</span>
            <span>{project.technology.join(" · ") || "No technology listed"}</span>
          </div>
        </div>
        <span className={`runner-badge runner-${integration.integrationStatus}`}>
          {integration.integrationStatus}
        </span>
      </div>

      {error ? <StatusMessage error>{error}</StatusMessage> : null}

      <div className="project-detail-grid">
        <section className="dashboard-card">
          <div className="section-heading compact">
            <div>
              <p className="eyebrow">Integration health</p>
              <h2>
                {detail.healthPassed}/{detail.healthTotal} checks passing
              </h2>
            </div>
          </div>
          <div className="project-health-list">
            {detail.health.map((check) => (
              <div className="project-health-item" key={check.key}>
                <span className={`project-health-mark ${check.passed ? "passed" : "failed"}`}>
                  {check.passed ? "✓" : "×"}
                </span>
                <div>
                  <strong>{check.label}</strong>
                  <p>{check.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="dashboard-card">
          <div className="section-heading compact">
            <div>
              <p className="eyebrow">Runner</p>
              <h2>Demo contract</h2>
            </div>
          </div>
          <dl className="project-contract-list">
            <div>
              <dt>Type</dt>
              <dd>{integration.projectType ?? "Not configured"}</dd>
            </div>
            <div>
              <dt>Runner</dt>
              <dd>{integration.runner ?? "Not configured"}</dd>
            </div>
            <div>
              <dt>Entry point</dt>
              <dd>{integration.entryPoint ?? "Not configured"}</dd>
            </div>
            <div>
              <dt>Repository path</dt>
              <dd>{integration.repositoryPath ?? "Not configured"}</dd>
            </div>
          </dl>
          {integration.reason ? <p className="runner-reason">{integration.reason}</p> : null}
          <button
            className="primary-button runner-button"
            type="button"
            disabled={!integration.runnable || running}
            onClick={() => void execute()}
          >
            {running ? "Running…" : integration.runnerEnabled ? "Run demo" : "Runner disabled"}
          </button>
        </section>
      </div>

      {result ? (
        <section className="dashboard-card">
          <div className="section-heading compact">
            <div>
              <p className="eyebrow">Latest result</p>
              <h2>{result.timedOut ? "Timed out" : `Exit ${result.exitCode}`}</h2>
            </div>
            <span>{result.durationMs} ms</span>
          </div>
          <div className="runner-result" aria-live="polite">
            {result.stdout ? <pre>{result.stdout}</pre> : null}
            {result.stderr ? <pre className="runner-stderr">{result.stderr}</pre> : null}
            {!result.stdout && !result.stderr ? <p>No output.</p> : null}
          </div>
        </section>
      ) : null}

      <section className="dashboard-card project-readme-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">Documentation</p>
            <h2>Project README</h2>
          </div>
        </div>
        {detail.readme ? (
          <pre className="project-readme">{detail.readme}</pre>
        ) : (
          <StatusMessage>No valid README.md is available for this project yet.</StatusMessage>
        )}
      </section>

      <section className="dashboard-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">Runtime history</p>
            <h2>Recent demo runs</h2>
          </div>
          <span className="member-count">{detail.recentRuns.length}</span>
        </div>
        {detail.recentRuns.length ? (
          <div className="project-run-history">
            {detail.recentRuns.map((run) => (
              <article className="project-run-history-item" key={run.id}>
                <div className="runner-result-meta">
                  <strong>{run.timedOut ? "Timed out" : `Exit ${run.exitCode}`}</strong>
                  <span>{run.durationMs} ms</span>
                  <span>{run.createdAt}</span>
                  {run.outputTruncated ? <span>preview truncated</span> : null}
                </div>
                {run.stdoutPreview ? <pre>{run.stdoutPreview}</pre> : null}
                {run.stderrPreview ? (
                  <pre className="runner-stderr">{run.stderrPreview}</pre>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <StatusMessage>No recorded demo runs yet.</StatusMessage>
        )}
      </section>
    </section>
  );
}
