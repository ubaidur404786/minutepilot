# 1) build the React chat page (python-service/web) into app/ui
FROM node:22-alpine AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# 2) the Python service, which serves the page and the API
FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
# the cache mount keeps downloaded packages between rebuilds
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY app ./app
COPY --from=web /src/app/ui ./app/ui
ENV DATA_DIR=/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
