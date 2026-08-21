---
title: Hakaa
emoji: 📜
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# Hakaa — حكّاء

**Hakaa** is an Arabic-first Retrieval-Augmented Generation (RAG) application for exploring historical books and documents through natural-language conversations.

The system provides two interfaces:

- A public chat interface where users select an available historical project and ask questions about its sources.
- A protected administration dashboard where administrators create and manage projects, upload documents, configure chunking, run indexing, and monitor project status.

Hakaa was originally built from the lightweight **mini-RAG** backend and was extended into a deployable, project-based historical knowledge platform.

Production: [https://hakaa.publicvm.com](https://hakaa.publicvm.com)

---

## Main features

- Arabic and English user interfaces.
- Separate public chat and protected administration dashboard.
- Named projects with automatically generated numeric IDs.
- Public/private project visibility and project lifecycle status.
- Upload and processing of `.txt` and `.pdf` documents.
- Configurable chunk size and overlap from the administration UI.
- Arabic-aware text preprocessing and recursive chunking.
- Preservation of source metadata during processing and retrieval.
- Semantic vector search using multilingual embeddings.
- Grounded answers generated only from retrieved document chunks.
- Source references containing the stored filename and page number when available.
- PostgreSQL for projects, assets, and chunks.
- pgvector as the primary vector database, with optional Qdrant support.
- HTTPS termination and reverse proxying through Nginx.
- Basic Authentication for the administration dashboard and ingestion endpoints.
- Monitoring through Prometheus, Grafana, Loki, and system exporters.
- Docker Compose deployment and GitHub Actions delivery workflow.

---

## How Hakaa works

Each collection of related historical sources is represented as a **project**.

1. The administrator creates a project and gives it a descriptive name.
2. PostgreSQL generates the project ID automatically.
3. One or more TXT or PDF sources are uploaded to that project.
4. Hakaa cleans and splits the text into overlapping chunks.
5. Chunk text and metadata are stored in PostgreSQL.
6. Multilingual embeddings are generated for the chunks.
7. The embeddings are stored in a project-specific vector collection.
8. The administrator marks the project as `ready` and optionally makes it public.
9. The public chat displays only projects that are both public and ready.
10. A user selects a project and asks a question.
11. Hakaa retrieves the most semantically relevant chunks and sends them to the generation model.
12. The response is displayed with its available source references.

---

## Application interfaces

### Public chat

The public interface is available at `/`.

It allows the user to:

- Select a public, ready project by name.
- Ask questions in Arabic or English.
- Receive answers grounded in the selected project's sources.
- View the filename and page number of the retrieved sources when that metadata is available.

### Administration dashboard

The administration interface is available at `/admin/` and is protected by Nginx Basic Authentication.

It allows an administrator to:

- Create projects without manually choosing numeric IDs.
- Edit the project name and description.
- Control project status and public visibility.
- Select an existing project.
- Upload TXT and PDF files.
- Select chunk size and overlap.
- Run the upload, processing, embedding, and indexing pipeline.
- View indexed-record counts and operation progress.
- Open the chat or monitoring dashboard.

---

## Document preprocessing

Hakaa performs a preprocessing stage before creating embeddings.

### Text cleaning

The preprocessing layer:

- Replaces non-breaking spaces.
- Removes invisible left-to-right and right-to-left marks.
- Normalizes repeated spaces and tabs.
- Normalizes unnecessary line breaks.
- Skips empty pages or documents.

### Recursive chunking

The current splitter uses LangChain's `RecursiveCharacterTextSplitter` and attempts to preserve meaningful Arabic boundaries in this order:

1. Paragraph breaks.
2. Line breaks.
3. Arabic question marks.
4. Full stops.
5. Arabic commas.
6. Spaces.
7. Individual characters as a final fallback.

The default configuration is:

| Setting | Default |
|---|---:|
| Chunk size | 400 characters |
| Chunk overlap | 60 characters |

Both values can be changed from the administration interface before processing a file. The overlap must be smaller than the chunk size.

### Preserved metadata

Each generated chunk can preserve:

- `source`
- `file_id`
- `page_number`
- `page_chunk_index`

PDF files preserve page-level boundaries. A plain TXT file is loaded as one document, so its chunks normally use page number `1` unless page boundaries are introduced by a future TXT parser.

---

## Retrieval and answer generation

The current retrieval pipeline uses dense semantic search:

1. The user's question is embedded as a query vector.
2. Hakaa searches the selected project's pgvector collection.
3. The most similar chunks are returned with their scores, metadata, and chunk IDs.
4. Duplicate source references are removed using `(file_id, page_number)` as the source key.
5. The retrieved chunks are formatted into the localized RAG prompt.
6. The generation model produces an answer based only on those chunks.
7. The API returns the answer and its deduplicated source list.

Example source object:

```json
{
  "title": "history.pdf",
  "page_number": 25,
  "chunk_id": 123,
  "score": 0.91
}
```

The second version of Hakaa is preparing the retrieval layer for lexical search, hybrid search, Reciprocal Rank Fusion, reranking, and measurable retrieval evaluation. These features should not be considered complete until they are implemented and evaluated.

---

## Technology stack

| Layer | Technology |
|---|---|
| Public UI | HTML, CSS, vanilla JavaScript |
| Administration UI | HTML, CSS, vanilla JavaScript |
| API framework | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| Relational database | PostgreSQL + pgvector extension |
| Vector database | pgvector (primary) or Qdrant (alternative) |
| Async database access | SQLAlchemy async + asyncpg |
| Database migrations | Alembic |
| File loading | LangChain loaders + PyMuPDF |
| Text splitting | RecursiveCharacterTextSplitter |
| Generation providers | OpenAI-compatible APIs, OpenRouter, Ollama, or Cohere |
| Embedding providers | Cohere or OpenAI-compatible APIs |
| Reverse proxy | Nginx |
| TLS certificates | Let's Encrypt + Certbot |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Logs | Loki |
| Host metrics | Node Exporter |
| PostgreSQL metrics | Postgres Exporter |
| Containerization | Docker Compose |
| Deployment automation | GitHub Actions over SSH |

---

## Architecture

```text
Browser
├── Public chat: /
└── Admin dashboard: /admin/
          │
          ▼
Nginx
├── HTTPS termination
├── Static UI delivery
├── Basic Auth for administration routes
└── /api/ reverse proxy
          │
          ▼
FastAPI
├── Project management
├── File upload and validation
├── Text preprocessing and chunking
├── Embedding and indexing
├── Retrieval
└── RAG answer generation
     │                 │
     ▼                 ▼
PostgreSQL          LLM providers
├── projects        ├── OpenRouter
├── assets          ├── Ollama
├── chunks          └── Cohere
└── pgvector collections
```

Each project uses a separate vector collection whose name is derived from the embedding dimension and project ID:

```text
collection_<embedding_size>_<project_id>
```

Example:

```text
collection_384_1003
```

---

## Repository layout

```text
mini-rag/
├── .github/
│   └── workflows/
│       └── deploy-main.yml            # production deployment workflow
├── docker/
│   ├── docker-compose.yml              # application and monitoring stack
│   ├── certbot/                        # local certificates and ACME files; ignored
│   ├── env/                            # runtime environment files
│   ├── minirag/
│   │   ├── Dockerfile
│   │   ├── entrypoint.sh               # runs migrations, then starts Uvicorn
│   │   └── alembic.ini
│   ├── nginx/
│   │   ├── default.conf                # HTTPS, static UI, auth, and API proxy
│   │   ├── auth/                       # local .htpasswd; ignored
│   │   └── html/
│   │       ├── index.html              # public chat interface
│   │       └── admin/
│   │           ├── index.html          # administration dashboard
│   │           ├── admin.css
│   │           └── admin.js
│   └── prometheus/
│       └── prometheus.yml
├── src/
│   ├── main.py                         # FastAPI application and dependency wiring
│   ├── requirements.txt
│   ├── controllers/
│   │   ├── DataController.py
│   │   ├── ProjectController.py
│   │   ├── ProcessController.py        # cleaning and recursive chunking
│   │   └── NLPController.py            # indexing, retrieval, answers, sources
│   ├── helpers/
│   │   └── config.py
│   ├── models/
│   │   ├── ProjectModel.py
│   │   ├── AssetModel.py
│   │   ├── ChunkModel.py
│   │   └── db_schemes/minirag/
│   │       ├── schemes/                # SQLAlchemy models
│   │       └── alembic/                # database migrations
│   ├── routes/
│   │   ├── base.py                     # health and public projects
│   │   ├── data.py                     # projects, uploads, and processing
│   │   ├── nlp.py                      # indexing, search, and answers
│   │   └── schemes/                    # request models
│   ├── stores/
│   │   ├── LLM/                        # generation and embedding abstractions
│   │   └── vectordb/                   # pgvector and Qdrant abstractions
│   ├── utils/
│   │   └── metrics.py
│   └── assets/
│       ├── files/                       # uploads grouped by project ID
│       └── databases/                   # local Qdrant storage when enabled
├── ARCHITECTURE.md
├── setup_guide.md
└── README.md
```

Runtime secrets, certificates, password files, uploaded data, and local backups must remain outside Git tracking.

---

## Quick start with Docker Compose

### 1. Configure environment files

```bash
cd docker/env

cp .env.example.postgres .env.postgres
cp .env.example.postgres-exporter .env.postgres-exporter
cp .env.example.grafana .env.grafana
cp .env.example.app .env.app
```

Edit the generated files and configure the PostgreSQL credentials, embedding provider, generation provider, model IDs, and API keys.

Never commit real environment files or API keys.

### 2. Prepare administration authentication

Create an htpasswd file in the ignored runtime directory:

```bash
mkdir -p docker/nginx/auth
htpasswd -c docker/nginx/auth/.htpasswd admin
chmod 644 docker/nginx/auth/.htpasswd
```

### 3. Start the stack

```bash
cd docker
docker compose config -q
docker compose up -d --build --remove-orphans
```

The FastAPI entrypoint runs:

```bash
alembic upgrade head
```

before starting Uvicorn, so committed migrations are applied during deployment.

### 4. Verify the deployment

```bash
docker compose ps
curl http://localhost/api/v1/
```

In the HTTPS production setup:

```bash
curl https://hakaa.publicvm.com/api/v1/
```

Main production URLs:

| Interface | URL |
|---|---|
| Public chat | `https://hakaa.publicvm.com/` |
| Administration | `https://hakaa.publicvm.com/admin/` |
| Health endpoint | `https://hakaa.publicvm.com/api/v1/` |

Prometheus, Grafana, PostgreSQL, Qdrant, Loki, and exporters remain internal to the Docker network unless explicitly proxied or accessed through a secure tunnel.

---

## API overview

Base path:

```text
/api/v1
```

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/` | Public | Application health and version |
| `GET` | `/projects` | Public | List projects that are public and ready |
| `GET` | `/data/projects` | Admin | List projects for administration |
| `POST` | `/data/projects` | Admin | Create a named project with an automatic ID |
| `POST` | `/data/upload/{project_id}` | Admin | Upload a TXT or PDF source |
| `POST` | `/data/process/{project_id}` | Admin | Clean and split uploaded source files |
| `POST` | `/nlp/index/push/{project_id}` | Admin | Generate embeddings and update the vector index |
| `GET` | `/nlp/index/info/{project_id}` | Admin | Return collection information and record count |
| `POST` | `/nlp/index/search/{project_id}` | API | Search the project's indexed chunks |
| `POST` | `/nlp/index/answer/{project_id}` | Public | Retrieve context and generate a grounded answer |

Project-update operations are also used by the administration dashboard to change a project's name, description, visibility, and status. Check the generated OpenAPI documentation for the exact method and path implemented by the current branch:

```text
/docs
```

---

## End-to-end API example

### 1. Create a project

```bash
curl -X POST "http://localhost/api/v1/data/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Islamic History",
    "project_description": "Selected historical sources",
    "is_public": false
  }'
```

Use the automatically generated `project_id` returned by the API in the following requests.

### 2. Upload a source

```bash
curl -X POST "http://localhost/api/v1/data/upload/<project_id>" \
  -F "file=@/path/to/history.pdf"
```

Save the returned `file_id` because the stored filename is generated by Hakaa.

### 3. Process the source

```bash
curl -X POST "http://localhost/api/v1/data/process/<project_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "<returned_file_id>",
    "chunk_size": 400,
    "overlap_size": 60,
    "do_reset": 0
  }'
```

### 4. Index the chunks

```bash
curl -X POST "http://localhost/api/v1/nlp/index/push/<project_id>" \
  -H "Content-Type: application/json" \
  -d '{"do_reset": 0}'
```

### 5. Search without generation

```bash
curl -X POST "http://localhost/api/v1/nlp/index/search/<project_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "من أسس المدينة؟",
    "limit": 5
  }'
```

### 6. Generate a grounded answer

```bash
curl -X POST "http://localhost/api/v1/nlp/index/answer/<project_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "من أسس المدينة ومتى؟",
    "limit": 5
  }'
```

Using `do_reset: 1` removes the project's existing chunks or vector collection before rebuilding. Use it only when intentionally replacing the current index. The administration interface currently uses `do_reset: 0` to protect existing data.

---

## Provider configuration

### Generation

| Provider | Backend value | Notes |
|---|---|---|
| OpenRouter | `OPENAI` | Set the OpenAI-compatible base URL to `https://openrouter.ai/api/v1` |
| Ollama | `OPENAI` | Use an OpenAI-compatible local endpoint such as `http://host.docker.internal:11434/v1/` |
| Cohere | `COHERE` | Requires a Cohere API key and generation model |

### Embeddings

| Provider | Backend value | Notes |
|---|---|---|
| Cohere | `COHERE` | The multilingual embedding models are suitable for Arabic and English sources |
| OpenAI-compatible | `OPENAI` | The configured embedding dimension must match the model output |

The production configuration currently uses multilingual embeddings with a vector size of `384`. Changing the embedding model or its dimension requires rebuilding affected vector collections.

---

## Vector database options

| Backend | Configuration value | Notes |
|---|---|---|
| pgvector | `PGVECTOR` | Primary backend; stored inside PostgreSQL |
| Qdrant | `QDRANT` | Alternative backend with its own Docker service and storage |

The pgvector provider creates an HNSW index when the collection reaches the configured indexing threshold.

---

## Prompt localization

RAG prompt templates are located in:

```text
src/stores/LLM/templates/locales/
```

Supported templates:

- Arabic: `ar`
- English: `en`

The prompt instructs the generation model to answer using only the retrieved sources and to respond in the language used by the question.

---

## Observability

Prometheus collects metrics from:

- FastAPI request middleware.
- Node Exporter.
- PostgreSQL Exporter.
- Prometheus itself.
- Qdrant when the optional backend is running.

Grafana provides dashboards for application, host, PostgreSQL, and vector-database monitoring. Loki collects service logs.

The services communicate through the internal `backend` Docker network. Only Nginx publishes ports `80` and `443` in the production configuration.

---

## HTTPS and certificate renewal

Production HTTPS uses Let's Encrypt certificates mounted into the Nginx container. Certbot renewal is executed by a root cron job twice daily, followed by an Nginx reload.

Certificate files and ACME runtime data live under `docker/certbot/` and must not be committed.

The Nginx configuration uses Docker's internal DNS resolver so FastAPI can be recreated without requiring an Nginx restart.

---

## Deployment workflow

Pushes to `main` trigger `.github/workflows/deploy-main.yml`.

The workflow:

1. Connects to the production server over SSH.
2. Updates the local `main` branch using a fast-forward-only pull.
3. Verifies required local certificate and authentication files.
4. Validates the Docker Compose configuration.
5. Builds and starts the services.
6. Validates and reloads Nginx.
7. Polls the HTTPS health endpoint.
8. Prints recent Nginx and FastAPI logs if deployment fails.

Deployment concurrency is restricted so that only one `main` deployment runs at a time.

---

## Release status

### Hakaa v1.0.0

The first stable release includes:

- Docker-based production deployment.
- HTTPS and automatic certificate renewal.
- Public historical chat interface.
- Protected bilingual administration dashboard.
- Project creation, naming, visibility, and status management.
- Automatic project IDs.
- TXT and PDF ingestion.
- Dense vector retrieval.
- Monitoring and deployment automation.

### Hakaa v2 — in development

Completed foundations:

- Improved Arabic text cleaning.
- Recursive and configurable chunking.
- Page-aware PDF processing.
- Metadata preservation through PostgreSQL and pgvector.
- Source references in the answer API and chat UI.

Planned retrieval work:

- Dense-search baseline evaluation.
- Arabic lexical retrieval.
- Hybrid dense and lexical retrieval.
- Reciprocal Rank Fusion.
- Reranking.
- Recall, MRR, nDCG, and latency comparison.

---

## Current limitations

- TXT files do not currently provide real page numbers.
- Existing collections must be reprocessed and reindexed to gain the new source metadata.
- OpenRouter free models may temporarily return HTTP `429` because of shared upstream rate limits.
- The process success signal still contains legacy vector-database wording even though processing writes chunks to PostgreSQL.
- Some legacy configuration names contain spelling mistakes and must not be renamed without updating the corresponding settings code and deployment files.
- The current production retrieval method is dense vector search; hybrid search and reranking are planned for Hakaa v2.

---

## Security notes

- Never commit API keys, database passwords, TLS private keys, or `.htpasswd` files.
- Rotate any credential that has been accidentally exposed.
- Keep `docker/env/`, `docker/certbot/`, and `docker/nginx/auth/` runtime secrets outside Git.
- Keep PostgreSQL, pgvector, Qdrant, Grafana, Prometheus, Loki, and exporters inaccessible from the public internet unless a protected access method is configured.
- The public project API returns only projects marked as public and ready.
- Administrative pages and ingestion operations are protected by Nginx Basic Authentication.

---

## Development roadmap

1. Establish a measurable dense-retrieval baseline.
2. Add Arabic lexical search.
3. Combine lexical and dense candidates using hybrid retrieval.
4. Apply Reciprocal Rank Fusion.
5. Add an optional reranking stage.
6. Evaluate relevance and latency against the baseline.
7. Improve source identity by preserving original filenames and richer document metadata.
8. Add background jobs and persisted ingestion progress for large books.
9. Add OCR support for scanned historical documents in a later release.

---

## License and attribution

Hakaa is built on the original mini-RAG project structure and extends it with historical-document workflows, project management, user interfaces, deployment, security, observability, and retrieval improvements.

When adding historical books, verify that their licenses or public-domain status permit processing and redistribution.
