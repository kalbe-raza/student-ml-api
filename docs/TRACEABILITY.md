# Part 21 — Traceability Chain

Every value below was taken from this repository and its registry — nothing is
illustrative.

## Version 1.1.0 (required chain)

```
Pull Request  #2
      |
      v
Merge Commit  12355787993dbc938c5eef6681451405b862eeca
      |
      v
Git Tag       v1.1.0
      |
      v
Docker Image  ghcr.io/kalbe-raza/student-ml-api:1.1.0
      |
      v
Image Digest  sha256:331c819532caf6bca77068735fb50eb2d336f0524474ece6457eee20a6fdaa6c
```

| Link | Value |
|---|---|
| Pull Request | [#2](https://github.com/kalbe-raza/student-ml-api/pull/2) — *feat: expose model metadata on /health and release 1.1.0* |
| Merge commit | `12355787993dbc938c5eef6681451405b862eeca` (short `1235578`) |
| Git tag | `v1.1.0` |
| Release run | [34506930589](https://github.com/kalbe-raza/student-ml-api/actions/runs/34506930589) |
| Image tags | `1.1.0`, `latest`, `1235578` |
| Image digest | `sha256:331c819532caf6bca77068735fb50eb2d336f0524474ece6457eee20a6fdaa6c` |

## Version 1.0.0

| Link | Value |
|---|---|
| Pull Request | [#1](https://github.com/kalbe-raza/student-ml-api/pull/1) |
| Merge commit | `9323ff4e9e8e262f3310f470f2932488d288a84a` (short `9323ff4`) |
| Git tag | `v1.0.0` |
| Release run | [34506445173](https://github.com/kalbe-raza/student-ml-api/actions/runs/34506445173) |
| Image tags | `1.0.0`, `9323ff4` (`latest` has since moved to 1.1.0) |
| Image digest | `sha256:156dae8bf5040e37ead186450df4d3f60cfb3bb17802f33367027354f1ccd311` |

## The chain is machine-verifiable in both directions

**Image → commit.** The image carries OCI labels written at build time:

```
$ docker inspect ghcr.io/kalbe-raza/student-ml-api:1.1.0 --format '{{json .Config.Labels}}'
org.opencontainers.image.version    1.1.0
org.opencontainers.image.revision   12355787993dbc938c5eef6681451405b862eeca
org.opencontainers.image.source     https://github.com/kalbe-raza/student-ml-api
org.opencontainers.image.created    2026-09-10T17:13:42Z
```

Given only a running container, `image.revision` names the exact commit that
produced it — no guessing from timestamps.

**Commit → image.** The release workflow also publishes a commit-SHA tag, so the
image built from commit `1235578` is addressable as
`ghcr.io/kalbe-raza/student-ml-api:1235578`.

**Tag → version.** The workflow derives `1.1.0` from the tag `v1.1.0`
(`VERSION="${RAW_TAG#v}"`); the version is never hard-coded. A guard step then
fails the release if the `VERSION` file disagrees with the tag, so the file, the
tag, the image tag and the reported `application_version` cannot drift apart.

## Consistency check across all five representations of 1.1.0

| Where the version appears | Value |
|---|---|
| `VERSION` file on `main` | `1.1.0` |
| Git tag | `v1.1.0` |
| Docker image tag | `1.1.0` |
| OCI label `image.version` | `1.1.0` |
| `/health` → `application_version` | `1.1.0` |
