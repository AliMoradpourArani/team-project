"""Authenticated in-app AI workspace, repository intelligence, and governed autonomy."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

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
from ...schemas.ai_autonomy import (
    AIActionProposalRequest,
    AIActionRecord,
    AIDebugRequest,
    AIDebugResponse,
    AIHealthScore,
    AIMemorySearchResponse,
    AINotification,
    AIOrchestrationResponse,
    AIProgressSyncRequest,
    AIProgressSyncResponse,
    AIRagQuery,
    AIRagResponse,
    AIRepoIndexResponse,
    AIWeeklyBrief,
)
from ...schemas.ai_review import AICodeReviewRequest, AICodeReviewResponse
from ...services import ai_agent, ai_autonomy, ai_code_review, ai_multi_agent, ai_workspace
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
    user_id = _student_user_id(principal)
    try:
        ai_autonomy.guard_prompt(user_id, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ai_agent.post_message(thread_id, payload.content, user_id)


@router.post("/threads/{thread_id}/messages/stream")
def stream_ai_message(
    thread_id: str,
    payload: AIAgentMessageWrite,
    principal: CsrfPrincipal,
) -> StreamingResponse:
    user_id = _student_user_id(principal)
    try:
        ai_autonomy.guard_prompt(user_id, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    # stream_message validates ownership eagerly so HTTP errors stay JSON responses.
    events = ai_agent.stream_message(thread_id, payload.content, user_id)
    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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


@router.get("/memory/search", response_model=AIMemorySearchResponse)
def search_ai_memory(
    principal: CurrentPrincipal,
    q: str = Query(min_length=2, max_length=1000),
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIMemorySearchResponse:
    return ai_autonomy.search_memory(_project_param(project_id), q, _student_user_id(principal))


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


@router.get("/weekly-brief", response_model=AIWeeklyBrief)
def get_ai_weekly_brief(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIWeeklyBrief:
    return ai_autonomy.weekly_brief(_project_param(project_id), _student_user_id(principal))


@router.get("/multi-agent-review", response_model=AIMultiAgentReview)
def get_ai_multi_agent_review(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIMultiAgentReview:
    return ai_agent.multi_agent_review(_project_param(project_id), _student_user_id(principal))


@router.get("/orchestrate", response_model=AIOrchestrationResponse)
def orchestrate_ai_agents(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIOrchestrationResponse:
    return ai_multi_agent.orchestrate(_project_param(project_id), _student_user_id(principal))


@router.post("/repo/index", response_model=AIRepoIndexResponse)
def index_ai_repository(
    principal: CsrfPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIRepoIndexResponse:
    return ai_autonomy.index_repository(_project_param(project_id), _student_user_id(principal))


@router.post("/repo/query", response_model=AIRagResponse)
def query_ai_repository(
    payload: AIRagQuery,
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIRagResponse:
    return ai_autonomy.query_repository(
        _project_param(project_id), payload, _student_user_id(principal)
    )


@router.post("/code-review", response_model=AICodeReviewResponse)
def review_code_with_ai(
    payload: AICodeReviewRequest,
    principal: CurrentPrincipal,
) -> AICodeReviewResponse:
    result = ai_code_review.review_diff(payload.projectId, payload.diff, _student_user_id(principal))
    return AICodeReviewResponse(**result)


@router.post("/debug", response_model=AIDebugResponse)
def debug_with_ai(payload: AIDebugRequest, principal: CurrentPrincipal) -> AIDebugResponse:
    return ai_autonomy.debug_logs(payload.projectId, payload.logs, _student_user_id(principal))


@router.get("/health", response_model=AIHealthScore)
def get_ai_health(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> AIHealthScore:
    return ai_autonomy.health_score(_project_param(project_id), _student_user_id(principal))


@router.post("/progress/sync", response_model=AIProgressSyncResponse)
def sync_ai_progress(
    payload: AIProgressSyncRequest,
    principal: CsrfPrincipal,
) -> AIProgressSyncResponse:
    return ai_autonomy.sync_progress(payload, _student_user_id(principal))


@router.get("/actions", response_model=list[AIActionRecord])
def list_ai_actions(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> list[AIActionRecord]:
    return ai_autonomy.list_actions(_project_param(project_id), _student_user_id(principal))


@router.post("/actions", response_model=AIActionRecord, status_code=status.HTTP_201_CREATED)
def propose_ai_action(payload: AIActionProposalRequest, principal: CsrfPrincipal) -> AIActionRecord:
    return ai_autonomy.propose_action(payload, _student_user_id(principal))


@router.post("/actions/{action_id}/approve", response_model=AIActionRecord)
def approve_ai_action(action_id: int, principal: CsrfPrincipal) -> AIActionRecord:
    return ai_autonomy.approve_action(action_id, _student_user_id(principal))


@router.post("/actions/{action_id}/execute", response_model=AIActionRecord)
def execute_ai_action(action_id: int, principal: CsrfPrincipal) -> AIActionRecord:
    try:
        return ai_autonomy.execute_action(action_id, _student_user_id(principal))
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/notifications", response_model=list[AINotification])
def list_ai_notifications(
    principal: CurrentPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> list[AINotification]:
    return ai_autonomy.list_notifications(_project_param(project_id), _student_user_id(principal))


@router.post("/notifications/refresh", response_model=list[AINotification])
def refresh_ai_notifications(
    principal: CsrfPrincipal,
    project_id: str | None = Query(default=None, alias="projectId"),
) -> list[AINotification]:
    return ai_autonomy.refresh_notifications(_project_param(project_id), _student_user_id(principal))
