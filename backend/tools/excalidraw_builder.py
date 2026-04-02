import json
import uuid
from langchain_core.tools import tool


def _uid() -> str:
    return uuid.uuid4().hex[:6]


def render_scene_to_elements(scene: dict, base_x: int = 0, base_y: int = 0) -> list[dict]:
    h = _uid()
    shapes = []
    title = str(scene.get("title", "AI Canvas"))
    summary = str(scene.get("summary", ""))[:900]
    key_points = [str(item) for item in scene.get("key_points", [])[:8]]
    code_example = str(scene.get("code_example", ""))
    sources = [str(item) for item in scene.get("sources", [])[:6]]

    shapes.append({
        "id": f"shape:title-{h}",
        "type": "geo",
        "x": base_x,
        "y": base_y - 110,
        "props": {
            "geo": "rectangle",
            "w": 420,
            "h": 72,
            "text": title,
            "fill": "semi",
            "color": "yellow",
            "size": "l",
        },
    })

    shapes.append({
        "id": f"shape:summary-{h}",
        "type": "geo",
        "x": base_x,
        "y": base_y,
        "props": {
            "geo": "rectangle",
            "w": 360,
            "h": 260,
            "text": summary,
            "fill": "semi",
            "color": "blue",
            "size": "m",
        },
    })

    concepts_text = "\n• ".join([""] + key_points).strip()
    shapes.append({
        "id": f"shape:concepts-{h}",
        "type": "geo",
        "x": base_x + 420,
        "y": base_y,
        "props": {
            "geo": "rectangle",
            "w": 300,
            "h": 240,
            "text": concepts_text,
            "fill": "semi",
            "color": "green",
            "size": "m",
        },
    })

    code_lines = "\n".join(code_example.splitlines()[:8])
    shapes.append({
        "id": f"shape:code-{h}",
        "type": "geo",
        "x": base_x,
        "y": base_y + 320,
        "props": {
            "geo": "rectangle",
            "w": 720,
            "h": 260,
            "text": code_lines,
            "fill": "semi",
            "color": "grey",
            "size": "s",
        },
    })

    shapes.append({
        "id": f"shape:sources-{h}",
        "type": "geo",
        "x": base_x + 800,
        "y": base_y + 10,
        "props": {
            "geo": "rectangle",
            "w": 300,
            "h": 220,
            "text": "\n• ".join(["Sources"] + sources),
            "fill": "semi",
            "color": "light-blue",
            "size": "s",
        },
    })

    shapes.append({
        "id": f"shape:arrow1-{h}",
        "type": "arrow",
        "x": base_x + 360,
        "y": base_y + 110,
        "props": {
            "start": {"type": "point", "x": 0, "y": 0},
            "end":   {"type": "point", "x": 60, "y": 0},
            "color": "grey",
        },
    })

    shapes.append({
        "id": f"shape:arrow2-{h}",
        "type": "arrow",
        "x": base_x + 520,
        "y": base_y + 240,
        "props": {
            "start": {"type": "point", "x": 0, "y": 0},
            "end":   {"type": "point", "x": -120, "y": 110},
            "color": "grey",
        },
    })

    shapes.append({
        "id": f"shape:arrow3-{h}",
        "type": "arrow",
        "x": base_x + 720,
        "y": base_y + 120,
        "props": {
            "start": {"type": "point", "x": 0, "y": 0},
            "end":   {"type": "point", "x": 80, "y": 0},
            "color": "grey",
        },
    })

    return shapes


@tool
def build_elements(scene_json: str, base_x: int = 0, base_y: int = 0) -> str:
    """Build tldraw shapes from a scene specification JSON string."""
    scene = json.loads(scene_json)
    return json.dumps(render_scene_to_elements(scene, base_x=base_x, base_y=base_y))
