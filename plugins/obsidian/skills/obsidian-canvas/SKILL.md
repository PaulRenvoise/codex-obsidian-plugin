---
name: obsidian-canvas
description: Create and edit Obsidian .canvas files using JSON Canvas nodes, edges, groups, and layout coordinates. Use when reading or modifying an Obsidian Canvas board.
---

# Obsidian Canvas

Obsidian stores Canvas boards as JSON Canvas documents with `.canvas` extensions. This skill describes the format; derive the board's content and organization from the user's request.

For files in the configured vault, follow [obsidian-vault](../obsidian-vault/SKILL.md) and its CLI wrapper. Preserve the configured vault and read-only setting. Prepare standalone drafts in the task workspace when appropriate; do not use direct file writes to bypass vault access controls.

## Document model

A document contains `nodes` and `edges` arrays, both optional in the format. Use `{"nodes": [], "edges": []}` for an empty board. Nodes can contain text, reference files or URLs, or visually group other nodes. Edges connect node IDs.

Read [schema](references/SCHEMA.md) for required fields, node types, connections, and layout. IDs are unique strings; 16-character hexadecimal strings are a convenient convention, not a schema requirement.

## Editing and layout

Read and parse an existing board before changing it. Preserve unrelated nodes, edges, IDs, unknown fields, and array order. Array order controls node stacking. Modify objects by ID rather than rebuilding the board from their visible labels.

Groups are geometric containers: place contained nodes within the group's rectangle rather than inventing a parent or children field. Keep existing layout unless the requested edit requires moving it. Allow room for labels and avoid accidental overlap; negative coordinates are valid.

File nodes should reference existing vault-relative paths, including extensions, unless the user explicitly wants placeholders. A node referencing a note does not contain that note's contents. Edge endpoint IDs must identify nodes, not file paths or edge IDs.

## Serialization and validation

Serialize with a JSON library rather than concatenating strings. Distinguish actual text newlines from literal backslash sequences. CLI content arguments can undergo their own escape processing; account for that layer and compare the parsed read-back content with the intended document.

Before saving, check required fields and types, unique IDs, and edge endpoints. When removing a node, remove or retarget its incident edges as appropriate. Save the complete JSON document with its `.canvas` extension through supported vault file operations, without an outer Markdown fence.

Read and parse the saved board to verify the result. Check layout in Obsidian when visual verification is needed and available; JSON validation alone cannot establish readability or rendering.

Adapted from [Kepano's json-canvas skill](https://github.com/kepano/obsidian-skills/tree/3ccff5338ea700537839b21900aa5358a0402c98/skills/json-canvas), renamed to `obsidian-canvas` for this plugin. Copyright (c) 2026 Steph Ango (@kepano); see [LICENSE](LICENSE). Format authority: [JSON Canvas 1.0](https://jsoncanvas.org/spec/1.0/).
