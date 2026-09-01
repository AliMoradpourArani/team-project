import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ErrorBoundary from "./ErrorBoundary";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ErrorBoundary", () => {
  it("shows a recoverable fallback when a child render fails", () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    function BrokenComponent(): never {
      throw new Error("render failed");
    }

    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong");
    expect(screen.getByRole("button", { name: "Reload application" })).toBeInTheDocument();
  });
});
