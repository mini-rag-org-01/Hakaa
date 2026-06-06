# mini-RAG — Architecture Reference

> **Version:** 0.1  
> **Stack generation:** Docker Compose · FastAPI · PostgreSQL + pgvector · Qdrant · Nginx · Prometheus · Grafana

This document is the authoritative reference for how mini-RAG is structured.
It answers two practical questions for every layer:

1. *Where does this piece of functionality live?*
2. *How does it participate in a live request?*

---

## 1. System-level overview

```
Browser / curl
      │
      ▼
  [ Nginx :80 ]  ← reverse-proxy, SSL termination point
      │
      ▼
  [ FastAPI :8000 ]  ← Uvicorn ASGI server (4 workers in Docker)
      │
      ├── PostgreSQL + pgvector :5432   ← relational store + vector index
      ├── Qdrant :6333/:6334            ← optional local vector store
      ├── Prometheus :9090              ← metrics scraping
      └── Grafana :3000                 ← metrics dashboards
```

All services live on a single Docker bridge network named `backend`.
They communicate by service name (e.g., `pgvector`, `fastapi`, `prometheus`).

---

## 2. Repository layout

```
mini-rag/
├── docker/
│   ├── docker-compose.yml          # full service graph
│   ├── .env.example                # Docker-level env template
│   ├── env/
│   │   ├── .env.app                # FastAPI runtime config (copied to src/.env in CI)
│   │   ├── .env.postgres           # PostgreSQL superuser credentials
│   │   ├── .env.postgres-exporter  # postgres_exporter DSN
│   │   └── .env.grafana            # Grafana admin credentials
│   ├── minirag/
│   │   ├── Dockerfile              # FastAPI image definition
│   │   ├── entrypoint.sh           # runs alembic then starts uvicorn
│   │   └── alembic.ini             # alembic config for the container
│   ├── nginx/
│   │   └── default.conf            # Nginx proxy rules
│   └── prometheus/
│       └── prometheus.yml          # scrape targets
├── src/
│   ├── main.py                     # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example                # application config template
│   ├── assets/
│   │   ├── files/                  # uploaded files, grouped by project_id
│   │   └── databases/              # local Qdrant embedded storage (when using QDRANT backend)
│   ├── controllers/                # business logic / service layer
│   ├── helpers/                    # settings loader
│   ├── models/                     # PostgreSQL ORM + data-access layer
│   │   └── db_schemes/minirag/     # Alembic migrations + SQLAlchemy schemas
│   ├── routes/                     # FastAPI HTTP endpoints
│   ├── stores/
│   │   ├── LLM/                    # LLM + embedding provider abstraction
│   │   └── vectordb/               # vector DB provider abstraction
│   └── utils/
│       └── metrics.py              # Prometheus middleware
└── ARCHITECTURE.md
```

---

## 3. Infrastructure layer — `docker/`

### `docker-compose.yml`

Defines eight services that run together:

| Service | Image | Port(s) | Role |
|---|---|---|---|
| `fastapi` | built from `Dockerfile` | 8000 | ASGI app |
| `nginx` | `nginx:stable-alpine` | 80 | Reverse proxy |
| `pgvector` | `pgvector/pgvector:0.8.2-pg18` | 5432 | PostgreSQL + vector extension |
| `qdrant` | `qdrant/qdrant:v1.18.2` | 6333, 6334 | Optional vector store |
| `prometheus` | `prom/prometheus:v3.12.0` | 9090 | Metrics collection |
| `grafana` | `grafana/grafana:11.6.15` | 3000 | Metrics dashboards |
| `node-exporter` | `prom/node-exporter:v1.11.1` | 9100 | Host-level OS metrics |
| `postgres-exporter` | `prometheuscommunity/postgres-exporter:v0.19.0` | 9187 | PostgreSQL metrics |

`fastapi` has a `depends_on` health-check on `pgvector` so the app only starts after PostgreSQL is ready.

### `docker/minirag/Dockerfile`

Base image: `ghcr.io/astral-sh/uv:0.11.19-python3.11-trixie` (uv-accelerated Python 3.11).

Build steps:

1. Install OS dependencies (libpq, image libs, build tools).
2. Copy `src/requirements.txt` and install with `uv pip install --system`.
3. Copy full `src/` tree into `/app`.
4. Copy `alembic.ini` into the expected Alembic location.
5. Copy and chmod `entrypoint.sh`.

`entrypoint.sh` runs `alembic upgrade head` before handing off to the `CMD` (`uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`).

### `docker/nginx/default.conf`

Nginx listens on port 80 and proxies all traffic to `http://fastapi:8000`.
It forwards `X-Real-IP`, `X-Forwarded-For`, and `X-Forwarded-Proto` headers.
The hidden Prometheus metrics path (`/TrhBVe_m5gg2002_E5VVqS`) is also proxied.

### `docker/prometheus/prometheus.yml`

Defines scrape targets so Prometheus pulls metrics from:

- `fastapi:8000` — application-level HTTP counters and latencies
- `node-exporter:9100` — CPU, memory, disk, network
- `postgres-exporter:9187` — PostgreSQL internals

---

## 4. Application entry point — `src/main.py`

`main.py` creates the FastAPI app, wires dependencies at startup, and registers routers.

### Startup sequence (`@app.on_event("startup")`)

1. Load `Settings` from `.env` via `get_settings()`.
2. Build the PostgreSQL async connection string:
   ```
   postgresql+asyncpg://<user>:<pass>@<host>:<port>/<db>
   ```
3. Create SQLAlchemy `AsyncEngine` and `AsyncSession` factory (`app.db_client`).
4. Instantiate `LLMProviderfactory` and build:
   - `app.generation_client` — generation provider (OpenAI-compatible or Cohere)
   - `app.embedding_client` — embedding provider (same choices)
5. Instantiate `VectorDBProviderFactory` and build `app.vectordb_client` (PGVector or Qdrant), then call `await app.vectordb_client.connect()` which enables the `vector` PostgreSQL extension.
6. Build `app.template_parser` with primary and fallback languages.
7. Register Prometheus middleware via `setup_metrics(app)`.

### Shutdown (`@app.on_event("shutdown")`)

- `app.db_engine.dispose()` — closes the SQLAlchemy connection pool.
- `await app.vectordb_client.disconnect()` — graceful teardown.

### Shared objects on `app`

Routes access these through `request.app`:

| Attribute | Type | Purpose |
|---|---|---|
| `app.db_client` | `AsyncSession` factory | PostgreSQL sessions |
| `app.db_engine` | `AsyncEngine` | Engine (used for disposal) |
| `app.generation_client` | `LLMInterface` | Text generation |
| `app.embedding_client` | `LLMInterface` | Vector embeddings |
| `app.vectordb_client` | `VectorDBInterface` | Vector storage/search |
| `app.template_parser` | `TemplateParser` | Localized prompt templates |

---

## 5. Settings — `src/helpers/config.py`

Defines a Pydantic `Settings` class that reads every configuration value from the `.env` file.

Key groups:

- App metadata (`APP_NAME`, `APP_VERSION`)
- File limits (`FILE_ALLOWED_TYPES`, `FILE_MAX_SIZE`, `FILE_DEFAULT_CHUNK_SIZE`)
- PostgreSQL (`POSTRGRES_USERNAME`, `POSTRGRES_PASSWORD`, `POSTRGRES_HOST`, `POSTRGRES_PORT`, `POSTRGRES_MAIN_DATABASE`)
- LLM providers (`GENERATION_BACKEND`, `EMBEDDING_BACKEND`, `OPENAI_API_KEY`, `OPENAI_API_URL`, `COHERE_API_KEY`, `GENERATION_MODEL_ID`, `EMBEDDING_MODEL_ID`, `EMBEDDING_MODEL_SIZE`)
- Generation defaults (`INPUT_DEFAULT_MAX_CHARACTERS`, `GENERATION_DEFAULT_MAX_TOKENS`, `GENERATION_DEFAULT_TEMPRATURE`)
- Vector DB (`VECTOR_DB_BACKEND`, `VECTOR_DB_PATH`, `VECTOR_DB_DISTANCE_METHOD`, `VECTOR_DB_INDEX_THRESHOLD`)
- Language (`PRIMARY_LANG`, `DEFAULT_LANG`)

---

## 6. Routes — `src/routes/`

Routes are the HTTP entry points. They parse input, orchestrate calls into controllers and models, and return JSON.

### `src/routes/base.py`

Endpoint: `GET /api/v1/`  
Returns `APP_NAME` and `APP_VERSION` from settings. Used as a health/welcome probe.

### `src/routes/data.py`

Endpoints:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/data/upload/{project_id}` | Accept a multipart file, save to disk, register in DB |
| `POST` | `/api/v1/data/process/{project_id}` | Split saved file into text chunks, store in DB |

**Upload path:**
1. Validate file type and size via `DataController`.
2. Resolve upload directory via `ProjectController.get_project_path()`.
3. Generate unique file name via `DataController.generate_unique_filepath()`.
4. Write file to `src/assets/files/<project_id>/` with `aiofiles`.
5. Create a `Project` record if it does not exist.
6. Create an `Asset` record in PostgreSQL.

**Process path:**
1. Load the `Asset` record (one file or all project files).
2. Read file from disk via `ProcessController.get_file_content()`.
3. Split into `Document` chunks via `ProcessController.process_file_content()`.
4. Bulk-insert `DataChunk` records into PostgreSQL via `ChunkModel`.

### `src/routes/nlp.py`

Endpoints:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/nlp/index/push/{project_id}` | Embed chunks and upsert into vector DB |
| `GET` | `/api/v1/nlp/index/info/{project_id}` | Read vector collection metadata |
| `POST` | `/api/v1/nlp/index/search/{project_id}` | Semantic search over embedded chunks |
| `POST` | `/api/v1/nlp/index/answer/{project_id}` | Full RAG: retrieve + generate an answer |

### `src/routes/schemes/`

Pydantic request-body models used for validation:

- `data.py` → `ProcessRequest` (`file_id`, `chunk_size`, `overlap_size`, `do_reset`)
- `nlp.py` → `PushRequest` (`do_reset`), `SearchRequest` (`text`, `limit`)

---

## 7. Controllers — `src/controllers/`

The service / business logic layer. Controllers are called by routes and call models and stores.

### `BaseController`

Provides:
- Access to `Settings` via `get_settings()`.
- `generate_random_string()` — used for unique file name generation.
- `get_database_path()` — resolves the local Qdrant storage path.

### `ProjectController`

`get_project_path(project_id)` — resolves and creates `src/assets/files/<project_id>/` on disk.

### `DataController`

- `validate_uploaded_file(file)` — checks MIME type and size limits.
- `get_clean_file_name(filename)` — sanitizes the original filename.
- `generate_unique_filepath(project_id, filename)` — prepends a random prefix to prevent collisions.

### `ProcessController`

- `get_file_loader(file_path)` — picks `TextLoader` for `.txt`, `PyMuPDFLoader` for `.pdf`.
- `get_file_content(asset)` — loads the file using the appropriate LangChain loader.
- `process_file_content(content, chunk_size, overlap_size)` — splits with `RecursiveCharacterTextSplitter`.

### `NLPController`

The core RAG service layer.

- `create_collection_name(project_id)` → `collection_<vector_size>_<project_id>`.
- `index_into_vector_db(project, chunks, chunk_ids)` — batch-embeds chunk texts, calls `vectordb_client.insert_many()`.
- `get_vector_db_collection_info(project)` — reads collection metadata from the vector DB.
- `search_vector_db_collection(project, text, limit)` — embeds the query, calls `vectordb_client.search_by_vector()`, normalizes results.
- `answer_rag_question(project, query, limit)` — retrieves relevant chunks, builds a localized prompt from templates, calls the generation client, returns `(answer, full_prompt, chat_history)`.

---

## 8. Models — `src/models/`

PostgreSQL data-access layer using SQLAlchemy async sessions.

### `BaseDataModel`

Stores `db_client` (the session factory) and settings. All model classes inherit from this.

### `ProjectModel`

Collection: `projects`  
Manages project records. Key methods: `create_instance`, `get_project_or_create_one`, `get_all_projects`.

### `AssetModel`

Collection: `assets`  
Manages uploaded file metadata. Key methods: `create_asset`, `get_asset_record`, `get_all_project_assets`.

### `ChunkModel`

Collection: `chunks`  
Manages text chunk records. Key methods: `insert_many_chunks`, `delete_chunks_by_project_id`, `get_poject_chunks` (paginated).

---

## 9. Database schemas — `src/models/db_schemes/minirag/`

SQLAlchemy ORM models and Alembic migration infrastructure.

### Schemas

| File | Table | Key columns |
|---|---|---|
| `schemes/project.py` | `projects` | `project_id` (alphanumeric, indexed) |
| `schemes/asset.py` | `assets` | `asset_project_id`, `asset_type`, `asset_name`, `asset_size`, `asset_config` |
| `schemes/data_chunk.py` | `chunks` | `chunk_text`, `chunk_metadata`, `chunk_order`, `chunk_project_id`, `chunk_asset_id`, `chunk_id` (PK, used as FK in vector tables) |
| `schemes/retrieved_document.py` | — | Output shape: `score`, `text` |

### Alembic migrations

- `alembic/env.py` — wires SQLAlchemy async engine into Alembic.
- `alembic/versions/a3413f817c66_initial_commit.py` — initial schema migration creating all three tables.

---

## 10. Enums — `src/models/enums/`

| File | Purpose |
|---|---|
| `ResponseEnums.py` | `ResponseSignal` — all API signal strings (e.g., `FILE_UPLOADED_SUCCESS`) |
| `ProcessingEnums.py` | Supported file extensions: `.txt`, `.pdf` |
| `AssetTypeEnum.py` | Asset categories: currently `FILE` only |
| `DataBaseEnum.py` | Collection name constants: `projects`, `chunks`, `assets` |

---

## 11. LLM stores — `src/stores/LLM/`

Abstracts LLM and embedding providers behind a common interface.

### `LLMInterface` (abstract)

Required methods:
- `set_generation_model(model_id)`
- `set_embedding_model(model_id, embedding_size)`
- `generate_text(prompt, chat_history)`
- `embed_text(text, document_type)`
- `embed_texts(texts, document_type)` — batch variant
- `construct_prompt(prompt, role)`

### `LLMProviderfactory`

Reads `GENERATION_BACKEND` and `EMBEDDING_BACKEND` from settings and returns the matching provider instance.

### `providers/OpenAIProvider.py`

OpenAI-compatible provider. Works with any endpoint that conforms to the OpenAI REST spec, including OpenRouter and Ollama. Handles single and batched embeddings.

### `providers/CoHereProvider.py`

Cohere provider. Handles text truncation, `input_type` mapping (`search_document` / `search_query`), and batched embeddings to stay within trial key rate limits.

### `LLMEnums.py`

- `LLMEnums` — provider name strings (`OPENAI`, `COHERE`)
- `OpenAIEnums` / `CohereEnums` — role constants and attribute names
- `DocumentTypeEnum` — `DOCUMENT` / `QUERY` used when embedding

---

## 12. Prompt templates — `src/stores/LLM/templates/`

### `template_parser.py`

Dynamically imports locale modules by language code. `get(group, key, vars)` returns the formatted template string.

### `locales/en/rag.py` and `locales/ar/rag.py`

Each locale file defines three template strings for the RAG prompt:

- `system_prompt` — tells the model to answer only from provided documents
- `document_prompt` — wraps one retrieved chunk with its index
- `footer_template` — appends the user's query at the end

Arabic templates support bilingual deployments out of the box.

---

## 13. Vector DB stores — `src/stores/vectordb/`

### `VectorDBInterface` (abstract)

Required methods: `connect`, `disconnect`, `is_collection_existed`, `list_all_collections`, `get_collection_info`, `create_collection`, `delete_collection`, `insert_one`, `insert_many`, `search_by_vector`.

### `VectorDBProviderFactory`

Reads `VECTOR_DB_BACKEND` and instantiates the matching provider:

- `PGVECTOR` → `PGVectorDBProvider`
- `QDRANT` → `QdrantDBProvider`

### `providers/PGVectorDBProvider.py`

Primary production backend. Uses SQLAlchemy async sessions and raw SQL with the `pgvector` extension.

Key behaviors:

- `connect()` — executes `CREATE EXTENSION IF NOT EXISTS vector`.
- `create_collection(name, embedding_size, do_reset)` — creates a table with columns `id`, `text`, `vector(N)`, `metadata jsonb`, `chunk_id` (FK → `chunks`).
- `insert_many(...)` — batched inserts (default batch size 50) using parameterized SQL.
- `create_vector_index(collection_name, index_type)` — creates an HNSW index once the row count exceeds `VECTOR_DB_INDEX_THRESHOLD` (default 100). Uses the configured distance operator.
- `search_by_vector(collection_name, vector, limit)` — cosine similarity search using the `<=>` pgvector operator, returns `RetrievedDocument` list sorted by descending score.

Distance methods supported: `cosine`, `dot`, `euclidean`.
Index types supported: `HNSW` (default), `IVFFlat`.

### `providers/QdrantDBProvider.py`

Local embedded Qdrant adapter. Still available as an alternative backend. Uses `qdrant_client` with a local path for zero-dependency vector storage.

### `VectorDBEnums.py`

- Provider names: `QDRANT`, `PGVECTOR`
- Distance methods: `cosine`, `dot`, `euclidean`
- PGVector-specific: table prefix, column names, index types, SQL distance operators

---

## 14. Observability — `src/utils/metrics.py`

Adds Prometheus instrumentation via `starlette-exporter` middleware.

Two metrics are collected for every HTTP request:

| Metric | Type | Labels |
|---|---|---|
| `http_requests_total` | Counter | `method`, `endpoint`, `status` |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` |

The scrape endpoint is exposed at a randomized path (`/TrhBVe_m5gg2002_E5VVqS`) to avoid accidental public exposure. Prometheus is configured to scrape this path.

---

## 15. Storage model — three layers

| Layer | Location | Contents |
|---|---|---|
| Disk | `src/assets/files/<project_id>/` | Raw uploaded files |
| PostgreSQL | `projects`, `assets`, `chunks` tables | Relational metadata and chunk text |
| Vector DB | PGVector table or Qdrant local path | Embeddings + FKs back to `chunks` |

---

## 16. Full request flow per endpoint

### Upload (`POST /api/v1/data/upload/{project_id}`)

```
route (data.py)
  └── DataController.validate_uploaded_file()
  └── ProjectController.get_project_path()       → creates disk dir
  └── DataController.generate_unique_filepath()
  └── aiofiles.open() write                       → disk
  └── ProjectModel.get_project_or_create_one()    → PostgreSQL
  └── AssetModel.create_asset()                   → PostgreSQL
  └── return JSON
```

### Process (`POST /api/v1/data/process/{project_id}`)

```
route (data.py)
  └── AssetModel.get_asset_record()               → PostgreSQL
  └── ProcessController.get_file_content()        → disk read
  └── ProcessController.process_file_content()    → LangChain split
  └── ChunkModel.delete_chunks_by_project_id()    → PostgreSQL (if do_reset)
  └── ChunkModel.insert_many_chunks()             → PostgreSQL
  └── return JSON
```

### Index push (`POST /api/v1/nlp/index/push/{project_id}`)

```
route (nlp.py)
  └── ChunkModel.get_poject_chunks()              → PostgreSQL (paginated)
  └── NLPController.index_into_vector_db()
        └── embedding_client.embed_text(batch)    → LLM API
        └── vectordb_client.create_collection()   → PostgreSQL / Qdrant
        └── vectordb_client.insert_many()         → PostgreSQL / Qdrant
  └── return JSON
```

### Search (`POST /api/v1/nlp/index/search/{project_id}`)

```
route (nlp.py)
  └── NLPController.search_vector_db_collection()
        └── embedding_client.embed_text(query)    → LLM API
        └── vectordb_client.search_by_vector()    → PostgreSQL / Qdrant
  └── return JSON
```

### Answer (`POST /api/v1/nlp/index/answer/{project_id}`)

```
route (nlp.py)
  └── NLPController.answer_rag_question()
        └── search_vector_db_collection()         → (see Search above)
        └── template_parser.get("rag", ...)       → localized prompt
        └── generation_client.generate_text()     → LLM API
  └── return JSON {answer, full_prompt, chat_history}
```

---

## 17. Known code issues (as of current commit)

| Location | Issue |
|---|---|
| `ChunkModel.get_poject_chunks` | Typo in method name (`poject`) |
| `NLPController.index_into_vector_db` | Response signal says "vectordb success" but endpoint only writes to PostgreSQL chunks table |
| `routes/nlp.py::get_project_index_info` | Returns raw provider object; needs `dict()` / `model_dump()` before `JSONResponse` |
| `models/db_schemes/minirag/schemes/project.py` | `get_indexes()` defined twice |
| `GENERATION_DEFAULT_TEMPRATURE` env key | Typo (`TEMPRATURE`) throughout `.env` and `config.py` |
| `docker/env/.env.app` | Contains real API keys — rotate before sharing the repository |
| `PGVectorDBProvider.insert_one` | SQL string has a trailing comma before `)` — will raise a syntax error |
| `PGVectorDBProvider.insert_many` | `if not metadata` guard is logically inverted; should be `if not metadata or len(metadata) == 0` |

---

## 18. Recommended reading order for new contributors

1. `docker/docker-compose.yml` — understand the full service graph first
2. `src/main.py` — see how the app is assembled at startup
3. `src/helpers/config.py` — understand all configuration knobs
4. `src/routes/data.py` and `src/routes/nlp.py` — follow the HTTP surface
5. `src/controllers/` — understand the business logic layer
6. `src/models/` — understand the PostgreSQL access layer
7. `src/stores/LLM/` — understand provider abstraction
8. `src/stores/vectordb/providers/PGVectorDBProvider.py` — the main vector backend
9. `src/utils/metrics.py` — observability layer
