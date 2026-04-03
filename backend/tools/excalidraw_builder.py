import json
import uuid
from langchain_core.tools import tool


def _uid() -> str:
    return uuid.uuid4().hex[:6]


def _layout_positions(layout: str, base_x: int, base_y: int) -> dict[str, tuple[int, int]]:
    if layout == "flowchart":
        return {
            "title": (base_x, base_y - 110),
            "summary": (base_x + 220, base_y),
            "concepts": (base_x + 220, base_y + 320),
            "code": (base_x + 220, base_y + 620),
            "sources": (base_x + 760, base_y + 160),
        }

    if layout == "architecture":
        return {
            "title": (base_x, base_y - 110),
            "summary": (base_x, base_y),
            "concepts": (base_x + 460, base_y),
            "code": (base_x, base_y + 340),
            "sources": (base_x + 820, base_y + 40),
        }

    if layout == "comparison":
        return {
            "title": (base_x, base_y - 110),
            "summary": (base_x + 180, base_y),
            "concepts": (base_x, base_y + 280),
            "code": (base_x + 420, base_y + 280),
            "sources": (base_x + 840, base_y + 280),
        }

    return {
        "title": (base_x, base_y - 110),
        "summary": (base_x, base_y),
        "concepts": (base_x + 420, base_y),
        "code": (base_x, base_y + 320),
        "sources": (base_x + 800, base_y + 10),
    }


def render_scene_to_elements(scene: dict, base_x: int = 0, base_y: int = 0) -> list[dict]:
    h = _uid()
    shapes = []
    layout = str(scene.get("layout", "concept_map"))
    positions = _layout_positions(layout, base_x, base_y)
    title = str(scene.get("title", "AI Canvas"))
    summary = str(scene.get("summary", ""))[:900]
    key_points = [str(item) for item in scene.get("key_points", [])[:8]]
    code_example = str(scene.get("code_example", ""))
    sources = [str(item) for item in scene.get("sources", [])[:6]]

    shapes.append({
        "id": f"shape:title-{h}",
        "type": "geo",
        "x": positions["title"][0],
        "y": positions["title"][1],
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
        "x": positions["summary"][0],
        "y": positions["summary"][1],
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
        "x": positions["concepts"][0],
        "y": positions["concepts"][1],
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
        "x": positions["code"][0],
        "y": positions["code"][1],
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
        "x": positions["sources"][0],
        "y": positions["sources"][1],
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
        "x": positions["summary"][0] + 360,
        "y": positions["summary"][1] + 110,
        "props": {
            "start": {"type": "point", "x": 0, "y": 0},
            "end":   {
                "type": "point",
                "x": positions["concepts"][0] - positions["summary"][0] - 360,
                "y": positions["concepts"][1] - positions["summary"][1],
            },
            "color": "grey",
        },
    })

    shapes.append({
        "id": f"shape:arrow2-{h}",
        "type": "arrow",
        "x": positions["concepts"][0] + 100,
        "y": positions["concepts"][1] + 220,
        "props": {
            "start": {"type": "point", "x": 0, "y": 0},
            "end":   {
                "type": "point",
                "x": positions["code"][0] - positions["concepts"][0] - 100,
                "y": positions["code"][1] - positions["concepts"][1] - 220,
            },
            "color": "grey",
        },
    })

    shapes.append({
        "id": f"shape:arrow3-{h}",
        "type": "arrow",
        "x": positions["concepts"][0] + 300,
        "y": positions["concepts"][1] + 120,
        "props": {
            "start": {"type": "point", "x": 0, "y": 0},
            "end":   {
                "type": "point",
                "x": positions["sources"][0] - positions["concepts"][0] - 300,
                "y": positions["sources"][1] - positions["concepts"][1] - 120,
            },
            "color": "grey",
        },
    })

    return shapes


@tool
def build_elements(scene_json: str, base_x: int = 0, base_y: int = 0) -> str:
    """Build tldraw shapes from a scene specification JSON string."""
    scene = json.loads(scene_json)
    return json.dumps(render_scene_to_elements(scene, base_x=base_x, base_y=base_y))
