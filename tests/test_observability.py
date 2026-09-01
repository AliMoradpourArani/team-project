"""Request-correlation behavior for the API boundary."""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_response_includes_generated_request_id():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_valid_caller_request_id_is_preserved():
    with TestClient(app) as client:
        response = client.get("/api/health", headers={"X-Request-ID": "phase-2-5-test"})

    assert response.headers["x-request-id"] == "phase-2-5-test"
