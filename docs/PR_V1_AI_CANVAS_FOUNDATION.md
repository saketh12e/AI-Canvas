# V1 AI Canvas Foundation

## Summary

This PR captures the first major pivot of LangCanvas from a fixed docs-to-cards prototype into a provider-aware AI canvas foundation.

The backend flow now follows:

`planner -> research -> synthesis -> canvas`

instead of:

`doc -> explainer -> visualizer`

This creates a stronger base for the product direction: an infinite canvas where users can ask for explanations, diagrams, architecture maps, and structured visual notes.

## What Was Built

- Replaced the old LangGraph pipeline with a V2 pipeline centered on planning, research, synthesis, and canvas scene generation
- Added provider-aware LLM wiring so the app can be extended to Gemini, OpenAI, Anthropic, and Grok
- Added new backend contracts for visual planning and scene rendering
- Updated the renderer so canvas output is richer and based on a scene spec instead of a rigid three-card template
- Updated SSE flow so the frontend receives staged progress events
- Added provider selection in the frontend UI
- Sanitized environment template values

## Main Files

- `backend/agents/graph.py`
- `backend/agents/planner_agent.py`
- `backend/agents/research_agent.py`
- `backend/agents/explainer_agent.py`
- `backend/agents/canvas_agent.py`
- `backend/llm/factory.py`
- `backend/config.py`
- `backend/main.py`
- `backend/tools/excalidraw_builder.py`
- `frontend/app/page.tsx`
- `frontend/app/lib/sse.ts`
- `frontend/app/components/InputBar.tsx`

## Verification

- `uv run python -m compileall backend`
- `uv run python -c "from backend.agents.graph import build_graph; build_graph(); print('graph ok')"`
- `cd frontend && npx tsc --noEmit`

## Current Limitations

- Real multi-source research is not finished yet
- BYOK persistence and settings management are not complete yet
- Only Gemini is configured in the current local environment
- OpenAI, Anthropic, and Grok are wired in code but require user-provided API keys
- Canvas placement is improved structurally but not yet fully context-aware

## Next Changes For V2

- Add Context7 for latest framework/library docs
- Add Firecrawl for search and scraping
- Add Playwright MCP for dynamic websites
- Add GitHub MCP for repo-aware research
- Build proper BYOK settings storage and validation
- Improve scene planning for architecture diagrams, comparisons, and flowcharts
- Add smarter placement so new clusters expand existing ideas instead of only appending linearly
- Run a full end-to-end app smoke test with live providers
