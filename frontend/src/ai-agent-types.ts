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
}
