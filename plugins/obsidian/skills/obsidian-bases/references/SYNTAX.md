# Bases syntax

## Minimal definition

```yaml
filters:
  and:
    - 'file.ext == "md"'
    - 'file.inFolder("Projects")'
properties:
  note.status:
    displayName: Status
views:
  - type: table
    name: Projects
    order:
      - file.name
      - note.status
```

Without filters, a Base starts from all vault files. There is no SQL-style `from` clause. Use note and file properties to select the intended dataset.

## Property namespaces

| Namespace | Meaning | Examples |
| --- | --- | --- |
| `note` | Frontmatter values; the prefix can be omitted | `note.status`, `status`, `note["due date"]` |
| `file` | File metadata and methods | `file.name`, `file.ext`, `file.mtime`, `file.tags`, `file.inFolder("Projects")` |
| `formula` | Named expressions defined in `formulas` | `formula.age_days` |

`properties` sets display names; it does not populate frontmatter. Do not manufacture note fields merely to make a view nonempty.

`this` refers to the file supplying the Base's context: normally the Base itself, the embedding note for an embedded Base, or the active file for a sidebar Base. Account for that context when comparing links or properties.

## Filters

A filter is either an expression string or an object containing one logical key: `and`, `or`, or `not`. Its value is a list of expressions or nested filter objects.

```yaml
filters:
  and:
    - 'file.ext == "md"'
    - or:
        - 'file.hasTag("project")'
        - 'file.inFolder("Projects")'
    - not:
        - 'status == "archived"'
```

Global and view filters combine with AND. Comparisons and functions use the same expression language as formulas, including `==`, `!=`, `>`, `>=`, `<`, `<=`, `&&`, `||`, and `!`.

## Views

A view declares a `type` and `name`. Table and cards are common view types; additional types and settings depend on installed capabilities. Preserve an existing view's options when making an unrelated change.

```yaml
views:
  - type: table
    name: Active projects
    filters: 'status != "archived"'
    order:
      - file.name
      - note.status
      - file.mtime
    groupBy:
      property: note.status
      direction: ASC
    sort:
      - property: file.mtime
        direction: DESC
    limit: 50
```

`order` selects displayed properties; `sort` orders rows. A view filter does not replace the global filters. Name views deliberately because embeds may reference them.

## YAML boundaries

Single-quote expressions containing double-quoted strings, such as `'status == "active"'`. Escape a literal single quote inside a YAML single-quoted string by doubling it. Quote display strings with YAML-significant characters. Use a YAML parser to distinguish a serialization error from an expression error in Obsidian.
