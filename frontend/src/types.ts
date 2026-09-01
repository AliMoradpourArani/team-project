export type ActivityStatus = "planned" | "in-progress" | "completed";
export type AuthRole = "student" | "professor";

export interface User {
  id: string;
  name: string;
  role: string;
}

export interface Activity {
  id: string;
  userId: string;
  date: string;
  title: string;
  status: ActivityStatus;
  projectId: string | null;
}

export interface ActivityInput {
  userId: string;
  date: string;
  title: string;
  status: ActivityStatus;
  projectId: string | null;
}

export interface Project {
  id: string;
  userId: string;
  name: string;
  description: string;
  technology: string[];
  status: string;
}

export interface AuthSession {
  username: string;
  displayName: string;
  role: AuthRole;
  userId: string | null;
  csrfToken: string;
}

export interface ProfessorMemberSummary {
  user: User;
  totalActivities: number;
  completedActivities: number;
  inProgressActivities: number;
  plannedActivities: number;
  activeProjects: number;
  latestActivityDate: string | null;
}

export interface ProfessorDashboardData {
  totals: {
    members: number;
    activities: number;
    completedActivities: number;
    activeProjects: number;
  };
  members: ProfessorMemberSummary[];
  recentActivities: Activity[];
}
