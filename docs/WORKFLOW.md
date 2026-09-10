# Workflow, Configuration and Design Decisions

## 1. Branch protection settings applied to `main` (Part 7)

| Setting | Value | Reason |
|---|---|---|
| Require a pull request before merging | **Enabled** | Makes direct pushes to `main` impossible; every change is reviewed. |
| Required approvals | **1** (0 for a solo repository, see note) | Forces an explicit review step. |
| Require status checks to pass before merging | **Enabled** | A PR cannot merge while CI is red. |
| Required checks | `Unit Tests`, `Docker Build Validation` | Both the test job and the Docker build check must be green. |
| Require branches to be up to date before merging | **Enabled** | Prevents "semantic" merge breakage from stale branches. |
| Require conversation resolution before merging | **Enabled** | Review comments must be addressed, not ignored. |
| Block force pushes | **Enabled** | `main` history can never be rewritten. |
| Block deletions | **Enabled** | `main` cannot be deleted accidentally. |
| Do not allow bypassing the above settings | **Enabled** | The rules also apply to repository administrators. |

> Note: on a single-maintainer repository GitHub will not let the PR author
> approve their own PR, so "required approvals" is set to 0 while every other
> rule stays enforced. The review step is still performed and documented on the
> PR itself. In a team repository this would be set to 1 or more.

### Verified by attempting a direct push to `main`

```
$ git push origin main
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote:
remote: - Changes must be made through a pull request.
remote:
remote: - 2 of 2 required status checks are expected.
To https://github.com/kalbe-raza/student-ml-api.git
 ! [remote rejected] main -> main (protected branch hook declined)
error: failed to push some refs
```

Because `enforce_admins` is enabled, the repository owner is blocked too — the
rule cannot be bypassed by the person who created it.

## 2. Merge strategy (Part 8)

**Selected strategy: Squash and Merge.**

Justification:

- Each Pull Request represents one logical, reviewed unit of change. Squashing
  makes `main` a linear list of *features*, not of work-in-progress commits.
- The intermediate commits (including the deliberately broken test commit and
  its fix) remain fully visible on the PR itself, so nothing is lost for audit
  purposes — the traceability chain runs PR → merge commit → tag → image.
- A linear `main` makes `git bisect` and rollback reasoning simple: one commit
  per feature, and every commit on `main` is a state that passed CI.
- The squash commit message retains the PR number (`(#1)`), which is what links
  the merge commit back to the Pull Request.

## 3. Why publishing images from every Pull Request is undesirable (Part 22)

- **Registry pollution.** Every push to every PR would create an image. The
  registry stops being a catalogue of releasable artifacts and becomes a pile of
  scratch builds.
- **Unreviewed code becomes deployable.** An image in the shared registry looks
  official. If any PR can publish, unreviewed and possibly failing code becomes
  pullable by anyone — including a deployment system.
- **Credential exposure.** Publishing requires write credentials. A workflow
  triggered by a PR — potentially from a fork — must never have write access to
  the registry, or a malicious PR could exfiltrate the token.
- **Meaningless versions.** A PR has no semantic version. You would be forced to
  publish to `latest` or a branch name, which destroys the version → artifact
  relationship.
- **Cost and time.** Pushing image layers on every commit is slow and consumes
  storage for artifacts nobody will ever deploy.

CI therefore *builds* the image to prove the Dockerfile is valid, then throws it
away. Only a semantic version tag — which can only exist on a reviewed, merged
commit — triggers a publish.

## 4. Benefit of a commit-specific image tag (Part 24)

Semantic tags describe *intent*; the commit tag describes *identity*.

- `latest` is mutable and `1.1.0` is intended to be immutable but can be
  re-pushed by mistake. The short SHA tag is unambiguous: it names exactly one
  commit.
- It closes the traceability loop in both directions — given a running
  container you can read its tag and go straight to the source commit; given a
  commit you can find the image that was built from it.
- It allows deploying an exact build for debugging without inventing a version
  number, and lets you prove that two environments are running the identical
  build.

## 5. Rollback: why the registry beats `git clone && pip install` (Part 20)

Rolling back with the registry is a single command against an **artifact that
already exists and has already been tested**:

```bash
docker run -d -p 5000:5000 ghcr.io/<owner>/student-ml-api:1.0.0
```

The alternative rebuilds the application at the worst possible moment:

- `git clone` + `pip install` re-resolves dependencies **now**, not at the time
  the version was released. An unpinned transitive dependency, a yanked package,
  or an unreachable index turns a rollback into a new, untested build.
- It depends on the host having the right Python version, compilers and system
  libraries. The container carries its own runtime.
- It is slow and can fail — exactly when the service is already broken.
- The result is not provably identical to what was tested. Pulling by digest is
  bit-for-bit the artifact that passed CI.

This is the "build once, promote the same artifact" principle: the image is
built one time and moved between environments unchanged.

## 6. Traceability chain (Part 21)

See [`TRACEABILITY.md`](TRACEABILITY.md).
