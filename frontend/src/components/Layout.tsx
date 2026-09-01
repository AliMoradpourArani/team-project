import type { ReactNode } from "react";

import type { AuthSession } from "../types";

interface Props {
  children: ReactNode;
  session?: AuthSession | null;
  onLogout?: () => void;
  currentPath?: string;
}

export default function Layout({ children, session, onLogout, currentPath = "/" }: Props) {
  const normalizedPath = currentPath.replace(/\/+$/, "") || "/";
  const homeHref =
    session?.role === "professor"
      ? "/professor"
      : session?.role === "student" && session.userId
        ? `/users/${session.userId}`
        : "/";
  const tabs =
    session?.role === "professor"
      ? [{ href: "/professor", label: "Team dashboard" }]
      : session?.role === "student" && session.userId
        ? [{ href: `/users/${session.userId}`, label: "My dashboard" }]
        : [];

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href={homeHref} data-link>
          Team Project
        </a>
        {tabs.length > 0 ? (
          <nav className="site-nav" aria-label="Main navigation">
            {tabs.map((tab) => {
              const isActive = normalizedPath === tab.href;
              return (
                <a
                  className={`nav-tab${isActive ? " nav-tab-active" : ""}`}
                  href={tab.href}
                  data-link
                  key={tab.href}
                  aria-current={isActive ? "page" : undefined}
                >
                  {tab.label}
                </a>
              );
            })}
          </nav>
        ) : null}
        {session ? (
          <div className="header-session">
            <span className="header-label">
              {session.displayName} · {session.role}
            </span>
            <button className="header-logout" type="button" onClick={onLogout}>
              Sign out
            </button>
          </div>
        ) : (
          <span className="header-label">Protected local workspace</span>
        )}
      </header>
      <main className="page-content">{children}</main>
    </div>
  );
}
