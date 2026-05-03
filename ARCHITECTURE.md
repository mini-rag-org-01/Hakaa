# Architecture Guide

This document explains the project architecture folder by folder and file by file, based on the current repository state.

It is meant to answer two questions:

1. Where does each piece of functionality live?
2. How do the files work together during a request?

## 1. Architecture in one view

The project follows this practical flow:

`FastAPI route -> controller/service -> model/repository -> storage/provider -> JSON response`

The code is not strict textbook MVC. It is closer to:

- `routes/` = HTTP entry points
- `controllers/` = business logic / service layer
- `models/` = MongoDB access layer
- `models/db_schemes/` = data schemas
- `stores/` = adapters for LLMs, templates, and vector DB

## 2. Top-level folders

### `docker/`

Purpose:

- local infrastructure for MongoDB

Files:

- `docker-compose.yml`
  - starts MongoDB
  - maps port `27017`
  - mounts persistent `mongodata`
- `.env.example`
  - template for Docker Mongo credentials
- `.env`
  - local Docker credentials for Mongo startup
- `mongodb/`
  - currently just a support folder for Docker-related content

### `src/`

Purpose:

- the actual application source

Important files:

- `.env`
  - local runtime configuration
  - should stay private
- `.env.example`
  - safe template for required app config
- `requirements.txt`
  - Python dependencies
- `main.py`
  - FastAPI app entry point

### `datasets/`

Purpose:

- sample or external data used during development

This folder is not part of the main runtime request path.

### `.vscode/`

Purpose:

- local editor/debug settings

These files are for developer tooling, not application logic.

## 3. Runtime data folders inside `src/`

### `src/assets/files/`

Purpose:

- physical uploaded files

Structure:

- files are grouped by `project_id`
- for example:
  - `src/assets/files/1/...`
  - `src/assets/files/3/...`

This is where `POST /api/v1/data/upload/{project_id}` writes uploaded files.

### `src/assets/databases/`

Purpose:

- local embedded vector DB storage

Current usage:

- Qdrant writes local files here through `QdrantClient(path=...)`

Example:

- `src/assets/databases/qdrant_db/`

## 4. Entry point

### `src/main.py`

Purpose:

- creates the FastAPI app
- wires shared dependencies at startup
- registers routers

What it does:

1. loads settings with `get_settings()`
2. connects to MongoDB
3. builds LLM provider clients
4. builds vector DB client
5. builds template parser
6. stores these objects on `app`
7. includes all route modules

Key shared objects attached to `app`:

- `app.db_client`
- `app.generation_client`
- `app.embedding_client`
- `app.vectordb_client`
- `app.template_parser`

Why it matters:

- routes later access these objects through `request.app`

## 5. `helpers/`

Purpose:

- configuration and small support utilities

### `src/helpers/config.py`

Purpose:

- defines the `Settings` class
- loads environment variables from `.env`

Key role:

- this is the central source of application configuration

Used by:

- `main.py`
- controllers
- route dependencies

### `src/helpers/__init__.py`

Purpose:

- currently empty
- marks the folder as a Python package

## 6. `routes/`

Purpose:

- define HTTP endpoints
- parse request input
- orchestrate calls into models and controllers
- return HTTP responses

### `src/routes/base.py`

Purpose:

- very small health/welcome API

Main endpoint:

- `GET /api/v1/`

Behavior:

- reads `APP_NAME` and `APP_VERSION` from settings
- returns them as JSON

### `src/routes/data.py`

Purpose:

- file upload and chunking endpoints

Main endpoints:

- `POST /api/v1/data/upload/{project_id}`
- `POST /api/v1/data/process/{project_id}`

Responsibilities:

- create or load projects
- validate uploaded files
- save files on disk
- create asset records in MongoDB
- load files back from disk
- split them into chunks
- insert chunk records into MongoDB

This file is one of the main orchestration layers in the app.

### `src/routes/nlp.py`

Purpose:

- vector indexing and search endpoints

Main endpoints:

- `POST /api/v1/nlp/index/push/{project_id}`
- `GET /api/v1/nlp/index/info/{project_id}`
- `POST /api/v1/nlp/index/search/{project_id}`

Responsibilities:

- load project chunks from MongoDB
- call the embedding provider
- push embeddings into Qdrant
- read Qdrant collection info
- search vector collections

### `src/routes/__init__.py`

Purpose:

- currently empty
- package marker for route modules

## 7. `routes/schemes/`

Purpose:

- request-body schemas for FastAPI routes

These are Pydantic models used for validation before route logic runs.

### `src/routes/schemes/data.py`

Contains:

- `ProcessRequest`

Used by:

- `POST /api/v1/data/process/{project_id}`

Fields:

- `file_id`
- `chunk_size`
- `overlap_size`
- `do_reset`

### `src/routes/schemes/nlp.py`

Contains:

- `PushRequest`
- `SearchRequest`

Used by:

- `POST /api/v1/nlp/index/push/{project_id}`
- `POST /api/v1/nlp/index/search/{project_id}`

### `src/routes/schemes/__init__.py`

Purpose:

- currently empty
- package marker

## 8. `controllers/`

Purpose:

- business logic and application-level services

These files should be read as the service layer of the project.

### `src/controllers/BaseController.py`

Purpose:

- shared controller helpers

Provides:

- access to settings
- base paths
- random string generation
- local database path builder

Used by:

- most other controllers
- vector DB provider factory

### `src/controllers/ProjectController.py`

Purpose:

- filesystem-level project folder management

Main method:

- `get_project_path(project_id)`

Behavior:

- resolves `src/assets/files/<project_id>/`
- creates the folder if it does not exist

### `src/controllers/DataController.py`

Purpose:

- upload-related logic

Main responsibilities:

- validate file type and size
- sanitize filenames
- generate unique stored file names

Key methods:

- `validate_uploaded_file()`
- `generate_unique_filepath()`
- `get_clean_file_name()`

### `src/controllers/ProcessController.py`

Purpose:

- read stored files and split them into chunks

Main responsibilities:

- detect file extension
- choose a loader (`TextLoader`, `PyMuPDFLoader`)
- load file content
- split content into chunk documents

Key methods:

- `get_file_loader()`
- `get_file_content()`
- `process_file_content()`

### `src/controllers/NLPController.py`

Purpose:

- handle vector indexing and retrieval logic

Main responsibilities:

- build project collection names
- embed chunk text
- create Qdrant collections
- insert vectors into Qdrant
- search Qdrant by embedded query

Key methods:

- `create_collection_name()`
- `index_into_vector_db()`
- `get_vector_db_collection_info()`
- `search_vector_db_collection()`

This controller is the main RAG-specific service layer.

### `src/controllers/__init__.py`

Purpose:

- re-exports controller classes for cleaner imports

## 9. `models/`

Purpose:

- MongoDB data access layer

These files encapsulate collection access and database operations.

### `src/models/BaseDataModel.py`

Purpose:

- shared base class for Mongo-related model classes

Provides:

- `db_client`
- settings access

### `src/models/ProjectModel.py`

Purpose:

- MongoDB access for project records

Main responsibilities:

- initialize the `projects` collection
- create indexes
- insert projects
- fetch existing project by `project_id`

Key methods:

- `create_instance()`
- `init_collection()`
- `create_project()`
- `get_project_or_create_one()`
- `get_all_projects()`

### `src/models/AssetModel.py`

Purpose:

- MongoDB access for uploaded file metadata

Main responsibilities:

- initialize the `assets` collection
- create indexes
- insert asset records
- fetch one asset by project and name
- fetch all assets for a project

Key methods:

- `create_asset()`
- `get_asset_record()`
- `get_all_project_assets()`

### `src/models/ChunkModel.py`

Purpose:

- MongoDB access for chunk records

Main responsibilities:

- initialize the `chunks` collection
- insert chunks one by one or in bulk
- delete chunks by project
- paginate chunks by project

Key methods:

- `create_chunk()`
- `insert_many_chunks()`
- `delete_chunks_by_project_id()`
- `get_poject_chunks()`

### `src/models/__init__.py`

Purpose:

- re-exports common enums used across the app

Current exports:

- `ResponseSignal`
- `ProcessingEnum`

## 10. `models/db_schemes/`

Purpose:

- Pydantic schemas for internal application data

These are not Mongo repositories. They are typed data models used by the repository layer and controllers.

### `src/models/db_schemes/project.py`

Purpose:

- schema for a project document

Fields:

- `id` mapped to Mongo `_id`
- `project_id`

Other responsibilities:

- validates that `project_id` is alphanumeric
- defines index metadata

### `src/models/db_schemes/asset.py`

Purpose:

- schema for an asset document

Fields:

- `id`
- `asset_project_id`
- `asset_type`
- `asset_name`
- `asset_size`
- `asset_config`
- `asset_pushed_at`

Also defines Mongo index metadata.

### `src/models/db_schemes/data_chunk.py`

Purpose:

- schema for a chunk document

Fields:

- `_id`
- `chunk_text`
- `chunk_metadata`
- `chunk_order`
- `chunk_project_id`
- `chunk_asset_id`

Also defines index metadata.

### `src/models/db_schemes/retrieved_document.py`

Purpose:

- normalized shape for search results returned from the vector DB layer

Fields:

- `score`
- `text`

### `src/models/db_schemes/__init__.py`

Purpose:

- re-exports the schema classes

## 11. `models/enums/`

Purpose:

- central enum definitions used across routes, controllers, and models

### `src/models/enums/ResponseEnums.py`

Purpose:

- defines application response signals

Examples:

- `FILE_UPLOADED_SUCCESS`
- `PROCESSING_FAILED`
- `INSERT_INTO_VECTORDB_SUCCESS`
- `VECTORDB_SEARCH_SUCCESS`

### `src/models/enums/ProcessingEnums.py`

Purpose:

- defines supported file extensions

Current values:

- `.txt`
- `pdf`

### `src/models/enums/AssetTypeEnum.py`

Purpose:

- defines asset categories

Current value:

- `FILE`

### `src/models/enums/DataBaseEnum.py`

Purpose:

- central names for Mongo collections

Current values:

- `projects`
- `chunks`
- `assets`

### `src/models/enums/__init__.py`

Purpose:

- currently empty
- package marker

## 12. `stores/`

Purpose:

- adapters for external systems and provider abstractions

This folder hides provider-specific logic from the route/controller layers.

### `src/stores/.env`

Purpose:

- local file inside the stores area

Current note:

- it is not part of the core application flow
- it should not contain secrets that are meant for commit

## 13. `stores/LLM/`

Purpose:

- LLM and embedding provider abstraction layer

### `src/stores/LLM/LLMEnums.py`

Purpose:

- enums/constants for provider selection and provider-specific values

Contains:

- `LLMEnums`
- `OpenAIEnums`
- `CohereEnums`
- `DocumentTypeEnum`

Used by:

- provider factory
- provider implementations
- `NLPController`

### `src/stores/LLM/LLMInterface.py`

Purpose:

- abstract base interface for provider implementations

Defines the required methods:

- `set_generation_model()`
- `set_embedding_model()`
- `generate_text()`
- `embed_text()`
- `embed_texts()`
- `construct_prompt()`

### `src/stores/LLM/LLMProviderFActory.py`

Purpose:

- factory that builds either the OpenAI provider or the Cohere provider from settings

Used at startup in `main.py`.

### `src/stores/LLM/__init__.py`

Purpose:

- package marker

## 14. `stores/LLM/providers/`

Purpose:

- concrete provider implementations

### `src/stores/LLM/providers/OpenAIProvider.py`

Purpose:

- OpenAI-compatible provider for:
  - generation
  - embeddings

Responsibilities:

- hold API credentials and model ids
- generate completions
- generate embeddings
- expose batched embedding helper

### `src/stores/LLM/providers/CoHereProvider.py`

Purpose:

- Cohere provider for:
  - generation
  - embeddings

Responsibilities:

- hold API credentials and model ids
- process/truncate text
- generate Cohere chat outputs
- generate single and batched embeddings

This file has been the source of several integration fixes around input type handling, attribute naming, and batched embeddings.

### `src/stores/LLM/providers/__init__.py`

Purpose:

- re-exports provider classes for the factory

## 15. `stores/LLM/templates/`

Purpose:

- prompt template loading and localization

### `src/stores/LLM/templates/template_parser.py`

Purpose:

- load localized template modules dynamically
- return formatted template content by group/key

Main concept:

- given a language and a group name, it imports the appropriate locale file dynamically

### `src/stores/LLM/templates/__init__.py`

Purpose:

- package marker

### `src/stores/LLM/templates/locales/`

Purpose:

- language-specific prompt definitions

#### `src/stores/LLM/templates/locales/en/rag.py`

Purpose:

- English RAG prompt templates

Contains:

- `system_prompt`
- `document_prompt`
- `footer_template`

#### `src/stores/LLM/templates/locales/ar/rag.py`

Purpose:

- Arabic RAG prompt templates

Contains:

- Arabic equivalents of the same RAG prompt sections

#### `__init__.py` files in locale folders

Purpose:

- package markers for dynamic imports

## 16. `stores/vectordb/`

Purpose:

- vector database abstraction layer

### `src/stores/vectordb/VectorDBEnums.py`

Purpose:

- defines supported vector DB providers and distance methods

Current values:

- provider: `QDRANT`
- distance methods:
  - `cosine`
  - `dot`

### `src/stores/vectordb/VectorDBInterface.py`

Purpose:

- abstract interface for vector DB providers

Defines required operations such as:

- connect
- create collection
- insert points
- search by vector

### `src/stores/vectordb/VectorDBProviderFactory.py`

Purpose:

- creates the configured vector DB provider

Current behavior:

- builds a `QdrantDBProvider`
- computes the local data path using `BaseController.get_database_path()`

### `src/stores/vectordb/__init__.py`

Purpose:

- package marker

## 17. `stores/vectordb/providers/`

Purpose:

- concrete vector DB implementation(s)

### `src/stores/vectordb/providers/QdrantDBProvider.py`

Purpose:

- local embedded Qdrant adapter

Responsibilities:

- connect/disconnect local Qdrant
- create or delete collections
- insert one or many points
- search by vector
- map raw Qdrant results into `RetrievedDocument`

Current implementation detail:

- uses `upsert(points=[models.PointStruct(...)])`

### `src/stores/vectordb/providers/__init__.py`

Purpose:

- re-exports vector DB provider classes

## 18. Request path by major endpoint

### Upload path

`routes/data.py::upload_data`

1. load or create project with `ProjectModel`
2. validate file with `DataController`
3. generate file path with `ProjectController` + `DataController`
4. write file to `assets/files/`
5. insert asset metadata with `AssetModel`
6. return JSON

### Process path

`routes/data.py::process_endpoint`

1. load project with `ProjectModel`
2. load asset record(s) with `AssetModel`
3. load file content with `ProcessController`
4. chunk the text with `ProcessController`
5. insert chunks with `ChunkModel`
6. return JSON

### Index path

`routes/nlp.py::index_project`

1. load project with `ProjectModel`
2. load paged chunks with `ChunkModel`
3. batch embed texts with `NLPController` -> provider
4. create collection with `QdrantDBProvider`
5. upsert vectors with `QdrantDBProvider`
6. return JSON

### Search path

`routes/nlp.py::search_index`

1. load project with `ProjectModel`
2. embed query with provider
3. search Qdrant with `QdrantDBProvider`
4. normalize results in `NLPController`
5. return JSON

## 19. Generated/runtime files you usually do not document line by line

These exist in the repo right now but are runtime artifacts, not core source code:

- `src/assets/files/...`
- `src/assets/databases/...`
- `src/.env`
- `src/.vscode/...`

They are important operationally, but they are not where the application logic lives.

## 20. Current cleanup opportunities

Some architecture-level improvements you may want later:

1. Move more orchestration out of route files and into service objects
2. Standardize naming and fix typos such as:
   - `get_poject_chunks`
   - `inseerted_item_count`
   - `LLMProviderFActory`
3. Normalize success/error signal naming
4. Remove duplicate `get_indexes()` in `project.py`
5. Fix Qdrant collection info serialization in `routes/nlp.py`
6. Audit provider implementations for consistency between OpenAI and Cohere paths

## 21. Best reading order for the codebase

If you are trying to understand the project from scratch, read files in this order:

1. `src/main.py`
2. `src/routes/base.py`
3. `src/routes/data.py`
4. `src/routes/nlp.py`
5. `src/controllers/`
6. `src/models/`
7. `src/stores/LLM/`
8. `src/stores/vectordb/`

That order follows the same path a real request takes through the application.
