import type { Activity, AIFinding, AITaskSuggestion } from "./types";

export interface AIAgentMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

export interface AIAgentThread {
  id: string;
  projectId: string | null;
  title: string;
  memory: string;
  createdAt: string;
  updatedAt: string;
  messages: AIAgentMessage[];
}

export interface AIAgentSnapshot {
  progressPercent: number;
  overdueTasks: Activity[];
  githubSignals: string[];
  findings: AIFinding[];
}

export interface AIAgentReply {
  thread: AIAgentThread;
  reply: AIAgentMessage;
  snapshot: AIAgentSnapshot;
  suggestedTasks: AITaskSuggestion[];
  provider: string;
  model: string | null;
  providerMessage: string | null;
}

export interface AIAgentReplanResponse {
  summary: string;
  tasks: AITaskSuggestion[];
  appliedActivities: Activity[];
  snapshot: AIAgentSnapshot;
}

export interface AIDailyBrief {
  projectId: string | null;
  headline: string;
  progressPercent: number;
  overdueCount: number;
  githubSignalCount: number;
  blockers: string[];
  priorities: string[];
}

export type AISpecialist =
  | "planner"
  | "project-manager"
  | "code-reviewer"
  | "debugger"
  | "progress-tracker"
  | "github-agent"
  | "documentation-agent";

export interface AISpecialistResult {
  specialist: AISpecialist;
  summary: string;
  findings: AIFinding[];
  suggestedTasks: AITaskSuggestion[];
}

export interface AIMultiAgentReview {
  projectId: string | null;
  results: AISpecialistResult[];
  executiveSummary: string;
}
