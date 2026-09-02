import { useEffect, useState } from "react";

import { getProfessorReviewQueue } from "../api";
import { useI18n } from "../i18n";
import "../project-review.css";
import type { ProfessorReviewQueueData } from "../types";
import StatusMessage from "./StatusMessage";

export default function ProfessorReviewQueue() {
  const { t } = useI18n();
  const [data, setData] = useState<ProfessorReviewQueueData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getProfessorReviewQueue()
      .then(setData)
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  if (error) return <StatusMessage error>{error}</StatusMessage>;
  if (!data) return <StatusMessage>{t("rq.loading")}</StatusMessage>;

  return (
    <section className="dashboard-card professor-review-queue">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{t("rq.eyebrow")}</p>
          <h2>{t("rq.title")}</h2>
        </div>
        <span className="member-count">{t("rq.projectsCount", { count: data.totalProjects })}</span>
      </div>

      <div className="review-queue-stats">
        <div>
          <span>{t("rq.pending")}</span>
          <strong>{data.pending}</strong>
        </div>
        <div>
          <span>{t("rq.inReview")}</span>
          <strong>{data.inReview}</strong>
        </div>
        <div>
          <span>{t("rq.changes")}</span>
          <strong>{data.changesRequested}</strong>
        </div>
        <div>
          <span>{t("rq.approved")}</span>
          <strong>{data.approved}</strong>
        </div>
      </div>

      <div className="review-queue-list">
        {data.items.map(({ project, review }) => (
          <a
            className="review-queue-row"
            href={`/projects/${project.id}`}
            data-link
            key={project.id}
          >
            <div>
              <strong>{project.name}</strong>
              <small>{project.userId}</small>
            </div>
            <span className={`review-status review-status-${review?.status ?? "pending"}`}>
              {review?.status ?? "pending"}
            </span>
            <strong className="review-queue-score">
              {review ? `${review.totalScore}/100` : "—"}
            </strong>
            <span className="card-arrow">↗</span>
          </a>
        ))}
      </div>
    </section>
  );
}
