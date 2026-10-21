---
name: obsidian-bases
description: Create and edit Obsidian .base files, including filters, formulas, properties, views, and summaries. Use for Bases definitions or database-like views over vault files.
---

# Obsidian Bases

A `.base` file is a YAML definition of views over files in a vault. It does not contain copies of the underlying notes. Preserve existing filters, formulas, views, and unfamiliar view-specific fields unless the requested change affects them.

For vault reads, writes, or queries, follow [obsidian-vault](../obsidian-vault/SKILL.md) and its CLI wrapper. Use explicit `.base` paths. Do not bypass the configured vault or read-only mode with direct file writes. A standalone definition can be drafted in the task workspace.

## Format primitives

- `filters` selects files globally. A view's filters further restrict that selection.
- `formulas` names computed expressions, referenced as `formula.name`.
- `properties` configures display metadata; note-property values remain in notes.
- `summaries` defines aggregate expressions for use by views.
- `views` contains named view definitions, their type, displayed properties, and optional grouping or sorting.

Read [syntax](references/SYNTAX.md) for a minimal definition, property namespaces, filters, quoting, and view configuration. Read [formulas](references/FORMULAS.md) when composing computed values or summaries. Consult installed view capabilities before choosing a view type that depends on another plugin.

## Querying and editing

Use wrapper help for `bases`, `base:views`, and `base:query` to inspect existing Bases and their results. These are distinct from editing the YAML definition. `base:create` creates an item through a Base; do not assume it creates a new `.base` definition.

When saving a definition, use the file operations documented by the vault skill and installed CLI help. Keep the `.base` extension and serialize YAML without an outer Markdown fence. In a Markdown note, a Base can instead be embedded as `![[Library.base]]`, with a named view such as `![[Library.base#Reading list]]`, or defined in a fenced `base` block.

## Validation

Parse the YAML, check that referenced formulas exist and are not circular, and check property names against relevant notes. Missing properties can be intentional; account for them in expressions instead of silently changing the notes. Preserve the intended global and view-level filtering.

Read back saved content. Query the relevant view when supported to catch formula or selection mistakes that YAML parsing cannot detect. Rendering and expression evaluation require Obsidian; do not claim them from a parser check alone.

Adapted from [Kepano's obsidian-bases skill](https://github.com/kepano/obsidian-skills/tree/3ccff5338ea700537839b21900aa5358a0402c98/skills/obsidian-bases). Copyright (c) 2026 Steph Ango (@kepano); see [LICENSE](LICENSE). Authoritative references: [Bases syntax](https://help.obsidian.md/bases/syntax) and [functions](https://help.obsidian.md/bases/functions).
