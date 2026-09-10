# Parts 16, 17, 19, 20 — Registry, Reproducibility and Rollback Evidence

All output below is captured from a real run against `ghcr.io`.

## Part 16 — Registry verification

```
student-ml-api
├── 1.0.0    sha256:156dae8bf5040e37ead186450df4d3f60cfb3bb17802f33367027354f1ccd311
├── 1.1.0    sha256:331c819532caf6bca77068735fb50eb2d336f0524474ece6457eee20a6fdaa6c
├── latest   sha256:331c819532caf6bca77068735fb50eb2d336f0524474ece6457eee20a6fdaa6c
├── 9323ff4  (commit tag for 1.0.0)
└── 1235578  (commit tag for 1.1.0)
```

## Part 17 — Artifact reproducibility (build machine → registry → runtime)

```
$ docker rmi student-ml-api:1.0.0
Untagged: student-ml-api:1.0.0
Deleted: sha256:8981df96979ce778ed1e26808c6a04505392685d4b722821873b150813d6fd29

$ docker images student-ml-api
IMAGE   ID   DISK USAGE   CONTENT SIZE          <-- gone locally

$ docker pull ghcr.io/kalbe-raza/student-ml-api:1.0.0
Digest: sha256:156dae8bf5040e37ead186450df4d3f60cfb3bb17802f33367027354f1ccd311
Status: Downloaded newer image for ghcr.io/kalbe-raza/student-ml-api:1.0.0

$ docker run -d --name student-ml-api -p 5000:5000 ghcr.io/kalbe-raza/student-ml-api:1.0.0
$ curl http://localhost:5000/health
{"application":"student-ml-api","status":"healthy","version":"1.0.0"}
```

The digest of the pulled artifact is identical to the digest the release
workflow published. The application was **not rebuilt** — the same bytes that
passed CI were downloaded and executed.

## Part 19 — `latest` points at 1.1.0 while 1.0.0 remains available

```
$ docker inspect ghcr.io/.../student-ml-api:1.1.0  --format '{{index .RepoDigests 0}}'
...@sha256:331c819532caf6bca77068735fb50eb2d336f0524474ece6457eee20a6fdaa6c

$ docker inspect ghcr.io/.../student-ml-api:latest --format '{{index .RepoDigests 0}}'
...@sha256:331c819532caf6bca77068735fb50eb2d336f0524474ece6457eee20a6fdaa6c
```

Identical digests — `latest` and `1.1.0` are the same artifact. `1.0.0` still
resolves to its own, different digest.

## Part 20 — Rollback without touching source code or rebuilding

Problem state (1.1.0 running):

```
$ curl http://localhost:5000/health
{"application":"student-ml-api","application_version":"1.1.0","model_version":"model-1","status":"healthy"}
```

Rollback — two commands, no code change, no build:

```
$ docker rm -f student-ml-api
$ docker run -d --name student-ml-api -p 5000:5000 ghcr.io/kalbe-raza/student-ml-api:1.0.0

$ curl http://localhost:5000/health
{"application":"student-ml-api","status":"healthy","version":"1.0.0"}      <-- 1.0.0 restored

$ curl -X POST http://localhost:5000/predict -d '{"value":21}' -H 'Content-Type: application/json'
{"input":21,"prediction":42}
```

Proof that nothing was rebuilt or edited:

```
$ git status --short                       # working tree clean
$ git log --oneline -1
1235578 feat: expose model metadata on /health and release 1.1.0 (#2)     <-- source still at 1.1.0

$ docker inspect student-ml-api --format '{{.Image}}'
sha256:156dae8bf5040e37ead186450df4d3f60cfb3bb17802f33367027354f1ccd311   <-- the 1.0.0 artifact

$ docker inspect ghcr.io/.../student-ml-api:1.0.0 --format '{{.Created}}'
2026-09-10T17:09:46Z                       <-- built at release time...
$ date -u
2026-09-10T17:15:51Z                       <-- ...not at rollback time
```

The checked-out source tree is version 1.1.0, yet the service is serving 1.0.0
from an image that was built six minutes earlier by the release workflow. The
rollback is a **registry operation**, entirely decoupled from the source tree.
