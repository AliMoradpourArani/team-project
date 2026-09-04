import type {
  AIAgentReply,
  AIAgentReplanResponse,
  AIAgentSnapshot,
  AIAgentThread,
  AIDailyBrief,
  AIHealthScore,
  AIMultiAgentReview,
  AIOrchestrationResult,
  AIProgressSyncResult,
  AIRepoIndexResult,
  AIStreamEvent,
  AIWeeklyBrief,
} from "./ai-agent-types";
import type {
  Activity,
  ActivityInput,
  AIStatus,
  AIWorkspaceInput,
  AIWorkspaceResult,
  AuthSession,
  DeliveryPreflightData,
  GithubImportResponse,
  GithubRepo,
  GithubStatus,
  ProfessorDashboardData,
  ProfessorGitHubDashboardData,
  ProfessorReviewQueueData,
  ProfessorSubmissionDashboardData,
  Project,
  ProjectCommitResponse,
  ProjectDetail,
  ProjectFile,
  ProjectFileEntry,
  ProjectIntegration,
  ProjectOnboarding,
  ProjectReview,
  ProjectReviewInput,
  ProjectRunResult,
  ProjectSubmission,
  ProjectSubmissionStatus,
  SubmissionReleaseDetail,
  SubmissionReleaseSummary,
  SubmissionSettings,
  SubmissionSettingsInput,
  User,
} from "./types";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

let csrfToken = "";

export class UnauthorizedError extends Error {}

async function parseError(response: Response): Promise<Error> {
  try {
    const body = (await response.json()) as { detail?: string; error?: string };
    const message = body.detail ?? body.error ?? `Request failed with ${response.status}.`;
    return response.status === 401 ? new UnauthorizedError(message) : new Error(message);
  } catch {
    const message = `Request failed with ${response.status}.`;
    return response.status === 401 ? new UnauthorizedError(message) : new Error(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && csrfToken) {
    headers.set("X-CSRF-Token", csrfToken);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function getCollection<T>(name: string): Promise<T[]> {
  return request<T[]>(`/api/${name}`);
}

function projectQuery(projectId: string | null): string {
  return projectId ? `?projectId=${encodeURIComponent(projectId)}` : "";
}

export async function login(username: string, password: string): Promise<AuthSession> {
  const session = await request<AuthSession>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  csrfToken = session.csrfToken;
  return session;
}

export async function getMe(): Promise<AuthSession> {
  const session = await request<AuthSession>("/api/auth/me");
  csrfToken = session.csrfToken;
  return session;
}

export async function logout(): Promise<void> {
  await request<void>("/api/auth/logout", { method: "POST" });
  csrfToken = "";
}

export const getUsers = (): Promise<User[]> => getCollection<User>("users");
export const getActivities = (): Promise<Activity[]> => getCollection<Activity>("activities");
export const getProjects = (): Promise<Project[]> => getCollection<Project>("projects");
export const getAIStatus = (): Promise<AIStatus> => request<AIStatus>("/api/ai/status");
export const getAIThreads = (): Promise<AIAgentThread[]> =>
  request<AIAgentThread[]>("/api/ai/threads");
export const getProjectIntegrations = (): Promise<ProjectIntegration[]> =>
  request<ProjectIntegration[]>("/api/projects/integrations");
export const getProjectOnboardingList = (): Promise<ProjectOnboarding[]> =>
  request<ProjectOnboarding[]>("/api/projects/onboarding");
export const getProjectDetail = (projectId: string): Promise<ProjectDetail> =>
  request<ProjectDetail>(`/api/projects/${projectId}/detail`);
export const getProjectOnboarding = (projectId: string): Promise<ProjectOnboarding> =>
  request<ProjectOnboarding>(`/api/projects/${projectId}/onboarding`);
export const getProjectReview = (projectId: string): Promise<ProjectReview | null> =>
  request<ProjectReview | null>(`/api/projects/${projectId}/review`);
export const getProjectSubmissionStatus = (projectId: string): Promise<ProjectSubmissionStatus> =>
  request<ProjectSubmissionStatus>(`/api/projects/${projectId}/submission`);
export const getProfessorDashboard = (): Promise<ProfessorDashboardData> =>
  request<ProfessorDashboardData>("/api/professor/dashboard");
export const getProfessorGitHubDashboard = (): Promise<ProfessorGitHubDashboardData> =>
  request<ProfessorGitHubDashboardData>("/api/professor/github");
export const getProfessorReviewQueue = (): Promise<ProfessorReviewQueueData> =>
  request<ProfessorReviewQueueData>("/api/professor/reviews");
export const getProfessorSubmissionDashboard = (): Promise<ProfessorSubmissionDashboardData> =>
  request<ProfessorSubmissionDashboardData>("/api/professor/submissions");
export const getProfessorDeliveryPreflight = (): Promise<DeliveryPreflightData> =>
  request<DeliveryPreflightData>("/api/professor/preflight");
export const getSubmissionReleases = (): Promise<SubmissionReleaseSummary[]> =>
  request<SubmissionReleaseSummary[]>("/api/professor/releases");
export const getSubmissionRelease = (releaseId: number): Promise<SubmissionReleaseDetail> =>
  request<SubmissionReleaseDetail>(`/api/professor/releases/${releaseId}`);

export async function runAIWorkspace(payload: AIWorkspaceInput): Promise<AIWorkspaceResult> {
  return request<AIWorkspaceResult>("/api/ai/workspace", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createAIThread(projectId: string | null): Promise<AIAgentThread> {
  return request<AIAgentThread>("/api/ai/threads", {
    method: "POST",
    body: JSON.stringify({ projectId, title: "Project copilot" }),
  });
}

export const getAIAgentSnapshot = (threadId: string): Promise<AIAgentSnapshot> =>
  request<AIAgentSnapshot>(`/api/ai/threads/${threadId}/snapshot`);

export async function postAIMessage(threadId: string, content: string): Promise<AIAgentReply> {
  return request<AIAgentReply>(`/api/ai/threads/${threadId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function streamAIMessage(
  threadId: string,
  content: string,
  onDelta: (delta: string) => void,
): Promise<AIAgentReply> {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
  const response = await fetch(`${API_BASE_URL}/api/ai/threads/${threadId}/messages/stream`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify({ content }),
  });
  if (!response.ok) throw await parseError(response);
  if (!response.body) throw new Error("The AI stream is not available in this browser.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalReply: AIAgentReply | null = null;

  const handleEvent = (raw: string): void => {
    const dataLine = raw.split("\n").find((line) => line.startsWith("data:"));
    if (!dataLine) return;
    const event = JSON.parse(dataLine.slice(5).trim()) as AIStreamEvent;
    if (event.type === "delta") {
      onDelta(event.value);
    } else if (event.type === "done") {
      finalReply = event.reply;
    } else if (event.type === "error") {
      throw new Error(event.message);
    }
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const raw of parts) {
      if (raw.trim()) handleEvent(raw);
    }
  }
  if (buffer.trim()) handleEvent(buffer);
  if (!finalReply) throw new Error("The AI stream ended without a final reply.");
  return finalReply;
}

export async function replanAIThread(
  threadId: string,
  applyTasks: boolean,
  taskCount = 5,
): Promise<AIAgentReplanResponse> {
  return request<AIAgentReplanResponse>(`/api/ai/threads/${threadId}/replan`, {
    method: "POST",
    body: JSON.stringify({ applyTasks, taskCount }),
  });
}

export const getAIDailyBrief = (projectId: string | null): Promise<AIDailyBrief> =>
  request<AIDailyBrief>(`/api/ai/brief${projectQuery(projectId)}`);

export const getAIWeeklyBrief = (projectId: string | null): Promise<AIWeeklyBrief> =>
  request<AIWeeklyBrief>(`/api/ai/weekly-brief${projectQuery(projectId)}`);

export const getAIHealth = (projectId: string | null): Promise<AIHealthScore> =>
  request<AIHealthScore>(`/api/ai/health${projectQuery(projectId)}`);

export const getAIMultiAgentReview = (projectId: string | null): Promise<AIMultiAgentReview> =>
  request<AIMultiAgentReview>(`/api/ai/multi-agent-review${projectQuery(projectId)}`);

export const getAIOrchestration = (projectId: string | null): Promise<AIOrchestrationResult> =>
  request<AIOrchestrationResult>(`/api/ai/orchestrate${projectQuery(projectId)}`);

export async function indexAIRepository(projectId: string | null): Promise<AIRepoIndexResult> {
  return request<AIRepoIndexResult>(`/api/ai/repo/index${projectQuery(projectId)}`, {
    method: "POST",
  });
}

export async function syncAIProgress(
  projectId: string | null,
  apply: boolean,
): Promise<AIProgressSyncResult> {
  return request<AIProgressSyncResult>("/api/ai/progress/sync", {
    method: "POST",
    body: JSON.stringify({ projectId, apply }),
  });
}

export async function refreshAINotifications(projectId: string | null): Promise<void> {
  await request(`/api/ai/notifications/refresh${projectQuery(projectId)}`, { method: "POST" });
}

export async function deleteAIThread(threadId: string): Promise<void> {
  await request<void>(`/api/ai/threads/${threadId}`, { method: "DELETE" });
}

export async function runProject(projectId: string): Promise<ProjectRunResult> {
  return request<ProjectRunResult>(`/api/projects/${projectId}/run`, { method: "POST" });
}

export async function saveProjectReview(
  projectId: string,
  payload: ProjectReviewInput,
): Promise<ProjectReview> {
  return request<ProjectReview>(`/api/projects/${projectId}/review`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteProjectReview(projectId: string): Promise<void> {
  await request<void>(`/api/projects/${projectId}/review`, { method: "DELETE" });
}

export async function submitProject(projectId: string): Promise<ProjectSubmission> {
  return request<ProjectSubmission>(`/api/projects/${projectId}/submit`, { method: "POST" });
}

export async function saveSubmissionSettings(
  payload: SubmissionSettingsInput,
): Promise<SubmissionSettings> {
  return request<SubmissionSettings>("/api/professor/submission-settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function createSubmissionRelease(label: string): Promise<SubmissionReleaseDetail> {
  return request<SubmissionReleaseDetail>("/api/professor/releases", {
    method: "POST",
    body: JSON.stringify({ label }),
  });
}

export async function createActivity(payload: ActivityInput): Promise<Activity> {
  return request<Activity>("/api/activities", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateActivity(id: string, payload: ActivityInput): Promise<Activity> {
  return request<Activity>(`/api/activities/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteActivity(id: string): Promise<void> {
  await request<void>(`/api/activities/${id}`, { method: "DELETE" });
}

export async function deleteProject(projectId: string): Promise<void> {
  await request<void>(`/api/projects/${projectId}`, { method: "DELETE" });
}

export const getGitHubStatus = (): Promise<GithubStatus> =>
  request<GithubStatus>("/api/github/status");

export function connectGitHub(username: string, token: string | null): Promise<GithubStatus> {
  return request<GithubStatus>("/api/github/connect", {
    method: "POST",
    body: JSON.stringify({ username, token }),
  });
}

export async function disconnectGitHub(): Promise<{ connected: boolean }> {
  return request<{ connected: boolean }>("/api/github/disconnect", { method: "POST" });
}

export function importGitHubRepo(fullName: string): Promise<GithubImportResponse> {
  return request<GithubImportResponse>("/api/github/import", {
    method: "POST",
    body: JSON.stringify({ fullName }),
  });
}

export const getGitHubRepos = (): Promise<GithubRepo[]> =>
  request<GithubRepo[]>("/api/github/repos");

export function getProjectFiles(projectId: string): Promise<ProjectFileEntry[]> {
  return request<ProjectFileEntry[]>(`/api/projects/${projectId}/files`);
}

export function getProjectFile(projectId: string, path: string): Promise<ProjectFile> {
  return request<ProjectFile>(`/api/projects/${projectId}/file?path=${encodeURIComponent(path)}`);
}

export function saveProjectFile(
  projectId: string,
  path: string,
  content: string,
): Promise<ProjectFile> {
  return request<ProjectFile>(`/api/projects/${projectId}/file`, {
    method: "PUT",
    body: JSON.stringify({ path, content }),
  });
}

export function commitProject(projectId: string, message: string): Promise<ProjectCommitResponse> {
  return request<ProjectCommitResponse>(`/api/projects/${projectId}/commit`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
