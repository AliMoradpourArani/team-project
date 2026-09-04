import { useEffect, useMemo, useState } from "react";

import { getProfessorDashboard } from "../api";
import { useI18n } from "../i18n";
import type { ProfessorDashboardData } from "../types";
import GitHubConnectButton from "./GitHubConnectButton";
import GitHubContributionPanel from "./GitHubContributionPanel";
import ProfessorReviewQueue from "./ProfessorReviewQueue";
import ProfessorSubmissionPanel from "./ProfessorSubmissionPanel";
import StatusMessage from "./StatusMessage";

export default function ProfessorDashboard() {
  const { t } = useI18n();
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
  if (!data) return <StatusMessage>{t("prof.loading")}</StatusMessage>;

  const completionRate = data.totals.activities
    ? Math.round((data.totals.completedActivities / data.totals.activities) * 100)
    : 0;

  return (
    <section className="professor-page">
      <div className="professor-hero">
        <div>
          <p className="eyebrow">{t("prof.eyebrow")}</p>
          <h1>
            {t("prof.team")}
            <br />
            <em>{t("prof.overview")}</em>
          </h1>
        </div>
        <div className="professor-summary-note">
          <strong>{completionRate}%</strong>
          <span>{t("prof.completionNote")}</span>
        </div>
      </div>

      <div className="stats-grid professor-stats">
        <article className="stat-card">
          <span>{t("prof.members")}</span>
          <strong>{data.totals.members}</strong>
        </article>
        <article className="stat-card">
          <span>{t("prof.activities")}</span>
          <strong>{data.totals.activities}</strong>
        </article>
        <article className="stat-card">
          <span>{t("prof.completed")}</span>
          <strong>{data.totals.completedActivities}</strong>
        </article>
        <article className="stat-card">
          <span>{t("prof.activeProjects")}</span>
          <strong>{data.totals.activeProjects}</strong>
        </article>
      </div>

      <section className="dashboard-card professor-members">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("prof.teamProgress")}</p>
            <h2>{t("prof.members")}</h2>
          </div>
          <span className="member-count">{t("prof.readOnly")}</span>
        </div>
        <div className="professor-member-list">
          {data.members.map((member) => {
            const rate = member.totalActivities
              ? Math.round((member.completedActivities / member.totalActivities) * 100)
              : 0;
            return (
              <div className="professor-member-row" key={member.user.id}>
                <span className="member-avatar">{member.user.name.charAt(0)}</span>
                <div className="professor-member-main">
                  <div className="professor-member-title">
                    <a href={`/users/${member.user.id}`} data-link>
                      <strong>{member.user.name}</strong>
                    </a>
                    <GitHubConnectButton
                      userId={member.user.id}
                      initialUsername={member.user.githubUsername ?? null}
                    />
                  </div>
                  <small>{member.user.role}</small>
                  <div className="progress-track" aria-label={t("prof.percentComplete", { rate })}>
                    <span style={{ width: `${rate}%` }} />
                  </div>
                </div>
                <dl className="member-metrics">
                  <div>
                    <dt>{t("prof.activities")}</dt>
                    <dd>{member.totalActivities}</dd>
                  </div>
                  <div>
                    <dt>{t("prof.done")}</dt>
                    <dd>{member.completedActivities}</dd>
                  </div>
                  <div>
                    <dt>{t("prof.activeProjects")}</dt>
                    <dd>{member.activeProjects}</dd>
                  </div>
                  <div>
                    <dt>{t("prof.lastActivity")}</dt>
                    <dd>{member.latestActivityDate ?? "—"}</dd>
                  </div>
                </dl>
                <a
                  className="card-arrow"
                  href={`/users/${member.user.id}`}
                  data-link
                  aria-label={`Open ${member.user.name} dashboard`}
                >
                  ↗
                </a>
              </div>
            );
          })}
        </div>
      </section>

      <section className="dashboard-card professor-recent">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("prof.acrossTeam")}</p>
            <h2>{t("prof.recentActivity")}</h2>
          </div>
          <span className="member-count">{t("prof.latest20")}</span>
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
                <span className={`pill ${activity.status}`}>{t(`status.${activity.status}`)}</span>
                <time>{activity.date}</time>
              </article>
            ))}
          </div>
        ) : (
          <StatusMessage>{t("timeline.noActivities")}</StatusMessage>
        )}
      </section>

      <GitHubContributionPanel />
      <ProfessorReviewQueue />
      <ProfessorSubmissionPanel />
    </section>
  );
}
