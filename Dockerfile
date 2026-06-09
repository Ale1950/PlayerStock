# PlayerStock — immagine SINGLE-ORIGIN: FastAPI serve /api + l'export web Expo.
# Multi-stage: (1) Node builda il bundle web, (2) Python lo serve + esegue il backend.

# ---- Stage 1: build export web (Expo) ----
FROM node:20-bookworm-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
# il preinstall (scripts/check-pkg.js) gira durante `npm ci`: serve PRIMA di npm ci
COPY frontend/scripts ./scripts
RUN npm ci
COPY frontend/ ./
# Variabili EXPO_PUBLIC_* inlinate al build:
#  - CLIENT ID Google = valore PUBBLICO (compare comunque nel bundle servito) → ok bakearlo.
#  - BACKEND_URL VUOTO ⇒ base API relativa "/api" (single-origin, niente CORS).
ARG EXPO_PUBLIC_GOOGLE_OAUTH_CLIENT_ID=48445371053-akld0ql4f36i9jdtcue0phcp31hsk5m2.apps.googleusercontent.com
ARG EXPO_PUBLIC_BACKEND_URL=
ENV EXPO_PUBLIC_GOOGLE_OAUTH_CLIENT_ID=$EXPO_PUBLIC_GOOGLE_OAUTH_CLIENT_ID \
    EXPO_PUBLIC_BACKEND_URL=$EXPO_PUBLIC_BACKEND_URL
RUN npx expo export -p web          # output: /web/dist

# ---- Stage 2: runtime Python (API + statico) ----
FROM python:3.11-slim AS app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STATIC_DIR=/app/static
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist /app/static
EXPOSE 8001
# 1 SOLO worker = 1 SOLO scheduler in-process (niente round duplicati).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 1"]
