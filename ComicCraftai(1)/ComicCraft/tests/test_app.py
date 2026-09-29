from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


client = TestClient(app)


def _set_mock(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("HF_TOKEN", "")
    get_settings.cache_clear()


def test_homepage(monkeypatch):
    _set_mock(monkeypatch)
    response = client.get("/")
    assert response.status_code == 200
    assert "Create My Comic" in response.text


def test_health(monkeypatch):
    _set_mock(monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["image_provider"] == "mock"


def test_full_json_pipeline(monkeypatch, tmp_path):
    _set_mock(monkeypatch)
    response = client.post(
        "/generate-comic/json",
        json={
            "story_prompt": "A brave fox discovers a hidden clock in a magical forest.",
            "character_name": "Ember",
            "setting": "forest",
            "tone": "funny",
            "art_style": "comic book",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["layout"]) == 5
    assert payload["pdf_url"].startswith("/download/")
    assert Path(payload["pdf_path"]).exists()

    download = client.get(payload["pdf_url"])
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/pdf")
