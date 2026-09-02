"""Authenticated in-app AI workspace and persistent agent endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query, Response, status

from ...schemas.ai import (
    AIAgentMessageWrite,
    AIAgentReplanRequest,
    AIAgentReplanResponse,
    AIAgentReply,
    AIAgentSnapshot,
    AIAgentThread,
    AIAgentThreadCreate,
    AIDailyBrief,
    AIGitHubLink,
    AIGitHubLinkWrite,
    AIMemoryItem,
    AIMemoryWrite,
    AIMultiAgentReview,
    AIStatusResponse,
    AIWorkspaceRequest,
    AIWorkspaceResponse,
)
from ...services import ai_agent, ai_workspace
from ..auth_dependencies import CsrfPrincipal, CurrentPrincipal

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _student_user_id(principal: CsrfPrincipal | CurrentPrincipal) -> str:
    if principal.role != "student" or principal.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The AI workspace is available to linked student workspaces.",
        )
    return principal.user_id


def _project_param(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status(principal: CurrentPrincipal) -> AIStatusResponse:
    del principal
    configured = bool(os.getenv("AI_API_KEY", "").strip())
    return AIStatusResponse(
        mode="provider" if configured else "local",
        provider="openai-compatible" if configured else "local",
        model=(os.getenv("AI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini") if configured else None,
    )


@router.post("/workspace", response_model=AIWorkspaceResponse)
def run_ai_workspace(payload: AIWorkspaceRequest, principal: CsrfPrincipal) -> AIWorkspaceResponse:
    return ai_workspace.run_workspace(payload, _student_user_id(principal))


@router.get("/threads", response_model=list[AIAgentThread])
def list_ai_threads(principal: CurrentPrincipal) -> list[AIAgentThread]:
    return ai_agent.list_threads(_student_user_id(principal))


@router.post("/threads", response_model=AIAgentThread, status_code=status.HTTP_201_CREATED)
def create_ai_thread(payload: AIAgentThreadCreate, principal: CsrfPrincipal) -> AIAgentThread:
    return ai_agent.create_thread(payload, _student_user_id(principal))


@router.get("/threads/{thread_id}/snapshot", response_model=AIAgentSnapshot)
def get_ai_snapshot(thread_id: str, principal: CurrentPrincipal) -> AIAgentSnapshot:
    return ai_agent.get_snapshot(thread_id, _student_user_id(principal))


@router.post("/threads/{thread_id}/messages", response_model=AIAgentReply)
def post_ai_message(
    thread_id: str,
    payload: AIAgentMessageWrite,
    principal: CsrfPrincipal,
) -> AIAgentReply:
    return ai_agent.post_message(thread_id, payload.content, _student_user_id(principal))


@router.post("/threads/{thread_id}/replan", response_model=AIAgentReplanResponse)
def replan_ai_thread(
    thread_id: str,
    payload: AIAgentReplanRequest,
    principal: CsrfPrincipal,
) -> AIAgentReplanResponse:
    return ai_agent.replan(thread_id, payload, _student_user_id(principal))


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_thread(thread_id: str, principal: CsrfPrincipal) -> Response:
    ai_agent.delete_thread(thread_id, _student_user_id(principal))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/memory", response_model=list[AIMemoryItem])
def list_ai_memory(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> list[AIMemoryItem]:
    return ai_agent.list_memory(_project_param(project_id), _student_user_id(principal))


@router.put("/memory", response_model=AIMemoryItem)
def upsert_ai_memory(
    payload: AIMemoryWrite,
    principal: CsrfPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIMemoryItem:
    return ai_agent.upsert_memory(
        _project_param(project_id), payload, _student_user_id(principal)
    )


@router.get("/github-links", response_model=list[AIGitHubLink])
def list_ai_github_links(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> list[AIGitHubLink]:
    return ai_agent.list_github_links(_project_param(project_id), _student_user_id(principal))


@router.post("/github-links", response_model=AIGitHubLink, status_code=status.HTTP_201_CREATED)
def create_ai_github_link(
    payload: AIGitHubLinkWrite,
    principal: CsrfPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIGitHubLink:
    return ai_agent.link_github(
        _project_param(project_id), payload, _student_user_id(principal)
    )


@router.get("/brief", response_model=AIDailyBrief)
def get_ai_daily_brief(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIDailyBrief:
    return ai_agent.daily_brief(_project_param(project_id), _student_user_id(principal))


@router.get("/multi-agent-review", response_model=AIMultiAgentReview)
def get_ai_multi_agent_review(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIMultiAgentReview:
    return ai_agent.multi_agent_review(_project_param(project_id), _student_user_id(principal))
