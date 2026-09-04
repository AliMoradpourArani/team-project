import type { ProjectFileEntry } from "../types";

export interface FileTreeNode {
  name: string;
  path: string;
  isDirectory: boolean;
  size: number;
  children: FileTreeNode[];
}

function findChild(children: FileTreeNode[], name: string): FileTreeNode | undefined {
  return children.find((child) => child.name === name);
}

/** Fold a flat entry list into a nested tree. Missing intermediate folders
 *  are synthesized so every file lands under its real parent chain. */
export function buildFileTree(entries: ProjectFileEntry[]): FileTreeNode[] {
  const roots: FileTreeNode[] = [];

  for (const entry of entries) {
    const segments = entry.path.split("/").filter((segment) => segment !== "");
    if (segments.length === 0) continue;
    const dirSegments = entry.isDirectory ? segments : segments.slice(0, -1);

    let level = roots;
    let current = "";
    let dirNode: FileTreeNode | undefined;
    for (const segment of dirSegments) {
      current = current ? `${current}/${segment}` : segment;
      let node = findChild(level, segment);
      if (!node) {
        node = { name: segment, path: current, isDirectory: true, size: 0, children: [] };
        level.push(node);
      } else {
        node.isDirectory = true;
        node.path = current;
      }
      dirNode = node;
      level = node.children;
    }

    if (entry.isDirectory) {
      if (dirNode) dirNode.size = entry.size;
      continue;
    }

    const leaf: FileTreeNode = {
      name: entry.name,
      path: entry.path,
      isDirectory: false,
      size: entry.size,
      children: [],
    };
    if (!findChild(level, leaf.name)) level.push(leaf);
  }

  sortFileTreeLevel(roots);
  return roots;
}

function sortFileTreeLevel(nodes: FileTreeNode[]): void {
  nodes.sort((a, b) => {
    if (a.isDirectory !== b.isDirectory) return a.isDirectory ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  for (const node of nodes) sortFileTreeLevel(node.children);
}

export function collectDirPaths(nodes: FileTreeNode[], into: string[] = []): string[] {
  for (const node of nodes) {
    if (node.isDirectory) {
      into.push(node.path);
      collectDirPaths(node.children, into);
    }
  }
  return into;
}

export function ancestorsOfPath(path: string): string[] {
  const segments = path.split("/").filter((segment) => segment !== "");
  const out: string[] = [];
  for (let depth = 1; depth < segments.length; depth += 1) {
    out.push(segments.slice(0, depth).join("/"));
  }
  return out;
}

export function toFileEntry(node: FileTreeNode): ProjectFileEntry {
  return {
    path: node.path,
    name: node.name,
    isDirectory: node.isDirectory,
    size: node.size,
  };
}
