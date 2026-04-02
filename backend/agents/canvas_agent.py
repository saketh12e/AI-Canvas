from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.state import AgentState
from backend.llm import get_llm, parse_json_object, parse_text_content
from backend.tools.excalidraw_builder import render_scene_to_elements

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "canvas_scene_skill.md"
_SKILL_CONTENT = _SKILL_PATH.read_text(encoding="utf-8")


def _fallback_scene(state: AgentState) -> dict:
    return {
        "title": state.get("canvas_title") or state["user_query"][:80],
        "layout": state.get("visual_goal", "concept_map"),
        "summary": state.get("explanation", ""),
        "key_points": state.get("key_concepts", []),
        "code_example": state.get("code_example", ""),
        "sources": state.get("sources", []),
        "connections": [
            {"from": "summary", "to": "concepts", "label": "supports"},
            {"from": "summary", "to": "code", "label": "applies"},
            {"from": "concepts", "to": "sources", "label": "references"},
        ],
    }


async def canvas_agent_node(state: AgentState) -> AgentState:
    llm = get_llm("canvas", state.get("selected_provider"))
    user_message = (
        f"User request: {state['user_query']}\n"
        f"Canvas title: {state.get('canvas_title', state['user_query'])}\n"
        f"Visual goal: {state.get('visual_goal', 'concept_map')}\n"
        f"Explanation:\n{state.get('explanation', '')}\n\n"
        f"Key concepts: {state.get('key_concepts', [])}\n"
        f"Code example:\n{state.get('code_example', '')[:2500]}\n"
        f"Sources: {state.get('sources', [])}\n"
    )
    response = await llm.ainvoke(
        [SystemMessage(content=_SKILL_CONTENT), HumanMessage(content=user_message)]
    )

    try:
        scene_spec = parse_json_object(parse_text_content(response))
    except Exception:
        scene_spec = _fallback_scene(state)

    elements = render_scene_to_elements(
        scene_spec,
        base_x=state.get("base_x", 0),
        base_y=state.get("base_y", 0),
    )

    return {
        **state,
        "scene_spec": scene_spec,
        "canvas_elements": elements,
    }
