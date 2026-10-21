# Canvas schema and layout

## Nodes

Every node requires:

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Unique node identifier |
| `type` | string | `text`, `file`, `link`, or `group` |
| `x`, `y` | integer | Top-left coordinates |
| `width`, `height` | integer | Dimensions in pixels |

Use positive dimensions for usable nodes. Nodes may have a `color`: a hex string such as `"#8855cc"` or a preset string `"1"` through `"6"`. Preset appearance is application-defined.

Additional fields depend on the type:

| Type | Required | Optional |
| --- | --- | --- |
| `text` | `text`: Markdown string | — |
| `file` | `file`: path string | `subpath`: heading/block reference starting with `#` |
| `link` | `url`: URL string | — |
| `group` | — | `label`, `background`, `backgroundStyle` |

`backgroundStyle` is `cover`, `ratio`, or `repeat`. Group backgrounds refer to images; group membership is determined by geometry, not an explicit list of children.

## Edges

Every edge requires its own unique string `id`, plus `fromNode` and `toNode` identifying existing nodes. Optional fields:

- `fromSide`, `toSide`: `top`, `right`, `bottom`, or `left`.
- `fromEnd`, `toEnd`: `none` or `arrow`; defaults are `none` and `arrow`, respectively.
- `label`: text displayed on the edge.
- `color`: the same representation used by nodes.

Preserve existing IDs and generate non-colliding IDs for additions. Validate node and edge identifier uniqueness and ensure each endpoint resolves to a node.

## Example

```json
{
  "nodes": [
    {
      "id": "group",
      "type": "group",
      "x": -40,
      "y": -40,
      "width": 760,
      "height": 300,
      "label": "Overview"
    },
    {
      "id": "summary",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 300,
      "height": 200,
      "text": "# Overview\n\nA short description."
    },
    {
      "id": "source",
      "type": "link",
      "x": 380,
      "y": 0,
      "width": 300,
      "height": 200,
      "url": "https://example.com"
    }
  ],
  "edges": [
    {
      "id": "reference",
      "fromNode": "summary",
      "fromSide": "right",
      "toNode": "source",
      "toSide": "left",
      "label": "Source"
    }
  ]
}
```

## Layout and checks

Coordinates grow rightward and downward. Array order places earlier nodes underneath later ones; preserve that order unless changing stacking is intended. A group usually precedes the nodes it visually contains.

Space nodes according to content size, using a consistent gap and group padding. Keep the existing board's conventions rather than enforcing fixed dimensions.

Parse the JSON and check each type's required fields. Reject dangling edge endpoints and duplicate IDs. Preserve unsupported fields during edits instead of stripping them as part of validation. Referenced files and images need separate existence checks in the configured vault.
