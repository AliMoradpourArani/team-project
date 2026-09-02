import { useCallback, useEffect, useState } from "react";

import { getProjectDetail, runProject } from "../api";
import "../project-runner.css";
import type { AuthRole, ProjectDetail, ProjectRunResult } from "../types";
import ProjectDemoPreview from "./ProjectDemoPreview";
import ProjectOnboardingPanel from "./ProjectOnboardingPanel";
import ProjectReviewPanel from "./ProjectReviewPanel";
import ProjectSubmissionPanel from "./ProjectSubmissionPanel";
import StatusMessage from "./StatusMessage";
import { useI18n } from "../i18n";

interface Props {
  projectId: string;
  backHref: string;
  role: AuthRole;
}

export default function ProjectDetailPage({ projectId, backHref, role }: Props) {
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [result, setResult] = useState<ProjectRunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const { t } = useI18n();

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
      setError(requestError instanceof Error ? requestError.message : t("pp.runError"));
    } finally {
      setRunning(false);
    }
  }

  if (error && !detail) return <StatusMessage error>{error}</StatusMessage>;
  if (!detail) return <StatusMessage>{t("pd.loading")}</StatusMessage>;

  const { project, integration } = detail;

  return (
    <section className="project-detail-page">
      <a className="back-link" href={backHref} data-link>
        {t("pd.back")}
      </a>

      <div className="project-detail-hero">
        <div>
          <p className="eyebrow">{t("pd.eyebrow")}</p>
          <h1>{project.name}</h1>
          <p>{project.description}</p>
          <div className="project-detail-meta">
            <span>{t("pd.owner", { userId: project.userId })}</span>
            <span>{t("pd.status", { status: project.status })}</span>
            <span>{project.technology.join(" · ") || t("app.noTechnology")}</span>
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
              <p className="eyebrow">{t("pd.healthEyebrow")}</p>
              <h2>
                {t("pd.checksPassing", {
                  passed: detail.healthPassed,
                  total: detail.healthTotal,
                })}
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
              <p className="eyebrow">{t("pd.demo")}</p>
              <h2>{t("pd.typedContract")}</h2>
            </div>
          </div>
          <dl className="project-contract-list">
            <div>
              <dt>{t("pd.contractType")}</dt>
              <dd>{integration.projectType ?? t("pd.notConfigured")}</dd>
            </div>
            <div>
              <dt>{t("pd.contractRunner")}</dt>
              <dd>{integration.runner ?? t("pd.notConfigured")}</dd>
            </div>
            <div>
              <dt>{t("pd.contractMode")}</dt>
              <dd>{integration.demoMode ?? t("pd.notConfigured")}</dd>
            </div>
            <div>
              <dt>{t("pd.contractEntry")}</dt>
              <dd>{integration.entryPoint ?? t("pd.notConfigured")}</dd>
            </div>
            <div>
              <dt>{t("pd.contractRepo")}</dt>
              <dd>{integration.repositoryPath ?? t("pd.notConfigured")}</dd>
            </div>
          </dl>
          {integration.reason ? <p className="runner-reason">{integration.reason}</p> : null}
          {integration.demoMode === "preview" ? (
            <p className="runner-safety-note">{t("pd.previewOnlyNote")}</p>
          ) : (
            <button
              className="primary-button runner-button"
              type="button"
              disabled={!integration.runnable || running}
              onClick={() => void execute()}
            >
              {running
                ? t("pp.running")
                : integration.runnerEnabled
                  ? t("pp.runDemo")
                  : t("pp.runnerDisabled")}
            </button>
          )}
        </section>
      </div>

      <ProjectOnboardingPanel projectId={projectId} role={role} />
      <ProjectReviewPanel projectId={projectId} role={role} />
      <ProjectSubmissionPanel projectId={projectId} role={role} />

      {detail.preview ? <ProjectDemoPreview preview={detail.preview} /> : null}

      {result ? (
        <section className="dashboard-card">
          <div className="section-heading compact">
            <div>
              <p className="eyebrow">{t("pd.latestResult")}</p>
              <h2>
                {result.timedOut
                  ? t("pp.timedOut")
                  : t("pp.exit", { code: result.exitCode ?? "—" })}
              </h2>
            </div>
            <span>{result.durationMs} ms</span>
          </div>
          <div className="runner-result" aria-live="polite">
            {result.stdout ? <pre>{result.stdout}</pre> : null}
            {result.stderr ? <pre className="runner-stderr">{result.stderr}</pre> : null}
            {!result.stdout && !result.stderr ? <p>{t("pp.noOutput")}</p> : null}
          </div>
        </section>
      ) : null}

      <section className="dashboard-card project-readme-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("pd.documentation")}</p>
            <h2>{t("pd.readmeTitle")}</h2>
          </div>
        </div>
        {detail.readme ? (
          <pre className="project-readme">{detail.readme}</pre>
        ) : (
          <StatusMessage>{t("pd.noReadme")}</StatusMessage>
        )}
      </section>

      <section className="dashboard-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("pd.runtimeHistory")}</p>
            <h2>{t("pd.recentRuns")}</h2>
          </div>
          <span className="member-count">{detail.recentRuns.length}</span>
        </div>
        {detail.recentRuns.length ? (
          <div className="project-run-history">
            {detail.recentRuns.map((run) => (
              <article className="project-run-history-item" key={run.id}>
                <div className="runner-result-meta">
                  <strong>
                    {run.timedOut ? t("pp.timedOut") : t("pp.exit", { code: run.exitCode ?? "—" })}
                  </strong>
                  <span>{run.durationMs} ms</span>
                  <span>{run.createdAt}</span>
                  {run.outputTruncated ? <span>{t("pd.previewTruncated")}</span> : null}
                </div>
                {run.stdoutPreview ? <pre>{run.stdoutPreview}</pre> : null}
                {run.stderrPreview ? (
                  <pre className="runner-stderr">{run.stderrPreview}</pre>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <StatusMessage>{t("pd.noRuns")}</StatusMessage>
        )}
      </section>
    </section>
  );
}
