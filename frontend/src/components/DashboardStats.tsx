import type { Activity, Project } from "../types";
import { useI18n } from "../i18n";

export default function DashboardStats({
  activities,
  projects,
}: {
  activities: Activity[];
  projects: Project[];
}) {
  const { t } = useI18n();
  const completed = activities.filter((activity) => activity.status === "completed").length;
  const inProgress = activities.filter((activity) => activity.status === "in-progress").length;
  const activeProjects = projects.filter((project) => project.status === "active").length;

  return (
    <div className="stats-grid">
      <article className="stat-card">
        <span>{t("stats.totalActivities")}</span>
        <strong>{activities.length}</strong>
      </article>
      <article className="stat-card">
        <span>{t("stats.completed")}</span>
        <strong>{completed}</strong>
      </article>
      <article className="stat-card">
        <span>{t("stats.inProgress")}</span>
        <strong>{inProgress}</strong>
      </article>
      <article className="stat-card">
        <span>{t("stats.activeProjects")}</span>
        <strong>{activeProjects}</strong>
      </article>
    </div>
  );
}
