# Uso opzionale per test web/server, non necessario per il setup.exe finale.
FROM node:20-bookworm AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY --from=frontend /app/frontend/dist ./frontend/dist
ENV MN_DESKTOP_DIST=/app/frontend/dist
ENV MN_BACKEND_PORT=8000
EXPOSE 8000
WORKDIR /app/backend
CMD ["python", "desktop_server.py"]
