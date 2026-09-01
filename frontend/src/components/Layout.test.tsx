import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Layout from "./Layout";

describe("Layout", () => {
  it("renders navigation tabs", () => {
    render(<Layout currentPath="/">Home content</Layout>);

    expect(screen.getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Ali-Workspace" })).toHaveAttribute(
      "href",
      "/ali-workspace",
    );
  });

  it("marks the Ali-Workspace tab active on its path", () => {
    render(<Layout currentPath="/ali-workspace">Workspace content</Layout>);

    const tab = screen.getByRole("link", { name: "Ali-Workspace" });
    expect(tab).toHaveClass("nav-tab-active");
    expect(tab).toHaveAttribute("aria-current", "page");
  });

  it("does not mark Home active on other pages", () => {
    render(<Layout currentPath="/ali-workspace">Workspace content</Layout>);

    expect(screen.getByRole("link", { name: "Home" })).not.toHaveClass("nav-tab-active");
  });
});
