# Excalidraw Canvas Skill

## Your role
Convert structured explanation data into Excalidraw elements[] JSON.
You must produce a valid JSON array of Excalidraw element objects.

## Element types you will use

### Text card (for explanation)
{
  "type": "text",
  "id": "unique_id_string",
  "x": number,
  "y": number,
  "width": 400,
  "height": auto,
  "text": "content here",
  "fontSize": 16,
  "fontFamily": 1,
  "textAlign": "left",
  "strokeColor": "#1e1e2e",
  "backgroundColor": "#e0f2fe",
  "fillStyle": "solid"
}

### Code card (for code_example)
{
  "type": "text",
  "id": "unique_id_string",
  "x": number,
  "y": number,
  "width": 500,
  "height": auto,
  "text": "code content",
  "fontSize": 14,
  "fontFamily": 3,
  "strokeColor": "#1e1e2e",
  "backgroundColor": "#1e1e2e",
  "fillStyle": "solid"
}

### Concept node (for each key_concept)
{
  "type": "rectangle",
  "id": "unique_id_string",
  "x": number,
  "y": number,
  "width": 160,
  "height": 44,
  "strokeColor": "#3b82f6",
  "backgroundColor": "#dbeafe",
  "fillStyle": "solid",
  "roundness": {"type": 3}
}

### Arrow (connecting concept nodes)
{
  "type": "arrow",
  "id": "unique_id_string",
  "x": number,
  "y": number,
  "width": number,
  "height": number,
  "points": [[0, 0], [dx, dy]],
  "strokeColor": "#3b82f6"
}

## Layout rules
- Explanation card: top-left of cluster, x=base_x, y=base_y
- Code card: directly below explanation, y=base_y+explanation_height+20
- Concept nodes: arranged horizontally to the right, x=base_x+440, y=base_y
- Each cluster occupies ~900x600px
- Next cluster placed at base_x+1000 to the right of the previous one
- All IDs must be unique strings (use short UUID-style: "el_001", "el_002", etc.)
- base_x and base_y are provided as input — use them exactly

## Output format
Return ONLY a valid JSON array. No markdown. No explanation text. Just the array.
