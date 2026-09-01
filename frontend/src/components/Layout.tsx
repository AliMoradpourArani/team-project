import type { ReactNode } from "react";

import type { AuthSession } from "../types";

interface Props {
  children: ReactNode;
  session?: AuthSession | null;
  onLogout?: () => void;
}

export default function Layout({ children, session, onLogout }: Props) {
  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" data-link>
          Team Project
        </a>
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
