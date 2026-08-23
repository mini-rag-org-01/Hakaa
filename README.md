# Hakaa — حكّاء

**Hakaa** is an Arabic-first Retrieval-Augmented Generation (RAG) application for exploring historical books and documents through natural-language conversations.

The project started as a lightweight **Mini-RAG** implementation and was gradually extended into a deployable historical RAG system with:

- Project-based document management.
- PDF/TXT ingestion.
- Semantic and lexical retrieval.
- Hybrid Search using Reciprocal Rank Fusion (RRF).
- Source metadata preservation.
- Public and administration interfaces.
- Dockerized deployment.
- Monitoring and CI/CD-oriented production setup.

The current version is **Hakaa V2**.

Production:

## Live Demo

[Hakaa — حكّاء](https://hakaa.publicvm.com)

---

## Project idea

Hakaa was originally built as a simple Mini-RAG system.

The first version followed the traditional RAG pipeline:

```text
Document
   ↓
Text extraction
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Database
   ↓
Semantic Search
   ↓
LLM
   ↓
Answer
```

The purpose of V1 was mainly to understand and implement the complete RAG flow.

After that, the project was developed into **Hakaa**, a historical RAG system focused on Arabic historical sources.

The current public project is based on:

```text
كتاب الكامل في التاريخ
```

The long-term vision is to expand Hakaa into a digital historical source platform that can contain multiple Arabic historical books and help users search, compare, and trace historical information back to its original source.

---

# Main Features

- Arabic-first historical RAG system.
- Public chat interface.
- Protected administration dashboard.
- Named projects with automatically generated IDs.
- Upload support for `.txt`.
- PDF page metadata preservation.
- Configurable chunk size and chunk overlap.
- Recursive Arabic-aware text chunking.
- Semantic Vector Search using pgvector.
- PostgreSQL Full-Text Search.
- GIN Index for lexical search.
- Hybrid Search combining Semantic and Lexical retrieval.
- Reciprocal Rank Fusion (RRF).
- Parallel execution of both retrieval pipelines using `asyncio`.
- Project-specific vector collections.
- Nemotron embeddings.
- PostgreSQL + pgvector as the main data and vector layer.
- Optional Qdrant support.
- Source filename and chunk metadata.
- Docker Compose deployment.
- Nginx reverse proxy.
- HTTPS using Let's Encrypt.
- Basic Authentication for administration routes.
- Prometheus metrics.
- Grafana monitoring.
- Loki service.
- PostgreSQL and Node exporters.
- Alembic migrations.
- Deployment workflow prepared for GitHub Actions.

---

# Hakaa Versions

## V1 — Mini-RAG

The first version used a basic dense retrieval pipeline.

```text
Question
   ↓
Embedding
   ↓
Vector Search
   ↓
Top-K Chunks
   ↓
LLM
   ↓
Answer
```

The focus of V1 was understanding:

- RAG basics.
- Embeddings.
- Chunking.
- Vector databases.
- LLM prompting.
- FastAPI.
- Docker.
- Project architecture.
- Production deployment.

---

## V2 — Hakaa

V2 improves retrieval quality by introducing **Hybrid Search**.

Instead of depending only on Semantic Search, Hakaa now combines:

```text
Semantic Search
+
Lexical Search
+
RRF
```

The main V2 retrieval architecture is:

```text
                    User Question
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       Semantic Search        Lexical Search
      pgvector + HNSW        PostgreSQL FTS
              │                 + GIN Index
              │                     │
              └──────────┬──────────┘
                         ▼
                         RRF
                         │
                         ▼
                    Final Top-K
                         │
                         ▼
                       LLM
                         │
                         ▼
               Answer + Sources
```

---

## V3 — Next Version

The next version of Hakaa will focus on two main improvements:

### 1. OCR

Add OCR support for scanned historical PDF books.

Currently Hakaa works best with:

- TXT files.
- PDFs containing extractable text.

Many historical books are available only as scanned pages, so V3 will introduce OCR to convert page images into searchable Arabic text.

Target flow:

```text
Scanned PDF
    ↓
Page Images
    ↓
Arabic OCR
    ↓
Extracted Text
    ↓
Chunking
    ↓
Embeddings
    ↓
Hybrid Search
```

### 2. Evaluation

The second goal of V3 is to evaluate the retrieval system properly.

Instead of depending only on manual testing, Hakaa will use a historical question-answer evaluation set to compare:

```text
Semantic Search
vs
Lexical Search
vs
Hybrid Search + RRF
```

Possible evaluation metrics include:

- Hit Rate@K
- Recall@K
- MRR
- Retrieval latency

The goal is to measure whether the correct historical chunk appears in the retrieved results and to evaluate whether Hybrid Search actually improves retrieval quality.

---

# Application Interfaces

Hakaa provides two interfaces.

---

## Public Chat

Available at:

```text
/
```

The public interface allows the user to:

- Select a public historical project.
- Ask a question in Arabic or English.
- Receive an answer based on the indexed project sources.
- View the retrieved source references returned by the backend.

The public chat sends questions to:

```text
POST /api/v1/nlp/index/answer/{project_id}
```

Example request:

```json
{
  "text": "من بنى بغداد؟",
  "limit": 5
}
```

---

## Administration Dashboard

Available at:

```text
/admin/
```

The administration dashboard is protected with Nginx Basic Authentication.

It allows the administrator to:

- Create projects.
- Edit project name and description.
- Change project status.
- Make a project public or private.
- Upload TXT and PDF files.
- Configure chunk size.
- Configure chunk overlap.
- Process uploaded documents.
- Generate embeddings.
- Build the search indexes.
- View indexed record counts.
- Reset and rebuild project chunks/indexes when required.

Project statuses include:

```text
draft
processing
ready
failed
```

---

# Project-Based Architecture

Hakaa is designed around projects.

Each project represents a separate historical knowledge collection.

Example:

```text
Hakaa
│
├── Project 1001
│   └── الكامل في التاريخ
│
├── Project 1002
│   └── تاريخ الطبري
│
└── Project 1003
    └── تاريخ بغداد
```

Each project contains:

- Project ID.
- Project name.
- Description.
- Status.
- Public/private flag.
- Uploaded assets.
- Processed chunks.
- Vector collection.

The vector collection naming convention is:

```text
collection_<embedding_size>_<project_id>
```

Example:

```text
collection_1024_1003
```

---

# Document Processing

Hakaa currently supports:

```text
.txt
.pdf
```

The processing pipeline is:

```text
Upload File
    ↓
Validate File
    ↓
Store File
    ↓
Load Text
    ↓
Clean Text
    ↓
Split into Chunks
    ↓
Store Chunks in PostgreSQL
    ↓
Generate Embeddings
    ↓
Store Vectors
    ↓
Build Indexes
```

---

# Text Cleaning

The preprocessing layer performs basic cleanup before chunking.

It includes:

- Replacing non-breaking spaces.
- Removing invisible RTL/LTR characters.
- Normalizing repeated spaces.
- Normalizing unnecessary line breaks.
- Removing empty content.

This is useful for Arabic PDF text, which may contain invisible formatting characters after extraction.

---

# Chunking

Hakaa uses:

```text
RecursiveCharacterTextSplitter
```

The splitter tries to preserve meaningful Arabic text boundaries.

Current separator priority:

```text
Paragraph break
Line break
Arabic question mark ؟
Full stop .
Arabic comma ،
Space
Character fallback
```

Default processing values:

```text
Chunk Size: 400
Chunk Overlap: 60
```

Both values can be changed from the administration dashboard.

The overlap must always be smaller than the chunk size.

---

# Metadata

Hakaa keeps metadata for each processed chunk.

Important fields include:

```text
file_id
page_number
page_chunk_index
chunk_id
chunk_order
project_id
```

This metadata is important because the final goal is not only to retrieve text, but also to connect each answer back to its historical source.

---

# Embeddings

Hakaa separates the embedding layer from the rest of the application using provider abstractions.

Available provider architecture includes:

```text
OpenAI-compatible providers
Cohere
Nemotron
```

The current Hakaa setup uses a Nemotron embedding provider.

The configured embedding size is:

```text
1024 dimensions
```

---

# Why 1024 Dimensions?

The currently used Nemotron model returns a native embedding vector of:

```text
2048 dimensions
```

Hakaa uses PostgreSQL with pgvector and an HNSW index.

For the standard pgvector `vector` type, HNSW supports vectors up to:

```text
2000 dimensions
```

Therefore:

```text
2048 > 2000
```

so the native 2048-dimensional vector cannot be indexed directly with the current standard HNSW setup.

The current implementation therefore:

```text
2048D Nemotron Vector
        ↓
Take the first 1024 dimensions
        ↓
L2 Normalization
        ↓
Store vector(1024)
```

This is currently an application-level solution.

One of the goals of V3 evaluation is to measure the effect of this decision on retrieval quality instead of assuming that it is optimal.

---

# Vector Search

Hakaa uses pgvector as the primary vector database.

The semantic retrieval layer uses:

```text
Cosine Similarity
+
HNSW Index
```

The query embedding is compared against stored chunk embeddings.

Conceptually:

```text
Question
    ↓
Embedding
    ↓
pgvector
    ↓
Cosine Similarity
    ↓
Semantic Results
```

---

# HNSW

Hakaa creates an HNSW index for vector retrieval.

Conceptually:

```sql
CREATE INDEX ...
USING hnsw (vector vector_cosine_ops);
```

The index is created once the collection reaches the configured threshold.

Current default threshold:

```text
100 records
```

For very small collections, exact vector search is sufficient and an approximate index is not immediately required.

---

# Lexical Search

Hakaa V2 adds lexical retrieval using PostgreSQL Full-Text Search.

This search focuses on the exact words and terms appearing in the question.

This is especially useful in historical text for:

- Person names.
- Place names.
- Historical terminology.
- Rare names.
- Exact expressions.

The lexical layer uses:

```text
PostgreSQL Full-Text Search
+
GIN Index
```

---

# GIN Index

Hakaa creates a PostgreSQL GIN index over the chunk text.

Conceptually:

```sql
CREATE INDEX ...
USING GIN (
    to_tsvector(
        'simple',
        text
    )
);
```

The lexical search uses PostgreSQL functions such as:

```text
to_tsvector
to_tsquery
ts_rank_cd
```

---

# Hybrid Search

Hakaa combines Semantic Search and Lexical Search.

```text
                 Query
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
   Semantic Search     Lexical Search
          │                 │
          └────────┬────────┘
                   ▼
                  RRF
                   │
                   ▼
              Final Results
```

The two retrieval systems solve different problems.

Semantic Search is good at:

```text
Meaning
Context
Similar expressions
```

Lexical Search is good at:

```text
Exact words
Names
Specific historical terms
```

Combining both gives Hakaa more than one retrieval signal.

---

# Parallel Search

Hakaa runs Semantic Search and Lexical Search in parallel using:

```python
asyncio.gather(...)
```

Instead of:

```text
Semantic
    ↓
wait
    ↓
Lexical
```

the system runs:

```text
       ┌── Semantic
Query ─┤
       └── Lexical

       ↓
      RRF
```

This reduces unnecessary retrieval latency.

---

# Reciprocal Rank Fusion — RRF

The results returned by Semantic Search and Lexical Search cannot simply be combined using their raw scores.

For example:

```text
Semantic Score = cosine similarity
Lexical Score  = ts_rank_cd
```

These values come from different scoring systems.

Hakaa therefore uses **Reciprocal Rank Fusion (RRF)**.

RRF combines the **ranking position** of each chunk instead of directly comparing the original scores.

The formula is:

```text
RRF Score = Σ 1 / (k + rank)
```

Hakaa currently uses:

```text
k = 60
```

---

## Simple RRF Example

Semantic Search:

```text
1. Chunk A
2. Chunk B
3. Chunk C
```

Lexical Search:

```text
1. Chunk D
2. Chunk A
3. Chunk C
```

Chunk A appears in both lists.

Its RRF score becomes approximately:

```text
1 / (60 + 1)
+
1 / (60 + 2)
```

So Chunk A receives support from both retrieval systems.

The final ranking therefore rewards chunks that perform well across both Semantic and Lexical retrieval.

A simple way to describe Hakaa's retrieval is:

```text
Semantic Search → Does the meaning match?
Lexical Search  → Do the important words match?
RRF             → How should both rankings be combined?
```

---

# Candidate Retrieval

Hakaa does not retrieve only the final number of chunks before fusion.

If the user requests:

```text
limit = 5
```

the system first retrieves a larger candidate set from each search pipeline.

Current logic:

```text
candidate_limit = max(limit × 3, 10)
```

with a maximum of:

```text
100
```

For example:

```text
Requested final results = 5

Semantic candidates = 15
Lexical candidates  = 15

             ↓
            RRF
             ↓

Final results = 5
```

This gives RRF enough candidates to properly compare the rankings.

---

# Answer Generation

After retrieval:

```text
Top-K Chunks
    ↓
Prompt Builder
    ↓
Generation Model
    ↓
Final Answer
```

The Arabic prompt instructs the model to:

- Use the retrieved documents only.
- Avoid unsupported information.
- Answer directly.
- Avoid unnecessary introductions.
- Answer in the same language as the question.
- Use clear Arabic when the question is Arabic.
- Avoid showing internal reasoning.
- State when the available sources do not contain enough information.

The current generation temperature is configured as:

```text
0.0
```

to reduce unnecessary variation in answers.

---

# Sources

Hakaa preserves source metadata during document processing and retrieval.

The backend can associate retrieved chunks with:

```text
filename
page number
chunk ID
retrieval score
```

The public interface is designed to show source references alongside answers.

This is important for Hakaa because historical information should remain connected to the original source.

---

# Provider Architecture

Hakaa uses provider/factory abstractions so the application is not tightly coupled to one vendor.

---

## LLM Providers

Conceptually:

```text
LLMProviderFactory
│
├── OpenAI-compatible Provider
├── Cohere Provider
└── Nemotron Provider
```

Generation and embeddings can use different providers.

---

## Vector Database Providers

```text
VectorDBProviderFactory
│
├── PGVectorDBProvider
└── QdrantDBProvider
```

The primary production vector backend is:

```text
PGVECTOR
```

Qdrant remains available as an alternative backend.

The complete Hybrid Search implementation currently depends on PostgreSQL because the lexical layer is based on PostgreSQL Full-Text Search.

---

# Rate Limit Handling

Free AI APIs may return:

```text
HTTP 429
```

Hakaa handles embedding rate limits during indexing with retries and backoff.

The indexing pipeline processes chunks in batches.

Current values:

```text
Batch Size: 50 chunks
Batch Delay: 10 seconds
```

Retry handling is used when a provider returns a temporary rate-limit error.

This is especially important when using free OpenRouter or Cohere limits.

---

# Database

Hakaa uses:

```text
PostgreSQL
+
pgvector
```

Main relational entities:

```text
Projects
Assets
Chunks
```

Vector collections are created separately per project.

Database operations use:

```text
SQLAlchemy Async
+
asyncpg
```

Database migrations use:

```text
Alembic
```

The Docker application entrypoint runs:

```bash
alembic upgrade head
```

before starting the FastAPI server.

---

# Technology Stack

| Layer | Technology |
|---|---|
| Public UI | HTML, CSS, Vanilla JavaScript |
| Admin UI | HTML, CSS, Vanilla JavaScript |
| API | FastAPI |
| Server | Uvicorn |
| Database | PostgreSQL |
| Vector Extension | pgvector |
| Semantic Index | HNSW |
| Lexical Search | PostgreSQL Full-Text Search |
| Lexical Index | GIN |
| Async | asyncio |
| ORM | SQLAlchemy Async |
| PostgreSQL Driver | asyncpg |
| Migrations | Alembic |
| PDF Loader | PyMuPDF / LangChain |
| Text Splitter | RecursiveCharacterTextSplitter |
| Embeddings | Nemotron / Cohere / compatible providers |
| Generation | OpenAI-compatible APIs / OpenRouter / Ollama / Cohere |
| Reverse Proxy | Nginx |
| HTTPS | Let's Encrypt / Certbot |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Logs | Loki |
| Host Metrics | Node Exporter |
| DB Metrics | PostgreSQL Exporter |
| Containers | Docker Compose |
| Deployment | Git + GitHub Actions / SSH deployment workflow |

---

# System Architecture

```text
Browser
│
├── Public Chat /
│
└── Admin Dashboard /admin/
          │
          ▼
        Nginx
          │
          ├── HTTPS
          ├── Static UI
          ├── Basic Auth for Admin
          └── /api/ Reverse Proxy
                  │
                  ▼
                FastAPI
                  │
       ┌──────────┼──────────┐
       │          │          │
       ▼          ▼          ▼
   Projects    Processing    NLP
       │          │          │
       │          │          ├── Semantic Search
       │          │          ├── Lexical Search
       │          │          ├── RRF
       │          │          └── Answer Generation
       │          │
       └──────────┼───────────────┐
                  │               │
                  ▼               ▼
             PostgreSQL       AI Providers
              + pgvector
```

---

# Repository Structure

```text
mini-rag/
├── src/
│   ├── main.py
│   ├── controllers/
│   │   ├── DataController.py
│   │   ├── ProjectController.py
│   │   ├── ProcessController.py
│   │   └── NLPController.py
│   ├── models/
│   │   ├── ProjectModel.py
│   │   ├── AssetModel.py
│   │   └── ChunkModel.py
│   ├── routes/
│   │   ├── base.py
│   │   ├── data.py
│   │   └── nlp.py
│   ├── stores/
│   │   ├── LLM/
│   │   │   ├── providers/
│   │   │   └── templates/
│   │   └── vectordb/
│   │       └── providers/
│   └── utils/
│       └── metrics.py
│
├── docker/
│   ├── docker-compose.yml
│   ├── minirag/
│   ├── nginx/
│   ├── prometheus/
│   └── certbot/
│
├── ARCHITECTURE.md
├── setup_guide.md
└── README.md
```

---

# Docker Services

The Docker Compose stack contains the main application and monitoring services.

| Service | Purpose |
|---|---|
| FastAPI | RAG backend |
| Nginx | Public web server and reverse proxy |
| PostgreSQL + pgvector | Database and vector storage |
| Qdrant | Optional vector database |
| Prometheus | Metrics collection |
| Grafana | Monitoring dashboards |
| Loki | Logging infrastructure |
| Node Exporter | Server metrics |
| PostgreSQL Exporter | Database metrics |

The services communicate using the Docker internal network.

Only required public services should be exposed externally.

---

# Nginx

Nginx is responsible for:

- Serving the public frontend.
- Serving the administration frontend.
- Reverse proxying `/api/` to FastAPI.
- HTTP → HTTPS redirect.
- TLS termination.
- Basic Authentication for admin routes.

Main public ports:

```text
80
443
```

Production domain:

```text
hakaa.publicvm.com
```

---

# Monitoring

Hakaa includes a monitoring stack based on:

```text
Prometheus
Grafana
Node Exporter
PostgreSQL Exporter
Loki
```

FastAPI also exposes application metrics.

Examples include:

```text
HTTP request count
HTTP request latency
HTTP response status
```

This allows the project to monitor the application instead of only checking whether the server is running.

---

# Deployment

Hakaa is designed to run as a Dockerized production application.

Typical deployment flow:

```text
Code
 ↓
Git
 ↓
GitHub
 ↓
Deployment Workflow
 ↓
Server
 ↓
Docker Compose
 ↓
Hakaa
```

The project also includes a systemd service wrapper for Docker Compose lifecycle management.

This makes Hakaa different from a notebook-only RAG experiment: the project has an actual application architecture, deployment layer, and monitoring environment.

---

# Quick Start

## Environment Files

Create runtime environment files from the examples.

```bash
cd docker/env

cp .env.example.app .env.app
cp .env.example.postgres .env.postgres
cp .env.example.grafana .env.grafana
cp .env.example.postgres-exporter .env.postgres-exporter
```

Edit the created files with local credentials and provider configuration.

Never commit real secrets.

---

## Admin Authentication

```bash
mkdir -p docker/nginx/auth
htpasswd -c docker/nginx/auth/.htpasswd admin
chmod 644 docker/nginx/auth/.htpasswd
```

---

## Start the Project

```bash
cd docker

docker compose config -q

docker compose up -d --build --remove-orphans
```

---

## Check Status

```bash
docker compose ps
```

---

## View Logs

```bash
docker compose logs --tail=100 fastapi
docker compose logs --tail=100 nginx
docker compose logs --tail=100 pgvector
```

---

# API Overview

Base path:

```text
/api/v1
```

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health/version |
| GET | `/projects` | Public ready projects |
| GET | `/data/projects` | Admin project list |
| POST | `/data/projects` | Create project |
| POST | `/data/upload/{project_id}` | Upload source |
| POST | `/data/process/{project_id}` | Process and chunk source |
| POST | `/nlp/index/push/{project_id}` | Generate embeddings and index |
| GET | `/nlp/index/info/{project_id}` | Index information |
| POST | `/nlp/index/search/{project_id}` | Hybrid retrieval |
| POST | `/nlp/index/answer/{project_id}` | Retrieve and generate answer |

---

# Example Workflow

## 1. Create Project

```bash
curl -X POST \
  "http://localhost/api/v1/data/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Islamic History",
    "project_description": "Historical sources",
    "is_public": false
  }'
```

---

## 2. Upload File

```bash
curl -X POST \
  "http://localhost/api/v1/data/upload/<project_id>" \
  -F "file=@/path/to/history.pdf"
```

---

## 3. Process

```bash
curl -X POST \
  "http://localhost/api/v1/data/process/<project_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "<file_id>",
    "chunk_size": 400,
    "overlap_size": 60,
    "do_reset": 0
  }'
```

---

## 4. Index

```bash
curl -X POST \
  "http://localhost/api/v1/nlp/index/push/<project_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "do_reset": 0
  }'
```

---

## 5. Search

```bash
curl -X POST \
  "http://localhost/api/v1/nlp/index/search/<project_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "من بنى بغداد؟",
    "limit": 5
  }'
```

---

## 6. Ask Hakaa

```bash
curl -X POST \
  "http://localhost/api/v1/nlp/index/answer/<project_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "من بنى بغداد؟",
    "limit": 5
  }'
```

---

# Current Limitations

The current version still has several limitations.

### Historical Dataset

The public system currently contains a limited historical source set.

The goal is to gradually add more Arabic historical sources.

### Scanned PDFs

Image-only scanned PDFs are not yet supported.

This will be addressed in V3 using OCR.

### Retrieval Evaluation

Hybrid Search is implemented, but formal evaluation is still required.

V3 will compare Semantic, Lexical, and Hybrid retrieval using a controlled historical evaluation dataset.

### Free Model Rate Limits

Free API providers can return HTTP `429` during periods of high demand.

Hakaa uses retry/backoff logic for embedding indexing, but external provider availability remains outside the application's control.

### Embedding Dimension Decision

The current 1024-dimensional representation is an implementation decision made to remain compatible with the current HNSW setup.

Its retrieval impact still needs to be evaluated.

---

# V3 — OCR + Evaluation

The next Hakaa version has two clear goals.

```text
In V3, Hakaa will move from manual retrieval inspection to a measurable evaluation process. A historical evaluation dataset will be created with questions and known relevant chunks, then Semantic Search, Lexical Search, and Hybrid Search + RRF will be compared using Hit Rate@K, Recall@K, MRR, nDCG@K, and Retrieval Latency.

```

The purpose of V3 is not only to support more historical documents, but also to begin measuring the retrieval system objectively.

The main question becomes:

> Does Hakaa retrieve the correct historical evidence reliably?

---

# Long-Term Vision

Hakaa is currently a Historical RAG system.

The long-term goal is to build a digital Arabic historical source platform.

Instead of simply asking an LLM to answer from memory:

```text
Question
   ↓
Historical Sources
   ↓
Evidence Retrieval
   ↓
Source-Aware Answer
```

Future collections may allow users to:

- Search multiple historical books.
- Find references to the same event in different sources.
- Compare historical narrations.
- Connect people, places, dates, and events.
- Trace every retrieved statement back to its source.

The role of Hakaa should not be to decide historical truth automatically.

Its role is to make historical evidence easier to retrieve, inspect, and compare.

---

# Current Project Summary

```text
Mini-RAG
   ↓
FastAPI Architecture
   ↓
Projects + Documents
   ↓
Arabic Text Processing
   ↓
Embeddings
   ↓
pgvector + HNSW
   ↓
PostgreSQL FTS + GIN
   ↓
Hybrid Search
   ↓
RRF
   ↓
Grounded Answer
   ↓
Docker
   ↓
Nginx + HTTPS
   ↓
Monitoring
   ↓
Production Deployment
   ↓
V3: OCR + Evaluation
```

Hakaa started as a small RAG learning project.

It is now a deployed historical RAG system with a clear architecture, retrieval pipeline, administration workflow, monitoring stack, and a roadmap focused on supporting scanned historical sources and evaluating retrieval quality.
