import { useCallback, useEffect, useState } from "react";

import { getProjectSubmissionStatus, submitProject } from "../api";
import "../submission.css";
import type { AuthRole, ProjectSubmissionStatus } from "../types";
import StatusMessage from "./StatusMessage";
import { useI18n } from "../i18n";

interface Props {
  projectId: string;
  role: AuthRole;
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ProjectSubmissionPanel({ projectId, role }: Props) {
  const [status, setStatus] = useState<ProjectSubmissionStatus | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { t } = useI18n();

  const load = useCallback(async () => {
    setStatus(await getProjectSubmissionStatus(projectId));
  }, [projectId]);

  useEffect(() => {
    setStatus(null);
    setError("");
    setMessage("");
    load().catch((requestError: Error) => setError(requestError.message));
  }, [load]);

  async function submit() {
    setError("");
    setMessage("");
    setSubmitting(true);
    try {
      const frozen = await submitProject(projectId);
      setMessage(t("sub.frozenSuccess", { version: frozen.version }));
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("sub.submitError"));
    } finally {
      setSubmitting(false);
    }
  }

  if (!status && error) return <StatusMessage error>{error}</StatusMessage>;
  if (!status) return <StatusMessage>{t("sub.loading")}</StatusMessage>;

  const latest = status.latestSubmission;
  const deadline = status.settings.deadlineAt
    ? new Date(status.settings.deadlineAt).toLocaleString()
    : t("sub.noDeadline");

  return (
    <section className="dashboard-card submission-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{t("sub.eyebrow")}</p>
          <h2>{latest ? t("sub.frozen", { version: latest.version }) : t("sub.notSubmitted")}</h2>
        </div>
        <span
          className={`submission-state ${status.settings.acceptingSubmissions ? "open" : "closed"}`}
        >
          {status.settings.acceptingSubmissions ? t("sub.open") : t("sub.closed")}
        </span>
      </div>

      <p className="runner-safety-note">{t("sub.safetyNote")}</p>

      <dl className="submission-meta">
        <div>
          <dt>{t("sub.deadline")}</dt>
          <dd>{deadline}</dd>
        </div>
        <div>
          <dt>{t("sub.history")}</dt>
          <dd>{status.historyCount}</dd>
        </div>
        {latest ? (
          <>
            <div>
              <dt>{t("sub.frozenAt")}</dt>
              <dd>{latest.submittedAt}</dd>
            </div>
            <div>
              <dt>{t("sub.source")}</dt>
              <dd>
                {latest.sourceFileCount} files · {formatBytes(latest.sourceTotalBytes)}
              </dd>
            </div>
            <div>
              <dt>{t("sub.reviewAtSubmit")}</dt>
              <dd>
                {latest.reviewStatus ?? t("sub.notReviewed")}
                {latest.reviewTotalScore !== null ? ` · ${latest.reviewTotalScore}/100` : ""}
              </dd>
            </div>
          </>
        ) : null}
      </dl>

      {latest ? (
        <div className="submission-digest">
          <span>{t("sub.sha256")}</span>
          <code>{latest.snapshotDigest}</code>
        </div>
      ) : null}

      {message ? <StatusMessage>{message}</StatusMessage> : null}
      {error ? <StatusMessage error>{error}</StatusMessage> : null}

      {role === "student" ? (
        <div className="submission-actions">
          <button
            className="primary-button"
            type="button"
            disabled={!status.canSubmit || submitting}
            onClick={() => void submit()}
          >
            {submitting ? t("sub.freezing") : latest ? t("sub.submitNew") : t("sub.submitSnapshot")}
          </button>
          {!status.canSubmit && status.blockedReason ? <small>{status.blockedReason}</small> : null}
        </div>
      ) : (
        <p className="submission-readonly">{t("sub.professorReadonly")}</p>
      )}
    </section>
  );
}
