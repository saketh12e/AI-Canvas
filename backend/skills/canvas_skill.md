# Canvas Skill — tldraw Shape Output

## Your job
You receive explanation, key_concepts, and code_example from the Explainer Agent.
Call the `build_elements` tool with those values to generate tldraw shapes for the canvas.

## What build_elements produces
Three connected cards rendered on the tldraw infinite canvas:

### geo shape (boxes/cards):
```json
{
  "id": "shape:card1-abc123",
  "type": "geo",
  "x": 0,
  "y": 0,
  "props": {
    "geo": "rectangle",
    "w": 320,
    "h": 240,
    "text": "content here",
    "fill": "semi",
    "color": "blue",
    "size": "m"
  }
}
```

Valid color values: `"blue"` | `"green"` | `"grey"` | `"yellow"` | `"violet"` | `"light-blue"`

### arrow shape (connections between cards):
```json
{
  "id": "shape:arrow1-abc123",
  "type": "arrow",
  "x": 320,
  "y": 120,
  "props": {
    "start": { "type": "point", "x": 0, "y": 0 },
    "end":   { "type": "point", "x": 60, "y": 0 },
    "color": "grey"
  }
}
```

## Card layout — THREE cards per query
Card 1 — Concept Card (blue, x=base_x): explanation text, w=320, h=240
Card 2 — Key Concepts Card (green, x=base_x+380): key_concepts as bullet list, w=280, h=200
Card 3 — Code Card (grey, x=base_x+710): first 8 lines of code_example, w=360, h=280
Arrow 1: connects Card 1 → Card 2
Arrow 2: connects Card 2 → Card 3

## Rules
- Call `build_elements` with the exact values from the state: explanation, key_concepts, code_example, base_x, base_y
- Do not modify or summarize the content before passing it to the tool
- Every shape id must be unique — the builder appends a short hash automatically
