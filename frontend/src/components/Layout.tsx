import type { ReactNode } from "react";

import { useI18n } from "../i18n";
import LanguageSwitcher from "../i18n/LanguageSwitcher";
import type { AuthSession } from "../types";

interface Props {
  children: ReactNode;
  session?: AuthSession | null;
  onLogout?: () => void;
  currentPath?: string;
}

export default function Layout({ children, session, onLogout, currentPath = "/" }: Props) {
  const { t } = useI18n();
  const tabs = [
    { href: "/", label: t("nav.home") },
    { href: "/ali-workspace", label: t("nav.aliWorkspace") },
  ];
  const normalizedPath = currentPath.replace(/\/+$/, "") || "/";

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" data-link>
          Team Project
        </a>
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
        <div className="header-tools">
          <LanguageSwitcher />
          {session ? (
            <div className="header-session">
              <span className="header-label">
                {session.displayName} · {session.role}
              </span>
              <button className="header-logout" type="button" onClick={onLogout}>
                {t("header.signOut")}
              </button>
            </div>
          ) : (
            <span className="header-label">{t("header.protectedWorkspace")}</span>
          )}
        </div>
      </header>
      <main className="page-content">{children}</main>
    </div>
  );
}
