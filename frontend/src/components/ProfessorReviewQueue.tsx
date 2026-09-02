import { useEffect, useState } from "react";

import { getProfessorReviewQueue } from "../api";
import "../project-review.css";
import type { ProfessorReviewQueueData } from "../types";
import StatusMessage from "./StatusMessage";

export default function ProfessorReviewQueue() {
  const [data, setData] = useState<ProfessorReviewQueueData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getProfessorReviewQueue()
      .then(setData)
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  if (error) return <StatusMessage error>{error}</StatusMessage>;
  if (!data) return <StatusMessage>Loading project review queue…</StatusMessage>;

  return (
    <section className="dashboard-card professor-review-queue">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Evaluation</p>
          <h2>Project review queue</h2>
        </div>
        <span className="member-count">{data.totalProjects} projects</span>
      </div>

      <div className="review-queue-stats">
        <div>
          <span>Pending</span>
          <strong>{data.pending}</strong>
        </div>
        <div>
          <span>In review</span>
          <strong>{data.inReview}</strong>
        </div>
        <div>
          <span>Changes</span>
          <strong>{data.changesRequested}</strong>
        </div>
        <div>
          <span>Approved</span>
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
