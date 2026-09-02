import { useEffect, useState } from "react";

import { getProfessorGitHubDashboard } from "../api";
import { useI18n } from "../i18n";
import type { ProfessorGitHubDashboardData } from "../types";
import StatusMessage from "./StatusMessage";

function shortDate(value: string | null, lang: string): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(lang === "fa" ? "fa-IR" : lang, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function GitHubContributionPanel() {
  const { t, lang } = useI18n();
  const [data, setData] = useState<ProfessorGitHubDashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getProfessorGitHubDashboard()
      .then(setData)
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  if (error) {
    return (
      <section className="dashboard-card github-panel">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("gh.eyebrow")}</p>
            <h2>{t("gh.repositoryActivity")}</h2>
          </div>
        </div>
        <StatusMessage error>{error}</StatusMessage>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="dashboard-card github-panel">
        <StatusMessage>{t("gh.loading")}</StatusMessage>
      </section>
    );
  }

  if (data.status === "unavailable" || !data.repository) {
    return (
      <section className="dashboard-card github-panel">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">{t("gh.eyebrow")}</p>
            <h2>{t("gh.repositoryActivity")}</h2>
          </div>
          <span className="member-count">{t("gh.offlineSafe")}</span>
        </div>
        <StatusMessage>{data.message ?? t("gh.unavailable")}</StatusMessage>
      </section>
    );
  }

  return (
    <section className="dashboard-card github-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{t("gh.eyebrow")}</p>
          <h2>{t("gh.repositoryActivity")}</h2>
        </div>
        <a className="text-link" href={data.repository.url} target="_blank" rel="noreferrer">
          {t("gh.openRepository")}
        </a>
      </div>

      <div className="github-repository-strip">
        <div>
          <span>{t("gh.repository")}</span>
          <strong>{data.repository.fullName}</strong>
        </div>
        <div>
          <span>{t("gh.defaultBranch")}</span>
          <strong>{data.repository.defaultBranch}</strong>
        </div>
        <div>
          <span>{t("gh.openPrs")}</span>
          <strong>{data.repository.openPullRequests}</strong>
        </div>
        <div>
          <span>{t("gh.lastPush")}</span>
          <strong>{shortDate(data.repository.lastPushedAt, lang)}</strong>
        </div>
      </div>

      <div className="github-member-grid">
        {data.members.map((member) => (
          <article className="github-member-card" key={member.userId}>
            <div className="github-member-heading">
              <div>
                <strong>{member.displayName}</strong>
                {member.githubUsername ? (
                  <a
                    href={`https://github.com/${member.githubUsername}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    @{member.githubUsername}
                  </a>
                ) : (
                  <small>{t("gh.notLinked")}</small>
                )}
              </div>
              <span className={`github-link-state ${member.linked ? "linked" : "unlinked"}`}>
                {member.linked ? t("gh.linked") : t("gh.notLinkedState")}
              </span>
            </div>
            <dl className="github-member-metrics">
              <div>
                <dt>{t("gh.commits")}</dt>
                <dd>{member.commits}</dd>
              </div>
              <div>
                <dt>{t("gh.prs")}</dt>
                <dd>{member.pullRequests}</dd>
              </div>
              <div>
                <dt>{t("gh.merged")}</dt>
                <dd>{member.mergedPullRequests}</dd>
              </div>
              <div>
                <dt>{t("gh.open")}</dt>
                <dd>{member.openPullRequests}</dd>
              </div>
            </dl>
            <small className="github-last-contribution">
              {t("gh.latestContribution", { date: shortDate(member.latestContributionAt, lang) })}
            </small>
          </article>
        ))}
      </div>

      <div className="github-timeline-heading">
        <div>
          <p className="eyebrow">{t("gh.contributionTimeline")}</p>
          <h3>{t("gh.recentRepositoryWork")}</h3>
        </div>
        <span className="member-count">{t("prof.latest20")}</span>
      </div>

      {data.timeline.length ? (
        <div className="github-timeline">
          {data.timeline.map((event) => (
            <a
              className="github-event"
              href={event.url}
              target="_blank"
              rel="noreferrer"
              key={`${event.kind}-${event.url}-${event.occurredAt}`}
            >
              <span className={`github-event-kind ${event.kind}`}>{event.kind}</span>
              <div>
                <strong>{event.title}</strong>
                <small>
                  @{event.githubUsername} · {event.detail}
                </small>
              </div>
              <time>{shortDate(event.occurredAt, lang)}</time>
            </a>
          ))}
        </div>
      ) : (
        <StatusMessage>{t("gh.noContributions")}</StatusMessage>
      )}

      <p className="github-footnote">{t("gh.footnote")}</p>
    </section>
  );
}
