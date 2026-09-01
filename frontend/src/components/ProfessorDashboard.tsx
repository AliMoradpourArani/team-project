import { useEffect, useMemo, useState } from "react";

import { getProfessorDashboard } from "../api";
import type { ProfessorDashboardData } from "../types";
import StatusMessage from "./StatusMessage";

export default function ProfessorDashboard() {
  const [data, setData] = useState<ProfessorDashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getProfessorDashboard()
      .then(setData)
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  const names = useMemo(
    () => new Map(data?.members.map((member) => [member.user.id, member.user.name]) ?? []),
    [data],
  );

  if (error) return <StatusMessage error>{error}</StatusMessage>;
  if (!data) return <StatusMessage>Loading professor dashboard…</StatusMessage>;

  const completionRate = data.totals.activities
    ? Math.round((data.totals.completedActivities / data.totals.activities) * 100)
    : 0;

  return (
    <section className="professor-page">
      <div className="professor-hero">
        <div>
          <p className="eyebrow">Professor dashboard</p>
          <h1>
            Team
            <br />
            <em>overview.</em>
          </h1>
        </div>
        <div className="professor-summary-note">
          <strong>{completionRate}%</strong>
          <span>team activity completion</span>
        </div>
      </div>

      <div className="stats-grid professor-stats">
        <article className="stat-card">
          <span>Members</span>
          <strong>{data.totals.members}</strong>
        </article>
        <article className="stat-card">
          <span>Activities</span>
          <strong>{data.totals.activities}</strong>
        </article>
        <article className="stat-card">
          <span>Completed</span>
          <strong>{data.totals.completedActivities}</strong>
        </article>
        <article className="stat-card">
          <span>Active projects</span>
          <strong>{data.totals.activeProjects}</strong>
        </article>
      </div>

      <section className="dashboard-card professor-members">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">Team progress</p>
            <h2>Members</h2>
          </div>
          <span className="member-count">read only</span>
        </div>
        <div className="professor-member-list">
          {data.members.map((member) => {
            const rate = member.totalActivities
              ? Math.round((member.completedActivities / member.totalActivities) * 100)
              : 0;
            return (
              <a
                className="professor-member-row"
                href={`/users/${member.user.id}`}
                data-link
                key={member.user.id}
              >
                <span className="member-avatar">{member.user.name.charAt(0)}</span>
                <div className="professor-member-main">
                  <strong>{member.user.name}</strong>
                  <small>{member.user.role}</small>
                  <div className="progress-track" aria-label={`${rate}% complete`}>
                    <span style={{ width: `${rate}%` }} />
                  </div>
                </div>
                <dl className="member-metrics">
                  <div>
                    <dt>Activities</dt>
                    <dd>{member.totalActivities}</dd>
                  </div>
                  <div>
                    <dt>Done</dt>
                    <dd>{member.completedActivities}</dd>
                  </div>
                  <div>
                    <dt>Active projects</dt>
                    <dd>{member.activeProjects}</dd>
                  </div>
                  <div>
                    <dt>Last activity</dt>
                    <dd>{member.latestActivityDate ?? "—"}</dd>
                  </div>
                </dl>
                <span className="card-arrow">↗</span>
              </a>
            );
          })}
        </div>
      </section>

      <section className="dashboard-card professor-recent">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">Across the team</p>
            <h2>Recent activity</h2>
          </div>
          <span className="member-count">latest 20</span>
        </div>
        {data.recentActivities.length ? (
          <div className="professor-activity-list">
            {data.recentActivities.map((activity) => (
              <article className="professor-activity-row" key={activity.id}>
                <span className={`status-dot ${activity.status}`} />
                <div>
                  <strong>{activity.title}</strong>
                  <small>{names.get(activity.userId) ?? activity.userId}</small>
                </div>
                <span className={`pill ${activity.status}`}>{activity.status}</span>
                <time>{activity.date}</time>
              </article>
            ))}
          </div>
        ) : (
          <StatusMessage>No activities recorded yet.</StatusMessage>
        )}
      </section>
    </section>
  );
}
