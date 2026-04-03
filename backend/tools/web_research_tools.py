import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.agents.state import EvidenceItem
from backend.config import settings


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalize_content(*parts: str) -> str:
    normalized = [part.strip() for part in parts if part and part.strip()]
    return "\n\n".join(normalized)


async def get_firecrawl_evidence(
    query: str,
    max_items: int = 2,
    runtime_keys: dict[str, str] | None = None,
) -> list[EvidenceItem]:
    api_key = (runtime_keys or {}).get("firecrawl_api_key") or settings.firecrawl_api_key
    if not api_key:
        return []

    payload = {
        "query": query,
        "limit": max_items,
        "sources": ["web"],
        "ignoreInvalidURLs": True,
        "scrapeOptions": {
            "formats": [{"type": "markdown"}],
        },
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{settings.firecrawl_base_url.rstrip('/')}/search"

    try:
        response = await asyncio.to_thread(_post_json, url, payload, headers)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    results = response.get("data", {}).get("web") or []
    evidence: list[EvidenceItem] = []
    for item in results[:max_items]:
        url_value = str(item.get("url", ""))
        markdown = str(item.get("markdown", ""))
        description = str(item.get("description", ""))
        if not url_value:
            continue
        evidence.append(
            {
                "title": str(item.get("title", url_value)),
                "url": url_value,
                "content": _normalize_content(markdown, description),
                "source_type": "firecrawl",
            }
        )
    return evidence


async def get_tavily_evidence(
    query: str,
    max_items: int = 2,
    runtime_keys: dict[str, str] | None = None,
) -> list[EvidenceItem]:
    api_key = (runtime_keys or {}).get("tavily_api_key") or settings.tavily_api_key
    if not api_key:
        return []

    payload = {
        "query": query,
        "search_depth": "basic",
        "max_results": max_items,
        "topic": "general",
        "include_answer": False,
        "include_raw_content": "markdown",
        "include_domains": [],
        "exclude_domains": [],
        "include_favicon": False,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{settings.tavily_base_url.rstrip('/')}/search"

    try:
        response = await asyncio.to_thread(_post_json, url, payload, headers)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    results = response.get("results") or []
    evidence: list[EvidenceItem] = []
    for item in results[:max_items]:
        url_value = str(item.get("url", ""))
        content = str(item.get("raw_content") or item.get("content") or "")
        if not url_value:
            continue
        evidence.append(
            {
                "title": str(item.get("title", url_value)),
                "url": url_value,
                "content": _normalize_content(content),
                "source_type": "tavily",
            }
        )
    return evidence
