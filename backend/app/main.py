"""HTTP entry point for the team project API."""

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..schemas.api import ErrorResponse
from ..services.queries import NotFoundError
from .api import activities, health, projects, users


def configured_origins() -> list[str]:
    """Read comma-separated browser origins, with local development defaults."""
    value = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    return [origin.strip() for origin in value.split(",") if origin.strip()]


app = FastAPI(
    title="Team Project API",
    version="0.1.0",
    description="Initial read-only API for the university team project.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(activities.router)
app.include_router(projects.router)


@app.exception_handler(NotFoundError)
def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Map unknown resources to a structured 404 response."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(error="Not Found", detail=str(exc)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return structured 422 errors without exposing internals."""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(error="Validation Error", detail=str(exc.errors()[:3])).model_dump(),
    )
