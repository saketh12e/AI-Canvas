from backend.config import settings


def get_research_connector_capabilities(
    runtime_keys: dict[str, str] | None = None,
) -> list[dict[str, str | bool]]:
    return [
        {
            "key": "context7",
            "label": "Context7",
            "available": True,
            "reason": "Built-in docs connector",
        },
        {
            "key": "mcpdoc",
            "label": "MCP Docs",
            "available": True,
            "reason": "Server-managed documentation MCP",
        },
        {
            "key": "firecrawl",
            "label": "Firecrawl",
            "available": bool((runtime_keys or {}).get("firecrawl_api_key") or settings.firecrawl_api_key),
            "reason": ""
            if ((runtime_keys or {}).get("firecrawl_api_key") or settings.firecrawl_api_key)
            else "FIRECRAWL_API_KEY required",
        },
        {
            "key": "tavily",
            "label": "Tavily",
            "available": bool((runtime_keys or {}).get("tavily_api_key") or settings.tavily_api_key),
            "reason": ""
            if ((runtime_keys or {}).get("tavily_api_key") or settings.tavily_api_key)
            else "TAVILY_API_KEY required",
        },
    ]


def summarize_research_report(source_details: list[dict]) -> dict:
    connectors_used = sorted(
        {
            item.get("source_type", "")
            for item in source_details
            if item.get("source_type")
        }
    )
    return {
        "connectors_used": connectors_used,
        "source_count": len(source_details),
    }
