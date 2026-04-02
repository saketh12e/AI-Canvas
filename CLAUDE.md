# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend
```bash
# Start backend (from repo root)
uv run uvicorn backend.main:app --reload --port 8000

# Add a Python dependency
uv add <package>

# Run a one-off Python script
uv run python -c "import backend.config"
```

### Frontend
```bash
cd frontend

npm run dev          # Start Next.js dev server (port 3000)
npm run build        # Production build
npx tsc --noEmit     # TypeScript type-check (run before claiming fixes are clean)

# After changing next.config.js or installing packages:
rm -rf .next && npm run dev
```

## Package Management Rules
- **Python**: `uv` only — never `pip install`. All deps in `pyproject.toml`.
- **Frontend**: npm (already installed, no changes needed unless adding a package).

## Architecture

### Data flow for a single user query
```
User types query → page.tsx
  → useSSEStream (lib/sse.ts) — POST /query with {query, session_id, base_x, base_y}
    → FastAPI /query endpoint (main.py) — StreamingResponse SSE
      → LangGraph pipeline (agents/graph.py):
          doc_agent → explainer_agent → visualizer_agent
      → SSE events: doc_fetched | explanation_ready | canvas_ready | done
  → onCanvasReady → setElements(mergeElements(...))
  → Canvas.tsx useEffect → editor.createShapes(newEls)  [tldraw]
```

### Backend structure
```
backend/
  config.py              — pydantic-settings; loads .env with explicit path; propagates GOOGLE_API_KEY
  main.py                — FastAPI app, lifespan (MCP init + Postgres checkpointer), SSE endpoint, canvas CRUD
  agents/
    state.py             — AgentState TypedDict (shared across all three agents)
    graph.py             — LangGraph StateGraph: START→doc_agent→explainer_agent→visualizer_agent→END
    doc_agent.py         — Tool-calling loop (max 6 rounds), fetches + resolves linked pages
    explainer_agent.py   — Single LLM call, outputs JSON {explanation, key_concepts, code_example, sources}
    visualizer_agent.py  — Calls build_elements tool; falls back to direct invoke if model skips tool call
  tools/
    mcpdoc_tools.py      — MultiServerMCPClient singleton; initialized once at lifespan; tools cached globally
    excalidraw_builder.py — build_elements @tool — outputs tldraw-native shape JSON (NOT Excalidraw format)
    link_resolver.py     — Extracts + scores links from fetched doc content; returns top 2 to resolve
  db/
    checkpointer.py      — get_postgres_connection_string(); handles both https:// and postgresql:// URLs
  skills/
    explainer_skill.md   — System prompt for Explainer Agent (JSON output schema)
    canvas_skill.md      — System prompt for Visualizer Agent (tldraw shape schema)
```

### Frontend structure
```
frontend/app/
  page.tsx              — Root component: owns elements[], sessionId state, orchestrates all SSE callbacks
  components/
    Canvas.tsx          — tldraw wrapper; editor stored in useRef (NOT useState); addedIdsRef deduplicates shapes
    InputBar.tsx        — Fixed top-0; avoids tldraw's bottom toolbar
    SessionSidebar.tsx  — Starts at top-16 to clear InputBar
  lib/
    sse.ts              — useSSEStream hook; uses fetch+ReadableStream (NOT EventSource — supports POST)
    canvas-utils.ts     — getRightmostX (reads props.w for tldraw shapes), getNextBaseX, mergeElements
```

## Key Gotchas

### Canvas shape format
`excalidraw_builder.py` outputs **tldraw-native shapes**, not Excalidraw format. Shape IDs start with `shape:` (e.g. `shape:concept-abc123`). Canvas.tsx passes them directly to `editor.createShapes()` — no conversion layer. The field in AgentState is still named `excalidraw_elements` for historical reasons.

### Gemini content parsing
`msg.content` from `langchain-google-genai` 4.x can be `str` or `list[dict]`. Both agents use `parse_gemini_content(msg)` to normalize. Never access `msg.content` directly without this helper.

### MCP client lifecycle
`MultiServerMCPClient` is initialized once in FastAPI lifespan via `init_mcp_client()`. Tools are cached in `_cached_tools`. Do NOT create a new client per request — the mcpdoc subprocess starts once only. `langchain-mcp-adapters ≥0.2` does not support context manager usage.

### Postgres checkpointer lifecycle
`AsyncPostgresSaver.from_conn_string()` returns an `_AsyncGeneratorContextManager` in `langgraph-checkpoint-postgres ≥3.0`. The lifespan in `main.py` manually calls `__aenter__`/`__aexit__` to keep the connection open for the process lifetime.

### sessionId hydration
`sessionId` is initialized as `""` (empty string) and set via `useEffect` from `localStorage`. Any `fetch` or `stream()` call guarded by `if (!sessionId) return` — do not remove these guards.

### SUPABASE_URL dual format
`get_postgres_connection_string()` accepts both `postgresql://...` (direct Postgres URL, used as-is) and `https://PROJECT.supabase.co` (Supabase dashboard URL, project ref extracted). The Supabase REST client (`create_client`) requires the `https://` form; if `SUPABASE_URL` is a postgres URL, the REST client is skipped and canvas endpoints return `{"elements": []}`.

## Environment Variables (`.env` in repo root)
```
GEMINI_API_KEY=...          # OR GOOGLE_API_KEY — config.py propagates to GOOGLE_API_KEY automatically
LANGSMITH_API_KEY=...
SUPABASE_URL=...             # Either postgresql://... or https://PROJECT.supabase.co
SUPABASE_SERVICE_KEY=...     # JWT service key (for REST client only, not Postgres auth)
MODEL_EXPLAINER=gemini-3.1-pro-preview
MODEL_VISUALIZER=gemini-3-flash-preview
MODEL_DOC_ROUTER=gemini-3.1-flash-lite-preview
```
