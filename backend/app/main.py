"""HTTP entry point for the team project API."""

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..schemas.api import ErrorResponse
from ..services.queries import NotFoundError
from .api import activities, auth, health, professor, projects, users
from .observability import request_observability


def configured_origins() -> list[str]:
    value = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    return [origin.strip() for origin in value.split(",") if origin.strip()]


app = FastAPI(
    title="Team Project API",
    version="0.9.0",
    description=(
        "Authenticated team activity, project demos, professor evaluation, immutable submissions, "
        "and frozen release manifests."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
)

app.middleware("http")(request_observability)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(activities.router)
app.include_router(projects.router)
app.include_router(professor.router)


@app.exception_handler(NotFoundError)
def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(error="Not Found", detail=str(exc)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(error="Validation Error", detail=str(exc.errors()[:3])).model_dump(),
    )


@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error="Invalid Request", detail=str(exc)).model_dump(),
    )
