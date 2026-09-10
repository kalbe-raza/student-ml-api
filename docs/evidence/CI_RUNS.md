# GitHub Actions Evidence — Workflow Run Links

Repository: https://github.com/kalbe-raza/student-ml-api

## Required evidence

| # | Requirement | Run | Result | Link |
|---|---|---|---|---|
| 1 | **Failed CI execution** (deliberate, Part 6) | `34505922291` | ✗ `Unit Tests` failed, `Docker Build Validation` skipped | [https://github.com/kalbe-raza/student-ml-api/actions/runs/34505922291](https://github.com/kalbe-raza/student-ml-api/actions/runs/34505922291) |
| 2 | **Successful CI execution** (after the fix) | `34506074928` | ✓ both jobs passed | [https://github.com/kalbe-raza/student-ml-api/actions/runs/34506074928](https://github.com/kalbe-raza/student-ml-api/actions/runs/34506074928) |

### Additional genuine CI failure (caught a real defect)

| # | Run | Result | Link |
|---|---|---|---|
| 0 | `34505618195` | ✗ `ModuleNotFoundError: No module named 'app'` — a real import-path bug CI caught before merge | [https://github.com/kalbe-raza/student-ml-api/actions/runs/34505618195](https://github.com/kalbe-raza/student-ml-api/actions/runs/34505618195) |

## Deliberate failure — captured log output

Run `34505922291`, job `Unit Tests`:

```
tests/test_app.py::test_health_endpoint FAILED                           [ 20%]
        assert response.status_code == 200
>       assert data["status"] == "wrong"
E       AssertionError: assert 'healthy' == 'wrong'
tests/test_app.py:26: AssertionError
=========================== short test summary info ============================
FAILED tests/test_app.py::test_health_endpoint - AssertionError: assert 'healthy' == 'wrong'
========================= 1 failed, 4 passed in 0.12s ==========================
##[error]Process completed with exit code 1.
```

Job graph for the failed run — note that the Docker job never ran:

```
JOBS
X Unit Tests in 8s
  ✓ Checkout code
  ✓ Set up Python
  ✓ Install dependencies
  X Run pytest
- Docker Build Validation            <-- skipped, it declares "needs: test"
```

## Successful CI — captured smoke-test output

Run `34506074928`, job `Docker Build Validation`:

```
#13 naming to docker.io/library/student-ml-api:ci-<sha> done
+ docker run -d --name ci-check -p 5000:5000 student-ml-api:ci-<sha>
{"application":"student-ml-api","status":"healthy","version":"1.0.0"}
health OK
```

The image is built and exercised, but never pushed — publishing happens only in
the tag-triggered release workflow.
