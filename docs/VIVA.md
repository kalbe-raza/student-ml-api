# Viva Preparation — grounded in this repository

Repository: https://github.com/kalbe-raza/student-ml-api
Registry: `ghcr.io/kalbe-raza/student-ml-api`

---

**1. Why should developers avoid directly pushing to `main`?**

Because `main` is the branch everything else is built from — releases are tagged
on it and images are published from those tags. A direct push skips review and
skips CI, so unverified code becomes releasable.

*In our repo:* `main` is protected and the rule is enforced. Attempting a direct
push is rejected with `GH006: Protected branch update failed — Changes must be
made through a pull request`. All work reached `main` through PR #1 and PR #2.

---

**2. What is the purpose of a Pull Request beyond simply merging code?**

It is the review and audit unit. It carries the rationale, the test evidence and
the discussion; it is the gate where CI results are enforced; and it becomes the
permanent record of *why* a change was made.

*In our repo:* PR #1 documents summary, changes, testing performed, Docker
impact and a checklist. It also preserves the intermediate history — including
the deliberately broken commit and its fix — which the squashed commit on `main`
does not show.

---

**3. Why should CI execute before a PR is merged?**

Because after the merge it is too late — a broken `main` blocks everyone and has
to be reverted. Pre-merge CI keeps the defect isolated to the branch.

*In our repo:* CI caught a genuine bug on PR #1 —
`ModuleNotFoundError: No module named 'app'`. It passed locally under
`python -m pytest` (which adds the CWD to `sys.path`) but failed on the runner's
bare `pytest`. Without pre-merge CI that would have landed on `main`.

---

**4. What is the difference between a Docker image and a container?**

The image is the immutable, layered filesystem plus metadata — the artifact at
rest. A container is a running instance of an image, with its own writable layer,
process and network namespace. One image, many containers.

*In our repo:* the image is
`ghcr.io/kalbe-raza/student-ml-api@sha256:156dae8…`; a container from it had ID
`0046ad10fb36`. Deleting the container leaves the image intact — which is exactly
what makes the rollback instant.

---

**5. Why should Docker images be versioned?**

So you can say precisely what is running, deploy a specific build deliberately,
and go back to a known-good one. Without versions there is no rollback target and
no way to correlate a production problem with a release.

*In our repo:* `1.0.0` and `1.1.0` both exist independently, which is the only
reason the Part 20 rollback was possible.

---

**6. Why is `latest` insufficient for production traceability?**

`latest` is a mutable pointer, not a version. It means "whatever was pushed most
recently", so it changes under you: two machines pulling `latest` a day apart can
run different code while both claiming to run `latest`. It also gives you nothing
to roll back *to*.

*In our repo:* `latest` pointed at digest `156dae8…` (1.0.0) and now points at
`331c819…` (1.1.0). The tag string is unchanged; the artifact is completely
different.

---

**7. Why should the same Docker artifact be promoted rather than rebuilt?**

Because a rebuild is a *new* artifact. Base images shift, transitive dependencies
resolve differently, build tools change — so a rebuild from the same source can
produce different bytes that were never tested. Promoting the identical digest
through staging to production means the thing you tested is the thing you ship.

*In our repo:* we deleted the local image and pulled from GHCR; the digest came
back identical (`sha256:156dae8…`), proving the runtime got the exact artifact
CI produced.

---

**8. What is the purpose of a container registry?**

It is the versioned, addressable storage and distribution point for build
artifacts — the boundary between "build once" and "run anywhere". It decouples
the build machine from every runtime environment.

*In our repo:* GHCR. The image was built by a GitHub-hosted runner and executed
on a local Windows machine that never compiled it.

---

**9. What is the difference between the CI workflow and the release workflow?**

Trigger and authority. CI runs on Pull Requests, has read-only permissions, and
*verifies* — it builds the image purely to prove the Dockerfile works, then
discards it. Release runs only on a `v*.*.*` tag, holds `packages: write`, and
*publishes*.

*In our repo:* `ci.yml` (`on: pull_request`, `permissions: contents: read`, no
push step) versus `release.yml` (`on: push: tags: v*.*.*`, `packages: write`,
`push: true`).

---

**10. Why should registry credentials be stored as secrets?**

Because anything in the repository is visible to anyone who can read it and lives
forever in Git history. A leaked registry credential lets an attacker publish a
malicious image under a trusted name — which then gets deployed automatically.

*In our repo:* no credential exists in the tree at all. The release workflow uses
the automatically-provided `GITHUB_TOKEN` secret, which GitHub mints per-run,
scopes to this repository, and expires when the job ends.

---

**11. How can you identify which source-code commit produced a Docker image?**

Two independent mechanisms in this repo:

- **OCI label.** `docker inspect ghcr.io/kalbe-raza/student-ml-api:1.1.0` shows
  `org.opencontainers.image.revision = 12355787993dbc938c5eef6681451405b862eeca`.
- **Commit-SHA tag.** The same image is also published as tag `1235578`.

The first works from a running container with no external lookup; the second lets
you go from a commit to its image.

---

**12. Why does Docker layer ordering affect CI/CD performance?**

Layers are cached in order, and invalidating one invalidates every layer after
it. Put the volatile thing (source) before the expensive thing (dependency
install) and you pay for the install on every commit.

*Measured in our repo:* changing `app.py` reused the cached `pip install` layer
(~1s rebuild); changing `requirements.txt` correctly invalidated it (11.2s).
Full output in `docs/evidence/PART25_build_cache.md`.

---

**13. How would you rollback from 1.1.0 to 1.0.0?**

```bash
docker rm -f student-ml-api
docker run -d --name student-ml-api -p 5000:5000 ghcr.io/kalbe-raza/student-ml-api:1.0.0
curl http://localhost:5000/health
```

No source change, no rebuild, no redeploy pipeline. We demonstrated it: the
working tree stayed on the 1.1.0 commit while the service served
`{"version":"1.0.0"}` from an image built minutes earlier.

For a *permanent* rollback you would also revert the code on `main` via a PR and
cut `v1.1.1` — but the immediate mitigation is the registry operation above.

---

**14. What is the relationship between a Git tag and a Docker image tag?**

The Git tag marks a point in source history; the Docker image tag names the
artifact built from it. In this project the second is **derived** from the first:

```bash
RAW_TAG="${GITHUB_REF#refs/tags/}"   # v1.1.0
VERSION="${RAW_TAG#v}"               # 1.1.0
```

The version is never hard-coded. A guard step additionally fails the release if
the `VERSION` file disagrees with the tag, so source version, Git tag, image tag
and the version reported by `/health` cannot drift apart.

---

**15. In an MLOps system, what problems arise when application version and model version change independently?**

They are two axes of change behind one endpoint, and conflating them makes
incidents unresolvable:

- **Attribution.** If prediction quality drops, was it the code or the model?
  With a single version number you cannot tell.
- **Rollback granularity.** You may need to revert the model while keeping a code
  fix, or vice versa. One version number forces you to revert both.
- **Combinatorial validity.** Not every code/model pair is compatible — a model
  may require a feature transform that only newer code implements.
- **Reproducibility.** Reproducing a past prediction requires *both* versions plus
  the data, not just a commit SHA.

*In our repo:* this is exactly why 1.1.0 splits `/health` into
`application_version` (`1.1.0`, read from the `VERSION` file) and `model_version`
(`model-1`). A production instance now self-reports both axes. The natural next
step is to carry the model version as its own OCI label and its own tag axis.

---

## Extra questions worth expecting

**Why squash and merge rather than a merge commit?**

Each PR is one reviewed unit of change, so `main` becomes a linear list of
features where every commit is a state that passed CI. The messy intermediate
history — including our deliberately broken commit — stays visible on the PR, so
nothing is lost for audit. Linear history also makes `git bisect` meaningful.

**Why does CI build the image if it throws it away?**

To fail fast. A Dockerfile can break independently of the tests (bad base image,
missing system dependency, broken `COPY`). Catching that on the PR means the
release workflow does not fail *after* a tag has already been pushed — at which
point the tag is public and the fix requires a new version.

**Why is `requirements-dev.txt` separate from `requirements.txt`?**

So `pytest` is never installed into the production image. The image contains only
what the service needs at runtime — smaller image, smaller attack surface.

**Why does the app read the version from a file instead of a constant?**

One source of truth. A constant in `app.py` and a `VERSION` file would inevitably
drift; reading the file makes drift impossible, and the release workflow's guard
step extends that guarantee to the Git tag.
