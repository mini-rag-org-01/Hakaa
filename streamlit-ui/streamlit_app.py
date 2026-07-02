import json
import os
import time
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


# =========================
# Config
# =========================

APP_TITLE = "Mini RAG Studio"
DEFAULT_API_BASE_URL = os.getenv("MINIRAG_API_BASE_URL", "http://localhost:8000")

# Use a persistent mounted path in Docker, example:
# MINIRAG_REGISTRY_PATH=/app/data/uploads_registry.json
REGISTRY_PATH = Path(os.getenv("MINIRAG_REGISTRY_PATH", "uploads_registry.json"))

DEFAULT_CHUNK_SIZE = int(os.getenv("MINIRAG_DEFAULT_CHUNK_SIZE", "600"))
DEFAULT_OVERLAP_SIZE = int(os.getenv("MINIRAG_DEFAULT_OVERLAP_SIZE", "100"))
DEFAULT_RETRIEVAL_LIMIT = int(os.getenv("MINIRAG_DEFAULT_RETRIEVAL_LIMIT", "3"))
PROJECT_START_ID = int(os.getenv("MINIRAG_PROJECT_START_ID", "1"))

STATE_VERSION = 2


# =========================
# Page setup
# =========================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================
# CSS
# =========================

st.markdown(
    """
<style>
:root {
  --bg: #0b1020;
  --card: rgba(255,255,255,0.065);
  --card-2: rgba(255,255,255,0.095);
  --stroke: rgba(255,255,255,0.12);
  --text: #eef2ff;
  --muted: #9ca3af;
  --brand: #7c3aed;
  --brand-2: #06b6d4;
  --success: #22c55e;
  --danger: #ef4444;
  --warning: #f59e0b;
}

.stApp {
  background:
    radial-gradient(circle at 15% 10%, rgba(124,58,237,0.22), transparent 30%),
    radial-gradient(circle at 85% 20%, rgba(6,182,212,0.18), transparent 28%),
    linear-gradient(135deg, #080b16 0%, #0b1020 55%, #0f172a 100%);
  color: var(--text);
}

[data-testid="stHeader"] {
  background: transparent;
}

.block-container {
  padding-top: 2rem;
  padding-bottom: 3rem;
  max-width: 1220px;
}

.hero {
  border: 1px solid var(--stroke);
  background: linear-gradient(135deg, rgba(255,255,255,0.09), rgba(255,255,255,0.035));
  border-radius: 28px;
  padding: 28px 30px;
  box-shadow: 0 24px 80px rgba(0,0,0,0.28);
  backdrop-filter: blur(16px);
  margin-bottom: 22px;
}

.hero h1 {
  margin: 0;
  font-size: 2.4rem;
  letter-spacing: -0.04em;
  line-height: 1.1;
}

.hero p {
  margin: 10px 0 0 0;
  color: var(--muted);
  font-size: 1.02rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.07);
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 0.85rem;
  color: #dbeafe;
  white-space: nowrap;
}

.dot {
  width: 8px;
  height: 8px;
  background: var(--success);
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 20px rgba(34,197,94,0.9);
}

.metric-card {
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.055);
  border-radius: 18px;
  padding: 14px 16px;
  min-height: 78px;
}

.metric-card .label {
  color: var(--muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.metric-card .value {
  font-size: 1.18rem;
  font-weight: 750;
  margin-top: 4px;
  overflow-wrap: anywhere;
}

.file-row {
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.045);
  border-radius: 18px;
  padding: 14px 16px;
  margin-bottom: 10px;
}

.file-title {
  font-weight: 750;
  font-size: 1rem;
}

.file-meta {
  color: var(--muted);
  font-size: 0.82rem;
  margin-top: 4px;
  overflow-wrap: anywhere;
}

.answer-box {
  border: 1px solid rgba(124,58,237,0.35);
  background: linear-gradient(135deg, rgba(124,58,237,0.12), rgba(6,182,212,0.08));
  border-radius: 22px;
  padding: 22px;
  line-height: 1.85;
  font-size: 1.05rem;
  white-space: normal;
}

.small-muted {
  color: var(--muted);
  font-size: 0.88rem;
}

.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand), var(--brand-2));
  font-weight: 800;
  margin-right: 8px;
}

.stButton > button {
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  padding: 0.68rem 1rem !important;
  font-weight: 700 !important;
  box-shadow: 0 12px 30px rgba(0,0,0,0.18);
}

.stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
  border-radius: 14px !important;
}

[data-testid="stFileUploader"] {
  border: 1px dashed rgba(255,255,255,0.22);
  border-radius: 18px;
  background: rgba(255,255,255,0.04);
  padding: 12px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 24px !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  background: rgba(255,255,255,0.045) !important;
  box-shadow: 0 18px 70px rgba(0,0,0,0.16);
}

hr {
  border-color: rgba(255,255,255,0.10);
}

div[data-testid="stTabs"] button {
  font-weight: 700;
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# Utilities
# =========================

def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def html_text(value: Any) -> str:
    return escape(str(value or ""), quote=True)


def html_multiline(value: Any) -> str:
    return "<br>".join(html_text(value).splitlines())


def clean_base_url(url: str) -> str:
    return str(url or "").strip().rstrip("/")


def safe_json_response(response: requests.Response) -> Dict[str, Any]:
    try:
        data = response.json()
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {"raw_text": response.text}


def api_result(ok: bool, status_code: Optional[int], data: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": ok, "status_code": status_code, "data": data}


def api_get(base_url: str, path: str, timeout: int = 30) -> Dict[str, Any]:
    try:
        response = requests.get(f"{clean_base_url(base_url)}{path}", timeout=timeout)
        return api_result(response.ok, response.status_code, safe_json_response(response))
    except requests.RequestException as exc:
        return api_result(False, None, {"error": str(exc)})


def api_post_json(base_url: str, path: str, payload: Dict[str, Any], timeout: int = 180) -> Dict[str, Any]:
    try:
        response = requests.post(f"{clean_base_url(base_url)}{path}", json=payload, timeout=timeout)
        return api_result(response.ok, response.status_code, safe_json_response(response))
    except requests.RequestException as exc:
        return api_result(False, None, {"error": str(exc)})


def api_upload_file(base_url: str, project_id: int, uploaded_file, timeout: int = 180) -> Dict[str, Any]:
    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "application/octet-stream",
            )
        }
        response = requests.post(
            f"{clean_base_url(base_url)}/api/v1/data/upload/{project_id}",
            files=files,
            timeout=timeout,
        )
        return api_result(response.ok, response.status_code, safe_json_response(response))
    except requests.RequestException as exc:
        return api_result(False, None, {"error": str(exc)})


@st.cache_data(ttl=12, show_spinner=False)
def cached_health_check(base_url: str) -> Dict[str, Any]:
    return api_get(base_url, "/api/v1/", timeout=6)


# =========================
# Registry / state
# =========================

def max_project_id(records: List[Dict[str, Any]]) -> int:
    ids: List[int] = []
    for item in records:
        try:
            ids.append(int(item.get("project_id", 0)))
        except Exception:
            continue
    return max(ids or [0])


def normalize_state(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, list):
        records = raw
        return {
            "version": STATE_VERSION,
            "next_project_id": max(PROJECT_START_ID, max_project_id(records) + 1),
            "records": records,
        }

    if isinstance(raw, dict):
        records = raw.get("records", [])
        if not isinstance(records, list):
            records = []

        stored_next_id = raw.get("next_project_id", PROJECT_START_ID)
        try:
            stored_next_id = int(stored_next_id)
        except Exception:
            stored_next_id = PROJECT_START_ID

        return {
            "version": STATE_VERSION,
            "next_project_id": max(stored_next_id, max_project_id(records) + 1, PROJECT_START_ID),
            "records": records,
        }

    return {
        "version": STATE_VERSION,
        "next_project_id": PROJECT_START_ID,
        "records": [],
    }


def load_state() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return normalize_state(None)

    try:
        with REGISTRY_PATH.open("r", encoding="utf-8") as file:
            raw = json.load(file)
        return normalize_state(raw)
    except Exception:
        return normalize_state(None)


def save_state(state: Dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_state(state)
    tmp_path = REGISTRY_PATH.with_suffix(REGISTRY_PATH.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as file:
        json.dump(normalized, file, ensure_ascii=False, indent=2)

    tmp_path.replace(REGISTRY_PATH)


def get_records(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = state.get("records", [])
    return records if isinstance(records, list) else []


def next_project_id(state: Dict[str, Any]) -> int:
    state = normalize_state(state)
    return int(state.get("next_project_id", PROJECT_START_ID))


def reserve_project_id(state: Dict[str, Any]) -> int:
    state.update(normalize_state(state))
    project_id = int(state["next_project_id"])
    state["next_project_id"] = project_id + 1
    save_state(state)
    return project_id


def add_record(state: Dict[str, Any], record: Dict[str, Any]) -> None:
    state.update(normalize_state(state))
    records = get_records(state)
    records.append(record)
    state["records"] = records
    state["next_project_id"] = max(int(state["next_project_id"]), int(record["project_id"]) + 1)
    save_state(state)


def selected_record_label(record: Dict[str, Any]) -> str:
    display_name = record.get("display_name") or record.get("original_filename") or "Untitled"
    project_id = record.get("project_id", "?")
    status = record.get("status", "unknown")
    return f"{display_name} · Project #{project_id} · {status}"


def find_record_by_label(records: List[Dict[str, Any]], label: str) -> Optional[Dict[str, Any]]:
    for record in records:
        if selected_record_label(record) == label:
            return record
    return None


def sorted_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(records, key=lambda x: int(x.get("project_id", 0)), reverse=True)


# =========================
# UI components
# =========================

def render_header(state: Dict[str, Any], api_base_url: str) -> None:
    records = get_records(state)
    health = cached_health_check(clean_base_url(api_base_url))
    is_online = bool(health.get("ok"))

    st.markdown(
        f"""
<div class="hero">
  <div style="display:flex; justify-content:space-between; gap:16px; align-items:flex-start; flex-wrap:wrap;">
    <div>
      <h1>Mini RAG Studio</h1>
      <p>Upload documents, index them, and ask focused questions from a clean testing workspace.</p>
    </div>
    <div class="status-pill">
      <span class="dot" style="background:{'#22c55e' if is_online else '#ef4444'}"></span>
      API {'Online' if is_online else 'Offline'}
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="label">Uploaded files</div><div class="value">{len(records)}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="label">Next project ID</div><div class="value">{next_project_id(state)}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card"><div class="label">API base URL</div><div class="value" style="font-size:0.95rem;">{html_text(api_base_url)}</div></div>',
            unsafe_allow_html=True,
        )


def render_file_card(record: Dict[str, Any]) -> None:
    title = html_text(record.get("display_name", "Untitled"))
    project_id = html_text(record.get("project_id", "?"))
    filename = html_text(record.get("original_filename", ""))
    created_at = html_text(record.get("created_at", ""))
    status = html_text(record.get("status", ""))

    st.markdown(
        f"""
<div class="file-row">
  <div class="file-title">{title}</div>
  <div class="file-meta">
    Project #{project_id} · {filename} · {created_at} · {status}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_recent_files(records: List[Dict[str, Any]]) -> None:
    if not records:
        st.markdown('<p class="small-muted">No uploaded files yet.</p>', unsafe_allow_html=True)
        return

    for record in sorted_records(records)[:6]:
        render_file_card(record)


def render_upload_page(api_base_url: str, state: Dict[str, Any]) -> None:
    records = get_records(state)

    st.markdown("### <span class='step-badge'>1</span>Upload a document", unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        with st.container(border=True):
            with st.form("upload_form", clear_on_submit=False):
                display_name = st.text_input(
                    "Document name",
                    placeholder="Example: Egypt History Notes",
                    help="This name will appear later in the Ask screen.",
                )

                uploaded_file = st.file_uploader(
                    "Document file",
                    type=["txt", "pdf"],
                    accept_multiple_files=False,
                    help="Supported test files: TXT and PDF.",
                )

                with st.expander("Advanced indexing settings", expanded=False):
                    a, b, c = st.columns(3)
                    with a:
                        chunk_size = st.number_input(
                            "Chunk size",
                            min_value=50,
                            max_value=5000,
                            value=DEFAULT_CHUNK_SIZE,
                            step=50,
                        )
                    with b:
                        overlap_size = st.number_input(
                            "Overlap",
                            min_value=0,
                            max_value=1000,
                            value=DEFAULT_OVERLAP_SIZE,
                            step=10,
                        )
                    with c:
                        auto_index = st.toggle("Auto index", value=True)

                upload_clicked = st.form_submit_button(
                    "Upload & prepare document",
                    type="primary",
                    use_container_width=True,
                )

    with right:
        st.markdown("### Recent documents")
        render_recent_files(records)

    if not upload_clicked:
        return

    if not display_name.strip():
        st.error("Document name is required.")
        st.stop()

    if uploaded_file is None:
        st.error("Choose a TXT or PDF file first.")
        st.stop()

    project_id = reserve_project_id(state)

    progress = st.progress(0, text="Starting upload...")
    status_box = st.empty()

    status_box.info(f"Uploading to Project #{project_id}...")
    upload_result = api_upload_file(api_base_url, project_id, uploaded_file, timeout=240)
    progress.progress(25, text="Upload completed. Processing...")

    if not upload_result.get("ok"):
        st.error("Upload failed.")
        st.json(upload_result)
        st.stop()

    upload_data = upload_result.get("data", {})
    file_id = upload_data.get("file_id") or upload_data.get("id") or upload_data.get("asset_id") or ""

    process_payload: Dict[str, Any] = {
        "chunk_size": int(chunk_size),
        "overlap_size": int(overlap_size),
        "do_reset": 1,
    }

    if file_id:
        process_payload["file_id"] = file_id

    status_box.info("Processing document into chunks...")
    process_result = api_post_json(
        api_base_url,
        f"/api/v1/data/process/{project_id}",
        process_payload,
        timeout=420,
    )
    progress.progress(55, text="Processing completed. Indexing...")

    if not process_result.get("ok"):
        st.error("Processing failed.")
        st.json(process_result)
        st.stop()

    push_result = {"ok": True, "status_code": None, "data": {"skipped": True}}
    if auto_index:
        status_box.info("Pushing chunks to vector index...")
        push_result = api_post_json(
            api_base_url,
            f"/api/v1/nlp/index/push/{project_id}",
            {"do_reset": 1},
            timeout=600,
        )

        if not push_result.get("ok"):
            st.error("Vector indexing failed.")
            st.json(push_result)
            st.stop()

    progress.progress(100, text="Ready.")
    status_box.success("Document is ready for questions.")

    record = {
        "project_id": project_id,
        "display_name": display_name.strip(),
        "original_filename": uploaded_file.name,
        "file_id": file_id,
        "size_bytes": uploaded_file.size,
        "mime_type": uploaded_file.type,
        "chunk_size": int(chunk_size),
        "overlap_size": int(overlap_size),
        "auto_indexed": bool(auto_index),
        "status": "ready" if auto_index else "processed",
        "created_at": now_iso(),
        "upload_response": upload_data,
    }

    add_record(state, record)

    st.session_state.selected_project_id = project_id
    st.session_state.page = "Ask"
    st.toast("Document added successfully.", icon="✅")
    time.sleep(0.5)
    st.rerun()


def render_ask_page(api_base_url: str, state: Dict[str, Any]) -> None:
    records = get_records(state)

    st.markdown("### <span class='step-badge'>2</span>Ask a question", unsafe_allow_html=True)

    if not records:
        st.warning("No documents available yet.")
        if st.button("Go to upload", use_container_width=True):
            st.session_state.page = "Upload"
            st.rerun()
        return

    records_sorted = sorted_records(records)
    labels = [selected_record_label(record) for record in records_sorted]

    default_index = 0
    selected_project_id = st.session_state.get("selected_project_id")
    if selected_project_id:
        for index, record in enumerate(records_sorted):
            if int(record.get("project_id", 0)) == int(selected_project_id):
                default_index = index
                break

    left, right = st.columns([0.95, 1.05], gap="large")

    with left:
        with st.container(border=True):
            selected_label = st.selectbox(
                "Document",
                labels,
                index=default_index,
                help="Choose any document uploaded before.",
            )

            selected_record = find_record_by_label(records, selected_label)
            if not selected_record:
                st.error("Selected document was not found.")
                st.stop()

            st.session_state.selected_project_id = int(selected_record["project_id"])
            render_file_card(selected_record)

            retrieval_limit = st.slider(
                "Retrieval limit",
                min_value=1,
                max_value=10,
                value=DEFAULT_RETRIEVAL_LIMIT,
                key="retrieval_limit",
            )

            show_debug = st.toggle("Show debug response", value=False, key="show_debug")

            if st.button("Index info", use_container_width=True):
                info_result = api_get(
                    api_base_url,
                    f"/api/v1/nlp/index/info/{int(selected_record['project_id'])}",
                    timeout=60,
                )
                st.json(info_result)

    with right:
        with st.container(border=True):
            question = st.text_area(
                "Question",
                placeholder="Ask something about the selected document...",
                height=150,
                key="question_text",
            )

            ask_col, search_col = st.columns(2)
            with ask_col:
                ask_clicked = st.button("Generate answer", type="primary", use_container_width=True)
            with search_col:
                search_clicked = st.button("Search only", use_container_width=True)

    if not ask_clicked and not search_clicked:
        return

    if not question.strip():
        st.error("Question is required.")
        st.stop()

    project_id = int(selected_record["project_id"])
    payload = {
        "text": question.strip(),
        "limit": int(retrieval_limit),
    }

    endpoint = "answer" if ask_clicked else "search"
    path = f"/api/v1/nlp/index/{endpoint}/{project_id}"
    mode = "answer" if ask_clicked else "search"

    with st.spinner("Searching and generating..." if ask_clicked else "Searching..."):
        start = time.time()
        result = api_post_json(api_base_url, path, payload, timeout=360 if ask_clicked else 180)
        elapsed = time.time() - start

    if not result.get("ok"):
        st.error(f"Request failed. HTTP {result.get('status_code')}")
        st.json(result)
        st.stop()

    data = result.get("data", {})

    if mode == "answer":
        answer = data.get("answer", "")
        st.markdown("### Answer")
        st.markdown(
            f'<div class="answer-box">{html_multiline(answer)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Generated in {elapsed:.2f}s · Project #{project_id}")
    else:
        st.markdown("### Search results")
        st.json(data)

    if show_debug:
        with st.expander("Debug response", expanded=False):
            st.json(data)


def render_settings_page(api_base_url: str, state: Dict[str, Any]) -> None:
    records = get_records(state)

    st.markdown("### Settings")

    c1, c2 = st.columns(2, gap="large")

    with c1:
        with st.container(border=True):
            st.markdown("#### Local registry")
            st.write(str(REGISTRY_PATH.resolve()))
            st.json(state)

    with c2:
        with st.container(border=True):
            st.markdown("#### Actions")

            if st.button("Clear local document list", type="secondary", use_container_width=True):
                state = normalize_state(state)
                state["records"] = []
                # Keep next_project_id to avoid accidental project-id reuse.
                save_state(state)
                st.session_state.selected_project_id = None
                st.toast("Local document list cleared. Next project ID was preserved.", icon="🗑️")
                st.rerun()

            if st.button("Refresh API health", use_container_width=True):
                cached_health_check.clear()
                st.rerun()

            health = cached_health_check(clean_base_url(api_base_url))
            st.markdown("#### Health")
            st.json(health)


# =========================
# Main
# =========================

state = load_state()

with st.sidebar:
    st.markdown("## Mini RAG Studio")
    api_base_url = st.text_input("API URL", value=DEFAULT_API_BASE_URL)
    st.divider()

    if "page" not in st.session_state:
        st.session_state.page = "Upload"

    page_options = ["Upload", "Ask", "Settings"]
    current_page = st.session_state.page if st.session_state.page in page_options else "Upload"

    page = st.radio(
        "Navigation",
        page_options,
        index=page_options.index(current_page),
        label_visibility="collapsed",
    )
    st.session_state.page = page

api_base_url = clean_base_url(api_base_url)

render_header(state, api_base_url)

if st.session_state.page == "Upload":
    render_upload_page(api_base_url, state)
elif st.session_state.page == "Ask":
    render_ask_page(api_base_url, state)
else:
    render_settings_page(api_base_url, state)
