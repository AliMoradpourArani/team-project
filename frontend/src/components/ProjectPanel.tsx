import { useEffect, useState } from "react";

import { getProjectIntegrations, runProject } from "../api";
import "../project-runner.css";
import type { Project, ProjectIntegration, ProjectRunResult } from "../types";
import StatusMessage from "./StatusMessage";

export default function ProjectPanel({ projects }: { projects: Project[] }) {
  const [integrations, setIntegrations] = useState<ProjectIntegration[]>([]);
  const [results, setResults] = useState<Record<string, ProjectRunResult>>({});
  const [runningId, setRunningId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    getProjectIntegrations()
      .then(setIntegrations)
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  async function execute(project: Project) {
    setError("");
    setRunningId(project.id);
    try {
      const result = await runProject(project.id);
      setResults((current) => ({ ...current, [project.id]: result }));
      setIntegrations(await getProjectIntegrations());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not run project.");
    } finally {
      setRunningId(null);
    }
  }

  return (
    <section className="dashboard-card projects-card project-runner-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Projects</p>
          <h2>Integrated work</h2>
        </div>
        <span className="member-count">{projects.length}</span>
      </div>

      <p className="runner-safety-note">
        Runner executes reviewed repository code only. It does not execute manifest shell commands
        and is not a sandbox for untrusted code.
      </p>

      {error ? <StatusMessage error>{error}</StatusMessage> : null}

      {projects.length > 0 ? (
        <div className="project-list">
          {projects.map((project) => {
            const integration = integrations.find((item) => item.projectId === project.id);
            const result = results[project.id];
            const statusLabel = integration?.integrationStatus ?? "checking";
            const statusClass = integration?.integrationStatus ?? "checking";

            return (
              <article className="project-item project-runner-item" key={project.id}>
                <span className="project-mark">↗</span>
                <div className="project-runner-content">
                  <div className="project-runner-heading">
                    <div>
                      <h3>{project.name}</h3>
                      <p>{project.description}</p>
                      <small>{project.technology.join(" · ") || "No technology listed"}</small>
                    </div>
                    <span className={`runner-badge runner-${statusClass}`}>{statusLabel}</span>
                  </div>

                  <div className="runner-controls">
                    <a className="text-link" href={`/projects/${project.id}`} data-link>
                      View project details
                    </a>
                    {integration ? (
                      <button
                        className="secondary-button runner-button"
                        type="button"
                        disabled={!integration.runnable || runningId === project.id}
                        onClick={() => void execute(project)}
                      >
                        {runningId === project.id
                          ? "Running…"
                          : integration.runnerEnabled
                            ? "Run demo"
                            : "Runner disabled"}
                      </button>
                    ) : null}
                  </div>

                  {integration ? (
                    <span className="runner-contract">
                      {integration.runner ?? "No runner"}
                      {integration.entryPoint ? ` · ${integration.entryPoint}` : ""}
                    </span>
                  ) : null}

                  {integration?.reason ? (
                    <p className="runner-reason">{integration.reason}</p>
                  ) : null}

                  {result ? (
                    <div className="runner-result" aria-live="polite">
                      <div className="runner-result-meta">
                        <strong>{result.timedOut ? "Timed out" : `Exit ${result.exitCode}`}</strong>
                        <span>{result.durationMs} ms</span>
                        {result.outputTruncated ? <span>output truncated</span> : null}
                      </div>
                      {result.stdout ? <pre>{result.stdout}</pre> : null}
                      {result.stderr ? <pre className="runner-stderr">{result.stderr}</pre> : null}
                      {!result.stdout && !result.stderr ? <p>No output.</p> : null}
                    </div>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <StatusMessage>No projects recorded yet.</StatusMessage>
      )}
    </section>
  );
}
