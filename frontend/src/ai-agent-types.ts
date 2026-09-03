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

export type AIStreamEvent =
  | { type: "start"; threadId: string }
  | { type: "delta"; value: string }
  | { type: "error"; message: string }
  | { type: "done"; reply: AIAgentReply };

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

export interface AIWeeklyBrief {
  projectId: string | null;
  headline: string;
  progressPercent: number;
  healthScore: number;
  completedTasks: number;
  inProgressTasks: number;
  overdueTasks: number;
  githubSignals: number;
  risks: string[];
  nextWeek: string[];
}

export interface AIHealthScore {
  projectId: string | null;
  overall: number;
  delivery: number;
  code: number;
  security: number;
  tests: number;
  schedule: number;
  documentation: number;
  reasons: string[];
}

export interface AIRepoIndexResult {
  projectId: string | null;
  filesIndexed: number;
  chunksIndexed: number;
  skippedFiles: number;
}

export interface AIProgressChange {
  activityId: string;
  fromStatus: string;
  toStatus: string;
  reason: string;
  applied: boolean;
}

export interface AIProgressSyncResult {
  projectId: string | null;
  changes: AIProgressChange[];
  updatedActivities: Activity[];
}

export interface AIOrchestrationResult {
  projectId: string | null;
  executiveSummary: string;
  consensus: string[];
  disagreements: string[];
  nextActions: string[];
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
