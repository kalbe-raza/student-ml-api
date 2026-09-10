"""Automated tests for student-ml-api."""

import json
from pathlib import Path

import pytest

from app import MODEL_VERSION, app as flask_app

VERSION = (Path(__file__).resolve().parents[1] / "VERSION").read_text(encoding="utf-8").strip()


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    """/health reports a healthy service, the application version and the model version."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["application"] == "student-ml-api"
    assert data["application_version"] == VERSION
    assert data["model_version"] == MODEL_VERSION


def test_health_reports_model_version_independently(client):
    """The model version is reported separately from the application version."""
    data = client.get("/health").get_json()
    assert data["model_version"] == "model-1"
    assert data["application_version"] != data["model_version"]


def test_predict_success(client):
    """A valid numeric input returns the echoed input and its prediction."""
    response = client.post("/predict", json={"value": 10})
    assert response.status_code == 200

    data = response.get_json()
    assert data["input"] == 10
    assert data["prediction"] == 20


def test_predict_missing_input(client):
    """A request without the 'value' field is rejected with HTTP 400."""
    response = client.post("/predict", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_predict_invalid_input(client):
    """A non-numeric 'value' is rejected with HTTP 400."""
    response = client.post("/predict", json={"value": "abc"})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_predict_rejects_non_json_body(client):
    """A malformed (non-JSON) body is rejected rather than causing a 500."""
    response = client.post("/predict", data="not-json", content_type="text/plain")
    assert response.status_code == 400
