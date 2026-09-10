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

## Container registry

Published to GitHub Container Registry:

```bash
docker pull ghcr.io/kalbe-raza/student-ml-api:1.1.0   # current release
docker pull ghcr.io/kalbe-raza/student-ml-api:1.0.0   # previous release, kept for rollback
docker pull ghcr.io/kalbe-raza/student-ml-api:latest  # -> 1.1.0
```

| Release | Git tag | Merge commit | Image digest |
|---|---|---|---|
| 1.1.0 | `v1.1.0` | `1235578` (PR #2) | `sha256:331c819532caf6bca77068735fb50eb2d336f0524474ece6457eee20a6fdaa6c` |
| 1.0.0 | `v1.0.0` | `9323ff4` (PR #1) | `sha256:156dae8bf5040e37ead186450df4d3f60cfb3bb17802f33367027354f1ccd311` |

## Documentation

- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) — branch protection settings, merge strategy, CI/release separation, rollback rationale.
- [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) — PR -> commit -> tag -> image -> digest chain.
- [`docs/FAILURE_ANALYSIS.md`](docs/FAILURE_ANALYSIS.md) — four reproduced failures with symptom, root cause, evidence and correction.
- [`docs/VIVA.md`](docs/VIVA.md) — question-by-question preparation grounded in this repository.
- [`docs/evidence/`](docs/evidence/) — captured CI runs, Docker inspection, build-cache analysis, registry and rollback output.
