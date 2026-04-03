import asyncio
import json
from typing import Any
from urllib.parse import quote_plus
from urllib.request import urlopen

from backend.agents.state import EvidenceItem

CONTEXT7_SEARCH_URL = "https://context7.com/api/v2/libs/search"
CONTEXT7_CONTEXT_URL = "https://context7.com/api/v2/context"

LIBRARY_HINTS: dict[str, list[str]] = {
    "next.js": ["nextjs", "next js", "app router"],
    "react": ["react", "hooks", "react app"],
    "fastapi": ["fastapi", "uvicorn", "pydantic api"],
    "langgraph": ["langgraph", "stategraph", "checkpointer"],
    "langchain": ["langchain", "agent", "retriever"],
    "langsmith": ["langsmith", "trace", "evaluation"],
    "openai": ["openai", "responses api", "chatgpt api"],
    "anthropic": ["anthropic", "claude", "messages api"],
    "tldraw": ["tldraw", "infinite canvas", "createShapes"],
    "supabase": ["supabase", "postgres", "realtime"],
}


def _fetch_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


async def search_context7_library(library_name: str, query: str) -> dict[str, Any] | None:
    url = (
        f"{CONTEXT7_SEARCH_URL}?libraryName={quote_plus(library_name)}"
        f"&query={quote_plus(query)}"
    )
    payload = await asyncio.to_thread(_fetch_json, url)
    results = payload.get("results") or []
    if not results:
        return None

    normalized = library_name.lower().replace(".", "").replace(" ", "")
    preferred = None
    for result in results:
        title = str(result.get("title", "")).lower().replace(".", "").replace(" ", "")
        result_id = str(result.get("id", "")).lower()
        if normalized in title or normalized in result_id:
            preferred = result
            break
    return preferred or results[0]


async def fetch_context7_context(library_id: str, query: str) -> str:
    url = (
        f"{CONTEXT7_CONTEXT_URL}?libraryId={quote_plus(library_id)}"
        f"&query={quote_plus(query)}&type=txt"
    )
    with urlopen(url, timeout=20) as response:
        return await asyncio.to_thread(response.read)


async def fetch_context7_text(library_id: str, query: str) -> str:
    url = (
        f"{CONTEXT7_CONTEXT_URL}?libraryId={quote_plus(library_id)}"
        f"&query={quote_plus(query)}&type=txt"
    )
    with urlopen(url, timeout=20) as response:
        body = await asyncio.to_thread(response.read)
    return body.decode("utf-8")


def detect_context7_candidates(query: str, research_queries: list[str]) -> list[str]:
    haystack = " ".join([query, *research_queries]).lower()
    candidates: list[str] = []
    for library_name, hints in LIBRARY_HINTS.items():
        if any(hint in haystack for hint in hints):
            candidates.append(library_name)

    if not candidates:
        return ["next.js", "react", "fastapi"]
    return candidates[:3]


async def get_context7_evidence(
    query: str,
    research_queries: list[str],
    max_items: int = 3,
) -> list[EvidenceItem]:
    candidates = detect_context7_candidates(query, research_queries)
    evidence: list[EvidenceItem] = []

    for library_name in candidates[:max_items]:
        try:
            search_result = await search_context7_library(library_name, query)
        except Exception:
            continue

        if not search_result:
            continue

        library_id = str(search_result.get("id", ""))
        title = str(search_result.get("title", library_name))
        if not library_id:
            continue

        try:
            content = await fetch_context7_text(library_id, query)
        except Exception:
            continue

        evidence.append(
            {
                "title": title,
                "url": f"https://context7.com{library_id}",
                "content": content,
                "source_type": "context7",
            }
        )

    return evidence
