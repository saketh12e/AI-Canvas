from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.state import AgentState
from backend.llm import get_llm, parse_json_object, parse_text_content

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "planner_skill.md"
_SKILL_CONTENT = _SKILL_PATH.read_text(encoding="utf-8")


def _fallback_plan(user_query: str) -> dict:
    lowered = user_query.lower()
    if any(word in lowered for word in ["architecture", "system design", "how does", "flow"]):
        visual_goal = "architecture"
    elif any(word in lowered for word in ["compare", "vs", "difference"]):
        visual_goal = "comparison"
    elif any(word in lowered for word in ["steps", "workflow", "process"]):
        visual_goal = "flowchart"
    else:
        visual_goal = "concept_map"

    return {
        "intent": "visual_explanation",
        "visual_goal": visual_goal,
        "canvas_title": user_query[:80],
        "research_queries": [user_query],
    }


async def planner_agent_node(state: AgentState) -> AgentState:
    llm = get_llm(
        "planner",
        state.get("selected_provider"),
        runtime_keys=state.get("runtime_keys", {}),
    )
    user_message = (
        f"User request: {state['user_query']}\n\n"
        "Return a single JSON object describing the best visual treatment."
    )
    messages = [
        SystemMessage(content=_SKILL_CONTENT),
        HumanMessage(content=user_message),
    ]
    response = await llm.ainvoke(messages)

    try:
        parsed = parse_json_object(parse_text_content(response))
    except Exception:
        parsed = _fallback_plan(state["user_query"])

    return {
        **state,
        "intent": parsed.get("intent", "visual_explanation"),
        "visual_goal": parsed.get("visual_goal", "concept_map"),
        "canvas_title": parsed.get("canvas_title", state["user_query"][:80]),
        "research_queries": parsed.get("research_queries") or [state["user_query"]],
        "messages": [*state.get("messages", []), HumanMessage(content=user_message), response],
        "error": None,
    }
