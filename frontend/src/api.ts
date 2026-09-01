import type {
  Activity,
  ActivityInput,
  AuthSession,
  ProfessorDashboardData,
  Project,
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
export const getProfessorDashboard = (): Promise<ProfessorDashboardData> =>
  request<ProfessorDashboardData>("/api/professor/dashboard");

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
