import { useEffect, useState } from "react";

import { getProfessorGitHubDashboard } from "../api";
import type { ProfessorGitHubDashboardData } from "../types";
import StatusMessage from "./StatusMessage";

function shortDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function GitHubContributionPanel() {
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
            <p className="eyebrow">GitHub integration</p>
            <h2>Repository activity</h2>
          </div>
        </div>
        <StatusMessage error>{error}</StatusMessage>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="dashboard-card github-panel">
        <StatusMessage>Loading GitHub contribution data…</StatusMessage>
      </section>
    );
  }

  if (data.status === "unavailable" || !data.repository) {
    return (
      <section className="dashboard-card github-panel">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">GitHub integration</p>
            <h2>Repository activity</h2>
          </div>
          <span className="member-count">offline-safe</span>
        </div>
        <StatusMessage>{data.message ?? "GitHub contribution data is unavailable."}</StatusMessage>
      </section>
    );
  }

  return (
    <section className="dashboard-card github-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">GitHub integration</p>
          <h2>Repository activity</h2>
        </div>
        <a className="text-link" href={data.repository.url} target="_blank" rel="noreferrer">
          Open repository ↗
        </a>
      </div>

      <div className="github-repository-strip">
        <div>
          <span>Repository</span>
          <strong>{data.repository.fullName}</strong>
        </div>
        <div>
          <span>Default branch</span>
          <strong>{data.repository.defaultBranch}</strong>
        </div>
        <div>
          <span>Open PRs</span>
          <strong>{data.repository.openPullRequests}</strong>
        </div>
        <div>
          <span>Last push</span>
          <strong>{shortDate(data.repository.lastPushedAt)}</strong>
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
                  <small>GitHub not linked</small>
                )}
              </div>
              <span className={`github-link-state ${member.linked ? "linked" : "unlinked"}`}>
                {member.linked ? "linked" : "not linked"}
              </span>
            </div>
            <dl className="github-member-metrics">
              <div>
                <dt>Commits</dt>
                <dd>{member.commits}</dd>
              </div>
              <div>
                <dt>PRs</dt>
                <dd>{member.pullRequests}</dd>
              </div>
              <div>
                <dt>Merged</dt>
                <dd>{member.mergedPullRequests}</dd>
              </div>
              <div>
                <dt>Open</dt>
                <dd>{member.openPullRequests}</dd>
              </div>
            </dl>
            <small className="github-last-contribution">
              Latest contribution: {shortDate(member.latestContributionAt)}
            </small>
          </article>
        ))}
      </div>

      <div className="github-timeline-heading">
        <div>
          <p className="eyebrow">Contribution timeline</p>
          <h3>Recent repository work</h3>
        </div>
        <span className="member-count">latest 20</span>
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
              <time>{shortDate(event.occurredAt)}</time>
            </a>
          ))}
        </div>
      ) : (
        <StatusMessage>
          No linked GitHub contributions found in the recent repository window.
        </StatusMessage>
      )}

      <p className="github-footnote">
        GitHub counts are a repository signal, not a productivity score. Commits shown here are
        recent commits reachable from the default branch; pull requests are counted separately.
      </p>
    </section>
  );
}
