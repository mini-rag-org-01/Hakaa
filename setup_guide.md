# Mini-RAG App — Full Setup Guide

## Prerequisites
- Windows 11/10 with WSL 2 installed
- Docker Desktop installed
- Miniconda installed (in WSL)
- Your project is at `D:\mini-rag-app` (accessible as `/mnt/d/mini-rag-app` in WSL)

---

## Step 1 — Start Docker Desktop (Windows)

1. Open **Docker Desktop** from the Start menu.
2. Wait until the bottom-left status shows **"Engine running"** (green icon in system tray).

> [!IMPORTANT]
> Do NOT proceed until Docker Desktop is fully running. This is required for all subsequent steps.

---

## Step 2 — Enable WSL 2 Integration in Docker Desktop

This allows the `docker` command to work inside your WSL/Ubuntu terminal.

1. In Docker Desktop, click the **gear icon ⚙️** (top-right) → **Settings**.
2. Go to **Resources** → **WSL Integration**.
3. Toggle ON: **"Enable integration with my default WSL distro"**.
4. Also toggle ON your specific distro (e.g., **Ubuntu**).
5. Click **"Apply & Restart"**.
6. Close and reopen your WSL terminal.

---

## Step 3 — Start MongoDB via Docker (from WSL terminal)

```bash
# Navigate to project root
cd /mnt/d/mini-rag-app

# Start MongoDB container in background
docker compose -f docker/docker-compose.yml up -d

# Verify it's running (you should see 'mongodb' listed)
docker ps
```

Expected output from `docker ps`:
```
CONTAINER ID   IMAGE             ...   PORTS                      NAMES
xxxxxxxxxxxx   mongo:7.0-jammy   ...   0.0.0.0:27017->27017/tcp   mongodb
```

> [!NOTE]
> Your `docker/.env` already has credentials set:
> - Username: `admin`
> - Password: `admin`
> These match what's in `src/.env` → `MONGODB_URL = "mongodb://admin:admin@localhost:27017"`

---

## Step 4 — Configure LLM Provider in `src/.env`

Your app currently points to **Ollama** (local LLM). You have two choices:

### Option A: Use OpenRouter (Recommended — no local setup needed)
Edit `src/.env` and make these changes:

```env
OPENAI_API_URL = "https://openrouter.ai/api/v1"                 # OPENROUTER
# OPENAI_API_URL = "http://localhost:11434/v1/"                  # OLLAMA

GENERATION_MODEL_ID = "openai/gpt-oss-120b:free"                # OPENROUTER
# GENERATION_MODEL_ID = "qwen2.5:3b"                             # OLLAMA
```

### Option B: Use Ollama (Local — requires Ollama installed on Windows)
1. Download and install Ollama from https://ollama.com
2. Open Ollama (it will run in the system tray).
3. Pull the model: open a terminal and run:
   ```bash
   ollama pull qwen2.5:3b
   ```
4. Keep `src/.env` as-is (already pointed to Ollama).

---

## Step 5 — Activate Conda Environment (WSL terminal)

```bash
conda activate mini-rag-app
```

If the environment doesn't exist yet, create it:
```bash
conda create -n mini-rag-app python=3.11 -y
conda activate mini-rag-app
pip install -r /mnt/d/mini-rag-app/src/requirements.txt
```

---

## Step 6 — Start the FastAPI Server (WSL terminal)

```bash
cd /mnt/d/mini-rag-app/src
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

---

## Step 7 — Verify Everything is Working

Open your browser and navigate to:
```
http://localhost:5000/docs
```
You should see the FastAPI Swagger UI with all your API endpoints.

---

## Summary — What Needs to Be Running

| Service | Where | How to Start |
|---|---|---|
| **Docker Desktop** | Windows | Start menu → Docker Desktop |
| **MongoDB** | Docker container | `docker compose -f docker/docker-compose.yml up -d` |
| **Ollama** (if using) | Windows | Start menu → Ollama |
| **FastAPI Server** | WSL terminal | `uvicorn main:app --reload --host 0.0.0.0 --port 5000` |

> [!TIP]
> Every time you restart your computer, you need to:
> 1. Start Docker Desktop
> 2. Start the MongoDB container (`docker compose up -d`)
> 3. Start Ollama (if using local LLM)
> 4. Run the FastAPI server

---

## Common Errors & Solutions

| Error | Cause | Fix |
|---|---|---|
| `ServerSelectionTimeoutError: localhost:27017 Connection refused` | MongoDB container not running | Run `docker compose -f docker/docker-compose.yml up -d` |
| `openai.APIConnectionError: Connection error` | Ollama not running OR wrong API URL | Start Ollama OR switch to OpenRouter in `.env` |
| `docker: command not found` in WSL | WSL integration not enabled | Follow Step 2 above |
| `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file` | Docker Desktop not running | Follow Step 1 above |
| `500 Internal Server Error` from Docker API | Docker Desktop in bad state | Restart Docker Desktop |
