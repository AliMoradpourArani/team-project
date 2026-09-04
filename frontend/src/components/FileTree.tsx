import { useEffect, useMemo, useState } from "react";

import { useI18n } from "../i18n";
import type { ProjectFileEntry } from "../types";
import {
  ancestorsOfPath,
  buildFileTree,
  collectDirPaths,
  toFileEntry,
  type FileTreeNode,
} from "./file-tree";

interface FileTreeProps {
  entries: ProjectFileEntry[];
  selectedPath: string | null;
  onSelectFile: (entry: ProjectFileEntry) => void;
}

export default function FileTree({ entries, selectedPath, onSelectFile }: FileTreeProps) {
  const { t } = useI18n();
  const nodes = useMemo(() => buildFileTree(entries), [entries]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  // Reset on project change; auto-expand ancestors of the selected file
  // (e.g. jumping in from an activity's attached files).
  useEffect(() => {
    setExpanded(new Set(selectedPath ? ancestorsOfPath(selectedPath) : []));
  }, [entries, selectedPath]);

  function toggle(path: string) {
    setExpanded((previous) => {
      const next = new Set(previous);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  function expandAll() {
    setExpanded(new Set(collectDirPaths(nodes)));
  }

  function collapseAll() {
    setExpanded(new Set());
  }

  function renderNodes(level: FileTreeNode[], depth: number) {
    return (
      <ul className={depth === 0 ? "gh-tree-root" : "gh-tree-children"}>
        {level.map((node) =>
          node.isDirectory ? (
            <li key={node.path}>
              <button
                className="gh-file-button gh-tree-toggle"
                type="button"
                aria-expanded={expanded.has(node.path)}
                aria-label={
                  expanded.has(node.path)
                    ? t("gh.collapseFolder", { name: node.name })
                    : t("gh.expandFolder", { name: node.name })
                }
                title={
                  expanded.has(node.path)
                    ? t("gh.collapseFolder", { name: node.name })
                    : t("gh.expandFolder", { name: node.name })
                }
                style={{ paddingInlineStart: `${0.5 + depth * 1.1}rem` }}
                onClick={() => toggle(node.path)}
              >
                <span
                  className={`gh-tree-arrow ${expanded.has(node.path) ? "open" : ""}`}
                  aria-hidden="true"
                >
                  ▸
                </span>
                <span aria-hidden="true">📁 </span>
                {node.name}
              </button>
              {expanded.has(node.path) ? renderNodes(node.children, depth + 1) : null}
            </li>
          ) : (
            <li key={node.path}>
              <button
                className={`gh-file-button ${node.path === selectedPath ? "active" : ""}`}
                type="button"
                title={node.path}
                style={{ paddingInlineStart: `${0.5 + depth * 1.1}rem` }}
                onClick={() => onSelectFile(toFileEntry(node))}
              >
                <span aria-hidden="true">📄 </span>
                {node.name}
              </button>
            </li>
          ),
        )}
      </ul>
    );
  }

  return (
    <div className="gh-tree">
      <div className="gh-tree-toolbar">
        <button className="gh-tree-bulk" type="button" onClick={expandAll}>
          {t("gh.expandAll")}
        </button>
        <button className="gh-tree-bulk" type="button" onClick={collapseAll}>
          {t("gh.collapseAll")}
        </button>
      </div>
      {renderNodes(nodes, 0)}
    </div>
  );
}
