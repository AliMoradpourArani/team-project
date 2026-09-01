import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ProjectDemoPreview from "./ProjectDemoPreview";

describe("ProjectDemoPreview", () => {
  it("renders static HTML in a sandboxed iframe", () => {
    render(
      <ProjectDemoPreview
        preview={{
          kind: "static-html",
          content:
            "<h1>Student site</h1><script>window.top.location='https://example.com'</script>",
          summary: "Sandboxed static HTML preview.",
          truncated: false,
        }}
      />,
    );

    const frame = screen.getByTitle("Sandboxed static project preview");
    expect(frame).toHaveAttribute("sandbox", "");
    expect(frame).toHaveAttribute("referrerpolicy", "no-referrer");
    expect(frame.getAttribute("srcdoc")).toContain("Content-Security-Policy");
    expect(frame.getAttribute("srcdoc")).toContain("script-src 'none'");
    expect(frame.getAttribute("srcdoc")).toContain("Student site");
  });

  it("renders OpenAPI JSON as text", () => {
    render(
      <ProjectDemoPreview
        preview={{
          kind: "openapi-json",
          content: '{\n  "openapi": "3.1.0"\n}',
          summary: "Student API · OpenAPI 3.1.0 · 2 paths",
          truncated: false,
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "OpenAPI contract" })).toBeInTheDocument();
    expect(screen.getByText("Student API · OpenAPI 3.1.0 · 2 paths")).toBeInTheDocument();
    const preview = document.querySelector("pre.project-openapi-preview");
    expect(preview).toHaveTextContent('"openapi": "3.1.0"');
  });
});
