# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-builder
WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATABASE_PATH=/app/data/.runtime/team-project.db \
    PROJECTS_ROOT=/app/projects \
    FRONTEND_DIST_PATH=/app/frontend/dist \
    AUTH_COOKIE_SECURE=true

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY projects ./projects
COPY tests ./tests
COPY docs ./docs
COPY .github ./.github
COPY data ./seed-data
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist
COPY scripts/railway-entrypoint.sh /usr/local/bin/railway-entrypoint

RUN chmod +x /usr/local/bin/railway-entrypoint \
    && mkdir -p /app/data

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/railway-entrypoint"]
