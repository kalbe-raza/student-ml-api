# Explicit, pinned base image — never python:latest, so builds are reproducible.
FROM python:3.11.9-slim

# Build-time metadata, supplied by the release workflow.
ARG APP_VERSION=dev
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown
ARG SOURCE_REPO=unknown

# OCI standard labels make the image traceable back to the exact commit.
LABEL org.opencontainers.image.title="student-ml-api" \
      org.opencontainers.image.description="Simple ML inference API used for the MLOps CI/CD exercise" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.source="${SOURCE_REPO}" \
      org.opencontainers.image.created="${BUILD_DATE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies are copied and installed first so this layer is cached and
# only re-executed when requirements.txt itself changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source changes far more often, so it is copied last.
COPY VERSION .
COPY app.py .

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Production WSGI server bound to 0.0.0.0 so the port mapping works.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
