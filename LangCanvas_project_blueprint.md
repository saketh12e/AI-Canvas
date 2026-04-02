# LangCanvas — LangChain Doc Visualizer Agent
## Claude Code Blueprint Prompt

---

## CRITICAL OPERATING INSTRUCTIONS FOR CLAUDE CODE

You are building a production-grade multi-agent application called **LangCanvas**.

**MANDATORY APPROVAL RULES — DO NOT SKIP:**
- Before writing ANY file, show the file path and a 3-line summary of what you intend to write. Wait for "yes" or "go ahead" before proceeding.
- Before installing ANY package, list all packages and versions. Wait for approval.
- Before creating or modifying the Supabase schema, show the SQL. Wait for approval.
- Before running ANY terminal command that modifies state (migrations, installs, builds), confirm first.
- After completing each major phase (backend scaffold, agent graph, frontend), STOP and ask for review before moving to the next phase.
- If you are uncertain about a design decision, present 2 options and ask which to proceed with. Do NOT guess.

**PACKAGE MANAGER: uv ONLY**
- All Python dependency management uses `uv`. Never use `pip install` directly.
- Initialize with `uv init`, add packages with `uv add`, run with `uv run`.
- Never create a `requirements.txt`. Use `pyproject.toml` exclusively.

---

## PROJECT OVERVIEW

**Name:** LangCanvas
**What it is:** A multi-agent system that reads live LangChain/LangGraph documentation via the official `mcpdoc` MCP server, explains concepts in plain English with working code examples, and renders everything as interactive Excalidraw cards on an infinite canvas frontend. Users build a visual personal knowledge graph of the LangChain ecosystem — session by session.

**Core user flow:**
1. User opens the app → sees an infinite Excalidraw canvas (blank)
2. User types a concept in the input bar: e.g. "Explain LangGraph checkpointing"
3. Backend multi-agent system fires:
   - **Doc Agent** fetches the relevant LangChain doc page via mcpdoc MCP
   - **Explainer Agent** reads the raw doc and generates: plain-English summary + key concepts list + runnable Python code example
   - **Visualizer Agent** converts the structured output into Excalidraw elements JSON
4. Canvas receives the elements and renders them as 3 connected cards:
   - Explanation card (text frame)
   - Code block card (monospace frame)
   - Flow diagram (connected nodes with arrows)
5. User can drag, annotate, connect cards, add freehand notes — full Excalidraw interactivity
6. Each new query session adds a new cluster of cards to the same infinite canvas
7. Canvas state persists across browser sessions via Supabase

---

## ARCHITECTURE

```
Frontend (Next.js + Excalidraw React component)
    ↕ SSE streaming
Backend (FastAPI)
    ↕ LangGraph supervisor graph
    ├── Doc Agent          → mcpdoc MCP tools (list_doc_sources, fetch_docs)
    ├── Explainer Agent    → Gemini LLM + large system prompt + session state
    └── Visualizer Agent   → Gemini LLM + SKILL.md (Excalidraw schema) + build_elements() tool
    ↕
Supabase Postgres (LangGraph checkpointer for session persistence)
```

---

## TECH STACK — EXACT VERSIONS

### Python Backend
- **Runtime:** Python 3.12+, managed by `uv`
- **Web framework:** `fastapi[standard]` + `uvicorn`
- **Agent framework:** `langgraph` + `langchain-core` + `langchain-google-genai`
- **MCP integration:** `langchain-mcp-adapters` + `mcpdoc` (run via uvx)
- **DB checkpointer:** `langgraph-checkpoint-postgres` + `psycopg[binary,pool]`
- **Supabase client:** `supabase`
- **Env management:** `python-dotenv`
- **Streaming:** FastAPI's `StreamingResponse` with SSE

### LLM Models (Google Gemini via langchain-google-genai)
- **Explainer Agent (primary):** `gemini-3.1-pro-preview` — best reasoning for doc comprehension
- **Visualizer Agent (structured output):** `gemini-3-flash-preview` — fast, sufficient for JSON generation
- **Doc Agent (routing only):** `gemini-3.1-flash-lite-preview` — cheapest, used only for tool routing decisions
- **IMPORTANT:** `response.content` from Gemini 3.x models in langchain-google-genai may return a list instead of string. Always parse with: `content = msg.content if isinstance(msg.content, str) else msg.content[0].get("text", "") if isinstance(msg.content, list) else str(msg.content)`

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Canvas:** `@excalidraw/excalidraw` React component (embedded directly — NOT the MCP version)
- **Styling:** Tailwind CSS + shadcn/ui
- **HTTP/SSE client:** native `EventSource` API for streaming
- **State:** React `useState` + `useRef` for canvas elements

---

## FILE STRUCTURE TO BUILD

```
langcanvas/
├── pyproject.toml                  # uv project file
├── .env.example                    # env var template
├── .env                            # actual secrets (gitignored)
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, SSE endpoint
│   ├── config.py                   # env vars, model config
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── graph.py                # LangGraph supervisor graph definition
│   │   ├── doc_agent.py            # Doc Agent node — mcpdoc MCP tools
│   │   ├── explainer_agent.py      # Explainer Agent node — Gemini + system prompt
│   │   ├── visualizer_agent.py     # Visualizer Agent node — Gemini + SKILL.md
│   │   └── state.py                # LangGraph TypedDict state schema
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── mcpdoc_tools.py         # Wraps mcpdoc MCP as LangChain tools
│   │   └── excalidraw_builder.py   # build_elements() @tool — converts structured JSON to Excalidraw elements[]
│   │
│   ├── skills/
│   │   └── excalidraw_skill.md     # SKILL.md for Visualizer Agent — Excalidraw schema rules
│   │
│   └── db/
│       ├── __init__.py
│       └── checkpointer.py         # Supabase Postgres checkpointer setup
│
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx             # Main page — canvas + input bar
        │   └── api/                 # (proxy routes if needed)
        ├── components/
        │   ├── Canvas.tsx           # Excalidraw component wrapper
        │   ├── InputBar.tsx         # Query input at bottom of screen
        │   └── SessionSidebar.tsx   # List of past sessions (left sidebar)
        └── lib/
            ├── sse.ts               # SSE client hook (useSSEStream)
            └── canvas-utils.ts      # Element positioning logic (place new cluster to right of last)
```

---

## PHASE 1 — PROJECT INITIALIZATION

### Step 1.1 — uv project init
```bash
mkdir langcanvas && cd langcanvas
uv init --python 3.12
uv add fastapi[standard] uvicorn langgraph langchain-core langchain-google-genai \
    langchain-mcp-adapters langgraph-checkpoint-postgres psycopg[binary,pool] \
    supabase python-dotenv
```

### Step 1.2 — .env.example
Create this file. Do NOT create .env — instruct user to copy and fill in:
```
GEMINI_API_KEY=your_google_ai_studio_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langcanvas

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here

# Model selection (do not change unless upgrading)
MODEL_EXPLAINER=gemini-3.1-pro-preview
MODEL_VISUALIZER=gemini-3-flash-preview
MODEL_DOC_ROUTER=gemini-3.1-flash-lite-preview
```

---

## PHASE 2 — LANGGRAPH STATE SCHEMA

File: `backend/agents/state.py`

```python
from typing import TypedDict, Optional, List, Any

class AgentState(TypedDict):
    # Input
    user_query: str
    session_id: str

    # Doc Agent output
    raw_doc_content: Optional[str]       # Raw markdown from fetch_docs()
    doc_url_used: Optional[str]          # Which URL was fetched

    # Explainer Agent output
    explanation: Optional[str]           # Deep conceptual explanation (NOT a summary)
    key_concepts: Optional[List[str]]    # Specific concept terms (3-6 items)
    code_example: Optional[str]          # Complete runnable Python code
    sources: Optional[List[str]]         # URLs fetched (primary + resolved links)

    # Visualizer Agent output
    excalidraw_elements: Optional[List[dict]]   # elements[] array for canvas

    # Conversation history (persists across turns via checkpointer)
    messages: List[Any]

    # Error handling
    error: Optional[str]
```

---

## PHASE 3 — MCPDOC MCP TOOL WRAPPER

File: `backend/tools/mcpdoc_tools.py`

The mcpdoc MCP server is started as a subprocess via uvx. Connect using `MultiServerMCPClient` from `langchain-mcp-adapters`. Expose two tools:

- `list_doc_sources()` — returns index of all available LangChain/LangGraph/LangSmith doc pages
- `fetch_docs(url: str)` — fetches a single doc page and returns its full markdown content as a string

**mcpdoc config:**
```python
MCP_CONFIG = {
    "langchain-docs": {
        "command": "uvx",
        "args": [
            "--from", "mcpdoc", "mcpdoc",
            "--urls",
            "LangChain:https://python.langchain.com/llms.txt",
            "LangGraph:https://langchain-ai.github.io/langgraph/llms.txt",
            "LangSmith:https://docs.smith.langchain.com/llms.txt",
            "--transport", "stdio"
        ],
        "transport": "stdio"
    }
}
```

Use `async with MultiServerMCPClient(MCP_CONFIG) as client:` pattern. The client must be initialized once at app startup and stored, not re-initialized per request (expensive subprocess startup).

**Return value of `fetch_docs`:** raw markdown string. Example:
```
## Persistence in LangGraph
LangGraph supports checkpointing through the Checkpointer interface.
Use MemorySaver for development, SqliteSaver or PostgresSaver for production.
graph = workflow.compile(checkpointer=checkpointer)
```

---

## PHASE 4 — DOC AGENT

File: `backend/agents/doc_agent.py`

**Model:** `gemini-3.1-flash-lite-preview` (cheapest — only does tool routing)
**Tools:** `list_doc_sources`, `fetch_docs` (from mcpdoc_tools.py)
**Role:** Given `state.user_query`, decide which doc page(s) are most relevant, fetch them, store raw content in `state.raw_doc_content`

**System prompt:**
```
You are a documentation retrieval specialist for the LangChain ecosystem.
Given a user's question, your job is to:
1. Call list_doc_sources() to get the index of available documentation
2. Identify the 1-2 most relevant doc pages for the question
3. Call fetch_docs(url) for each relevant page
4. Return the combined raw content — do NOT summarize, do NOT modify the text

You only fetch documentation. You do not explain or generate code.
```

**Node logic:**
- Takes `state.user_query`
- Calls tools to fetch docs
- Returns `state` with `raw_doc_content` and `doc_url_used` populated

---

## PHASE 4.5 — HYPERLINK RESOLUTION IN DOC AGENT

File: `backend/tools/link_resolver.py`

When `fetch_docs()` returns a page, it contains markdown hyperlinks pointing to related concepts.
Example: `See [Checkpointer](https://langchain-ai.github.io/langgraph/concepts/checkpointer/)`

The Doc Agent must resolve the most relevant linked pages, not just read the primary page.

### Implementation

```python
import re
from urllib.parse import urlparse

ALLOWED_DOMAINS = [
    "langchain-ai.github.io",
    "python.langchain.com",
    "docs.smith.langchain.com",
]

def extract_links(markdown: str) -> list[str]:
    """Extract all URLs from markdown link syntax [text](url)"""
    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    matches = re.findall(pattern, markdown)
    return [(text, url) for text, url in matches]

def filter_allowed_links(links: list[tuple]) -> list[str]:
    """Keep only links from allowed LangChain domains"""
    allowed = []
    for text, url in links:
        domain = urlparse(url).netloc
        if any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS):
            allowed.append((text, url))
    return allowed

def score_links_by_query(links: list[tuple], query: str) -> list[tuple]:
    """Score links by keyword overlap with the user query. Returns sorted list."""
    query_words = set(query.lower().split())
    scored = []
    for text, url in links:
        link_words = set(text.lower().replace("-", " ").split())
        # Also check URL path segments
        path_words = set(url.lower().replace("/", " ").replace("-", " ").split())
        overlap = len(query_words & (link_words | path_words))
        scored.append((overlap, text, url))
    scored.sort(reverse=True)
    return [(text, url) for _, text, url in scored]

def get_links_to_resolve(markdown: str, query: str, max_links: int = 2) -> list[str]:
    """Main function: extract, filter, score, and return top N URLs to follow"""
    all_links = extract_links(markdown)
    allowed = filter_allowed_links(all_links)
    scored = score_links_by_query(allowed, query)
    # Deduplicate URLs
    seen = set()
    result = []
    for text, url in scored:
        if url not in seen and len(result) < max_links:
            seen.add(url)
            result.append(url)
    return result
```

### Doc Agent updated flow with link resolution:
```
1. list_doc_sources() → get index
2. Identify primary page URL from index based on user_query
3. fetch_docs(primary_url) → get raw_markdown_1
4. get_links_to_resolve(raw_markdown_1, user_query, max_links=2) → [url_2, url_3]
5. fetch_docs(url_2) → raw_markdown_2   (if links found)
6. fetch_docs(url_3) → raw_markdown_3   (if links found)
7. Concatenate: state.raw_doc_content = raw_markdown_1 + "\n\n---\n\n" + raw_markdown_2 + ...
8. state.doc_url_used = [primary_url, url_2, url_3]
```

**Cap:** Max 3 total pages fetched (1 primary + 2 linked). This prevents runaway token costs
while ensuring the Explainer Agent has cross-referenced context.

---

## PHASE 5 — EXPLAINER AGENT

File: `backend/agents/explainer_agent.py`

**Model:** `gemini-3.1-pro-preview` (best reasoning)
**Tools:** None — reads from `state.raw_doc_content`
**Role:** Deep conceptual explanation — NOT a summary. A teacher, not a summarizer.

### The Explainer Agent Skill (SKILL.md — load into system prompt at init)

File: `backend/skills/explainer_skill.md`

```markdown
# Explainer Agent Skill — LangChain Deep Explanation

## Your identity
You are a senior LangChain/LangGraph engineer with 3 years of production experience
building agentic systems. You are now teaching a developer who knows Python well
but is new to the LangChain ecosystem. You have just read the official documentation
for a concept they asked about.

## What you are NOT doing
- You are NOT summarizing the documentation. Do not restate what the docs say.
- You are NOT giving a bullet-point overview. That's what the docs already are.
- You are NOT explaining every single thing on the page. Focus on what they asked.

## What you ARE doing
You are doing what a senior engineer does when a junior asks them a question:
1. You understand what they're actually confused about
2. You explain the mental model first — the "why" before the "what"
3. You use a concrete analogy from everyday life or familiar programming concepts
4. You walk through exactly how this works mechanically, step by step
5. You show working code that demonstrates the concept in a realistic scenario
6. You point out the common mistakes and gotchas that the docs don't mention

## Explanation structure — MANDATORY

Your output must be a JSON object with exactly these fields:

### explanation (string)
Write 3-5 paragraphs. Each paragraph has a specific job:

**Paragraph 1 — The mental model:**
Start with an analogy. "Think of X like..." or "This is similar to..." — connect
the concept to something the developer already knows. Git commits, database transactions,
function calls, event listeners — pick the closest match.

**Paragraph 2 — What problem it solves:**
Explain WHY this exists. What was painful or impossible without it?
What specific failure mode does it prevent? Make this concrete.

**Paragraph 3 — How it works mechanically:**
Now explain the actual mechanism. Use precise terminology but define each term
when you introduce it. Reference the specific APIs and classes involved.

**Paragraph 4 — The practical usage pattern:**
Describe when a developer reaches for this in real code. What are the setup steps?
What are the configuration options that actually matter (not the exhaustive list)?

**Paragraph 5 — Gotchas and common mistakes (REQUIRED):**
What does every developer get wrong the first time? What does the error message
look like when they mess it up? What's the non-obvious thing the docs bury in a footnote?
This paragraph is what makes your explanation worth reading over the docs themselves.

### key_concepts (array of strings)
3-6 items. Each item must be:
- A noun phrase (not a sentence)
- Specific to the concept asked about (not generic LangChain terms)
- Something a developer would search for if confused
- Maximum 5 words
Example: ["thread-based state isolation", "PostgresSaver vs MemorySaver", "config thread_id"]

### code_example (string)
A complete, runnable Python script. Requirements:
- All imports at the top (including uv/pip install comments for packages)
- Realistic variable names (not foo, bar, x, y)
- Every non-obvious line has an inline comment explaining WHY, not what
- Demonstrates a real use case, not a toy example
- Shows the concept being used correctly AND shows what happens if you get it wrong
  (in a comment or try/except)
- Must work with langchain>=0.3, langgraph>=0.2, langchain-google-genai>=2.0
- If the concept requires Supabase/Postgres, use MemorySaver as fallback with a comment
  explaining how to swap to PostgresSaver in production

### sources (array of strings)
List the URLs that were fetched to build this explanation.
This lets the user go read the original docs if they want more depth.

## JSON output rules
- Output ONLY the JSON object. No markdown code fences. No preamble. No "Here is the..."
- All string values use escaped newlines (\n) for multi-paragraph content
- The code_example field contains the full Python code as a single escaped string
- If the documentation content is insufficient to answer the question deeply,
  say so explicitly in the explanation and describe what additional information is needed

## Conversation continuity
If there are previous messages in the conversation history:
- Reference what was explained before: "Building on the checkpointing we covered..."
- Do not re-explain concepts already covered unless asked
- Connect new concepts to previously explained ones
- Track what code examples have already been shown and build on them
```

**Gemini response.content parsing (REQUIRED — apply before JSON parsing):**
```python
def parse_gemini_content(msg) -> str:
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and "text" in part:
                return part["text"]
            elif isinstance(part, str):
                return part
    return str(content)
```

**Node logic:**
- Load `explainer_skill.md` once at agent initialization → inject as system prompt
- Takes `state.raw_doc_content` + `state.user_query` + `state.messages` + `state.doc_url_used`
- Builds user message:
  ```
  User question: {user_query}
  
  Documentation fetched from: {doc_url_used}
  
  ---RAW DOCUMENTATION START---
  {raw_doc_content}
  ---RAW DOCUMENTATION END---
  
  Now explain this concept deeply following your skill instructions.
  Output only valid JSON.
  ```
- Calls Gemini, parses content with `parse_gemini_content()`
- Strips any markdown fences if present: `content.strip().lstrip("```json").rstrip("```")`
- Parses JSON with try/except — on failure, returns a structured error object
- Returns `state` with `explanation`, `key_concepts`, `code_example`, `sources` populated

---

## PHASE 6 — VISUALIZER AGENT + EXCALIDRAW SKILL

### 6.1 — SKILL.md
File: `backend/skills/excalidraw_skill.md`

```markdown
# Excalidraw Canvas Skill

## Your role
Convert structured explanation data into Excalidraw elements[] JSON.
You must produce a valid JSON array of Excalidraw element objects.

## Element types you will use

### Text card (for explanation)
{
  "type": "text",
  "id": "unique_id_string",
  "x": number,
  "y": number,
  "width": 400,
  "height": auto,
  "text": "content here",
  "fontSize": 16,
  "fontFamily": 1,
  "textAlign": "left",
  "strokeColor": "#1e1e2e",
  "backgroundColor": "#e0f2fe",
  "fillStyle": "solid"
}

### Code card (for code_example)
{
  "type": "text",
  "id": "unique_id_string",
  "x": number,
  "y": number,
  "width": 500,
  "height": auto,
  "text": "code content",
  "fontSize": 14,
  "fontFamily": 3,      ← use 3 for monospace
  "strokeColor": "#1e1e2e",
  "backgroundColor": "#1e1e2e",
  "fillStyle": "solid"
}

### Concept node (for each key_concept)
{
  "type": "rectangle",
  "id": "unique_id_string",
  "x": number,
  "y": number,
  "width": 160,
  "height": 44,
  "strokeColor": "#3b82f6",
  "backgroundColor": "#dbeafe",
  "fillStyle": "solid",
  "roundness": {"type": 3}
}

### Arrow (connecting concept nodes)
{
  "type": "arrow",
  "id": "unique_id_string",
  "x": number,
  "y": number,
  "width": number,
  "height": number,
  "points": [[0, 0], [dx, dy]],
  "strokeColor": "#3b82f6"
}

## Layout rules
- Explanation card: top-left of cluster, x=base_x, y=base_y
- Code card: directly below explanation, y=base_y+explanation_height+20
- Concept nodes: arranged horizontally to the right, x=base_x+440, y=base_y
- Each cluster occupies ~900x600px
- Next cluster placed at base_x+1000 to the right of the previous one
- All IDs must be unique strings (use short UUID-style: "el_001", "el_002", etc.)
- base_x and base_y are provided as input — use them exactly

## Output format
Return ONLY a valid JSON array. No markdown. No explanation text. Just the array.
```

### 6.2 — build_elements() custom tool
File: `backend/tools/excalidraw_builder.py`

This is a Python `@tool` function that:
- Takes the structured output from Explainer Agent
- Generates Excalidraw elements[] following the skill rules
- Returns the elements array as a JSON string

The Visualizer Agent calls this tool with the structured data, the SKILL.md is loaded into its system context.

### 6.3 — Visualizer Agent
File: `backend/agents/visualizer_agent.py`

**Model:** `gemini-3-flash-preview` (fast, structured JSON output)
**Tools:** `build_elements` (custom tool)
**Skill loaded:** `backend/skills/excalidraw_skill.md` read at agent initialization, injected into system prompt

**Node logic:**
- Loads skill content from SKILL.md at startup
- Takes `state.explanation` + `state.key_concepts` + `state.code_example`
- Calls `build_elements()` tool with the structured data
- Parses returned JSON
- Returns `state.excalidraw_elements`

---

## PHASE 7 — LANGGRAPH SUPERVISOR GRAPH

File: `backend/agents/graph.py`

**Graph structure:** Linear pipeline (not parallel fan-out for V1 — simpler, easier to debug)
```
START → doc_agent → explainer_agent → visualizer_agent → END
```

**State persistence:** Use `AsyncPostgresSaver` from `langgraph-checkpoint-postgres`
connected to Supabase Postgres. The `thread_id` (= session_id from frontend) is passed
as `config = {"configurable": {"thread_id": session_id}}` on every graph invocation.

**Streaming:** Use `graph.astream_events()` to stream intermediate outputs. Emit SSE events at each node completion:
```
data: {"type": "doc_fetched", "url": "..."}
data: {"type": "explanation_ready", "explanation": "...", "key_concepts": [...], "code_example": "..."}
data: {"type": "canvas_ready", "elements": [...]}
data: {"type": "done"}
```

---

## PHASE 8 — FASTAPI BACKEND

File: `backend/main.py`

### Endpoints

**POST /query** (SSE streaming)
```
Body: { "query": string, "session_id": string, "base_x": number, "base_y": number }
Response: text/event-stream
Events: doc_fetched → explanation_ready → canvas_ready → done
```

**GET /sessions/{session_id}/canvas**
```
Returns: { "elements": [...] }   ← full saved canvas state from Supabase
```

**POST /sessions/{session_id}/canvas**
```
Body: { "elements": [...] }   ← save user's current canvas (after manual edits)
```

**GET /health** — basic health check

### CORS
Enable CORS for `http://localhost:3000` in development.

### Lifespan events
Initialize `MultiServerMCPClient` on startup (subprocess must start once).
Tear down on shutdown.

---

## PHASE 9 — SUPABASE POSTGRES SETUP

### Tables needed

**1. canvas_sessions** (stores user canvas state)
```sql
CREATE TABLE canvas_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT UNIQUE NOT NULL,
  elements JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**2. LangGraph checkpoint tables** (created automatically by `langgraph-checkpoint-postgres`)
Run the setup command from the library after connecting — do NOT create manually.

Show this SQL to the user for approval before running in Supabase SQL editor.

---

## PHASE 10 — NEXT.JS FRONTEND

### Canvas component (`src/components/Canvas.tsx`)
- Import: `import { Excalidraw } from "@excalidraw/excalidraw"`
- Props: `elements: ExcalidrawElement[]`, `onElementsChange: (elements) => void`
- Use `excalidrawAPI` ref to programmatically add elements:
  ```ts
  excalidrawAPI.updateScene({ elements: [...existingElements, ...newElements] })
  ```
- On user manual edit: debounce 2s, then POST /sessions/{session_id}/canvas to save

### Input bar (`src/components/InputBar.tsx`)
- Fixed at bottom of screen
- Text input + Submit button
- On submit: open SSE connection to POST /query
- Show loading indicator while streaming

### SSE hook (`src/lib/sse.ts`)
```ts
// useSSEStream(query, sessionId, baseX, baseY)
// Opens EventSource, parses events, calls callbacks:
// onDocFetched(url) → show toast "Fetching docs from..."
// onExplanationReady(data) → show explanation preview in sidebar
// onCanvasReady(elements) → call excalidrawAPI.updateScene()
// onDone() → hide loading indicator
```

### Element positioning logic (`src/lib/canvas-utils.ts`)
- Track the rightmost x coordinate of existing elements
- Place each new cluster at `rightmost_x + 100`
- Pass `base_x` and `base_y` to the /query endpoint

---

## PHASE 11 — RUNNING THE PROJECT

```bash
# Backend
cd langcanvas
uv run uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd langcanvas/frontend
npm install
npm run dev
```

---

## WHAT TO BUILD IN ORDER (phases)

Claude Code must build in this exact order, confirming with the user at each phase boundary:

1. ✅ Project init + uv setup + .env.example
2. ✅ State schema (state.py)
3. ✅ mcpdoc tool wrapper (mcpdoc_tools.py)
4. ✅ Doc Agent (doc_agent.py)
5. ✅ Explainer Agent (explainer_agent.py)
6. ✅ Excalidraw SKILL.md + build_elements tool + Visualizer Agent
7. ✅ LangGraph supervisor graph (graph.py)
8. ✅ FastAPI app (main.py) with SSE endpoint
9. ✅ Supabase schema (show SQL, wait for user to run in Supabase dashboard)
10. ✅ Next.js frontend (Canvas + InputBar + SSE hook)
11. ✅ Integration test (run both servers, test one query end-to-end)

---

## KNOWN ISSUES TO HANDLE PROACTIVELY

1. **Gemini content parsing:** Apply `parse_gemini_content()` to every Gemini response before processing. Gemini 3.x returns `content` as a list in langchain-google-genai — raw string access will break.

2. **mcpdoc subprocess startup:** Start `MultiServerMCPClient` once in FastAPI lifespan. Do NOT start it per request — too slow.

3. **JSON parsing from LLM:** Always wrap JSON.parse in try/catch with a fallback. If Explainer Agent returns malformed JSON, return a generic error element on the canvas rather than crashing.

4. **SSE in Next.js:** Use native `fetch` with `ReadableStream` for POST-based SSE (EventSource only supports GET). Implement a `useSSEStream` hook using `fetch` + streaming body reader.

5. **Excalidraw SSR:** The `@excalidraw/excalidraw` package is client-side only. Wrap in `dynamic(() => import(...), { ssr: false })` in Next.js.

6. **CORS + streaming:** Set `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no` headers on SSE responses.

---

## SUCCESS CRITERIA FOR V1

- [ ] User types "Explain LangGraph checkpointing" → 3 Excalidraw cards appear on canvas
- [ ] Each card has correct content (explanation / code / diagram)
- [ ] Canvas persists after browser refresh (loads from Supabase)
- [ ] User can drag, resize, annotate cards freely
- [ ] New query adds new cluster to the right of existing cards
- [ ] LangSmith trace shows all 3 agent nodes executing in sequence
- [ ] No hardcoded API keys anywhere (all from .env)
