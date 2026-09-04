import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ProjectFileEntry } from "../types";
import FileTree from "./FileTree";
import { buildFileTree } from "./file-tree";

const entries: ProjectFileEntry[] = [
  { path: "main.py", name: "main.py", isDirectory: false, size: 10 },
  { path: "src", name: "src", isDirectory: true, size: 0 },
  { path: "src/app.py", name: "app.py", isDirectory: false, size: 20 },
  { path: "src/lib", name: "lib", isDirectory: true, size: 0 },
  { path: "src/lib/util.py", name: "util.py", isDirectory: false, size: 30 },
  { path: "README.md", name: "README.md", isDirectory: false, size: 5 },
];

describe("buildFileTree", () => {
  it("nests files under folders and sorts folders first", () => {
    const roots = buildFileTree(entries);

    expect(roots.map((node) => node.name)).toEqual(["src", "main.py", "README.md"]);
    const src = roots[0];
    expect(src.children.map((node) => node.name)).toEqual(["lib", "app.py"]);
    expect(src.children[0].children.map((node) => node.name)).toEqual(["util.py"]);
  });

  it("synthesizes missing intermediate folders", () => {
    const roots = buildFileTree([{ path: "a/b/c.py", name: "c.py", isDirectory: false, size: 1 }]);

    expect(roots.map((node) => node.name)).toEqual(["a"]);
    expect(roots[0].children.map((node) => node.name)).toEqual(["b"]);
    expect(roots[0].children[0].children.map((node) => node.name)).toEqual(["c.py"]);
  });
});

describe("FileTree", () => {
  it("shows top-level entries with folders collapsed by default", () => {
    render(<FileTree entries={entries} selectedPath={null} onSelectFile={() => undefined} />);

    expect(screen.getByRole("button", { name: "Expand src" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "main.py" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "app.py" })).not.toBeInTheDocument();
  });

  it("expands a folder on toggle and indents its children", () => {
    render(<FileTree entries={entries} selectedPath={null} onSelectFile={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Expand src" }));

    const child = screen.getByRole("button", { name: "app.py" });
    expect(child).toBeInTheDocument();
    const parent = screen.getByRole("button", { name: "Collapse src" });
    const childIndent = (child as HTMLButtonElement).style.paddingInlineStart;
    const parentIndent = (parent as HTMLButtonElement).style.paddingInlineStart;
    expect(parseFloat(childIndent)).toBeGreaterThan(parseFloat(parentIndent));

    fireEvent.click(parent);
    expect(screen.queryByRole("button", { name: "app.py" })).not.toBeInTheDocument();
  });

  it("selects a file and auto-expands ancestors of the selected path", () => {
    const onSelectFile = vi.fn();
    render(
      <FileTree entries={entries} selectedPath="src/lib/util.py" onSelectFile={onSelectFile} />,
    );

    expect(screen.getByRole("button", { name: "util.py" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "README.md" }));
    expect(onSelectFile).toHaveBeenCalledWith({
      path: "README.md",
      name: "README.md",
      isDirectory: false,
      size: 5,
    });
  });

  it("expands and collapses every folder at once", () => {
    render(<FileTree entries={entries} selectedPath={null} onSelectFile={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Expand all" }));
    expect(screen.getByRole("button", { name: "util.py" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Collapse all" }));
    expect(screen.queryByRole("button", { name: "util.py" })).not.toBeInTheDocument();
  });
});
