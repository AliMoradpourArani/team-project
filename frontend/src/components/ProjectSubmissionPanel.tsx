import { useCallback, useEffect, useState } from "react";

import { getProjectSubmissionStatus, submitProject } from "../api";
import "../submission.css";
import type { AuthRole, ProjectSubmissionStatus } from "../types";
import StatusMessage from "./StatusMessage";

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
      setMessage(`Submission v${frozen.version} frozen successfully.`);
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not submit project.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!status && error) return <StatusMessage error>{error}</StatusMessage>;
  if (!status) return <StatusMessage>Loading submission status…</StatusMessage>;

  const latest = status.latestSubmission;
  const deadline = status.settings.deadlineAt
    ? new Date(status.settings.deadlineAt).toLocaleString()
    : "No deadline configured";

  return (
    <section className="dashboard-card submission-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Submission</p>
          <h2>{latest ? `Frozen submission · v${latest.version}` : "Not submitted yet"}</h2>
        </div>
        <span
          className={`submission-state ${status.settings.acceptingSubmissions ? "open" : "closed"}`}
        >
          {status.settings.acceptingSubmissions ? "open" : "closed"}
        </span>
      </div>

      <p className="runner-safety-note">
        A submission stores an immutable runtime snapshot and SHA-256 fingerprint of the reviewed
        project source. Later Git changes do not rewrite previous submissions.
      </p>

      <dl className="submission-meta">
        <div>
          <dt>Deadline</dt>
          <dd>{deadline}</dd>
        </div>
        <div>
          <dt>Submission history</dt>
          <dd>{status.historyCount}</dd>
        </div>
        {latest ? (
          <>
            <div>
              <dt>Frozen at</dt>
              <dd>{latest.submittedAt}</dd>
            </div>
            <div>
              <dt>Source</dt>
              <dd>
                {latest.sourceFileCount} files · {formatBytes(latest.sourceTotalBytes)}
              </dd>
            </div>
            <div>
              <dt>Review at submit</dt>
              <dd>
                {latest.reviewStatus ?? "not reviewed"}
                {latest.reviewTotalScore !== null ? ` · ${latest.reviewTotalScore}/100` : ""}
              </dd>
            </div>
          </>
        ) : null}
      </dl>

      {latest ? (
        <div className="submission-digest">
          <span>SHA-256</span>
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
            {submitting
              ? "Freezing…"
              : latest
                ? "Submit new frozen version"
                : "Submit frozen snapshot"}
          </button>
          {!status.canSubmit && status.blockedReason ? <small>{status.blockedReason}</small> : null}
        </div>
      ) : (
        <p className="submission-readonly">Professor view · submission history is immutable.</p>
      )}
    </section>
  );
}
