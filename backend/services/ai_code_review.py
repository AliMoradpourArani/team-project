"""Diff-aware repository review grounded in indexed code and project invariants."""

from __future__ import annotations

import re

from ..schemas.ai import AIFinding
from ..schemas.ai_autonomy import AIRagQuery
from . import ai_autonomy, ai_workspace

_SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}")
_DANGEROUS_PATTERNS = (
    (re.compile(r"\beval\s*\("), "Dynamic eval introduced", "Avoid eval on untrusted or model-generated content."),
    (re.compile(r"\bexec\s*\("), "Dynamic exec introduced", "Avoid exec on untrusted or model-generated content."),
    (re.compile(r"subprocess\.[A-Za-z_]+\([^\n]*shell\s*=\s*True"), "Shell execution enabled", "Prefer argument arrays and shell=False."),
    (re.compile(r"verify\s*=\s*False"), "TLS verification disabled", "Keep TLS certificate verification enabled."),
)


def review_diff(project_id: str | None, diff: str, user_id: str) -> dict[str, object]:
    ai_workspace._project(project_id, user_id)  # noqa: SLF001
    findings: list[AIFinding] = []
    added = "\n".join(line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    if _SECRET_RE.search(added):
        findings.append(
            AIFinding(
                severity="error",
                title="Possible secret committed in diff",
                detail="The added lines contain a credential-like assignment.",
                recommendation="Move credentials to server-side secret storage and rotate any exposed value.",
            )
        )
    for pattern, title, recommendation in _DANGEROUS_PATTERNS:
        if pattern.search(added):
            findings.append(
                AIFinding(
                    severity="warning",
                    title=title,
                    detail="A security-sensitive implementation pattern appears in added code.",
                    recommendation=recommendation,
                )
            )
    if "backend/database/migrations/" in diff and "DROP TABLE" in added.upper():
        findings.append(
            AIFinding(
                severity="error",
                title="Destructive migration detected",
                detail="A migration adds DROP TABLE, conflicting with append-only migration safety expectations.",
                recommendation="Use additive schema evolution and an explicit migration/rollback plan.",
            )
        )
    source_changes = any(marker in diff for marker in ("backend/", "frontend/src/"))
    test_changes = any(marker in diff for marker in ("tests/", ".test.", ".spec."))
    if source_changes and not test_changes:
        findings.append(
            AIFinding(
                severity="warning",
                title="Implementation changed without visible tests",
                detail="The diff changes application source but contains no obvious test-file changes.",
                recommendation="Add or update tests that exercise the changed behavior and regression path.",
            )
        )
    query_terms = " ".join(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", added)[:50])
    hits = []
    if query_terms:
        hits = ai_autonomy.query_repository(
            project_id,
            AIRagQuery(query=query_terms, topK=6),
            user_id,
        ).hits
    summary = (
        f"Reviewed diff with {len(findings)} actionable finding(s) and "
        f"{len(hits)} repository-context match(es)."
    )
    return {"summary": summary, "findings": findings, "context": hits}
