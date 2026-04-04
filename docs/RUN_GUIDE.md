# Run Guide

## Local Startup

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

Open:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Runtime capabilities: `http://localhost:8000/runtime/capabilities`

## Recommended Way To Test

You can run the app in two different ways.

### Option 1: `.env` driven

Copy `.env.example` to `.env` and add whichever keys you want to test.

### Option 2: Browser-local BYOK

Start the backend and frontend with no `.env`.

Then:

1. Open the app
2. Click `Settings`
3. Paste the provider keys you want to test
4. Optionally paste Firecrawl, Tavily, or GitHub token values
5. Choose a provider from the prompt bar
6. Submit a query

## Useful Test Prompts

### General docs query

```text
Explain Next.js app router architecture for a chat app
```

### Current web-aware query

```text
What is the latest recommended way to structure a FastAPI + Next.js chat app?
```

### GitHub repo-aware query

```text
Explain github.com/vercel/next.js architecture as a visual canvas
```

### LangGraph ecosystem query

```text
Explain LangGraph checkpointing and how it fits into a production agent system
```

## Validation Commands

### Backend compile

```bash
uv run python -m compileall backend
```

### Frontend type-check

```bash
cd frontend
npx tsc --noEmit
```

## Expected Runtime Behavior

- If a provider has no key, the UI should warn you before sending the request
- If browser-local settings contain a key, the provider badge should show as ready
- Context7 and MCP docs should appear as built-in connectors
- Firecrawl and Tavily should activate when their keys are provided
- GitHub connector should work for public repositories even without a token, but rate limits will be lower
