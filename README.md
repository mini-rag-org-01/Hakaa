---
title: Mini RAG
emoji: 🔎
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Mini RAG

FastAPI mini RAG application with Supabase pgvector.

# mini-RAG

A lightweight Retrieval-Augmented Generation (RAG) backend built with FastAPI.

Upload documents, embed them, and query them with natural language — mini-RAG handles the full pipeline from file ingestion to LLM-generated answers.

---

## What it does

1. **Upload** — accept `.txt` or `.pdf` files per project
2. **Process** — split files into overlapping text chunks stored in PostgreSQL
3. **Index** — embed chunks using an LLM provider and store vectors in a vector DB
4. **Search** — retrieve the most semantically similar chunks for any query
5. **Answer** — generate a grounded answer from retrieved chunks using an LLM

---

## Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| Relational DB | PostgreSQL 18 + pgvector extension |
| Vector DB | pgvector (primary) or Qdrant (alternative) |
| Async DB driver | SQLAlchemy async + asyncpg |
| DB migrations | Alembic |
| File loading | LangChain + PyMuPDF |
| LLM providers | OpenAI-compatible (OpenRouter, Ollama) · Cohere |
| Reverse proxy | Nginx |
| Observability | Prometheus + Grafana + node-exporter + postgres-exporter |
| Containerization | Docker Compose |

---

## Repository layout

```
mini-rag/
├── docker/
│   ├── docker-compose.yml         # full 8-service stack
│   ├── env/                       # environment files (not committed with real keys)
│   ├── minirag/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh          # runs alembic then starts uvicorn
│   ├── nginx/default.conf
│   └── prometheus/prometheus.yml
├── src/
│   ├── main.py                    # FastAPI app, startup wiring
│   ├── requirements.txt
│   ├── controllers/               # business logic / service layer
│   ├── helpers/config.py          # settings loader
│   ├── models/                    # PostgreSQL models and data-access layer
│   │   └── db_schemes/minirag/    # SQLAlchemy ORM schemas + Alembic migrations
│   ├── routes/                    # HTTP endpoints
│   ├── stores/
│   │   ├── LLM/                   # generation + embedding provider abstraction
│   │   └── vectordb/              # vector DB provider abstraction
│   ├── utils/metrics.py           # Prometheus middleware
│   └── assets/
│       ├── files/                 # uploaded files (grouped by project_id)
│       └── databases/             # local Qdrant storage (if using QDRANT backend)
├── ARCHITECTURE.md
├── setup_guide.md
└── README.md
```

---

## Quick start (Docker Compose)

### 1. Configure environment files

```bash
cd docker/env

cp .env.example.postgres         .env.postgres
cp .env.example.postgres-exporter .env.postgres-exporter
cp .env.example.grafana          .env.grafana
cp .env.example.app              .env.app
```

Edit each file. The most important one is `.env.app` — set your LLM provider keys and PostgreSQL credentials.

### 2. Start all services

```bash
cd docker
docker compose up -d --build
```

### 3. Verify

```
http://localhost/docs       → FastAPI Swagger UI
http://localhost:9090       → Prometheus
http://localhost:3000       → Grafana
```

For local dev setup (Windows + WSL 2 + Conda), see `setup_guide.md`.

---

## API overview

Base URL: `http://localhost/api/v1` (via Nginx) or `http://localhost:8000/api/v1` (direct)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — returns app name and version |
| `POST` | `/data/upload/{project_id}` | Upload a file into a project |
| `POST` | `/data/process/{project_id}` | Split uploaded file(s) into chunks |
| `POST` | `/nlp/index/push/{project_id}` | Embed chunks and push into vector DB |
| `GET` | `/nlp/index/info/{project_id}` | Get vector collection metadata |
| `POST` | `/nlp/index/search/{project_id}` | Semantic search over indexed chunks |
| `POST` | `/nlp/index/answer/{project_id}` | Full RAG: retrieve + generate answer |

---

## End-to-end pipeline example

```bash
# 1. Upload
curl -X POST "http://localhost/api/v1/data/upload/1" \
  -F "file=@/path/to/document.txt"

# 2. Process (chunk)
curl -X POST "http://localhost/api/v1/data/process/1" \
  -H "Content-Type: application/json" \
  -d '{"file_id":"<returned_file_id>","chunk_size":1000,"overlap_size":100,"do_reset":1}'

# 3. Index (embed + store vectors)
curl -X POST "http://localhost/api/v1/nlp/index/push/1" \
  -H "Content-Type: application/json" \
  -d '{"do_reset":1}'

# 4. Ask a question
curl -X POST "http://localhost/api/v1/nlp/index/answer/1" \
  -H "Content-Type: application/json" \
  -d '{"text":"What is this document about?","limit":5}'
```

---

## LLM provider options

### Generation

| Provider | `GENERATION_BACKEND` | Notes |
|---|---|---|
| OpenRouter | `OPENAI` | Remote API, no local install, set `OPENAI_API_URL=https://openrouter.ai/api/v1` |
| Ollama | `OPENAI` | Local models, set `OPENAI_API_URL=http://host.docker.internal:11434/v1/` |
| Cohere | `COHERE` | Set `COHERE_API_KEY` |

### Embedding

| Provider | `EMBEDDING_BACKEND` | Notes |
|---|---|---|
| Cohere | `COHERE` | `embed-multilingual-light-v3.0` supports 100+ languages |
| OpenAI | `OPENAI` | `text-embedding-3-small` (size 1536) or `text-embedding-3-large` |

---

## Vector DB options

| Backend | `VECTOR_DB_BACKEND` | Notes |
|---|---|---|
| pgvector | `PGVECTOR` | Runs inside the PostgreSQL container, no extra service needed |
| Qdrant | `QDRANT` | Separate Qdrant container, stores local files under `src/assets/databases/` |

The pgvector backend creates an HNSW index automatically once a collection reaches `VECTOR_DB_INDEX_THRESHOLD` rows (default 100).

---

## Prompt language support

RAG prompts are localized. Templates live in `src/stores/LLM/templates/locales/`.

Supported languages out of the box:

- English (`en`)
- Arabic (`ar`)

Set `PRIMARY_LANG` and `DEFAULT_LANG` in `.env` to control which templates are used.

---

## Observability

Prometheus scrapes metrics from three sources:

- FastAPI app — HTTP request counts and latencies per endpoint
- Node Exporter — host CPU, memory, disk, network
- Postgres Exporter — PostgreSQL connection pool, query performance, table sizes

Import the standard Grafana dashboards (IDs `1860` for Node Exporter and `9628` for PostgreSQL) to get instant visibility.

---

## Key configuration variables

| Variable | Default | Description |
|---|---|---|
| `POSTRGRES_HOST` | `pgvector` (Docker) | PostgreSQL host |
| `VECTOR_DB_BACKEND` | `PGVECTOR` | `PGVECTOR` or `QDRANT` |
| `GENERATION_BACKEND` | `OPENAI` | `OPENAI` or `COHERE` |
| `EMBEDDING_BACKEND` | `COHERE` | `OPENAI` or `COHERE` |
| `EMBEDDING_MODEL_SIZE` | `384` | Must match the model's actual output dimension |
| `PRIMARY_LANG` | `en` | Prompt template language |
| `VECTOR_DB_INDEX_THRESHOLD` | `100` | Rows needed before HNSW index is created |

See `src/.env.example` for the full list.

---

## Known issues

- `GENERATION_DEFAULT_TEMPRATURE` env key has a typo (matches the code — do not correct the env key without also updating `config.py`).
- `GET /nlp/index/info/{project_id}` returns a raw provider object that needs serialization cleanup before it is fully JSON-safe.
- The process endpoint success signal mentions "vectordb" even though this step only writes to PostgreSQL — it is misleading but harmless.

See `Errors&Sol.txt` for specific bugs encountered and their fixes.
See `ARCHITECTURE.md` for a full codebase breakdown.

---

## Security

- Do not commit real API keys. Rotate any keys that appear in `.env` files before sharing this repository.
- All `.env` files under `src/` are excluded by `.gitignore`. Files under `docker/env/` must be managed manually.
- The Prometheus metrics endpoint is exposed at a randomized path to limit accidental public exposure.
