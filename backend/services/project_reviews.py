"""Runtime-only professor reviews for member projects."""

from __future__ import annotations

from ..database.connection import connect
from ..schemas.api import ProjectResponse
from ..schemas.project_review import (
    ProfessorReviewQueueItem,
    ProfessorReviewQueueResponse,
    ProjectReviewInput,
    ProjectReviewResponse,
)


def _response_from_row(row) -> ProjectReviewResponse:
    return ProjectReviewResponse(
        projectId=row["project_id"],
        reviewerUsername=row["reviewer_username"],
        status=row["status"],
        functionalityScore=row["functionality_score"],
        codeQualityScore=row["code_quality_score"],
        documentationScore=row["documentation_score"],
        integrationScore=row["integration_score"],
        contributionScore=row["contribution_score"],
        totalScore=(
            row["functionality_score"]
            + row["code_quality_score"]
            + row["documentation_score"]
            + row["integration_score"]
            + row["contribution_score"]
        ),
        feedback=row["feedback"],
        updatedAt=row["updated_at"],
    )


def get_review(project_id: str) -> ProjectReviewResponse | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT r.*, a.username AS reviewer_username
            FROM project_reviews AS r
            JOIN auth_accounts AS a ON a.id = r.reviewer_account_id
            WHERE r.project_id = ?
            """,
            (project_id,),
        ).fetchone()
    return _response_from_row(row) if row is not None else None


def save_review(
    project_id: str, reviewer_account_id: int, payload: ProjectReviewInput
) -> ProjectReviewResponse:
    with connect() as connection, connection:
        connection.execute(
            """
            INSERT INTO project_reviews (
                project_id,
                reviewer_account_id,
                status,
                functionality_score,
                code_quality_score,
                documentation_score,
                integration_score,
                contribution_score,
                feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                reviewer_account_id=excluded.reviewer_account_id,
                status=excluded.status,
                functionality_score=excluded.functionality_score,
                code_quality_score=excluded.code_quality_score,
                documentation_score=excluded.documentation_score,
                integration_score=excluded.integration_score,
                contribution_score=excluded.contribution_score,
                feedback=excluded.feedback,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                project_id,
                reviewer_account_id,
                payload.status,
                payload.functionalityScore,
                payload.codeQualityScore,
                payload.documentationScore,
                payload.integrationScore,
                payload.contributionScore,
                payload.feedback,
            ),
        )
    review = get_review(project_id)
    if review is None:
        raise RuntimeError("Project review could not be persisted.")
    return review


def delete_review(project_id: str) -> None:
    with connect() as connection, connection:
        connection.execute("DELETE FROM project_reviews WHERE project_id = ?", (project_id,))


def get_review_queue(projects: list[ProjectResponse]) -> ProfessorReviewQueueResponse:
    items = [
        ProfessorReviewQueueItem(project=project, review=get_review(project.id))
        for project in projects
    ]
    return ProfessorReviewQueueResponse(
        totalProjects=len(items),
        pending=sum(item.review is None for item in items),
        inReview=sum(item.review is not None and item.review.status == "in-review" for item in items),
        changesRequested=sum(
            item.review is not None and item.review.status == "changes-requested" for item in items
        ),
        approved=sum(item.review is not None and item.review.status == "approved" for item in items),
        items=items,
    )
