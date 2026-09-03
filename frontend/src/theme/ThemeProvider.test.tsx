import { render, screen, fireEvent } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { applyInitialTheme, ThemeProvider, useTheme } from "./ThemeProvider";

function Probe() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button type="button" onClick={toggleTheme}>
      theme:{theme}
    </button>
  );
}

beforeEach(() => {
  window.localStorage.clear();
  delete document.documentElement.dataset.theme;
});

describe("ThemeProvider", () => {
  it("defaults to light and does not auto-set a dark attribute", () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );
    expect(screen.getByRole("button").textContent).toBe("theme:light");
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("toggles between light and dark", () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("button").textContent).toBe("theme:dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("button").textContent).toBe("theme:light");
  });

  it("persists the theme to localStorage", () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByRole("button"));
    expect(window.localStorage.getItem("forgeflow.theme")).toBe("dark");
  });

  it("migrates a legacy team-project.theme value", () => {
    window.localStorage.setItem("team-project.theme", "dark");
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );
    expect(screen.getByRole("button").textContent).toBe("theme:dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("applyInitialTheme sets the attribute before rendering", () => {
    window.localStorage.setItem("forgeflow.theme", "dark");
    applyInitialTheme();
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
