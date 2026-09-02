import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Activity } from "../types";
import CalendarView from "./CalendarView";

const activities: Activity[] = [
  {
    id: "hossein-2026-09-02-review",
    userId: "hossein",
    date: "2026-09-02",
    title: "Review pull requests",
    status: "planned",
    projectId: null,
  },
];

describe("CalendarView", () => {
  it("shows activities for a selected date", () => {
    render(<CalendarView activities={activities} />);

    fireEvent.click(screen.getByRole("button", { name: "2026-09-02, 1 activity" }));
    expect(screen.getByText("Review pull requests")).toBeInTheDocument();
  });

  it("moves to the month of a newly created or rescheduled activity", () => {
    const augustActivity: Activity = {
      id: "hossein-2026-08-31-existing",
      userId: "hossein",
      date: "2026-08-31",
      title: "Existing activity",
      status: "planned",
      projectId: null,
    };
    const septemberActivity: Activity = {
      id: "hossein-2026-09-01-new",
      userId: "hossein",
      date: "2026-09-01",
      title: "New September activity",
      status: "planned",
      projectId: null,
    };
    const { rerender } = render(<CalendarView activities={[augustActivity]} />);

    rerender(<CalendarView activities={[augustActivity, septemberActivity]} />);

    expect(screen.getByRole("button", { name: "2026-09-01, 1 activity" })).toBeInTheDocument();
    expect(screen.getByText("New September activity")).toBeInTheDocument();
  });
});
