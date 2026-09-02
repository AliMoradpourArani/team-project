import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  createSubmissionRelease,
  getProfessorSubmissionDashboard,
  getSubmissionRelease,
  getSubmissionReleases,
  saveSubmissionSettings,
} from "../api";
import "../submission.css";
import type { ProfessorSubmissionDashboardData, SubmissionReleaseSummary } from "../types";
import StatusMessage from "./StatusMessage";

function toLocalDateTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return shifted.toISOString().slice(0, 16);
}

export default function ProfessorSubmissionPanel() {
  const [data, setData] = useState<ProfessorSubmissionDashboardData | null>(null);
  const [releases, setReleases] = useState<SubmissionReleaseSummary[]>([]);
  const [isOpen, setIsOpen] = useState(true);
  const [deadline, setDeadline] = useState("");
  const [releaseLabel, setReleaseLabel] = useState("");
  const [saving, setSaving] = useState(false);
  const [creatingRelease, setCreatingRelease] = useState(false);
  const [exportingReleaseId, setExportingReleaseId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [nextData, nextReleases] = await Promise.all([
      getProfessorSubmissionDashboard(),
      getSubmissionReleases(),
    ]);
    setData(nextData);
    setReleases(nextReleases);
    setIsOpen(nextData.settings.isOpen);
    setDeadline(toLocalDateTime(nextData.settings.deadlineAt));
  }, []);

  useEffect(() => {
    load().catch((requestError: Error) => setError(requestError.message));
  }, [load]);

  async function saveSettings(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await saveSubmissionSettings({
        isOpen,
        deadlineAt: deadline ? new Date(deadline).toISOString() : null,
      });
      setMessage("Submission settings saved.");
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not save settings.");
    } finally {
      setSaving(false);
    }
  }

  async function freezeRelease(event: FormEvent) {
    event.preventDefault();
    setCreatingRelease(true);
    setError("");
    setMessage("");
    try {
      const release = await createSubmissionRelease(releaseLabel);
      setMessage(`Release “${release.label}” frozen.`);
      setReleaseLabel("");
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not freeze release.");
    } finally {
      setCreatingRelease(false);
    }
  }

  async function exportReport(release: SubmissionReleaseSummary) {
    setExportingReleaseId(release.id);
    setError("");
    setMessage("");
    try {
      const detail = await getSubmissionRelease(release.id);
      const blob = new Blob([JSON.stringify(detail, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `team-project-release-${release.id}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setMessage(`Report for “${release.label}” exported.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not export report.");
    } finally {
      setExportingReleaseId(null);
    }
  }

  if (!data && error) return <StatusMessage error>{error}</StatusMessage>;
  if (!data) return <StatusMessage>Loading submission controls…</StatusMessage>;

  return (
    <section className="dashboard-card professor-submission-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Submission &amp; release</p>
          <h2>Final delivery control</h2>
        </div>
        <span
          className={`submission-state ${data.settings.acceptingSubmissions ? "open" : "closed"}`}
        >
          {data.settings.acceptingSubmissions ? "accepting" : "closed"}
        </span>
      </div>

      <div className="submission-summary-grid">
        <article>
          <span>Projects</span>
          <strong>{data.totalProjects}</strong>
        </article>
        <article>
          <span>Submitted</span>
          <strong>{data.submittedProjects}</strong>
        </article>
        <article>
          <span>Pending</span>
          <strong>{data.pendingProjects}</strong>
        </article>
        <article>
          <span>Approved reviews</span>
          <strong>{data.approvedProjects}</strong>
        </article>
      </div>

      <form className="submission-settings-form" onSubmit={(event) => void saveSettings(event)}>
        <label className="submission-toggle">
          <input
            type="checkbox"
            checked={isOpen}
            onChange={(event) => setIsOpen(event.target.checked)}
          />
          <span>Accept project submissions</span>
        </label>
        <label>
          <span>Deadline</span>
          <input
            type="datetime-local"
            value={deadline}
            onChange={(event) => setDeadline(event.target.value)}
          />
        </label>
        <button className="secondary-button" type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save submission settings"}
        </button>
      </form>

      <div className="professor-submission-list">
        {data.items.map((item) => (
          <a
            className="professor-submission-row"
            href={`/projects/${item.project.id}`}
            data-link
            key={item.project.id}
          >
            <div>
              <strong>{item.project.name}</strong>
              <small>{item.project.userId}</small>
            </div>
            <span>
              {item.latestSubmission ? `v${item.latestSubmission.version}` : "not submitted"}
            </span>
            <span>
              {item.review ? `${item.review.status} · ${item.review.totalScore}/100` : "no review"}
            </span>
            <span className="card-arrow">↗</span>
          </a>
        ))}
      </div>

      <div className={`release-readiness ${data.releaseReady ? "ready" : "blocked"}`}>
        <strong>{data.releaseReady ? "Ready to freeze release" : "Release blocked"}</strong>
        <span>
          {data.releaseReady
            ? "Every project has a frozen submission and an approved professor review."
            : data.releaseBlockedReason}
        </span>
      </div>

      <form className="release-form" onSubmit={(event) => void freezeRelease(event)}>
        <label>
          <span>Release label</span>
          <input
            type="text"
            maxLength={120}
            placeholder="Final submission · Fall 2026"
            value={releaseLabel}
            onChange={(event) => setReleaseLabel(event.target.value)}
          />
        </label>
        <button
          className="primary-button"
          type="submit"
          disabled={!data.releaseReady || !releaseLabel.trim() || creatingRelease}
        >
          {creatingRelease ? "Freezing release…" : "Freeze final release"}
        </button>
      </form>

      {message ? <StatusMessage>{message}</StatusMessage> : null}
      {error ? <StatusMessage error>{error}</StatusMessage> : null}

      <div className="frozen-release-list">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">Immutable history</p>
            <h3>Frozen releases</h3>
          </div>
          <span className="member-count">{releases.length}</span>
        </div>
        {releases.length ? (
          releases.map((release) => (
            <article className="frozen-release-row" key={release.id}>
              <div>
                <strong>{release.label}</strong>
                <small>
                  {release.projectCount} projects · {release.createdAt}
                </small>
              </div>
              <div className="frozen-release-actions">
                <code title={release.manifestDigest}>{release.manifestDigest.slice(0, 12)}…</code>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={exportingReleaseId === release.id}
                  onClick={() => void exportReport(release)}
                  aria-label={`Export ${release.label} report`}
                >
                  {exportingReleaseId === release.id ? "Exporting…" : "Export report"}
                </button>
              </div>
            </article>
          ))
        ) : (
          <p className="submission-empty">No frozen team release yet.</p>
        )}
      </div>
    </section>
  );
}
