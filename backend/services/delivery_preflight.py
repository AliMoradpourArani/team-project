"""Phase 11 final-delivery preflight built from existing authoritative readiness models."""

from __future__ import annotations

from datetime import UTC, datetime

from ..database.connection import connect
from ..schemas.api import ProjectResponse
from ..schemas.delivery_preflight import (
    DeliveryPreflightGate,
    DeliveryPreflightResponse,
    ProjectDeliveryPreflight,
)
from . import delivery_rules, project_onboarding, project_reviews, submissions


def _runtime_accounts_gate(projects: list[ProjectResponse]) -> DeliveryPreflightGate:
    required_students = {project.userId for project in projects}
    with connect() as connection:
        professor_count = int(
            connection.execute(
                "SELECT COUNT(*) AS count FROM auth_accounts WHERE role = 'professor'"
            ).fetchone()["count"]
        )
        rows = connection.execute(
            "SELECT user_id FROM auth_accounts WHERE role = 'student' AND user_id IS NOT NULL"
        ).fetchall()
    available_students = {row["user_id"] for row in rows}
    missing = sorted(required_students - available_students)
    passed = professor_count > 0 and not missing
    if passed:
        detail = "Professor access and every tracked project owner have local accounts."
    else:
        parts = []
        if professor_count == 0:
            parts.append("no professor account")
        if missing:
            parts.append(f"missing student account(s): {', '.join(missing)}")
        detail = "; ".join(parts) + "."
    return DeliveryPreflightGate(
        key="runtime-accounts",
        label="Runtime accounts",
        passed=passed,
        detail=detail,
        remediation="Run `make auth-bootstrap` and create/rotate the required professor and student accounts.",
    )


def _project_preflight(project: ProjectResponse) -> ProjectDeliveryPreflight:
    onboarding = project_onboarding.get_onboarding(project)
    submission = submissions.get_latest_submission(project.id)
    review = project_reviews.get_review(project.id)
    review_after_submission = delivery_rules.review_covers_submission(review, submission)

    gates = [
        DeliveryPreflightGate(
            key="integration",
            label="Integration readiness",
            passed=onboarding.readyForSubmission,
            detail=(
                f"Member project onboarding is {onboarding.completedGates}/{onboarding.totalGates}."
            ),
            remediation=onboarding.nextAction,
        ),
        DeliveryPreflightGate(
            key="frozen-submission",
            label="Frozen submission",
            passed=submission is not None,
            detail=(
                f"Latest immutable submission is v{submission.version}."
                if submission is not None
                else "No immutable submission has been frozen for this project."
            ),
            remediation="The project owner must freeze the latest integrated source from the project submission panel.",
        ),
        DeliveryPreflightGate(
            key="professor-approval",
            label="Professor approval",
            passed=review is not None and review.status == "approved",
            detail=(
                f"Current professor review status is {review.status}."
                if review is not None
                else "No professor review exists for this project."
            ),
            remediation="The professor must complete the rubric and set the project review to approved.",
        ),
        DeliveryPreflightGate(
            key="approval-sequence",
            label="Approval covers frozen version",
            passed=review_after_submission,
            detail=(
                "The approved review was recorded after the latest frozen submission."
                if review_after_submission
                else "The final approval must be recorded after the latest frozen submission so the reviewed version is unambiguous."
            ),
            remediation="Freeze the final source first, then have the professor review and approve that frozen version before creating a release candidate.",
        ),
    ]
    ready = all(gate.passed for gate in gates)
    return ProjectDeliveryPreflight(
        project=project,
        status="ready" if ready else "blocked",
        latestSubmissionVersion=submission.version if submission is not None else None,
        reviewStatus=review.status if review is not None else None,
        reviewAfterSubmission=review_after_submission,
        gates=gates,
    )


def get_delivery_preflight(projects: list[ProjectResponse]) -> DeliveryPreflightResponse:
    project_reports = [_project_preflight(project) for project in projects]
    account_gate = _runtime_accounts_gate(projects)
    all_integrated = bool(project_reports) and all(
        next(gate for gate in report.gates if gate.key == "integration").passed
        for report in project_reports
    )
    all_frozen = bool(project_reports) and all(
        report.latestSubmissionVersion is not None for report in project_reports
    )
    all_reviewed_after_freeze = bool(project_reports) and all(
        report.reviewAfterSubmission for report in project_reports
    )

    global_gates = [
        DeliveryPreflightGate(
            key="tracked-projects",
            label="Tracked project set",
            passed=bool(projects),
            detail=(
                f"{len(projects)} tracked project(s) are included in final-delivery evaluation."
                if projects
                else "No tracked projects are available for final delivery."
            ),
            remediation="Add valid authoritative project records under data/projects/ before final delivery.",
        ),
        account_gate,
        DeliveryPreflightGate(
            key="all-integrated",
            label="All projects integrated",
            passed=all_integrated,
            detail=(
                "Every tracked project passes the Phase 10 onboarding contract."
                if all_integrated
                else "At least one tracked project still has blocking integration gates."
            ),
            remediation="Run `python -m backend.project_check --strict` and resolve every pending or invalid project.",
        ),
        DeliveryPreflightGate(
            key="all-frozen",
            label="All projects frozen",
            passed=all_frozen,
            detail=(
                "Every tracked project has an immutable submission."
                if all_frozen
                else "At least one tracked project has no frozen final submission."
            ),
            remediation="Have each project owner freeze the final integrated source before professor approval.",
        ),
        DeliveryPreflightGate(
            key="final-approval-order",
            label="Final approvals cover frozen submissions",
            passed=all_reviewed_after_freeze,
            detail=(
                "Every latest frozen submission was followed by an approved professor review."
                if all_reviewed_after_freeze
                else "At least one final approval is missing or predates the latest frozen submission."
            ),
            remediation="After all final submissions are frozen, review and approve each project once more before freezing the release candidate.",
        ),
    ]

    ready_projects = sum(report.status == "ready" for report in project_reports)
    project_blockers = sum(
        1 for report in project_reports for gate in report.gates if gate.blocking and not gate.passed
    )
    global_blockers = sum(gate.blocking and not gate.passed for gate in global_gates)
    blocker_count = project_blockers + global_blockers
    ready = blocker_count == 0
    summary = (
        "READY TO FREEZE RELEASE CANDIDATE"
        if ready
        else f"BLOCKED: {blocker_count} final-delivery gate(s) still require attention"
    )
    return DeliveryPreflightResponse(
        status="ready" if ready else "blocked",
        releaseCandidateReady=ready,
        totalProjects=len(project_reports),
        readyProjects=ready_projects,
        blockingProjects=len(project_reports) - ready_projects,
        blockerCount=blocker_count,
        generatedAt=datetime.now(UTC).isoformat(),
        localCheckCommand="make delivery-preflight",
        summary=summary,
        globalGates=global_gates,
        projects=project_reports,
    )
