from typing import Any, Literal, TypedDict


class EvidenceItem(TypedDict, total=False):
    title: str
    url: str
    content: str
    source_type: str


class SceneSpec(TypedDict, total=False):
    title: str
    layout: str
    summary: str
    key_points: list[str]
    code_example: str
    sources: list[str]
    connections: list[dict[str, str]]


class AgentState(TypedDict, total=False):
    user_query: str
    session_id: str
    base_x: int
    base_y: int
    selected_provider: Literal["gemini", "openai", "anthropic", "grok"] | str

    intent: str
    visual_goal: str
    canvas_title: str
    research_queries: list[str]

    evidence: list[EvidenceItem]
    raw_doc_content: str
    sources: list[str]

    explanation: str
    key_concepts: list[str]
    code_example: str

    scene_spec: SceneSpec
    canvas_elements: list[dict]

    messages: list[Any]
    error: str | None
