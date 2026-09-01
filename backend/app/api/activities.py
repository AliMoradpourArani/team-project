"""Activity routes with owner-only student writes and professor read access."""

from fastapi import APIRouter, HTTPException, Response, status

from ...schemas.api import ActivityResponse, ActivityWrite
from ...services import activity_writes, auth, queries
from ..auth_dependencies import CsrfPrincipal, CurrentPrincipal

router = APIRouter(prefix="/api/activities", tags=["activities"])


def _assert_student_owner(principal: auth.Principal, user_id: str) -> None:
    if principal.role != "student" or principal.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professor access is read-only.",
        )
    if principal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own activities.",
        )


def _find_activity(activity_id: str) -> ActivityResponse:
    activity = next(
        (item for item in queries.list_activities() if item.id == activity_id),
        None,
    )
    if activity is None:
        raise queries.NotFoundError(f"Unknown activity: {activity_id}")
    return activity


@router.get("", response_model=list[ActivityResponse])
def list_activities(principal: CurrentPrincipal) -> list[ActivityResponse]:
    activities = queries.list_activities()
    if principal.role == "professor":
        return activities
    return [activity for activity in activities if activity.userId == principal.user_id]


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(payload: ActivityWrite, principal: CsrfPrincipal) -> ActivityResponse:
    _assert_student_owner(principal, payload.userId)
    return activity_writes.create_activity(payload)


@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: str,
    payload: ActivityWrite,
    principal: CsrfPrincipal,
) -> ActivityResponse:
    existing = _find_activity(activity_id)
    _assert_student_owner(principal, existing.userId)
    _assert_student_owner(principal, payload.userId)
    return activity_writes.update_activity(activity_id, payload)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: str, principal: CsrfPrincipal) -> Response:
    existing = _find_activity(activity_id)
    _assert_student_owner(principal, existing.userId)
    activity_writes.delete_activity(activity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
