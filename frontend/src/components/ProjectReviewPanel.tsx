import { useEffect, useMemo, useState } from "react";

import { deleteProjectReview, getProjectReview, saveProjectReview } from "../api";
import "../project-review.css";
import type { AuthRole, ProjectReview, ProjectReviewInput, ProjectReviewStatus } from "../types";
import StatusMessage from "./StatusMessage";

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

const STATUS_LABELS: Record<ProjectReviewStatus, string> = {
  "in-review": "In review",
  "changes-requested": "Changes requested",
  approved: "Approved",
};

export default function ProjectReviewPanel({ projectId, role }: Props) {
  const [review, setReview] = useState<ProjectReview | null>(null);
  const [form, setForm] = useState<ProjectReviewInput>(EMPTY_REVIEW);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

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
      setMessage("Review saved.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not save review.");
    } finally {
      setSaving(false);
    }
  }

  async function resetReview() {
    if (!review || !window.confirm("Reset this project review?")) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await deleteProjectReview(projectId);
      setReview(null);
      setForm(EMPTY_REVIEW);
      setMessage("Review reset to pending.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not reset review.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <StatusMessage>Loading professor review…</StatusMessage>;

  if (role === "student") {
    return (
      <section className="dashboard-card project-review-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">Professor review</p>
            <h2>{review ? STATUS_LABELS[review.status] : "Pending review"}</h2>
          </div>
          {review ? <strong className="review-total">{review.totalScore}/100</strong> : null}
        </div>
        {error ? <StatusMessage error>{error}</StatusMessage> : null}
        {review ? (
          <>
            <ReviewScores review={review} />
            <div className="review-feedback">
              <strong>Feedback</strong>
              <p>{review.feedback || "No written feedback yet."}</p>
              <small>Updated {review.updatedAt}</small>
            </div>
          </>
        ) : (
          <StatusMessage>Your professor has not reviewed this project yet.</StatusMessage>
        )}
      </section>
    );
  }

  return (
    <section className="dashboard-card project-review-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Professor evaluation</p>
          <h2>{review ? "Update rubric" : "Start review"}</h2>
        </div>
        <strong className="review-total">{draftTotal}/100</strong>
      </div>

      <p className="runner-safety-note">
        Evaluation is runtime-only. Saving this form does not modify student Git data, activities,
        or project source.
      </p>

      {error ? <StatusMessage error>{error}</StatusMessage> : null}
      {message ? <StatusMessage>{message}</StatusMessage> : null}

      <label className="review-status-field">
        <span>Review status</span>
        <select
          value={form.status}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              status: event.target.value as ProjectReviewStatus,
            }))
          }
        >
          <option value="in-review">In review</option>
          <option value="changes-requested">Changes requested</option>
          <option value="approved">Approved</option>
        </select>
      </label>

      <div className="review-score-editor">
        <ScoreInput
          label="Functionality"
          max={30}
          value={form.functionalityScore}
          onChange={(value) => setScore("functionalityScore", value)}
        />
        <ScoreInput
          label="Code quality"
          max={20}
          value={form.codeQualityScore}
          onChange={(value) => setScore("codeQualityScore", value)}
        />
        <ScoreInput
          label="Documentation"
          max={15}
          value={form.documentationScore}
          onChange={(value) => setScore("documentationScore", value)}
        />
        <ScoreInput
          label="Integration"
          max={20}
          value={form.integrationScore}
          onChange={(value) => setScore("integrationScore", value)}
        />
        <ScoreInput
          label="Contribution"
          max={15}
          value={form.contributionScore}
          onChange={(value) => setScore("contributionScore", value)}
        />
      </div>

      <label className="review-feedback-field">
        <span>Feedback</span>
        <textarea
          rows={5}
          maxLength={4000}
          value={form.feedback}
          placeholder="Explain strengths, requested changes, and next steps."
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
          {saving ? "Saving…" : "Save review"}
        </button>
        {review ? (
          <button
            className="secondary-button"
            type="button"
            disabled={saving}
            onClick={() => void resetReview()}
          >
            Reset review
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
  const rows = [
    ["Functionality", review.functionalityScore, 30],
    ["Code quality", review.codeQualityScore, 20],
    ["Documentation", review.documentationScore, 15],
    ["Integration", review.integrationScore, 20],
    ["Contribution", review.contributionScore, 15],
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
