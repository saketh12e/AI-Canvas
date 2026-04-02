from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from backend.agents.state import AgentState, EvidenceItem
from backend.llm.factory import get_llm
from backend.tools.link_resolver import get_links_to_resolve
from backend.tools.mcpdoc_tools import get_mcp_tools

SYSTEM_PROMPT = """You are the research agent for an AI canvas application.

Use the available tools to gather the most relevant and current documentation you can.
Prefer official docs and fetch only the pages that directly help answer the user's request.
"""


async def research_agent_node(state: AgentState) -> AgentState:
    tools = get_mcp_tools()
    llm = get_llm("research", state.get("selected_provider")).bind_tools(tools)

    research_queries = state.get("research_queries") or [state["user_query"]]
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
    evidence: list[EvidenceItem] = []
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
                evidence.append(
                    {
                        "title": url.rsplit("/", 1)[-1] or url,
                        "url": url,
                        "content": result_text,
                        "source_type": "mcpdoc",
                    }
                )

    if evidence:
        fetch_tool = tool_map.get("fetch_docs")
        linked_urls = get_links_to_resolve(evidence[0]["content"], state["user_query"], max_links=2)
        for url in linked_urls:
            if not fetch_tool or url in seen_urls:
                continue
            try:
                linked_content = await fetch_tool.ainvoke({"url": url})
            except Exception:
                continue
            linked_text = str(linked_content)
            seen_urls.add(url)
            evidence.append(
                {
                    "title": url.rsplit("/", 1)[-1] or url,
                    "url": url,
                    "content": linked_text,
                    "source_type": "mcpdoc",
                }
            )

    combined_content = "\n\n---\n\n".join(item["content"] for item in evidence)

    return {
        **state,
        "evidence": evidence,
        "raw_doc_content": combined_content,
        "sources": [item["url"] for item in evidence if item.get("url")],
    }
