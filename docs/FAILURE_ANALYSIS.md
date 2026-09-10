# Part 26 — Failure Analysis

Each failure below was deliberately reproduced, observed, diagnosed and
corrected. Symptom, root cause, evidence and correction are recorded for each.

---

## Failure 1 — Failed `pytest` in CI (mandatory demonstration, Part 6)

**Symptom**
The Pull Request check `CI / Unit Tests` reported a red ✗. The
`Docker Build Validation` job never started, and the PR showed
"All checks have failed", blocking the merge.

**Root cause**
`tests/test_app.py::test_health_endpoint` asserted
`data["status"] == "wrong"` while `/health` correctly returns `"healthy"`.
The test's expectation, not the application, was incorrect.

**Evidence**
```
FAILED tests/test_app.py::test_health_endpoint - AssertionError: assert 'healthy' == 'wrong'
E       - wrong
E       + healthy
=========================== 1 failed, 4 passed ===========================
Error: Process completed with exit code 1.
```
```
JOBS
X Unit Tests in 8s
  X Run pytest
- Docker Build Validation            <-- skipped: it declares "needs: test"
```

The `Docker Build Validation` job never ran, because it declares `needs: test`
— a test failure stops the pipeline before any image is built.

Failed run: https://github.com/kalbe-raza/student-ml-api/actions/runs/34505922291
Fixed run: https://github.com/kalbe-raza/student-ml-api/actions/runs/34506074928

**Correction**
The assertion was restored to `data["status"] == "healthy"` and pushed as
`fix: correct health endpoint test`. Pushing to the PR branch automatically
re-ran CI, which then passed both jobs and unblocked the merge.

**Lesson**
CI ran *before* the merge, so a broken assertion never reached `main`. Job
dependencies (`needs:`) also prevented wasting build minutes on a Docker build
for code that had already failed its tests.

---

## Failure 2 — Application bound to `127.0.0.1` inside the container

**Symptom**
`docker run -d --name student-ml-api -p 5000:5000 student-ml-api:1.0.0`
started successfully and `docker ps` showed the container `Up`, but from the
host:

```
$ curl http://localhost:5000/health
curl: (52) Empty reply from server
```

The container looked completely healthy — no crash, no restart loop.

**Root cause**
The server was bound to the loopback interface *inside the container's own
network namespace*:

```
[INFO] Listening at: http://127.0.0.1:5000
```

`127.0.0.1` inside a container refers to that container, not the host. Docker's
`-p 5000:5000` forwards host traffic to the **container's external interface**,
so packets arrived at an address the process was not listening on. Port
publishing was fine; the *bind address* was wrong.

**Evidence**
```
$ docker ps --filter name=fail-bind --format "{{.Names}}  {{.Status}}  {{.Ports}}"
fail-bind  Up 5 seconds  0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   <-- looks fine

$ docker logs fail-bind
[2026-09-10 16:58:26 +0000] [1] [INFO] Starting gunicorn 22.0.0
[2026-09-10 16:58:26 +0000] [1] [INFO] Listening at: http://127.0.0.1:5000 (1)   <-- loopback only
[2026-09-10 16:58:26 +0000] [1] [INFO] Using worker: sync

$ curl http://localhost:5000/health                  # from the HOST
curl: (52) Empty reply from server

$ docker exec fail-bind python -c "import urllib.request;     print(urllib.request.urlopen('http://127.0.0.1:5000/health').read().decode())"
{"application":"student-ml-api","status":"healthy","version":"1.0.0"}   <-- works INSIDE
```
Working inside the container but failing from the host is the signature of this
fault. Note that `docker ps` still shows the port mapping as correct, which is
why the log line and the inside/outside comparison are the decisive evidence.

**Correction**
The `CMD` binds to all interfaces:

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
```

and `app.py` uses `app.run(host="0.0.0.0", ...)` for local development. The
health check then succeeded from the host.

**Lesson**
"Container is running" is not "application is reachable". Containerised services
must bind `0.0.0.0`. The CI workflow now curls `/health` from outside the
container, so this class of fault fails the pipeline instead of reaching a user.

---

## Failure 3 — Wrong container port mapping

**Symptom**
```
$ docker run -d --name fail-port -p 5000:8000 student-ml-api:1.0.0
$ curl http://localhost:5000/health
curl: (52) Empty reply from server
```

**Root cause**
`-p HOST:CONTAINER` maps host port 5000 to **container port 8000**, but the
application listens on 5000 inside the container. Nothing was bound to 8000, so
Docker forwarded traffic into a closed port. `EXPOSE 5000` in the Dockerfile is
only documentation — it does not publish or remap anything.

**Evidence**
```
$ docker ps --filter name=fail-port --format "{{.Names}}  {{.Status}}  {{.Ports}}"
fail-port  Up 4 seconds  0.0.0.0:5000->8000/tcp, [::]:5000->8000/tcp

$ docker inspect fail-port --format '{{json .NetworkSettings.Ports}}'
{"8000/tcp":[{"HostIp":"0.0.0.0","HostPort":"5000"},{"HostIp":"::","HostPort":"5000"}]}
```
The decisive detail: only `8000/tcp` appears in the mapping. Port `5000/tcp` —
the port the application actually listens on — is not published at all, so
traffic arriving on host port 5000 is forwarded to a closed container port.

**Correction**
Use `-p 5000:5000`, matching the `EXPOSE`d and `--bind`-ed container port:

```bash
docker run -d --name student-ml-api -p 5000:5000 student-ml-api:1.0.0
```

**Lesson**
Three numbers must agree: the port the process binds, the port `EXPOSE`d, and
the container side of `-p`. `docker port <name>` is the fastest way to confirm
what is actually published.

---

## Failure 4 — Missing module on the CI runner (a genuine defect CI caught)

This failure was **not** deliberate. It is included because it is exactly the
kind of defect a Pull Request pipeline exists to catch.

**Symptom**
The first CI run on PR #1 failed during test collection, even though the same
test suite passed on the developer machine moments earlier.

```
collecting ... collected 0 items / 1 error
tests/test_app.py:8: in <module>
    from app import app as flask_app
E   ModuleNotFoundError: No module named 'app'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
##[error]Process completed with exit code 2.
```

**Root cause**
A works-on-my-machine discrepancy in how pytest was invoked. Locally the suite
was run as `python -m pytest`, and the `-m` form implicitly prepends the current
working directory to `sys.path`, so `import app` resolved. The CI workflow runs
the bare `pytest` console script, which does **not** add the CWD. With
pytest's default `prepend` import mode only the test file's own directory
(`tests/`) goes on `sys.path`, so the project root — and therefore `app.py` —
was never importable on the runner.

**Evidence**
Identical code, two different results:

```
$ python -m pytest -q      # developer machine
5 passed in 0.23s

$ pytest                   # CI runner
E   ModuleNotFoundError: No module named 'app'
```

**Correction**
Made the import path explicit in configuration rather than depending on how
pytest happens to be launched — added `pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Re-verified locally with the **bare** `pytest` command (the same form CI uses)
before pushing: `5 passed`. The follow-up CI run passed both jobs.

**Lesson**
Reproduce the CI invocation exactly, not an equivalent-looking one. Environment
assumptions that hold implicitly on a developer machine are the most common
cause of "passes locally, fails in CI", and pinning them in configuration is the
durable fix. This is also the clearest argument for requiring CI to pass before
merge: the bug was invisible locally and would otherwise have landed on `main`.
