"""Activity routes."""

from fastapi import APIRouter

from ...schemas.api import ActivityResponse
from ...services import queries

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=list[ActivityResponse])
def list_activities() -> list[ActivityResponse]:
    """List tracked daily activities, ordered by date."""
    return queries.list_activities()
