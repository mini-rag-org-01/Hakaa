APP_NAME="mini-RAG"
APP_VERSION="0.1"
OPEN_API_KEY=""

#============================== FILE CONFIG ==============================
FILE_ALLOWED_TYPES=["text/plain", "application/pdf"]
FILE_MAX_SIZE=15
FILE_DEFAULT_CHUNK_SIZE=512000
POSTGRES_USERNAME="postgres"
POSTGRES_PASSWORD="minirag7777"
POSTGRES_HOST="pgvector"
POSTGRES_PORT=5432
POSTGRES_MAIN_DATABASE="minirag"


#============================== LLM CONFIG ===============================
GENERATION_BACKEND="OPENAI"
EMBEDDING_BACKEND="COHERE"
OPENAI_API_KEY="sk-or-v1-"
OPENAI_API_URL_LITERAL=["https://openrouter.", "http:/"]
OPENAI_API_URL="https://openrouter."
COHERE_API_KEY="cohere_"
GENERATION_MODEL_ID_LITERAL = ["openai/gpt-oss-120b:free","qwen2.5:3b"]
GENERATION_MODEL_ID="openai/gpt-oss-20b:free"
EMBEDDING_MODEL_ID="embed-multilingual-light-v3.0"
EMBEDDING_MODEL_SIZE=384
INPUT_DEFAULT_MAX_CHARACTERS=384
GENERATION_DEFAULT_MAX_TOKENS=200
GENERATION_DEFAULT_TEMPRATURE=0.1

#============================== VECTOR DB CONFIG =========================
VECTOR_DB_BACKEND_LITERAL=["QDRANT", "PGVECTOR"]
VECTOR_DB_BACKEND="PGVECTOR"
VECTOR_DB_PATH="qdrant_db"
VECTOR_DB_DISTANCE_METHOD="cosine"
VECTOR_DB_INDEX_THRESHOLD = 100

#============================== TEMPLATE CONFIG ==========================
DEFAULT_LANG="en"
PRIMARY_LANG="en"
