# mini-RAG — Setup Guide

This guide covers two ways to run mini-RAG:

- **Option A — Full Docker Compose** (recommended): every service runs in a container.
- **Option B — Local dev** (Windows + WSL 2 + Conda): FastAPI runs on your machine, infrastructure runs in Docker.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker Desktop | Latest stable | Required for both options |
| Docker Compose | v2 (bundled with Docker Desktop) | Use `docker compose`, not `docker-compose` |
| Python | 3.11 | Only needed for Option B |
| Conda / Miniconda | Any | Only needed for Option B |
| WSL 2 + Ubuntu | Any LTS | Only needed for Option B on Windows |

---

## Option A — Full Docker Compose (recommended)

All eight services (FastAPI, Nginx, PostgreSQL + pgvector, Qdrant, Prometheus, Grafana, Node Exporter, Postgres Exporter) run in Docker.

### Step 1 — Start Docker Desktop

Open Docker Desktop and wait until the bottom-left status shows **"Engine running"** (green icon).

Do not proceed until Docker is fully up.

### Step 2 — Configure environment files

All environment files live under `docker/env/`. You must create real copies from the examples before bringing services up.

```bash
cd docker/env

# PostgreSQL credentials
cp .env.example.postgres .env.postgres
# Edit .env.postgres and set POSTGRES_USER and POSTGRES_PASSWORD

# PostgreSQL metrics exporter
cp .env.example.postgres-exporter .env.postgres-exporter
# Edit .env.postgres-exporter and set DATA_SOURCE_NAME to match your postgres credentials

# Grafana admin credentials
cp .env.example.grafana .env.grafana
# Edit .env.grafana and set GF_SECURITY_ADMIN_USER and GF_SECURITY_ADMIN_PASSWORD

# FastAPI application config
cp .env.example.app .env.app
# Edit .env.app — see the "Application environment" section below for all keys
```

### Step 3 — Configure the application environment (`.env.app`)

This is the most important file. Open `docker/env/.env.app` and fill in:

**LLM provider — choose Generation backend:**

```env
GENERATION_BACKEND="OPENAI"
# For OpenRouter (no local install needed):
OPENAI_API_URL="https://openrouter.ai/api/v1"
OPENAI_API_KEY="sk-or-v1-..."
GENERATION_MODEL_ID="openai/gpt-oss-120b:free"

# OR for local Ollama (must be reachable from the container):
# OPENAI_API_URL="http://host.docker.internal:11434/v1/"
# GENERATION_MODEL_ID="qwen2.5:3b"
```

**Embedding backend:**

```env
EMBEDDING_BACKEND="COHERE"
COHERE_API_KEY="..."
EMBEDDING_MODEL_ID="embed-multilingual-light-v3.0"
EMBEDDING_MODEL_SIZE=384

# OR use OpenAI embeddings:
# EMBEDDING_BACKEND="OPENAI"
# EMBEDDING_MODEL_ID="text-embedding-3-small"
# EMBEDDING_MODEL_SIZE=1536
```

**Vector DB backend — choose one:**

```env
VECTOR_DB_BACKEND="PGVECTOR"   # uses the pgvector PostgreSQL container
# OR
# VECTOR_DB_BACKEND="QDRANT"   # uses the Qdrant container
```

**PostgreSQL connection (must match `.env.postgres`):**

```env
POSTRGRES_USERNAME="postgres"
POSTRGRES_PASSWORD="your_password"
POSTRGRES_HOST="pgvector"        # Docker service name, not localhost
POSTRGRES_PORT=5432
POSTRGRES_MAIN_DATABASE="minirag"
```

### Step 4 — Build and start all services

From the `docker/` directory:

```bash
cd docker
docker compose up -d --build
```

The `--build` flag rebuilds the FastAPI image. Omit it on subsequent starts when the image has not changed.

Check that all containers are healthy:

```bash
docker compose ps
```

Expected output (all should show `running`):

```
NAME                        STATUS
fastapi                     running
nginx                       running
pgvector                    running
qdrant                      running
prometheus                  running
grafana                     running
minirag-node-exporter       running
minirag-postgres-exporter   running
```

### Step 5 — Run database migrations

The entrypoint script runs Alembic automatically. Confirm the migration ran:

```bash
docker compose logs fastapi | grep alembic
```

You should see output like:

```
INFO  [alembic.runtime.migration] Running upgrade -> a3413f817c66, initial commit
```

### Step 6 — Verify the stack

| URL | What you should see |
|---|---|
| `http://localhost/docs` | FastAPI Swagger UI (via Nginx) |
| `http://localhost:8000/docs` | FastAPI Swagger UI (direct) |
| `http://localhost:9090` | Prometheus UI |
| `http://localhost:3000` | Grafana login |
| `http://localhost:6333/dashboard` | Qdrant dashboard (if using QDRANT backend) |

---

## Option B — Local dev (Windows + WSL 2)

Use this path for faster iteration — FastAPI reloads on code changes without rebuilding the Docker image.

### Step 1 — Start Docker Desktop

Same as Option A, Step 1.

### Step 2 — Enable WSL 2 integration in Docker Desktop

1. Go to Docker Desktop → gear icon → **Settings** → **Resources** → **WSL Integration**.
2. Toggle ON **"Enable integration with my default WSL distro"**.
3. Toggle ON your specific distro (e.g., **Ubuntu**).
4. Click **"Apply & Restart"** and reopen your WSL terminal.

### Step 3 — Start infrastructure services only

You only need PostgreSQL (and optionally Qdrant) for local dev:

```bash
cd /mnt/d/mini-rag/docker

# Start just the database services:
docker compose up -d pgvector qdrant
```

Verify PostgreSQL is ready:

```bash
docker compose ps pgvector
# Status should show: healthy
```

### Step 4 — Configure `src/.env`

```bash
cd /mnt/d/mini-rag/src
cp .env.example .env
```

Open `src/.env` and set:

```env
# PostgreSQL — localhost because FastAPI is running on your machine, not in Docker
POSTRGRES_HOST="localhost"
POSTRGRES_PORT=5432
POSTRGRES_USERNAME="postgres"
POSTRGRES_PASSWORD="your_password"       # must match docker/env/.env.postgres
POSTRGRES_MAIN_DATABASE="minirag"

# LLM providers (see Option A Step 3 for all choices)
GENERATION_BACKEND="OPENAI"
OPENAI_API_URL="https://openrouter.ai/api/v1"
OPENAI_API_KEY="sk-or-v1-..."
GENERATION_MODEL_ID="openai/gpt-oss-120b:free"

EMBEDDING_BACKEND="COHERE"
COHERE_API_KEY="..."
EMBEDDING_MODEL_ID="embed-multilingual-light-v3.0"
EMBEDDING_MODEL_SIZE=384

VECTOR_DB_BACKEND="PGVECTOR"
```

### Step 5 — Create and activate a Conda environment

```bash
conda create -n mini-rag-app python=3.11 -y
conda activate mini-rag-app
```

### Step 6 — Install Python dependencies

Run this from `src/`:

```bash
cd /mnt/d/mini-rag/src
pip install -r requirements.txt
```

The `requirements.txt` includes `asyncpg`, `pgvector`, `sqlalchemy`, and `alembic`, so all PostgreSQL drivers are installed automatically.

### Step 7 — Run Alembic migrations

The Alembic config for local dev is at `src/models/db_schemes/minirag/alembic.ini`.

```bash
cd /mnt/d/mini-rag/src/models/db_schemes/minirag
alembic upgrade head
```

Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade -> a3413f817c66, initial commit
```

### Step 8 — Start the FastAPI server

```bash
cd /mnt/d/mini-rag/src
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

Expected output:

```
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Open `http://localhost:5000/docs` in your browser to confirm everything is working.

---

## Using a local Ollama model (optional)

Ollama lets you run LLMs on your own hardware without sending data to external APIs.

1. Download and install Ollama from https://ollama.com.
2. Pull a model:
   ```bash
   ollama pull qwen2.5:3b
   ```
3. Update `.env`:
   ```env
   GENERATION_BACKEND="OPENAI"
   OPENAI_API_URL="http://localhost:11434/v1/"    # local dev
   # OPENAI_API_URL="http://host.docker.internal:11434/v1/"   # Docker Compose
   OPENAI_API_KEY="ollama"                        # any non-empty string
   GENERATION_MODEL_ID="qwen2.5:3b"
   ```

> Ollama does not provide embedding models by default. Continue using Cohere or OpenAI for `EMBEDDING_BACKEND`.

---

## End-to-end API walkthrough

Once the server is running, test the full pipeline:

### 1. Health check

```bash
curl http://localhost:5000/api/v1/
# Docker Compose via Nginx:
curl http://localhost/api/v1/
```

### 2. Upload a file

```bash
curl -X POST "http://localhost:5000/api/v1/data/upload/1" \
  -F "file=@/absolute/path/to/your/document.txt"
```

Response:
```json
{
  "signal": "file_uploaded_success",
  "file_id": "abc123_document.txt",
  "asset_id": "..."
}
```

Save the `file_id` for the next step.

### 3. Process the file into chunks

```bash
curl -X POST "http://localhost:5000/api/v1/data/process/1" \
  -H "Content-Type: application/json" \
  -d '{"file_id":"abc123_document.txt","chunk_size":1000,"overlap_size":100,"do_reset":1}'
```

### 4. Push chunks into the vector DB

```bash
curl -X POST "http://localhost:5000/api/v1/nlp/index/push/1" \
  -H "Content-Type: application/json" \
  -d '{"do_reset":1}'
```

### 5. Search semantically

```bash
curl -X POST "http://localhost:5000/api/v1/nlp/index/search/1" \
  -H "Content-Type: application/json" \
  -d '{"text":"What is this document about?","limit":5}'
```

### 6. Ask a question (RAG answer)

```bash
curl -X POST "http://localhost:5000/api/v1/nlp/index/answer/1" \
  -H "Content-Type: application/json" \
  -d '{"text":"Summarize the main points.","limit":5}'
```

---

## What needs to run every time you restart

### Option A (Docker Compose)

```bash
cd docker
docker compose up -d
```

Everything starts automatically. Migrations run at container startup.

### Option B (local dev)

| Step | Command |
|---|---|
| 1. Start Docker Desktop | From Windows Start menu |
| 2. Start PostgreSQL | `docker compose up -d pgvector` |
| 3. Start Ollama (if using) | Open Ollama from Start menu |
| 4. Activate Conda | `conda activate mini-rag-app` |
| 5. Start FastAPI | `cd src && uvicorn main:app --reload --host 0.0.0.0 --port 5000` |

---

## Environment variable reference

| Variable | Example | Description |
|---|---|---|
| `APP_NAME` | `mini-RAG` | Application name returned by the health endpoint |
| `APP_VERSION` | `0.1` | Version string |
| `FILE_ALLOWED_TYPES` | `["text/plain","application/pdf"]` | Accepted MIME types |
| `FILE_MAX_SIZE` | `15` | Max file size in MB |
| `FILE_DEFAULT_CHUNK_SIZE` | `512000` | Default chunk size in bytes |
| `POSTRGRES_USERNAME` | `postgres` | PostgreSQL username |
| `POSTRGRES_PASSWORD` | `...` | PostgreSQL password |
| `POSTRGRES_HOST` | `pgvector` (Docker) / `localhost` (local) | PostgreSQL host |
| `POSTRGRES_PORT` | `5432` | PostgreSQL port |
| `POSTRGRES_MAIN_DATABASE` | `minirag` | Database name |
| `GENERATION_BACKEND` | `OPENAI` or `COHERE` | LLM generation provider |
| `EMBEDDING_BACKEND` | `OPENAI` or `COHERE` | Embedding provider |
| `OPENAI_API_KEY` | `sk-or-v1-...` | OpenAI / OpenRouter / Ollama key |
| `OPENAI_API_URL` | `https://openrouter.ai/api/v1` | Provider base URL |
| `COHERE_API_KEY` | `...` | Cohere API key |
| `GENERATION_MODEL_ID` | `openai/gpt-oss-120b:free` | Model name for generation |
| `EMBEDDING_MODEL_ID` | `embed-multilingual-light-v3.0` | Model name for embeddings |
| `EMBEDDING_MODEL_SIZE` | `384` | Embedding vector dimension |
| `INPUT_DEFAULT_MAX_CHARACTERS` | `384` | Input truncation limit |
| `GENERATION_DEFAULT_MAX_TOKENS` | `200` | Max tokens for generation output |
| `GENERATION_DEFAULT_TEMPRATURE` | `0.1` | Generation temperature (note: typo in key name is intentional — matches code) |
| `VECTOR_DB_BACKEND` | `PGVECTOR` or `QDRANT` | Vector DB backend |
| `VECTOR_DB_PATH` | `qdrant_db` | Local Qdrant storage folder (QDRANT backend only) |
| `VECTOR_DB_DISTANCE_METHOD` | `cosine` | Distance metric: `cosine`, `dot`, `euclidean` |
| `VECTOR_DB_INDEX_THRESHOLD` | `100` | Min rows before HNSW index is created |
| `PRIMARY_LANG` | `en` | Prompt template language |
| `DEFAULT_LANG` | `en` | Fallback language if template not found |

---

## Security notes

- **Never commit real API keys.** The `docker/env/.env.app` file in this repository already has keys — rotate them immediately if you share this project publicly.
- `.gitignore` excludes `.env` files in `src/` but not necessarily in `docker/env/`. Double-check before pushing.
- The Prometheus metrics endpoint is exposed at a randomized path to reduce accidental exposure — do not publicize the path.
- The Grafana and PostgreSQL admin passwords should be changed from defaults before any public deployment.
