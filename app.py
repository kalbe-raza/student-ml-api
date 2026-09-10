"""student-ml-api — a minimal prediction service used to demonstrate a
professional MLOps CI/CD workflow (PR -> CI -> merge -> tag -> image -> registry)."""

import os
from pathlib import Path

from flask import Flask, jsonify, request

APPLICATION_NAME = "student-ml-api"

# The served model is versioned independently of the application itself, so a
# model swap and a code change can be told apart from the /health response.
MODEL_VERSION = "model-1"


def _read_version() -> str:
    """Single source of truth for the application version: the VERSION file."""
    version_file = Path(__file__).resolve().parent / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"


APPLICATION_VERSION = _read_version()

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "application": APPLICATION_NAME,
            "application_version": APPLICATION_VERSION,
            "model_version": MODEL_VERSION,
        }
    )


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict) or "value" not in payload:
        return jsonify({"error": "Missing required field: 'value'"}), 400

    value = payload["value"]

    # bool is a subclass of int in Python, so it must be rejected explicitly.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return jsonify({"error": "Field 'value' must be a number"}), 400

    return jsonify({"input": value, "prediction": value * 2})


if __name__ == "__main__":
    # 0.0.0.0 so the service is reachable from outside the container.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
