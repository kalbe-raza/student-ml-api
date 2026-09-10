# Part 25 — Docker Build Cache Analysis

All three builds used **identical `--build-arg` values**, so the only variable
was the source file that changed.

## Build A — only `app.py` modified

```
#6  [3/7] COPY requirements.txt .                                   CACHED
#7  [4/7] RUN pip install --no-cache-dir -r requirements.txt        CACHED
#8  [2/7] WORKDIR /app                                              CACHED
#9  [5/7] COPY VERSION .                                            CACHED
#10 [6/7] COPY app.py .                                             DONE 0.2s
#11 [7/7] RUN useradd ... && chown -R appuser:appuser /app          DONE 0.5s
```

**Layers reused:** base image, `WORKDIR`, `COPY requirements.txt`, and — most
importantly — the expensive `pip install` layer.
**Rebuilt:** only `COPY app.py` and the trailing `useradd`/`chown` layer.
**Dependency install time: 0s.**

## Build B — `requirements.txt` modified

```
#6  [2/7] WORKDIR /app                                              CACHED
#7  [3/7] COPY requirements.txt .                                   DONE 0.1s
#8  [4/7] RUN pip install --no-cache-dir -r requirements.txt        DONE 11.2s
#9  [5/7] COPY VERSION .                                            DONE 0.2s
#10 [6/7] COPY app.py .                                             DONE 0.3s
#11 [7/7] RUN useradd ...                                           DONE 0.7s
```

**Dependency install time: 11.2s** — the cache was correctly invalidated.

## Why this COPY ordering is preferable

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt      # <- expensive, rarely changes
COPY app.py .                            # <- cheap, changes constantly
```

Docker caches layers **in order**, and invalidating one layer invalidates every
layer after it. Application code changes on almost every commit, while
dependencies change rarely. By copying `requirements.txt` first and installing
before the source is copied, the costly `pip install` layer stays valid across
ordinary code changes.

The alternative:

```dockerfile
COPY . .                                 # any code change invalidates this
RUN pip install -r requirements.txt      # ...so pip re-runs every single time
```

`COPY . .` puts the constantly-changing source *before* the install step, so a
one-character change to `app.py` forces a full dependency reinstall. In this
project that is the difference between a **~1 second** rebuild and an
**~11 second** rebuild; on a real ML image with torch/numpy it is the difference
between seconds and many minutes on every CI run.
