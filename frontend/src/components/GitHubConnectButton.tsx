import { useEffect, useState } from "react";

import { connectGitHub, getGitHubStatus } from "../api";
import "../github-connect.css";
import { useI18n } from "../i18n";
import type { GithubStatus } from "../types";

interface GitHubConnectButtonProps {
  /** Student user id this button belongs to (used for display-only mode). */
  userId: string;
  /** Known GitHub username from the tracked profile (professor/read-only view). */
  initialUsername?: string | null;
  /**
   * When true the button manages its own GitHub service connection
   * (student's own workspace). When false it renders read-only boxes:
   * the linked GitHub id, or a "not connected yet" note. Professors
   * can never connect on behalf of a student.
   */
  canConnect?: boolean;
}

function GitHubLogo() {
  return (
    <svg className="gh-connect-logo" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>
  );
}

function LinkedIdBox({ username, title }: { username: string; title: string }) {
  return (
    <span className="gh-connect-slot">
      <span className="gh-status-box is-linked" role="status" title={title}>
        <GitHubLogo />
        <a
          className="gh-connect-id"
          href={`https://github.com/${username}`}
          target="_blank"
          rel="noreferrer"
        >
          @{username}
        </a>
      </span>
    </span>
  );
}

export default function GitHubConnectButton({
  userId,
  initialUsername = null,
  canConnect = false,
}: GitHubConnectButtonProps) {
  const { t } = useI18n();
  const [status, setStatus] = useState<GithubStatus | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [username, setUsername] = useState("");
  const [token, setToken] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");

  // Automatically check the GitHub service: load live status on mount
  // for the student's own workspace.
  useEffect(() => {
    if (!canConnect) return;
    let active = true;
    getGitHubStatus()
      .then((next) => {
        if (active) setStatus(next);
      })
      .catch(() => {
        if (active) {
          setStatus({
            connected: false,
            username: null,
            syncedAt: null,
            canPush: false,
          });
        }
      });
    return () => {
      active = false;
    };
  }, [canConnect, userId]);

  // Professor / read-only view: status boxes only, never a button. The
  // professor can never connect on behalf of a student.
  if (!canConnect) {
    const linkedUsername = (initialUsername ?? "").trim();
    if (linkedUsername) {
      return (
        <LinkedIdBox
          username={linkedUsername}
          title={t("gh.connectedAs", { username: linkedUsername })}
        />
      );
    }
    return (
      <span className="gh-connect-slot">
        <span className="gh-status-box is-unlinked" role="status">
          <GitHubLogo />
          <span>{t("gh.notConnectedYet")}</span>
        </span>
      </span>
    );
  }

  const liveUsername = status?.username?.trim() || (initialUsername ?? "").trim();

  async function handleConnect() {
    const trimmedUsername = username.trim();
    if (!trimmedUsername || connecting) return;
    setConnecting(true);
    setError("");
    try {
      // Authorized through the GitHub service: the backend verifies the
      // username, and verifies a supplied token live against api.github.com.
      const next = await connectGitHub(trimmedUsername, token.trim() || null);
      setStatus(next);
      setUsername("");
      setToken("");
      setExpanded(false);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("gh.connectError"));
    } finally {
      setConnecting(false);
    }
  }

  // Connected student dashboard: show just the student GitHub id in the
  // shared green box, no connect button.
  if (status?.connected && liveUsername) {
    return (
      <LinkedIdBox
        username={liveUsername}
        title={t("gh.connectedAs", { username: liveUsername })}
      />
    );
  }

  return (
    <span className="gh-connect-slot">
      {!expanded ? (
        <button
          className="gh-connect"
          type="button"
          onClick={() => {
            setError("");
            setExpanded(true);
          }}
        >
          <GitHubLogo />
          <span>{t("gh.connectGitHub")}</span>
        </button>
      ) : (
        <span className="gh-connect-form-mini">
          <label className="gh-connect-label">
            <span>{t("gh.username")}</span>
            <input
              type="text"
              value={username}
              maxLength={39}
              placeholder={t("gh.usernamePlaceholder")}
              aria-label={t("gh.username")}
              title={t("gh.usernameHint")}
              autoComplete="username"
              onChange={(event) => setUsername(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void handleConnect();
                if (event.key === "Escape") setExpanded(false);
              }}
            />
            <small className="gh-connect-hint">{t("gh.usernameHint")}</small>
          </label>
          <label className="gh-connect-label">
            <span>{t("gh.token")}</span>
            <input
              type="password"
              value={token}
              placeholder={t("gh.tokenPlaceholder")}
              aria-label={t("gh.token")}
              title={t("gh.tokenHint")}
              autoComplete="off"
              onChange={(event) => setToken(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void handleConnect();
                if (event.key === "Escape") setExpanded(false);
              }}
            />
            <small className="gh-connect-hint">{t("gh.tokenHint")}</small>
          </label>
          {error ? <p className="gh-connect-error">{error}</p> : null}
          <span className="gh-connect-actions">
            <button
              className="gh-connect connected"
              type="button"
              disabled={connecting || !username.trim()}
              onClick={() => void handleConnect()}
            >
              {connecting ? t("gh.connecting") : t("gh.connect")}
            </button>
            <button className="gh-connect" type="button" onClick={() => setExpanded(false)}>
              {t("form.cancel")}
            </button>
          </span>
        </span>
      )}
    </span>
  );
}
