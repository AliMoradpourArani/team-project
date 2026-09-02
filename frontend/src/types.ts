export type ActivityStatus = "planned" | "in-progress" | "completed";
export type AuthRole = "student" | "professor";
export type ProjectReviewStatus = "in-review" | "changes-requested" | "approved";

export interface User {
  id: string;
  name: string;
  role: string;
  githubUsername?: string | null;
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

export interface ProjectIntegration {
  projectId: string;
  userId: string;
  name: string;
  integrationStatus: "ready" | "not-integrated" | "invalid";
  runnerEnabled: boolean;
  runnable: boolean;
  previewable?: boolean;
  demoMode?: "execute" | "preview" | null;
  projectType: string | null;
  runner: string | null;
  entryPoint: string | null;
  repositoryPath: string | null;
  reason: string | null;
}

export interface ProjectHealthCheck {
  key: string;
  label: string;
  passed: boolean;
  detail: string;
}

export interface ProjectPreview {
  kind: "static-html" | "openapi-json";
  content: string;
  summary: string;
  truncated: boolean;
}

export interface ProjectRunHistoryItem {
  id: number;
  projectId: string;
  runner: string;
  exitCode: number | null;
  timedOut: boolean;
  durationMs: number;
  stdoutPreview: string;
  stderrPreview: string;
  outputTruncated: boolean;
  createdAt: string;
}

export interface ProjectDetail {
  project: Project;
  integration: ProjectIntegration;
  health: ProjectHealthCheck[];
  healthPassed: number;
  healthTotal: number;
  readme: string | null;
  preview?: ProjectPreview | null;
  recentRuns: ProjectRunHistoryItem[];
}

export interface ProjectRunResult {
  projectId: string;
  runner: string;
  exitCode: number | null;
  timedOut: boolean;
  durationMs: number;
  stdout: string;
  stderr: string;
  outputTruncated: boolean;
}

export interface ProjectReviewInput {
  status: ProjectReviewStatus;
  functionalityScore: number;
  codeQualityScore: number;
  documentationScore: number;
  integrationScore: number;
  contributionScore: number;
  feedback: string;
}

export interface ProjectReview extends ProjectReviewInput {
  projectId: string;
  reviewerUsername: string;
  totalScore: number;
  updatedAt: string;
}

export interface ProfessorReviewQueueItem {
  project: Project;
  review: ProjectReview | null;
}

export interface ProfessorReviewQueueData {
  totalProjects: number;
  pending: number;
  inReview: number;
  changesRequested: number;
  approved: number;
  items: ProfessorReviewQueueItem[];
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

export interface GitHubRepositorySummary {
  fullName: string;
  url: string;
  defaultBranch: string;
  openPullRequests: number;
  lastPushedAt: string | null;
}

export interface GitHubMemberContribution {
  userId: string;
  displayName: string;
  githubUsername: string | null;
  linked: boolean;
  commits: number;
  pullRequests: number;
  openPullRequests: number;
  mergedPullRequests: number;
  latestContributionAt: string | null;
}

export interface GitHubTimelineEvent {
  kind: "commit" | "pull-request";
  userId: string;
  githubUsername: string;
  title: string;
  url: string;
  occurredAt: string;
  detail: string;
}

export interface ProfessorGitHubDashboardData {
  status: "ok" | "unavailable";
  message: string | null;
  repository: GitHubRepositorySummary | null;
  members: GitHubMemberContribution[];
  timeline: GitHubTimelineEvent[];
  generatedAt: string;
}
