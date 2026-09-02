"""Authenticated in-app AI workspace endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, status

from ...schemas.ai import AIStatusResponse, AIWorkspaceRequest, AIWorkspaceResponse
from ...services import ai_workspace
from ..auth_dependencies import CsrfPrincipal, CurrentPrincipal

router = APIRouter(prefix="/api/ai", tags=["ai"])


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
    if principal.role != "student" or principal.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The AI workspace is available to linked student workspaces.",
        )
    return ai_workspace.run_workspace(payload, principal.user_id)
