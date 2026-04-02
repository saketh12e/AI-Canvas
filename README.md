# AI Canvas

AI Canvas is an infinite-canvas learning and thinking workspace where a user asks a question and the backend turns it into a visual explanation on the canvas.

This V1 milestone reshapes the project from a fixed docs-to-cards prototype into a provider-aware AI canvas foundation. The current system can plan a visual response, gather supporting documentation, synthesize an explanation, and render a canvas cluster in the frontend.

## V1 Scope

- Infinite canvas frontend built with `tldraw`
- FastAPI backend with streamed progress updates over SSE
- LangGraph orchestration pipeline
- Provider-aware model layer for:
  - Gemini
  - OpenAI
  - Anthropic
  - Grok
- Canvas-oriented backend stages:
  - `planner`
  - `research`
  - `synthesis`
  - `canvas`

## Architecture

Current request flow:

```text
User prompt
  -> planner agent
  -> research agent
  -> synthesis agent
  -> canvas agent
  -> tldraw scene rendering
```

The backend streams staged events to the frontend:

- `plan_ready`
- `research_ready`
- `explanation_ready`
- `canvas_ready`
- `done`

## Project Structure

```text
backend/
  agents/
  db/
  llm/
  skills/
  tools/
  main.py
  config.py

frontend/
  app/
    components/
    lib/
```

## Current Tech Stack

### Backend

- FastAPI
- LangGraph
- LangChain
- Google Gemini integration
- OpenAI integration
- Anthropic integration
- Supabase for persistence

### Frontend

- Next.js 14
- React 18
- tldraw
- Tailwind CSS

## Running Locally

### Backend

```bash
uv run uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment

Copy `.env.example` to `.env` and add your own keys.

Important notes:

- Gemini is the currently configured default path in local development
- OpenAI, Anthropic, and Grok are wired in code and require their own API keys
- `.env` is intentionally ignored and should never be committed

## Verification

Backend compile check:

```bash
uv run python -m compileall backend
```

Frontend type-check:

```bash
cd frontend
npx tsc --noEmit
```

## What Is Already Built

- Provider-aware LLM factory
- New LangGraph V2 pipeline
- Scene-based canvas rendering foundation
- Provider selection in the input UI
- PR summary for this milestone in `docs/PR_V1_AI_CANVAS_FOUNDATION.md`

## What Comes Next

- Add better multi-source research with Context7, Firecrawl, Playwright MCP, and GitHub MCP
- Build BYOK settings and persistence
- Improve context-aware canvas placement
- Add richer scene types for comparisons, architecture diagrams, and workflows
- Run full end-to-end testing with live providers
