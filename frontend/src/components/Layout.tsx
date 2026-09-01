import type { ReactNode } from "react";

export default function Layout({
  children,
  currentPath = "/",
}: {
  children: ReactNode;
  currentPath?: string;
}) {
  const tabs = [
    { href: "/", label: "Home" },
    { href: "/ali-workspace", label: "Ali-Workspace" },
  ];

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" data-link>
          Team Project
        </a>
        <nav className="site-nav" aria-label="Main navigation">
          {tabs.map((tab) => {
            const isActive =
              tab.href === "/" ? currentPath === "/" : currentPath.startsWith(tab.href);
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
        <span className="header-label">Local workspace</span>
      </header>
      <main className="page-content">{children}</main>
    </div>
  );
}
