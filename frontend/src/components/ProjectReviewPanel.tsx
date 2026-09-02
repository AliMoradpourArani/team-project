import { useEffect, useMemo, useState } from "react";

import { deleteProjectReview, getProjectReview, saveProjectReview } from "../api";
import "../project-review.css";
import type { AuthRole, ProjectReview, ProjectReviewInput, ProjectReviewStatus } from "../types";
import StatusMessage from "./StatusMessage";
import { useI18n } from "../i18n";

interface Props {
  projectId: string;
  role: AuthRole;
}

const EMPTY_REVIEW: ProjectReviewInput = {
  status: "in-review",
  functionalityScore: 0,
  codeQualityScore: 0,
  documentationScore: 0,
  integrationScore: 0,
  contributionScore: 0,
  feedback: "",
};

export default function ProjectReviewPanel({ projectId, role }: Props) {
  const [review, setReview] = useState<ProjectReview | null>(null);
  const [form, setForm] = useState<ProjectReviewInput>(EMPTY_REVIEW);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const { t } = useI18n();
  const statusLabel = (status: ProjectReviewStatus) =>
    status === "in-review"
      ? t("rv.inReview")
      : status === "changes-requested"
        ? t("rv.changesRequested")
        : t("rv.approved");

  useEffect(() => {
    setLoading(true);
    setError("");
    setMessage("");
    getProjectReview(projectId)
      .then((current) => {
        setReview(current);
        setForm(current ?? EMPTY_REVIEW);
      })
      .catch((requestError: Error) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, [projectId]);

  const draftTotal = useMemo(
    () =>
      form.functionalityScore +
      form.codeQualityScore +
      form.documentationScore +
      form.integrationScore +
      form.contributionScore,
    [form],
  );

  function setScore(
    field:
      | "functionalityScore"
      | "codeQualityScore"
      | "documentationScore"
      | "integrationScore"
      | "contributionScore",
    value: string,
  ) {
    setForm((current) => ({ ...current, [field]: Number(value) || 0 }));
  }

  async function save() {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const saved = await saveProjectReview(projectId, form);
      setReview(saved);
      setForm(saved);
      setMessage(t("rv.saved"));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("rv.saveError"));
    } finally {
      setSaving(false);
    }
  }

  async function resetReview() {
    if (!review || !window.confirm(t("rv.resetConfirm"))) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await deleteProjectReview(projectId);
      setReview(null);
      setForm(EMPTY_REVIEW);
      setMessage(t("rv.resetToPending"));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("rv.resetError"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <StatusMessage>{t("rv.loading")}</StatusMessage>;

  if (role === "student") {
    return (
      <section className="dashboard-card project-review-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("rv.professorEyebrow")}</p>
            <h2>{review ? statusLabel(review.status) : t("rv.pending")}</h2>
          </div>
          {review ? <strong className="review-total">{review.totalScore}/100</strong> : null}
        </div>
        {error ? <StatusMessage error>{error}</StatusMessage> : null}
        {review ? (
          <>
            <ReviewScores review={review} />
            <div className="review-feedback">
              <strong>{t("rv.feedback")}</strong>
              <p>{review.feedback || t("rv.noFeedback")}</p>
              <small>{t("rv.updatedAt", { date: review.updatedAt })}</small>
            </div>
          </>
        ) : (
          <StatusMessage>{t("rv.notReviewedYet")}</StatusMessage>
        )}
      </section>
    );
  }

  return (
    <section className="dashboard-card project-review-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{t("rv.evaluationEyebrow")}</p>
          <h2>{review ? t("rv.updateRubric") : t("rv.startReview")}</h2>
        </div>
        <strong className="review-total">{draftTotal}/100</strong>
      </div>

      <p className="runner-safety-note">{t("rv.evaluationNote")}</p>

      {error ? <StatusMessage error>{error}</StatusMessage> : null}
      {message ? <StatusMessage>{message}</StatusMessage> : null}

      <label className="review-status-field">
        <span>{t("rv.status")}</span>
        <select
          value={form.status}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              status: event.target.value as ProjectReviewStatus,
            }))
          }
        >
          <option value="in-review">{t("rv.inReview")}</option>
          <option value="changes-requested">{t("rv.changesRequested")}</option>
          <option value="approved">{t("rv.approved")}</option>
        </select>
      </label>

      <div className="review-score-editor">
        <ScoreInput
          label={t("rv.functionality")}
          max={30}
          value={form.functionalityScore}
          onChange={(value) => setScore("functionalityScore", value)}
        />
        <ScoreInput
          label={t("rv.codeQuality")}
          max={20}
          value={form.codeQualityScore}
          onChange={(value) => setScore("codeQualityScore", value)}
        />
        <ScoreInput
          label={t("rv.documentation")}
          max={15}
          value={form.documentationScore}
          onChange={(value) => setScore("documentationScore", value)}
        />
        <ScoreInput
          label={t("rv.integration")}
          max={20}
          value={form.integrationScore}
          onChange={(value) => setScore("integrationScore", value)}
        />
        <ScoreInput
          label={t("rv.contribution")}
          max={15}
          value={form.contributionScore}
          onChange={(value) => setScore("contributionScore", value)}
        />
      </div>

      <label className="review-feedback-field">
        <span>{t("rv.feedback")}</span>
        <textarea
          rows={5}
          maxLength={4000}
          value={form.feedback}
          placeholder={t("rv.feedbackPlaceholder")}
          onChange={(event) => setForm((current) => ({ ...current, feedback: event.target.value }))}
        />
      </label>

      <div className="review-actions">
        <button
          className="primary-button"
          type="button"
          disabled={saving}
          onClick={() => void save()}
        >
          {saving ? t("form.saving") : t("rv.saveReview")}
        </button>
        {review ? (
          <button
            className="secondary-button"
            type="button"
            disabled={saving}
            onClick={() => void resetReview()}
          >
            {t("rv.resetReview")}
          </button>
        ) : null}
      </div>
    </section>
  );
}

function ScoreInput({
  label,
  max,
  value,
  onChange,
}: {
  label: string;
  max: number;
  value: number;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      <span>{label}</span>
      <div className="review-score-input">
        <input
          aria-label={label}
          type="number"
          min={0}
          max={max}
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
        <small>/{max}</small>
      </div>
    </label>
  );
}

function ReviewScores({ review }: { review: ProjectReview }) {
  const { t } = useI18n();

  const rows = [
    [t("rv.functionality"), review.functionalityScore, 30],
    [t("rv.codeQuality"), review.codeQualityScore, 20],
    [t("rv.documentation"), review.documentationScore, 15],
    [t("rv.integration"), review.integrationScore, 20],
    [t("rv.contribution"), review.contributionScore, 15],
  ] as const;

  return (
    <div className="review-score-summary">
      {rows.map(([label, score, max]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>
            {score}/{max}
          </strong>
        </div>
      ))}
    </div>
  );
}
