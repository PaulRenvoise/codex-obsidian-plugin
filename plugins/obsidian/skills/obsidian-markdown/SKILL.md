---
name: obsidian-markdown
description: Create and edit Obsidian Markdown with internal links, embeds, callouts, block references, and YAML properties. Use when writing or interpreting these formats in Obsidian notes.
---

# Obsidian Markdown

Use this skill for Obsidian's additions to Markdown. Preserve the note's existing style, property names, and link conventions; add structure only when it serves the requested content. Frontmatter, titles, tags, and callouts are optional.

For reads or writes in the configured vault, follow [obsidian-vault](../obsidian-vault/SKILL.md) and its CLI wrapper. This format skill does not select another vault or authorize direct writes around read-only mode. Standalone drafts can be prepared in the task workspace.

## Internal links and block references

```markdown
[[Note]]
[[Folder/Note|Display text]]
[[Note#Heading]]
[[Note#^block-id]]
[[#Heading in this note]]
```

Use a folder-qualified target when names are ambiguous. Non-Markdown files need their extensions. Obsidian also supports standard Markdown internal links such as `[Note](Folder/Note.md)`; preserve that convention when the vault uses it, and URL-encode spaces in Markdown destinations.

A block reference points to an explicit ID:

```markdown
A paragraph that can be referenced. ^block-id

- A list item
- Another item

^list-id
```

IDs for lists and quotes go on a separate line after the block. Preserve existing IDs when editing content other notes may reference. In a Markdown table, escape the pipe in an aliased wikilink as `\|` so it does not split the cell.

## Embeds

Prefix an internal link with `!` to embed its target:

```markdown
![[Note#Heading]]
![[Attachments/image.png|300]]
![[Attachments/document.pdf#page=3]]
![[Library.base#Reading list]]
```

Read [embeds](references/EMBEDS.md) for media, block, and search-result examples. Check referenced vault files and headings rather than inventing targets.

## Callouts

```markdown
> [!note] Optional title
> Content of the callout.

> [!tip]- Initially collapsed
> Expand to read this content.
```

`+` marks an initially expanded foldable callout. Read [callouts](references/CALLOUTS.md) for types, aliases, and nesting. Preserve any custom types already used by the vault.

## Properties and tags

Properties are a YAML block at the beginning of a note. Preserve value types and existing fields when editing. Quote values that YAML could misinterpret, especially internal links. Read [properties](references/PROPERTIES.md) when adding or changing metadata.

Inline tags use `#tag` or `#parent/child`; frontmatter tags omit the leading `#`. Tags may contain numbers but cannot consist entirely of numbers.

## Other syntax and verification

`==text==` highlights text. `%%comment%%` hides text in reading view but does not make it private or remove it from the file. Obsidian supports math, Mermaid blocks, and footnotes; preserve those blocks when changing surrounding prose.

After saving through the vault wrapper, check the changed content, YAML types, and link targets. Claim visual verification only if the note was actually inspected in Obsidian.

Adapted from [Kepano's obsidian-markdown skill](https://github.com/kepano/obsidian-skills/tree/3ccff5338ea700537839b21900aa5358a0402c98/skills/obsidian-markdown). Copyright (c) 2026 Steph Ango (@kepano); see [LICENSE](LICENSE). Authoritative syntax: [Obsidian Help](https://help.obsidian.md/obsidian-flavored-markdown).
