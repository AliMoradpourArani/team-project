import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { deleteActivity, getActivities, getMe, getProjects, getUsers, logout } from "./api";
import ActivityForm from "./components/ActivityForm";
import CalendarView from "./components/CalendarView";
import DashboardStats from "./components/DashboardStats";
import Layout from "./components/Layout";
import LoginPage from "./components/LoginPage";
import ProfessorDashboard from "./components/ProfessorDashboard";
import StatusMessage from "./components/StatusMessage";
import TimelineView from "./components/TimelineView";
import type { Activity, AuthSession, Project, User } from "./types";

function useNavigation(): [string, (path: string, replace?: boolean) => void] {
  const [pathname, setPathname] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => setPathname(window.location.pathname);
    const handleLinkClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      const link = target?.closest<HTMLAnchorElement>("a[data-link]");
      if (!link || link.origin !== window.location.origin) return;
      event.preventDefault();
      window.history.pushState({}, "", link.pathname);
      setPathname(link.pathname);
    };

    window.addEventListener("popstate", handlePopState);
    document.addEventListener("click", handleLinkClick);
    return () => {
      window.removeEventListener("popstate", handlePopState);
      document.removeEventListener("click", handleLinkClick);
    };
  }, []);

  const navigate = useCallback((path: string, replace = false) => {
    if (replace) window.history.replaceState({}, "", path);
    else window.history.pushState({}, "", path);
    setPathname(path);
  }, []);

  return [pathname, navigate];
}

interface TeamState {
  users: User[];
  activities: Activity[];
  projects: Project[];
}

function UserPage({ userId, readOnly }: { userId: string; readOnly: boolean }) {
  const [state, setState] = useState<TeamState>({ users: [], activities: [], projects: [] });
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Activity | null>(null);

  async function loadData() {
    const [users, activities, projects] = await Promise.all([
      getUsers(),
      getActivities(),
      getProjects(),
    ]);
    setState({ users, activities, projects });
  }

  useEffect(() => {
    setError("");
    setEditing(null);
    loadData().catch((requestError: Error) => setError(requestError.message));
  }, [userId]);

  const user = state.users.find((candidate) => candidate.id === userId);
  const activities = state.activities.filter((activity) => activity.userId === userId);
  const projects = state.projects.filter((project) => project.userId === userId);

  async function removeActivity(activity: Activity) {
    if (readOnly || !window.confirm(`Delete "${activity.title}"?`)) return;
    try {
      await deleteActivity(activity.id);
      if (editing?.id === activity.id) setEditing(null);
      await loadData();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not delete activity.");
    }
  }

  if (error) return <StatusMessage error>{error}</StatusMessage>;
  if (state.users.length === 0) return <StatusMessage>Loading user dashboard…</StatusMessage>;
  if (!user) {
    return (
      <div className="empty-state">
        <p className="eyebrow">404</p>
        <h1>User not found</h1>
      </div>
    );
  }

  return (
    <section className="user-page">
      {readOnly ? (
        <a className="back-link" href="/professor" data-link>
          ← Professor dashboard
        </a>
      ) : null}
      <div className="profile-header dashboard-profile">
        <span className="profile-avatar">{user.name.charAt(0)}</span>
        <div>
          <p className="eyebrow">
            {readOnly ? "Professor · read-only member view" : "Member dashboard"}
          </p>
          <h1>{user.name}</h1>
          <p className="role-label">{user.role}</p>
        </div>
      </div>

      <DashboardStats activities={activities} projects={projects} />

      <div className={`dashboard-grid ${readOnly ? "read-only-dashboard-grid" : ""}`}>
        {!readOnly ? (
          <ActivityForm
            userId={userId}
            projects={projects}
            editing={editing}
            onSaved={loadData}
            onCancelEdit={() => setEditing(null)}
          />
        ) : null}
        <CalendarView activities={activities} />
      </div>

      <TimelineView
        activities={activities}
        onEdit={readOnly ? undefined : setEditing}
        onDelete={readOnly ? undefined : removeActivity}
      />

      <section className="dashboard-card projects-card">
        <div className="section-heading compact">
          <div>
            <p className="eyebrow">Projects</p>
            <h2>Connected work</h2>
          </div>
          <span className="member-count">{projects.length}</span>
        </div>
        {projects.length > 0 ? (
          <div className="project-list">
            {projects.map((project) => (
              <article className="project-item" key={project.id}>
                <span className="project-mark">↗</span>
                <div>
                  <h3>{project.name}</h3>
                  <p>{project.description}</p>
                  <small>{project.technology.join(" · ") || "No technology listed"}</small>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <StatusMessage>No projects recorded yet.</StatusMessage>
        )}
      </section>
    </section>
  );
}

export default function App() {
  const [pathname, navigate] = useNavigation();
  const [session, setSession] = useState<AuthSession | null | undefined>(undefined);

  useEffect(() => {
    getMe()
      .then((current) => {
        setSession(current);
        if (current.role === "student" && current.userId) {
          navigate(`/users/${current.userId}`, true);
        } else if (current.role === "professor" && window.location.pathname === "/") {
          navigate("/professor", true);
        }
      })
      .catch(() => setSession(null));
  }, [navigate]);

  async function signOut() {
    try {
      await logout();
    } finally {
      setSession(null);
      navigate("/", true);
    }
  }

  if (session === undefined) {
    return (
      <Layout>
        <StatusMessage>Checking session…</StatusMessage>
      </Layout>
    );
  }

  if (session === null) {
    return (
      <Layout>
        <LoginPage
          onLogin={(current) => {
            setSession(current);
            navigate(
              current.role === "professor" ? "/professor" : `/users/${current.userId}`,
              true,
            );
          }}
        />
      </Layout>
    );
  }

  const userMatch = pathname.match(/^\/users\/([^/]+)\/?$/);
  let content: ReactNode;

  if (session.role === "student") {
    if (!session.userId) {
      content = (
        <StatusMessage error>Student account is not linked to a tracked user.</StatusMessage>
      );
    } else {
      content = <UserPage userId={session.userId} readOnly={false} />;
    }
  } else if (userMatch) {
    content = <UserPage userId={userMatch[1]} readOnly />;
  } else {
    content = <ProfessorDashboard />;
  }

  return (
    <Layout session={session} onLogout={signOut}>
      {content}
    </Layout>
  );
}
