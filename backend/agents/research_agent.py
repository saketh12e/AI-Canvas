import asyncio

import asyncio

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from backend.agents.state import AgentState, EvidenceItem
from backend.llm.factory import get_llm
from backend.tools.context7_tools import get_context7_evidence
from backend.tools.github_research_tools import detect_github_repo, get_github_repo_evidence
from backend.tools.link_resolver import get_links_to_resolve
from backend.tools.mcpdoc_tools import get_mcp_tools
from backend.tools.research_registry import build_connector_plan, summarize_research_report
from backend.tools.web_research_tools import get_firecrawl_evidence, get_tavily_evidence

SYSTEM_PROMPT = """You are the research agent for an AI canvas application.

Use the available tools to gather the most relevant and current documentation you can.
Prefer official docs and fetch only the pages that directly help answer the user's request.
"""


def _is_langchain_ecosystem_query(query: str, research_queries: list[str]) -> bool:
    haystack = " ".join([query, *research_queries]).lower()
    return any(
        token in haystack
        for token in ["langchain", "langgraph", "langsmith", "mcp", "agent"]
    )


def _merge_evidence(*evidence_sets: list[EvidenceItem]) -> list[EvidenceItem]:
    merged: list[EvidenceItem] = []
    seen: set[tuple[str, str]] = set()
    for evidence in evidence_sets:
        for item in evidence:
            key = (item.get("source_type", ""), item.get("url", ""))
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


async def research_agent_node(state: AgentState) -> AgentState:
    research_queries = state.get("research_queries") or [state["user_query"]]
    runtime_keys = state.get("runtime_keys", {})
    context7_evidence = await get_context7_evidence(state["user_query"], research_queries)
    github_evidence: list[EvidenceItem] = []
    web_evidence: list[EvidenceItem] = []
    github_repo_hint = detect_github_repo(state["user_query"]) is not None
    connector_plan = build_connector_plan(
        state["user_query"],
        state.get("visual_goal", "concept_map"),
        len(context7_evidence),
        has_github_repo_hint=github_repo_hint,
    )

    mcp_evidence: list[EvidenceItem] = []
    messages = []

    if "github" in connector_plan:
        github_evidence = await get_github_repo_evidence(
            state["user_query"],
            runtime_keys=runtime_keys,
        )

    if "mcpdoc" in connector_plan and _is_langchain_ecosystem_query(state["user_query"], research_queries):
        tools = get_mcp_tools()
        llm = get_llm(
            "research",
            state.get("selected_provider"),
            runtime_keys=runtime_keys,
        ).bind_tools(tools)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"User request: {state['user_query']}\n"
                    f"Intent: {state.get('intent', 'visual_explanation')}\n"
                    f"Visual goal: {state.get('visual_goal', 'concept_map')}\n"
                    f"Research queries: {research_queries}"
                )
            ),
        ]

        tool_map = {tool.name: tool for tool in tools}
        seen_urls: set[str] = set()

        for _ in range(6):
            response = await llm.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                tool = tool_map.get(tool_call["name"])
                if tool is None:
                    continue

                result = await tool.ainvoke(tool_call["args"])
                result_text = str(result)
                messages.append(ToolMessage(content=result_text, tool_call_id=tool_call["id"]))

                if tool_call["name"] != "fetch_docs":
                    continue

                url = tool_call["args"].get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    mcp_evidence.append(
                        {
                            "title": url.rsplit("/", 1)[-1] or url,
                            "url": url,
                            "content": result_text,
                            "source_type": "mcpdoc",
                            "query_used": state["user_query"],
                        }
                    )

        if mcp_evidence:
            fetch_tool = tool_map.get("fetch_docs")
            linked_urls = get_links_to_resolve(
                mcp_evidence[0]["content"],
                state["user_query"],
                max_links=2,
            )
            for url in linked_urls:
                if not fetch_tool or url in seen_urls:
                    continue
                try:
                    linked_content = await fetch_tool.ainvoke({"url": url})
                except Exception:
                    continue
                linked_text = str(linked_content)
                seen_urls.add(url)
                mcp_evidence.append(
                    {
                        "title": url.rsplit("/", 1)[-1] or url,
                        "url": url,
                        "content": linked_text,
                        "source_type": "mcpdoc",
                        "query_used": state["user_query"],
                    }
                )

    current_evidence = _merge_evidence(
        [
            {**item, "query_used": state["user_query"]}
            for item in context7_evidence
        ],
        [
            {**item, "query_used": state["user_query"]}
            for item in github_evidence
        ],
        mcp_evidence,
    )

    if any(connector in connector_plan for connector in ["firecrawl", "tavily"]) and len(current_evidence) < 3:
        firecrawl_evidence, tavily_evidence = await asyncio.gather(
            get_firecrawl_evidence(state["user_query"], runtime_keys=runtime_keys),
            get_tavily_evidence(state["user_query"], runtime_keys=runtime_keys),
        )
        web_evidence = _merge_evidence(firecrawl_evidence, tavily_evidence)

    normalized_context7 = [
        {
            **item,
            "query_used": state["user_query"],
        }
        for item in context7_evidence
    ]
    normalized_web = [
        {
            **item,
            "query_used": state["user_query"],
        }
        for item in web_evidence
    ]
    normalized_github = [
        {
            **item,
            "query_used": state["user_query"],
        }
        for item in github_evidence
    ]
    evidence = _merge_evidence(normalized_context7, normalized_github, normalized_web, mcp_evidence)
    combined_content = "\n\n---\n\n".join(item["content"] for item in evidence)
    research_report = summarize_research_report(evidence)
    research_report["connector_plan"] = connector_plan

    return {
        **state,
        "messages": messages or state.get("messages", []),
        "evidence": evidence,
        "raw_doc_content": combined_content,
        "sources": [item["url"] for item in evidence if item.get("url")],
        "source_details": evidence,
        "research_report": research_report,
        "connector_plan": connector_plan,
    }
