"""Shared Phase 10 readiness model for API, UI, and local project checks."""

from __future__ import annotations

from ..schemas.api import ProjectResponse
from ..schemas.project_onboarding import (
    ProjectContractOption,
    ProjectOnboardingGate,
    ProjectOnboardingResponse,
)
from . import project_runner

SUPPORTED_CONTRACTS = [
    ProjectContractOption(
        projectType="cli",
        runner="python-script-v1",
        demoMode="execute",
        entryPointExample="main.py",
    ),
    ProjectContractOption(
        projectType="static-web",
        runner="static-site-v1",
        demoMode="preview",
        entryPointExample="index.html",
    ),
    ProjectContractOption(
        projectType="api",
        runner="openapi-json-v1",
        demoMode="preview",
        entryPointExample="openapi.json",
    ),
]


def _remediation(key: str, project: ProjectResponse) -> str:
    remedies = {
        "project-record": (
            f"Keep data/projects/{project.id}.json valid and owned by {project.userId}."
        ),
        "manifest": (
            "Add project.json under projects/<owner>/<project-directory>/ using one of the supported typed contracts."
        ),
        "owner": (
            f"Set manifest owner_id to {project.userId} and keep the project under projects/{project.userId}/."
        ),
        "paths": (
            "Make repository_path match the real project directory and keep entry_point inside that directory."
        ),
        "runner": (
            "Use cli/python-script-v1, static-web/static-site-v1, or api/openapi-json-v1 with the matching entry-point type."
        ),
        "readme": (
            "Add a UTF-8 README.md covering purpose, setup, input, output, and how the professor can demo the project."
        ),
    }
    return remedies.get(key, "Resolve this blocking integration check before opening the project PR.")


def get_onboarding(project: ProjectResponse) -> ProjectOnboardingResponse:
    detail = project_runner.project_detail(project)
    gates = [
        ProjectOnboardingGate(
            key=check.key,
            label=check.label,
            passed=check.passed,
            detail=check.detail,
            remediation=_remediation(check.key, project),
        )
        for check in detail.health
    ]

    completed = sum(1 for gate in gates if gate.passed)
    all_passed = completed == len(gates)
    integration_status = detail.integration.integrationStatus
    if integration_status == "invalid":
        status = "invalid"
    elif integration_status == "ready" and all_passed:
        status = "ready"
    else:
        status = "pending"

    failed = next((gate for gate in gates if not gate.passed), None)
    next_action = (
        "Integration gates are complete. Run the local check, open a normal feature PR, and wait for CI/review before submitting."
        if failed is None and status == "ready"
        else failed.remediation
        if failed is not None
        else "Complete the typed project integration contract before submission."
    )

    return ProjectOnboardingResponse(
        projectId=project.id,
        userId=project.userId,
        name=project.name,
        status=status,
        readyForSubmission=status == "ready",
        completedGates=completed,
        totalGates=len(gates),
        expectedMetadataPath=f"data/projects/{project.id}.json",
        expectedRepositoryPath=(
            detail.integration.repositoryPath
            or f"projects/{project.userId}/<project-directory>"
        ),
        localCheckCommand=f"make project-check PROJECT_ID={project.id}",
        nextAction=next_action,
        gates=gates,
        supportedContracts=SUPPORTED_CONTRACTS,
    )


def list_onboarding(projects: list[ProjectResponse]) -> list[ProjectOnboardingResponse]:
    return [get_onboarding(project) for project in projects]
