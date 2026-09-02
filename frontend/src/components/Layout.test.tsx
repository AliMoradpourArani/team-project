import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { AuthSession } from "../types";
import Layout from "./Layout";

const studentSession: AuthSession = {
  username: "ali",
  displayName: "Ali",
  role: "student",
  userId: "ali",
  csrfToken: "csrf-student",
};

const professorSession: AuthSession = {
  username: "professor",
  displayName: "Professor",
  role: "professor",
  userId: null,
  csrfToken: "csrf-professor",
};

describe("Layout", () => {
  it("does not render a user-specific navigation item before authentication", () => {
    render(<Layout currentPath="/">Home content</Layout>);

    expect(screen.queryByRole("link", { name: "Ali-Workspace" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ForgeFlow AI" })).toHaveAttribute("href", "/");
  });

  it("renders the generic student dashboard navigation from the session user id", () => {
    render(
      <Layout session={studentSession} currentPath="/users/ali">
        Student content
      </Layout>,
    );

    const dashboard = screen.getByRole("link", { name: "My dashboard" });
    expect(dashboard).toHaveAttribute("href", "/users/ali");
    expect(dashboard).toHaveClass("nav-tab-active");
    expect(dashboard).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "ForgeFlow AI" })).toHaveAttribute(
      "href",
      "/users/ali",
    );
  });

  it("renders professor navigation without student-specific routes", () => {
    render(
      <Layout session={professorSession} currentPath="/professor">
        Professor content
      </Layout>,
    );

    const dashboard = screen.getByRole("link", { name: "Team dashboard" });
    expect(dashboard).toHaveAttribute("href", "/professor");
    expect(dashboard).toHaveClass("nav-tab-active");
    expect(screen.queryByText("Ali-Workspace")).not.toBeInTheDocument();
  });
});
