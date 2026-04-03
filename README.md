# AI Canvas

AI Canvas is an infinite-canvas learning and thinking workspace where a user asks a question and the backend turns it into a visual explanation on the canvas.

The project is now at a V2 foundation stage. It has moved from a fixed docs-to-cards prototype into a provider-aware AI canvas system with multi-source research and browser-local BYOK runtime settings.

## V2 Scope

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
- Multi-source research inputs:
  - Context7
  - MCP docs
  - Firecrawl
  - Tavily
- Browser-local BYOK settings for:
  - model providers
  - research connectors

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

The frontend also reads runtime capability metadata from:

- `GET /runtime/capabilities`

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
- Multi-source research foundation with Context7 plus optional Firecrawl and Tavily connectors
- Runtime capabilities endpoint for provider and connector readiness
- Provider selection in the input UI
- Browser-local runtime settings panel for BYOK testing
- Per-request runtime key overrides so `.env` is optional during testing

## Release Notes

- V1 summary: `docs/PR_V1_AI_CANVAS_FOUNDATION.md`
- V2 summary: `docs/PR_V2_RESEARCH_AND_BYOK.md`
- Commit history: `docs/COMMIT_HISTORY.md`

## What Comes Next

- Add connector ranking and fallback policy
- Add GitHub and Playwright research connectors
- Improve context-aware canvas placement
- Add richer scene types for comparisons, architecture diagrams, and workflows
- Run full end-to-end testing with live providers
