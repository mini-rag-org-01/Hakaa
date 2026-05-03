# mini-rag-app

`mini-rag-app` is a FastAPI backend for a small retrieval-augmented generation workflow.

At a high level, the app does this:

1. Upload a file into a project
2. Save the file on disk and register it in MongoDB
3. Split the file into chunks and store those chunks in MongoDB
4. Embed the chunks with an LLM embedding provider
5. Store the embeddings in Qdrant
6. Search the Qdrant collection later by embedding a query

This README is updated to match the current repository layout and code paths.

For a folder-by-folder and file-by-file breakdown of the codebase, see `ARCHITECTURE.md`.

## Current stack

- Python API: FastAPI
- App server: Uvicorn
- Request/body validation: Pydantic
- Async MongoDB driver: Motor
- File I/O: `aiofiles`
- Document loading and chunking: LangChain + PyMuPDF
- Embedding / generation providers:
  - OpenAI-compatible provider
  - Cohere provider
- Vector database: Qdrant local embedded storage

## Repository layout

```text
mini-rag-app/
├─ docker/                 # Docker Compose for MongoDB
├─ src/
│  ├─ controllers/         # Business logic / service layer
│  ├─ helpers/             # App settings
│  ├─ models/              # MongoDB access layer
│  ├─ routes/              # FastAPI endpoints
│  ├─ stores/              # LLM and vector DB adapters
│  ├─ assets/
│  │  ├─ files/            # Uploaded files grouped by project id
│  │  └─ databases/        # Local Qdrant storage path
│  ├─ .env.example         # Application environment template
│  ├─ requirements.txt
│  └─ main.py
└─ README.md
```

## How the data flows

The current request lifecycle looks like this:

1. FastAPI receives an HTTP request in `src/routes/`
2. The route parses path params, body payloads, and dependencies
3. The route calls:
   - `src/controllers/` for business logic
   - `src/models/` for MongoDB work
4. `src/stores/` handles external systems:
   - embedding / generation providers
   - Qdrant vector storage
5. The route returns a JSON response

For this codebase, the practical architecture is:

`route -> controller/service -> model/repository -> database/provider -> response`

## Prerequisites

- Python 3.11 is the best match for the current environment used by the repo
- Conda or Miniconda
- Docker Desktop or Docker Engine if you want to run MongoDB with Compose

## Setup

### 1. Create and activate a virtual environment

Example with Conda:

```bash
conda create -n mini-rag-app python=3.11
conda activate mini-rag-app
```

### 2. Install Python dependencies

Run this from `src/`:

```bash
cd src
pip install -r requirements.txt
```

### 3. Configure MongoDB

This project uses MongoDB for:

- projects
- assets
- chunks

The repository already includes a Compose file for MongoDB in `docker/docker-compose.yml`.

Copy the Docker env template:

```bash
cd ../docker
cp .env.example .env
```

Example values:

```env
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=admin
```

Then start MongoDB:

```bash
docker compose up -d
```

If you run the command from somewhere else, point Docker Compose to the file explicitly:

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 4. Configure the application env

Copy the application env template:

```bash
cd ../src
cp .env.example .env
```

Then fill in the provider keys and model names you want to use.

Important:

- `GENERATION_BACKEND` supports:
  - `OPENAI`
  - `COHERE`
- `EMBEDDING_BACKEND` supports:
  - `OPENAI`
  - `COHERE`
- `VECTOR_DB_BACKEND` currently supports:
  - `QDRANT`

### 5. Run the API server

From `src/`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

Base URL:

```text
http://127.0.0.1:5000
```

## Startup lifecycle

At startup, `src/main.py` does the following:

1. Loads settings from `.env`
2. Connects to MongoDB
3. Creates the generation provider
4. Creates the embedding provider
5. Creates the vector DB provider
6. Connects the Qdrant local client
7. Creates a template parser using language settings

Shared app-level objects are stored on the FastAPI app instance and later accessed from routes through `request.app`, for example:

- `request.app.db_client`
- `request.app.generation_client`
- `request.app.embedding_client`
- `request.app.vectordb_client`

## API flow: end-to-end pipeline

The intended pipeline is:

1. `POST /api/v1/data/upload/{project_id}`
2. `POST /api/v1/data/process/{project_id}`
3. `POST /api/v1/nlp/index/push/{project_id}`
4. `POST /api/v1/nlp/index/search/{project_id}`

### Step 1: Upload a file

Endpoint:

```http
POST /api/v1/data/upload/{project_id}
```

Purpose:

- ensure the project exists in MongoDB
- validate the uploaded file
- write the file to disk under `src/assets/files/<project_id>/`
- create an asset record in MongoDB

Request:

- `multipart/form-data`
- field name must be exactly `file`

Example with `curl`:

```bash
curl -X POST "http://127.0.0.1:5000/api/v1/data/upload/1" \
  -F "file=@/absolute/path/to/wiki.txt"
```

Typical response:

```json
{
  "signal": "file_uploaded_success",
  "file_id": "randomkey_wiki.txt",
  "asset_id": "..."
}
```

What happens internally:

- route: `src/routes/data.py::upload_data`
- Mongo access:
  - `ProjectModel.create_instance()`
  - `ProjectModel.get_project_or_create_one()`
  - `AssetModel.create_instance()`
  - `AssetModel.create_asset()`
- business logic:
  - `DataController.validate_uploaded_file()`
  - `DataController.generate_unique_filepath()`
  - `ProjectController.get_project_path()`

### Step 2: Process file(s) into chunks

Endpoint:

```http
POST /api/v1/data/process/{project_id}
```

Purpose:

- load the uploaded asset records from MongoDB
- read the physical file from disk
- split the file into chunks
- store those chunks in MongoDB

Example request:

```json
{
  "file_id": "randomkey_wiki.txt",
  "chunk_size": 100,
  "overlap_size": 20,
  "do_reset": 1
}
```

Example `curl`:

```bash
curl -X POST "http://127.0.0.1:5000/api/v1/data/process/1" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\":\"randomkey_wiki.txt\",\"chunk_size\":100,\"overlap_size\":20,\"do_reset\":1}"
```

Current behavior:

- if `file_id` is provided, it processes one file
- if `file_id` is omitted, it tries to process all project files

What happens internally:

- route: `src/routes/data.py::process_endpoint`
- Mongo access:
  - `ProjectModel.get_project_or_create_one()`
  - `AssetModel.get_asset_record()` or `AssetModel.get_all_project_assets()`
  - `ChunkModel.delete_chunks_by_project_id()`
  - `ChunkModel.insert_many_chunks()`
- business logic:
  - `ProcessController.get_file_content()`
  - `ProcessController.process_file_content()`

Document loading:

- `.txt` -> `TextLoader`
- `.pdf` -> `PyMuPDFLoader`

Chunking:

- handled by `RecursiveCharacterTextSplitter`

Typical response:

```json
{
  "signal": "iinsert into vectordb success ",
  "inserted_chunks": 42,
  "processed_files": 1
}
```

Note:

That success signal name is misleading in the current code. This endpoint stores chunks in MongoDB; it does not index vectors yet.

### Step 3: Push chunks into Qdrant

Endpoint:

```http
POST /api/v1/nlp/index/push/{project_id}
```

Purpose:

- fetch project chunks from MongoDB
- generate embeddings for those chunks
- create a per-project Qdrant collection if needed
- upsert vectors into Qdrant

Example request:

```json
{
  "do_reset": 1
}
```

Example `curl`:

```bash
curl -X POST "http://127.0.0.1:5000/api/v1/nlp/index/push/1" \
  -H "Content-Type: application/json" \
  -d "{\"do_reset\":1}"
```

What happens internally:

- route: `src/routes/nlp.py::index_project`
- Mongo access:
  - `ProjectModel.get_project_or_create_one()`
  - `ChunkModel.get_poject_chunks()`
- business logic:
  - `NLPController.index_into_vector_db()`
- provider calls:
  - embedding provider: `embed_texts(...)`
  - vector DB provider: `create_collection(...)`
  - vector DB provider: `insert_many(...)`

Collection naming:

- Qdrant collection name is built as:

```text
collection_<project_id>
```

Batching:

The current code uses batched embedding in `NLPController.index_into_vector_db()` so that one page of chunk texts is embedded in a single provider call. This helps reduce API calls, especially when using a trial Cohere key.

Typical response:

```json
{
  "signal": "iinsert into vectordb success ",
  "inseerted_item_count": 42
}
```

### Step 4: Inspect vector collection info

Endpoint:

```http
GET /api/v1/nlp/index/info/{project_id}
```

Purpose:

- read the Qdrant collection metadata for the project collection

Example:

```bash
curl "http://127.0.0.1:5000/api/v1/nlp/index/info/1"
```

Internal path:

- route: `src/routes/nlp.py::get_project_index_info`
- controller: `NLPController.get_vector_db_collection_info()`
- vector provider: `QdrantDBProvider.get_collection_info()`

Current caveat:

This route currently returns a raw Qdrant object inside `JSONResponse`. That object should be converted to a JSON-safe dict before returning it, for example with `model_dump()` or `dict()` depending on the installed Qdrant client version.

### Step 5: Search the vector index

Endpoint:

```http
POST /api/v1/nlp/index/search/{project_id}
```

Purpose:

- embed the query text
- search the project Qdrant collection
- return retrieved chunk candidates

Example request:

```json
{
  "text": "Who is Sherlock Holmes?",
  "limit": 5
}
```

Example `curl`:

```bash
curl -X POST "http://127.0.0.1:5000/api/v1/nlp/index/search/1" \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Who is Sherlock Holmes?\",\"limit\":5}"
```

Internal path:

- route: `src/routes/nlp.py::search_index`
- controller: `NLPController.search_vector_db_collection()`
- provider:
  - embedding provider -> query embedding
  - Qdrant provider -> `search_by_vector()`

Typical response:

```json
{
  "signal": "VECTORDB_SEARCH_SUCCESS",
  "RESULTS": [
    {
      "score": 0.92,
      "text": "..."
    }
  ]
}
```

## Storage model

This app uses three different storage layers.

### 1. Files on disk

Uploaded files are stored under:

```text
src/assets/files/<project_id>/
```

### 2. MongoDB

Current collections:

- `projects`
- `assets`
- `chunks`

### 3. Qdrant local embedded storage

Qdrant uses a local path built from:

- `VECTOR_DB_PATH`
- stored under `src/assets/databases/`

So if:

```env
VECTOR_DB_PATH=qdrant_db
```

then the local database directory becomes:

```text
src/assets/databases/qdrant_db
```

## Current environment variables

Use `src/.env.example` as the source of truth for app config.

Important groups:

### App

- `APP_NAME`
- `APP_VERSION`

### File processing

- `FILE_ALLOWED_TYPES`
- `FILE_MAX_SIZE`
- `FILE_DEFAULT_CHUNK_SIZE`

### MongoDB

- `MONGODB_URL`
- `MONGODB_DATABASE`

### LLM / embedding

- `GENERATION_BACKEND`
- `EMBEDDING_BACKEND`
- `OPENAI_API_KEY`
- `OPENAI_API_URL`
- `COHERE_API_KEY`
- `GENERATION_MODEL_ID`
- `EMBEDDING_MODEL_ID`
- `EMBEDDING_MODEL_SIZE`
- `INPUT_DEFAULT_MAX_CHARACTERS`
- `GENERATION_DEFAULT_MAX_TOKENS`
- `GENERATION_DEFAULT_TEMPRATURE`

### Vector DB

- `VECTOR_DB_BACKEND`
- `VECTOR_DB_PATH`
- `VECTOR_DB_DISTANCE_METHOD`

### Template language

- `PRIMARY_LANG`
- `DEFAULT_LANG`

## Known caveats in the current code

These are worth knowing while working with the latest repository state:

1. `GET /api/v1/nlp/index/info/{project_id}` needs response serialization cleanup for the Qdrant `CollectionInfo` object.
2. `src/models/db_schemes/project.py` currently defines `get_indexes()` twice.
3. `src/routes/data.py` uses a success signal name for `/process` that suggests vector insertion even though the endpoint is only chunking into MongoDB.
4. Some names still contain typos, for example:
   - `get_poject_chunks`
   - `inseerted_item_count`
   - `GENERATION_DEFAULT_TEMPRATURE`
5. Trial Cohere keys can still hit rate limits on large indexing jobs, even with batching.

## Recommended request sequence for manual testing

1. Health / welcome:

```bash
curl "http://127.0.0.1:5000/api/v1/"
```

2. Upload:

```bash
curl -X POST "http://127.0.0.1:5000/api/v1/data/upload/1" \
  -F "file=@/absolute/path/to/wiki.txt"
```

3. Process:

```bash
curl -X POST "http://127.0.0.1:5000/api/v1/data/process/1" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\":\"<returned file_id>\",\"chunk_size\":1000,\"overlap_size\":50,\"do_reset\":1}"
```

4. Index push:

```bash
curl -X POST "http://127.0.0.1:5000/api/v1/nlp/index/push/1" \
  -H "Content-Type: application/json" \
  -d "{\"do_reset\":1}"
```

5. Search:

```bash
curl -X POST "http://127.0.0.1:5000/api/v1/nlp/index/search/1" \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"What is this file about?\",\"limit\":5}"
```

## Security note

Do not commit real provider keys into `src/.env`.

If real keys were previously stored in the repository or local screenshots/logs, rotate them before sharing the project.
