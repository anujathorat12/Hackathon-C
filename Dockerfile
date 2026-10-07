# ── Stage 1: build the React studio ─────────────────────────────────────────────
FROM node:20-alpine AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ── Stage 2: FastAPI app serving the API and the built UI on one port ──────────
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ backend/
COPY shared/ shared/
COPY --from=ui /ui/dist frontend/dist
WORKDIR /app/backend
EXPOSE 8000
# Hosting platforms (Render, Railway) provide $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
