from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.frontend_static import install_frontend


def _build_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text("<html>forgeflow</html>", encoding="utf-8")
    (assets / "app.js").write_text("console.log('ok')", encoding="utf-8")
    return dist


def test_frontend_static_serves_index_assets_and_spa_fallback(tmp_path: Path):
    app = FastAPI()
    install_frontend(app, _build_dist(tmp_path))
    client = TestClient(app)

    assert client.get("/").status_code == 200
    assert "forgeflow" in client.get("/").text
    assert client.get("/assets/app.js").text == "console.log('ok')"
    assert client.get("/projects/demo").status_code == 200


def test_frontend_static_does_not_mask_missing_api_routes(tmp_path: Path):
    app = FastAPI()
    install_frontend(app, _build_dist(tmp_path))
    client = TestClient(app)

    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
