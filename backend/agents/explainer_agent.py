from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

from backend.agents.state import AgentState
from backend.llm import get_llm, parse_json_object, parse_text_content

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "synthesis_skill.md"
_SKILL_CONTENT = _SKILL_PATH.read_text(encoding="utf-8")


async def synthesis_agent_node(state: AgentState) -> AgentState:
    llm = get_llm("synthesis", state.get("selected_provider"))
    evidence = state.get("evidence", [])
    evidence_blocks = []
    for item in evidence[:4]:
        evidence_blocks.append(
            f"TITLE: {item.get('title', 'Untitled')}\n"
            f"URL: {item.get('url', '')}\n"
            f"CONTENT:\n{item.get('content', '')[:4000]}"
        )

    user_message = (
        f"User request: {state['user_query']}\n"
        f"Intent: {state.get('intent', 'visual_explanation')}\n"
        f"Visual goal: {state.get('visual_goal', 'concept_map')}\n"
        f"Canvas title: {state.get('canvas_title', state['user_query'])}\n\n"
        f"Sources: {state.get('sources', [])}\n\n"
        f"---EVIDENCE START---\n{'\n\n---\n\n'.join(evidence_blocks)}\n---EVIDENCE END---\n\n"
        "Create a structured explanation for the AI canvas.\n"
        f"Output only valid JSON."
    )

    messages = [
        SystemMessage(content=_SKILL_CONTENT),
        *state.get("messages", []),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)
    raw_text = parse_text_content(response)

    try:
        parsed = parse_json_object(raw_text)
        return {
            **state,
            "explanation": parsed.get("explanation", ""),
            "key_concepts": parsed.get("key_concepts", []),
            "code_example": parsed.get("code_example", ""),
            "sources": parsed.get("sources", state.get("sources", [])),
            "messages": [*state.get("messages", []), HumanMessage(content=user_message), response],
            "error": None,
        }
    except Exception as e:
        return {
            **state,
            "explanation": f"Failed to parse explanation JSON: {e}\n\nRaw response:\n{raw_text[:500]}",
            "key_concepts": [],
            "code_example": "",
            "sources": state.get("sources", []),
            "error": f"JSON parse error: {e}",
        }


async def explainer_agent_node(state: AgentState) -> AgentState:
    return await synthesis_agent_node(state)
