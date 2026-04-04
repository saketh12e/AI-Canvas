# V2 Complete

## Summary

This document captures the completed V2 milestone for the current development cycle.

V2 now includes:

- provider-aware model routing
- browser-local BYOK settings
- per-request runtime key overrides
- multi-source research
- connector readiness reporting
- connector planning and fallback
- GitHub repo-aware research

## What V2 Can Do

- Accept a prompt and classify it into a canvas-oriented task
- Research with Context7 and MCP docs by default
- Fall back to Firecrawl and Tavily when broader/current web research is needed
- Pull repo-level context from GitHub when the user references a GitHub repository
- Let the user supply runtime keys in the browser without editing tracked files
- Show provider and connector readiness before sending a request

## Main Technical Outcomes

- `planner -> research -> synthesis -> canvas` remains the core pipeline
- Research is now connector-driven instead of single-source
- The frontend can run in local BYOK mode with no committed secrets
- The backend supports request-scoped provider and connector keys

## Key Files

- `backend/agents/research_agent.py`
- `backend/tools/context7_tools.py`
- `backend/tools/web_research_tools.py`
- `backend/tools/github_research_tools.py`
- `backend/tools/research_registry.py`
- `backend/llm/factory.py`
- `backend/main.py`
- `frontend/app/components/SettingsPanel.tsx`
- `frontend/app/components/InputBar.tsx`
- `frontend/app/page.tsx`

## Remaining Future Work

These are now future-version items, not blockers for V2:

- Playwright connector for dynamic pages
- deeper GitHub code-level analysis
- stronger scene and layout intelligence
- broader live integration testing
