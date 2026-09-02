"""Phase 10 member-project onboarding and integration gate contracts."""

from typing import Literal

from pydantic import BaseModel

OnboardingStatus = Literal["ready", "pending", "invalid"]


class ProjectOnboardingGate(BaseModel):
    key: str
    label: str
    passed: bool
    blocking: bool = True
    detail: str
    remediation: str


class ProjectContractOption(BaseModel):
    projectType: Literal["cli", "static-web", "api"]
    runner: Literal["python-script-v1", "static-site-v1", "openapi-json-v1"]
    demoMode: Literal["execute", "preview"]
    entryPointExample: str


class ProjectOnboardingResponse(BaseModel):
    projectId: str
    userId: str
    name: str
    status: OnboardingStatus
    readyForSubmission: bool
    completedGates: int
    totalGates: int
    expectedMetadataPath: str
    expectedRepositoryPath: str
    localCheckCommand: str
    nextAction: str
    gates: list[ProjectOnboardingGate]
    supportedContracts: list[ProjectContractOption]
