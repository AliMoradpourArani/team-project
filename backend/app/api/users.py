"""User routes with role-based visibility."""

from fastapi import APIRouter, HTTPException, status

from ...schemas.api import UserResponse
from ...services import auth, queries
from ..auth_dependencies import CurrentPrincipal

router = APIRouter(prefix="/api/users", tags=["users"])


def _assert_can_view(user_id: str, principal: auth.Principal) -> None:
    if principal.role == "student" and principal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile.",
        )


@router.get("", response_model=list[UserResponse])
def list_users(principal: CurrentPrincipal) -> list[UserResponse]:
    if principal.role == "professor":
        return queries.list_users()
    if principal.user_id is None:
        return []
    return [queries.get_user(principal.user_id)]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, principal: CurrentPrincipal) -> UserResponse:
    _assert_can_view(user_id, principal)
    return queries.get_user(user_id)
