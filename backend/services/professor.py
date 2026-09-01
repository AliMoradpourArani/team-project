"""Professor dashboard aggregation over the shared project data."""

from __future__ import annotations

from ..schemas.auth import ProfessorDashboardResponse, ProfessorMemberSummary, ProfessorTotals
from . import queries


def get_professor_dashboard() -> ProfessorDashboardResponse:
    users = queries.list_users()
    activities = queries.list_activities()
    projects = queries.list_projects()

    members: list[ProfessorMemberSummary] = []
    for user in users:
        user_activities = [activity for activity in activities if activity.userId == user.id]
        user_projects = [project for project in projects if project.userId == user.id]
        latest = max((activity.date for activity in user_activities), default=None)
        members.append(
            ProfessorMemberSummary(
                user=user,
                totalActivities=len(user_activities),
                completedActivities=sum(a.status == "completed" for a in user_activities),
                inProgressActivities=sum(a.status == "in-progress" for a in user_activities),
                plannedActivities=sum(a.status == "planned" for a in user_activities),
                activeProjects=sum(project.status.lower() in {"active", "in-progress"} for project in user_projects),
                latestActivityDate=latest,
            )
        )

    recent = sorted(activities, key=lambda item: (item.date, item.id), reverse=True)[:20]
    return ProfessorDashboardResponse(
        totals=ProfessorTotals(
            members=len(users),
            activities=len(activities),
            completedActivities=sum(a.status == "completed" for a in activities),
            activeProjects=sum(project.status.lower() in {"active", "in-progress"} for project in projects),
        ),
        members=members,
        recentActivities=recent,
    )
