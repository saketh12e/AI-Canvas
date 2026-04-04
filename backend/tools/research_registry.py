from backend.config import settings


def build_connector_plan(
    query: str,
    visual_goal: str,
    context7_count: int,
    has_github_repo_hint: bool,
) -> list[str]:
    lowered = query.lower()
    plan: list[str] = []

    if has_github_repo_hint:
        plan.append("github")

    if any(token in lowered for token in ["langchain", "langgraph", "langsmith", "mcp"]):
        plan.extend(["mcpdoc", "context7"])
    else:
        plan.append("context7")

    if visual_goal in {"architecture", "comparison", "flowchart"}:
        plan.extend(["firecrawl", "tavily"])
    elif any(token in lowered for token in ["latest", "recent", "today", "news", "current"]):
        plan.extend(["firecrawl", "tavily"])
    elif context7_count < 2:
        plan.extend(["firecrawl", "tavily"])

    deduped: list[str] = []
    for connector in plan:
        if connector not in deduped:
            deduped.append(connector)
    return deduped


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
        {
            "key": "github",
            "label": "GitHub",
            "available": True,
            "reason": "Public GitHub REST access, token optional for higher limits",
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
