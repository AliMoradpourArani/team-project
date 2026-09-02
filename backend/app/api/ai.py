"""Authenticated in-app AI workspace endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Response, status

from ...schemas.ai import (
    AIAgentMessageWrite,
    AIAgentReply,
    AIAgentThread,
    AIAgentThreadCreate,
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


@router.post("/threads/{thread_id}/messages", response_model=AIAgentReply)
def post_ai_message(
    thread_id: str,
    payload: AIAgentMessageWrite,
    principal: CsrfPrincipal,
) -> AIAgentReply:
    return ai_agent.post_message(thread_id, payload.content, _student_user_id(principal))


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_thread(thread_id: str, principal: CsrfPrincipal) -> Response:
    ai_agent.delete_thread(thread_id, _student_user_id(principal))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
