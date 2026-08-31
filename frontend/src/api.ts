import type { Activity, Project, User } from "./types";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

async function getCollection<T>(name: string): Promise<T[]> {
  const response = await fetch(`${API_BASE_URL}/api/${name}`);
  if (!response.ok) {
    throw new Error(`Could not load ${name}.`);
  }
  return (await response.json()) as T[];
}

export const getUsers = (): Promise<User[]> => getCollection<User>("users");
export const getActivities = (): Promise<Activity[]> => getCollection<Activity>("activities");
export const getProjects = (): Promise<Project[]> => getCollection<Project>("projects");
