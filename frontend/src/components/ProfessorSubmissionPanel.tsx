import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  createSubmissionRelease,
  getProfessorDeliveryPreflight,
  getProfessorSubmissionDashboard,
  getSubmissionRelease,
  getSubmissionReleases,
  saveSubmissionSettings,
} from "../api";
import "../submission.css";
import type {
  DeliveryPreflightData,
  ProfessorSubmissionDashboardData,
  SubmissionReleaseSummary,
} from "../types";
import StatusMessage from "./StatusMessage";
import { useI18n } from "../i18n";

function toLocalDateTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return shifted.toISOString().slice(0, 16);
}

export default function ProfessorSubmissionPanel() {
  const [data, setData] = useState<ProfessorSubmissionDashboardData | null>(null);
  const [preflight, setPreflight] = useState<DeliveryPreflightData | null>(null);
  const [releases, setReleases] = useState<SubmissionReleaseSummary[]>([]);
  const [isOpen, setIsOpen] = useState(true);
  const [deadline, setDeadline] = useState("");
  const [releaseLabel, setReleaseLabel] = useState("");
  const [saving, setSaving] = useState(false);
  const [creatingRelease, setCreatingRelease] = useState(false);
  const [exportingReleaseId, setExportingReleaseId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const { t } = useI18n();

  const load = useCallback(async () => {
    const [nextData, nextPreflight, nextReleases] = await Promise.all([
      getProfessorSubmissionDashboard(),
      getProfessorDeliveryPreflight(),
      getSubmissionReleases(),
    ]);
    setData(nextData);
    setPreflight(nextPreflight);
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
      setMessage(t("ps.settingsSaved"));
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("ps.settingsError"));
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
      setMessage(t("ps.releaseFrozen", { label: release.label }));
      setReleaseLabel("");
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("ps.releaseError"));
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
      setMessage(t("ps.exported", { label: release.label }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("ps.exportError"));
    } finally {
      setExportingReleaseId(null);
    }
  }

  if ((!data || !preflight) && error) return <StatusMessage error>{error}</StatusMessage>;
  if (!data || !preflight) return <StatusMessage>{t("ps.loading")}</StatusMessage>;

  return (
    <section className="dashboard-card professor-submission-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{t("ps.eyebrow")}</p>
          <h2>{t("ps.title")}</h2>
        </div>
        <span
          className={`submission-state ${data.settings.acceptingSubmissions ? "open" : "closed"}`}
        >
          {data.settings.acceptingSubmissions ? t("ps.accepting") : t("ps.closed")}
        </span>
      </div>

      <div className="submission-summary-grid">
        <article>
          <span>{t("ps.summaryProjects")}</span>
          <strong>{data.totalProjects}</strong>
        </article>
        <article>
          <span>{t("ps.summarySubmitted")}</span>
          <strong>{data.submittedProjects}</strong>
        </article>
        <article>
          <span>{t("ps.summaryPending")}</span>
          <strong>{data.pendingProjects}</strong>
        </article>
        <article>
          <span>{t("ps.summaryApproved")}</span>
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
          <span>{t("ps.acceptSubmissions")}</span>
        </label>
        <label>
          <span>{t("ps.deadline")}</span>
          <input
            type="datetime-local"
            value={deadline}
            onChange={(event) => setDeadline(event.target.value)}
          />
        </label>
        <button className="secondary-button" type="submit" disabled={saving}>
          {saving ? t("form.saving") : t("ps.saveSettings")}
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
              {item.latestSubmission ? `v${item.latestSubmission.version}` : t("ps.notSubmitted")}
            </span>
            <span>
              {item.review
                ? `${item.review.status} · ${item.review.totalScore}/100`
                : t("ps.noReview")}
            </span>
            <span className="card-arrow">↗</span>
          </a>
        ))}
      </div>

      <section className={`delivery-preflight ${preflight.status}`}>
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("ps.preflightEyebrow")}</p>
            <h3>{preflight.summary}</h3>
          </div>
          <span
            className={`submission-state ${preflight.releaseCandidateReady ? "open" : "closed"}`}
          >
            {preflight.releaseCandidateReady
              ? t("ps.ready")
              : t("ps.blockers", { count: preflight.blockerCount })}
          </span>
        </div>
        <div className="delivery-preflight-meta">
          <span>
            {t("ps.projectsReady", {
              ready: preflight.readyProjects,
              total: preflight.totalProjects,
            })}
          </span>
          <code>{preflight.localCheckCommand}</code>
        </div>
        <div className="delivery-preflight-gates">
          {preflight.globalGates.map((gate) => (
            <article className={gate.passed ? "passed" : "blocked"} key={gate.key}>
              <strong>
                {gate.passed ? "✓" : "×"} {gate.label}
              </strong>
              <span>{gate.detail}</span>
              {!gate.passed ? <small>{gate.remediation}</small> : null}
            </article>
          ))}
        </div>
        <div className="delivery-project-grid">
          {preflight.projects.map((project) => {
            const failed = project.gates.filter((gate) => !gate.passed);
            return (
              <a
                href={`/projects/${project.project.id}`}
                data-link
                className={`delivery-project ${project.status}`}
                key={project.project.id}
              >
                <div>
                  <strong>{project.project.name}</strong>
                  <small>{project.project.userId}</small>
                </div>
                <span>{project.status}</span>
                <small>
                  {project.latestSubmissionVersion
                    ? t("ps.frozenV", { version: project.latestSubmissionVersion })
                    : t("ps.notFrozen")}
                  {project.reviewStatus
                    ? t("ps.statusPrefix", { status: project.reviewStatus })
                    : t("ps.noReviewSuffix")}
                </small>
                {failed.length ? <small>{failed[0].remediation}</small> : null}
              </a>
            );
          })}
        </div>
      </section>

      <div className={`release-readiness ${preflight.releaseCandidateReady ? "ready" : "blocked"}`}>
        <strong>
          {preflight.releaseCandidateReady ? t("ps.readyToFreeze") : t("ps.releaseBlocked")}
        </strong>
        <span>{preflight.releaseCandidateReady ? t("ps.readyMessage") : preflight.summary}</span>
      </div>

      <form className="release-form" onSubmit={(event) => void freezeRelease(event)}>
        <label>
          <span>{t("ps.releaseLabel")}</span>
          <input
            type="text"
            maxLength={120}
            placeholder={t("ps.releasePlaceholder")}
            value={releaseLabel}
            onChange={(event) => setReleaseLabel(event.target.value)}
          />
        </label>
        <button
          className="primary-button"
          type="submit"
          disabled={!preflight.releaseCandidateReady || !releaseLabel.trim() || creatingRelease}
        >
          {creatingRelease ? t("ps.freezingCandidate") : t("ps.freezeRelease")}
        </button>
      </form>

      {message ? <StatusMessage>{message}</StatusMessage> : null}
      {error ? <StatusMessage error>{error}</StatusMessage> : null}

      <div className="frozen-release-list">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("ps.immutableHistory")}</p>
            <h3>{t("ps.frozenReleases")}</h3>
          </div>
          <span className="member-count">{releases.length}</span>
        </div>
        {releases.length ? (
          releases.map((release) => (
            <article className="frozen-release-row" key={release.id}>
              <div>
                <strong>{release.label}</strong>
                <small>
                  {t("ps.projectsCount", { count: release.projectCount })} · {release.createdAt}
                </small>
              </div>
              <div className="frozen-release-actions">
                <code title={release.manifestDigest}>{release.manifestDigest.slice(0, 12)}…</code>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={exportingReleaseId === release.id}
                  onClick={() => void exportReport(release)}
                  aria-label={t("ps.exportAria", { label: release.label })}
                >
                  {exportingReleaseId === release.id ? t("ps.exporting") : t("ps.exportReport")}
                </button>
              </div>
            </article>
          ))
        ) : (
          <p className="submission-empty">{t("ps.noFrozenRelease")}</p>
        )}
      </div>
    </section>
  );
}
