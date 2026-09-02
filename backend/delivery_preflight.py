"""Run the final-delivery preflight against the current local runtime state."""

from __future__ import annotations

import argparse
import json

from .services import delivery_preflight, queries


def _print_gate(gate, indent: str = "") -> None:
    mark = "PASS" if gate.passed else "FAIL"
    print(f"{indent}{mark:4}  {gate.label}: {gate.detail}")
    if not gate.passed:
        print(f"{indent}      Fix: {gate.remediation}")


def _print_report(report) -> None:
    print(f"[{report.status.upper()}] {report.summary}")
    print(
        f"Projects: {report.readyProjects}/{report.totalProjects} ready · "
        f"blockers: {report.blockerCount}"
    )
    print("\nGlobal gates")
    for gate in report.globalGates:
        _print_gate(gate, "  ")
    for project in report.projects:
        print(
            f"\n[{project.status.upper()}] {project.project.id} · "
            f"submission={project.latestSubmissionVersion or '-'} · "
            f"review={project.reviewStatus or '-'}"
        )
        for gate in project.gates:
            _print_gate(gate, "  ")
    print(f"\nLocal command: {report.localCheckCommand}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print blockers but exit successfully. Useful for diagnostics and CI smoke checks.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    args = parser.parse_args()

    report = delivery_preflight.get_delivery_preflight(queries.list_projects())
    if args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
    else:
        _print_report(report)

    if not args.report_only and not report.releaseCandidateReady:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
