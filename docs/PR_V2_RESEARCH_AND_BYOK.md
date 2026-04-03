# V2 Research And BYOK

## Summary

This update moves AI Canvas from a V1 architecture foundation into a more usable V2 development state.

The biggest changes in this slice are:

- multi-source research connectors
- runtime capability reporting
- browser-local BYOK settings
- per-request runtime key overrides

This means the app can now:

- combine Context7, MCP docs, Firecrawl, and Tavily as research sources
- show which providers and connectors are currently ready
- accept keys from the browser without requiring permanent `.env` edits

## What Was Built

- Added Context7-backed research connector logic
- Added optional Firecrawl and Tavily web research connectors
- Added connector registry and runtime capability reporting
- Added browser-local settings panel for API keys
- Added per-request runtime key flow from frontend to backend
- Updated all core agents to honor runtime provider keys
- Improved the frontend status area so readiness and source usage are visible

## Main Files

- `backend/tools/context7_tools.py`
- `backend/tools/web_research_tools.py`
- `backend/tools/research_registry.py`
- `backend/agents/research_agent.py`
- `backend/llm/factory.py`
- `backend/main.py`
- `frontend/app/components/SettingsPanel.tsx`
- `frontend/app/components/InputBar.tsx`
- `frontend/app/lib/sse.ts`
- `frontend/app/page.tsx`

## Verification

- `uv run python -m compileall backend`
- `cd frontend && npx tsc --noEmit`
- runtime capability smoke tests for configured vs runtime-injected keys

## Notes

- No real API keys were added to the repository
- BYOK values are stored in browser localStorage only
- Runtime keys are sent only with user requests
- `.env` remains optional for testing

## What Still Comes Next

- connector ranking and fallback logic
- GitHub connector
- Playwright connector
- stronger scene planning and layout behavior
- end-to-end live testing with real keys
