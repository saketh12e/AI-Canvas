import json
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Load .env before any other imports so env vars are available at module level
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from backend.llm.factory import get_provider_capabilities
from backend.tools.mcpdoc_tools import init_mcp_client, shutdown_mcp_client
from backend.tools.research_registry import get_research_connector_capabilities
from backend.db.checkpointer import get_postgres_connection_string
from backend.agents.graph import build_graph
from backend.config import settings

# Supabase client for canvas persistence
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# App state (set during lifespan)
# ---------------------------------------------------------------------------
_graph = None
_supabase: Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph, _supabase

    # Start mcpdoc subprocess
    await init_mcp_client()

    # ── Postgres checkpointer (langgraph-checkpoint-postgres ≥3.0) ──────────
    # from_conn_string() is an async context manager in this version.
    # We manually enter/exit so the connection stays open for the whole process.
    _pg_cm = None
    checkpointer = None

    if settings.supabase_url:
        try:
            _pg_cm = AsyncPostgresSaver.from_conn_string(
                get_postgres_connection_string()
            )
            checkpointer = await _pg_cm.__aenter__()
            await checkpointer.setup()
            print("[INFO] Postgres checkpointer ready")
        except Exception as e:
            print(f"[WARNING] Could not connect to Supabase Postgres: {e}")
            if _pg_cm is not None:
                try:
                    await _pg_cm.__aexit__(None, None, None)
                except Exception:
                    pass
            _pg_cm = None
            checkpointer = None

    if checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        print("[WARNING] Running without persistence (MemorySaver fallback)")

    _graph = build_graph(checkpointer=checkpointer)

    # Supabase REST client for canvas table.
    # Requires the Supabase dashboard URL (https://PROJECT.supabase.co).
    # If SUPABASE_URL is a raw postgres:// connection string, skip REST client.
    _supabase_https_url = settings.supabase_url
    if _supabase_https_url and not _supabase_https_url.startswith("https://"):
        print("[WARNING] SUPABASE_URL is not an https:// URL — skipping REST client")
        _supabase_https_url = None

    if _supabase_https_url and settings.supabase_service_key:
        try:
            _supabase = create_client(_supabase_https_url, settings.supabase_service_key)
            print("[INFO] Supabase REST client ready")
        except Exception as e:
            print(f"[WARNING] Supabase REST client failed: {e}")
            _supabase = None

    yield  # ── app runs ────────────────────────────────────────────────────

    # Cleanup: close Postgres connection if it was opened
    if _pg_cm is not None:
        try:
            await _pg_cm.__aexit__(None, None, None)
        except Exception:
            pass

    await shutdown_mcp_client()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="LangCanvas API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str
    session_id: str = ""
    base_x: int = 0
    base_y: int = 0
    provider: str = ""
    runtime_keys: dict[str, str] = {}


class CanvasSaveRequest(BaseModel):
    elements: list


# ---------------------------------------------------------------------------
# SSE streaming endpoint
# ---------------------------------------------------------------------------
@app.post("/query")
async def query_endpoint(req: QueryRequest):
    session_id = req.session_id or str(uuid.uuid4())

    async def event_stream() -> AsyncGenerator[str, None]:
        config = {"configurable": {"thread_id": session_id}}
        initial_state = {
            "user_query": req.query,
            "session_id": session_id,
            "base_x": req.base_x,
            "base_y": req.base_y,
            "selected_provider": req.provider or "",
            "runtime_keys": req.runtime_keys or {},
            "intent": "",
            "visual_goal": "",
            "canvas_title": "",
            "research_queries": [],
            "evidence": [],
            "messages": [],
            "raw_doc_content": "",
            "sources": [],
            "source_details": [],
            "research_report": {},
            "explanation": "",
            "key_concepts": [],
            "code_example": "",
            "scene_spec": {},
            "canvas_elements": [],
            "error": None,
        }

        try:
            async for event in _graph.astream_events(initial_state, config=config, version="v2"):
                kind = event.get("event")
                name = event.get("name", "")

                if kind == "on_chain_end" and name == "planner_agent":
                    output = event.get("data", {}).get("output", {})
                    yield f"data: {json.dumps({'type': 'plan_ready', 'intent': output.get('intent', ''), 'visual_goal': output.get('visual_goal', ''), 'canvas_title': output.get('canvas_title', '')})}\n\n"

                elif kind == "on_chain_end" and name == "research_agent":
                    output = event.get("data", {}).get("output", {})
                    urls = output.get("sources") or []
                    details = output.get("source_details") or []
                    report = output.get("research_report") or {}
                    yield f"data: {json.dumps({'type': 'research_ready', 'sources': urls, 'source_details': details, 'connectors': report.get('connectors_used', []), 'research_report': report})}\n\n"

                elif kind == "on_chain_end" and name == "synthesis_agent":
                    output = event.get("data", {}).get("output", {})
                    yield f"data: {json.dumps({'type': 'explanation_ready', 'explanation': output.get('explanation', ''), 'key_concepts': output.get('key_concepts', []), 'code_example': output.get('code_example', '')})}\n\n"

                elif kind == "on_chain_end" and name == "canvas_agent":
                    output = event.get("data", {}).get("output", {})
                    elements = output.get("canvas_elements", [])
                    yield f"data: {json.dumps({'type': 'canvas_ready', 'elements': elements, 'session_id': session_id, 'scene': output.get('scene_spec', {})})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Canvas persistence endpoints
# ---------------------------------------------------------------------------
@app.get("/sessions/{session_id}/canvas")
async def get_canvas(session_id: str):
    try:
        if _supabase is not None:
            result = _supabase.table("canvas_sessions").select("elements").eq("session_id", session_id).execute()
            if result.data:
                return {"elements": result.data[0]["elements"]}
        return {"elements": []}
    except Exception as e:
        print(f"[canvas] fetch error: {e}")
        return {"elements": []}


@app.post("/sessions/{session_id}/canvas")
async def save_canvas(session_id: str, req: CanvasSaveRequest):
    try:
        if _supabase is not None:
            _supabase.table("canvas_sessions").upsert(
                {"session_id": session_id, "elements": req.elements},
                on_conflict="session_id",
            ).execute()
            return {"status": "saved"}
        return {"status": "no_db"}
    except Exception as e:
        print(f"[canvas] save error: {e}")
        return {"status": "error", "detail": str(e)}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/runtime/capabilities")
async def runtime_capabilities():
    return {
        "providers": get_provider_capabilities(),
        "connectors": get_research_connector_capabilities(),
    }
