# student-ml-api

A minimal ML inference API used to demonstrate a professional MLOps workflow:

```
feature branch -> Pull Request -> CI -> review -> merge -> version tag -> release workflow -> container registry
```

## Endpoints

| Method | Path       | Description                                   |
|--------|------------|-----------------------------------------------|
| GET    | `/health`  | Service status, application name, application version and model version. |
| POST   | `/predict` | Returns `prediction = value * 2`.             |

```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/predict -H "Content-Type: application/json" -d '{"value": 10}'
```

## Local development

```bash
pip install -r requirements-dev.txt
pytest -v
python app.py
```

## Docker

```bash
docker build -t student-ml-api:$(cat VERSION) .
docker run -d --name student-ml-api -p 5000:5000 student-ml-api:$(cat VERSION)
curl http://localhost:5000/health
```

## Versioning

`VERSION` is the single source of truth for the application version. The release
workflow derives the image version from the pushed Git tag (`v1.0.0` -> `1.0.0`)
and fails the build if the tag and the `VERSION` file disagree.

## Workflows

| Workflow | Trigger | Responsibility |
|---|---|---|
| `.github/workflows/ci.yml` | Pull Request to `main`, pushes to non-main branches | Test, validate, Docker build check. **Never publishes.** |
| `.github/workflows/release.yml` | Push of a `v*.*.*` tag | Test, build, version, publish to GHCR. |

## Documentation

- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) — branch protection, merge strategy, traceability, rollback.
- [`docs/FAILURE_ANALYSIS.md`](docs/FAILURE_ANALYSIS.md) — deliberate failures, diagnosis and corrections.
