import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getProjectFiles } from "../api";
import type { Activity } from "../types";
import ActivityForm from "./ActivityForm";

vi.mock("../api", () => ({
  createActivity: vi.fn(),
  getProjectFiles: vi.fn(),
  updateActivity: vi.fn(),
}));

const editing: Activity = {
  id: "a1",
  userId: "ali",
  date: "2026-09-01",
  title: "some work",
  status: "in-progress",
  projectId: "demo",
};

const baseProps = {
  userId: "ali",
  projects: [
    {
      id: "demo",
      userId: "ali",
      name: "demo",
      description: "demo project",
      technology: ["Python"],
      status: "active",
    },
  ],
  editing,
  onSaved: vi.fn(),
  onCancelEdit: vi.fn(),
};

describe("ActivityForm attached files", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getProjectFiles).mockResolvedValue([
      { path: "main.py", name: "main.py", isDirectory: false, size: 10 },
      { path: "app", name: "app", isDirectory: true, size: 0 },
    ]);
  });

  it("lists previously attached code files when editing a linked activity", async () => {
    const onOpenInEditor = vi.fn();
    render(<ActivityForm {...baseProps} onOpenInEditor={onOpenInEditor} />);

    expect(await screen.findByText("Attached code files")).toBeInTheDocument();
    expect(await screen.findByText("main.py")).toBeInTheDocument();
    expect(screen.queryByText("app")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open in code editor" }));
    expect(onOpenInEditor).toHaveBeenCalledWith("demo", "main.py");
  });

  it("shows no attached files section for a brand-new activity", () => {
    render(<ActivityForm {...baseProps} editing={null} />);

    expect(screen.queryByText("Attached code files")).not.toBeInTheDocument();
    expect(getProjectFiles).not.toHaveBeenCalled();
  });
});
