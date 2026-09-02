"""Small shared invariants for final-delivery sequencing."""

from datetime import UTC, datetime


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def review_covers_submission(review, submission) -> bool:
    """Return true only when an approved review was recorded after the frozen submission."""
    if review is None or submission is None or review.status != "approved":
        return False
    return timestamp(review.updatedAt) >= timestamp(submission.submittedAt)
