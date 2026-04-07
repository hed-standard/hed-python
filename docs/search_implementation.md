---
html_meta:
  description: Comparison of the three HED string search implementations in hedtools - basic_search, QueryHandler, and StringQueryHandler
  keywords: HED search, string search, query handler, basic search, performance, hedtools, pattern matching
---

```{index} search, string search, query, QueryHandler, StringQueryHandler, basic_search
```

# HED search implementations

HEDtools provides three distinct mechanisms for searching HED-annotated data. They share a common goal — "does this HED string match this query?" — but differ substantially in their inputs, capabilities, schema requirements, and performance characteristics. Choosing the right implementation depends on whether you need schema-aware ancestor matching, full group-structural queries, or raw throughput on unannotated strings.

## Overview of the three implementations

### `basic_search` — regex-based flat matching

Located in {mod}`hed.models.basic_search`, the `find_matching()` function operates directly on a `pd.Series` of raw HED strings using compiled regular expressions. It requires no schema and no parsing step, making it the fastest option for bulk row filtering.

Key characteristics:

- Input is a `pd.Series` of raw strings; output is a `pd.Series[bool]` mask.
- The query is compiled once into a regex and applied with `Series.str.contains`.
- Matches are purely literal — `Event` does not match `Sensory-event`.
- `@A` in a basic-search query means A **must be present** anywhere in the string (note: this is the **opposite** of what `@A` means in `QueryHandler`/`StringQueryHandler`).
- `~A` means A must not appear anywhere (global negation).
- `(A, B)` syntax checks that A and B appear at the same nesting level.
- Wildcard `A*` expands to the regex `A.*?`, which can span `/` and match mid-token substrings.

Use `basic_search` when you are working with a large series of raw strings, don't need ancestor matching, and want maximum throughput. See {func}`hed.models.basic_search.find_matching`.

### `QueryHandler` — schema-backed object search

Located in {mod}`hed.models.query_handler`, `QueryHandler` is the full-featured search engine. It compiles a query string into an expression tree once, then evaluates that tree against `HedString` objects that have already been parsed against a loaded `HedSchema`.

Key characteristics:

- Input is a `HedString` object; a full `HedSchema` is required.
- Output is a `list[SearchResult]` containing `HedTag` / `HedGroup` object references, useful for tag-level introspection (not just row filtering).
- Supports the complete query language: `&&`, `||`, `~`, `@`, `{}`, `[]`, `{:}`, `?`, `??`, `???`.
- `@A` means A must **not** appear anywhere in the string.
- Ancestor matching is exact — the schema normalises both query and string tags to short form, so `Event` matches `Sensory-event` because the schema knows `Sensory-event` descends from `Event`.
- Per-string cost includes a full HedString parse and schema tag resolution.

Use `QueryHandler` when you need schema-aware ancestor matching, or when you want object references (e.g., to retrieve the matched group for further processing). See {class}`hed.models.query_handler.QueryHandler`.

### `StringQueryHandler` — tree-based schema-optional search

Located in {mod}`hed.models.string_search`, `StringQueryHandler` is a new middle-ground implementation that inherits from `QueryHandler` and reuses the full expression-tree compiler, but operates on raw strings rather than pre-parsed `HedString` objects.

It parses each raw HED string into a lightweight {class}`~hed.models.string_search.StringNode` tree that duck-types the `HedGroup`/`HedTag` interfaces expected by the existing expression evaluators — so all `QueryHandler` query syntax works unchanged.

Key characteristics:

- Input is a raw string (or a `pd.Series` via {func}`~hed.models.string_search.search_series`).
- Schema is **optional**: pass a `schema_lookup` dict (see {mod}`hed.models.schema_lookup`) to enable ancestor matching for long-form strings; omit it for purely literal matching.
- Output is a list (truthy/falsy) — row-filtering only, no object references.
- Supports the same full query syntax as `QueryHandler` (`&&`, `||`, `~`, `@`, `{}`, etc.).
- `@A` carries the same semantics as `QueryHandler` — A must **not** be present.
- Without a schema lookup, `Event` does **not** match `Sensory-event` (short-form strings). With a schema lookup, ancestor matching works for long-form strings (`Event/Sensory-event`).
- Parse cost is a lightweight recursive split — much cheaper than a full HedString + schema parse.

Use `StringQueryHandler` when you have raw strings (not `HedString` objects), need the full `QueryHandler` query syntax, and either don't have a schema available or want faster processing at the cost of losing full schema-aware ancestor matching. See {class}`hed.models.string_search.StringQueryHandler`.

### Generating a schema lookup

If you want `StringQueryHandler` to resolve ancestors for long-form strings without a full schema parse per row, you can pre-generate a lookup dictionary from a `HedSchema`:

```python
from hed import load_schema_version
from hed import generate_schema_lookup, save_schema_lookup, load_schema_lookup

schema = load_schema_version("8.4.0")
lookup = generate_schema_lookup(schema)  # {short_name_casefold: tag_terms_tuple}

# Persist for reuse
save_schema_lookup(lookup, "hed840_lookup.json")
lookup = load_schema_lookup("hed840_lookup.json")
```

See {func}`hed.models.schema_lookup.generate_schema_lookup`.

______________________________________________________________________

## Comparison tables

### Core characteristics

| Property              | `basic_search`             | `QueryHandler`                                     | `StringQueryHandler`                            |
| --------------------- | -------------------------- | -------------------------------------------------- | ----------------------------------------------- |
| **Input**             | `pd.Series` of raw strings | `HedString` object                                 | Raw string or `pd.Series` (via `search_series`) |
| **Schema required**   | No                         | Yes — full `HedSchema` for tag parsing             | No; optional `schema_lookup` dict               |
| **Output**            | `pd.Series[bool]` mask     | `list[SearchResult]` with `HedTag`/`HedGroup` refs | `list` (truthy/falsy); `StringNode` refs        |
| **Result usable for** | Row filtering              | Row filtering + tag/group introspection            | Row filtering only                              |
| **Batch API**         | Native (`series`)          | Manual loop                                        | `search_series(series, query)`                  |
| **Parse cost**        | Regex compilation once     | Full `HedString` + schema parse per string         | Lightweight tree parse per string               |
| **Unrecognised tags** | Matched literally          | Silent match failure (`tag_terms = ()`)            | Matched literally                               |

### Query syntax

| Feature                      | `basic_search` query syntax                         | `QueryHandler` / `StringQueryHandler` query syntax |
| ---------------------------- | --------------------------------------------------- | -------------------------------------------------- |
| **AND**                      | Space or comma between terms (context-dependent)    | `A && B` or `A, B`                                 |
| **OR**                       | Not supported                                       | `A \|\| B`                                         |
| **Absent from string (`@`)** | ⚠️ `@A` means A **must be present** anywhere        | `@A` means A must **not** appear anywhere          |
| **Must-not-appear (`~`)**    | `~A` — A must not appear anywhere (global)          | `~A` — negation within group context (local)       |
| **Prefix wildcard**          | `A*` → regex `A.*?` (spans `/`, matches substrings) | `A*` → prefix on short form only                   |
| **Full regex per term**      | Yes (`regex=True` mode)                             | No                                                 |
| **Quoted exact match**       | No                                                  | `"A"` — exact match, no ancestor search            |
| **Implicit default**         | If no `(` or `@`: all terms become "anywhere"       | No implicit conversion — must be explicit          |

### Group / structural operators

| Feature                           | `basic_search`                            | `QueryHandler`                               | `StringQueryHandler`   |
| --------------------------------- | ----------------------------------------- | -------------------------------------------- | ---------------------- |
| **Same nesting level**            | `(A, B)` — A and B at same relative level | N/A — use `{A, B}`                           | N/A — use `{A, B}`     |
| **Same parenthesised group `{}`** | No                                        | `{A, B}` — must share a direct parent group  | Same as `QueryHandler` |
| **Exact group `{:}`**             | No                                        | `{A, B:}` — same group, no other children    | Same                   |
| **Optional exact group**          | No                                        | `{A, B: C}` — A and B required, C optional   | Same                   |
| **Descendant group `[]`**         | No                                        | `[A, B]` — both in same subtree at any depth | Same                   |
| **Any child `?`**                 | No                                        | `?` — any tag or group child                 | Same                   |
| **Any tag child `??`**            | No                                        | `??` — any leaf (non-group) child            | Same                   |
| **Any group child `???`**         | No                                        | `???` — any parenthesised group child        | Same                   |
| **Nested query operators**        | No                                        | Yes — full recursive composition             | Same                   |

### Ancestor / cross-form search

| Scenario                                                | `basic_search`                                    | `QueryHandler`                          | `StringQueryHandler`                                             |
| ------------------------------------------------------- | ------------------------------------------------- | --------------------------------------- | ---------------------------------------------------------------- |
| Query `Event`, string `Sensory-event` (short form)      | ❌ literal only                                   | ✅ `tag_terms` from schema              | ✅ with `schema_lookup`; ❌ without                              |
| Query `Event`, string `Event/Sensory-event` (long form) | ❌ `Event` ≠ `Event/Sensory-event`                | ✅ schema normalises                    | ✅ slash-split produces `tag_terms = ("event", "sensory-event")` |
| Query `Event/Sensory-event`, string `Sensory-event`     | ❌                                                | ✅ schema normalises both to short form | ❌ no schema to normalise                                        |
| Schema-free ancestor search                             | `convert_query()` + long-form series (workaround) | N/A — schema always required            | ✅ works natively for long-form strings                          |
| Tag `Def/Name` matched by query `Def`                   | ❌ literal prefix mismatch                        | ✅ `short_base_tag = "Def"`             | ✅ `tag_terms` contains `"def"`                                  |

### Critical semantic traps

These differences are silent — no error, just wrong answers if you mix up query strings across implementations:

| Operator          | `basic_search`                                           | `QueryHandler` / `StringQueryHandler`                                               |
| ----------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `@A`              | A **must** appear anywhere in the string                 | A must **not** appear anywhere in the string                                        |
| `~A`              | A must not appear **anywhere** (global)                  | A must not appear in any group that also matches the rest of the expression (local) |
| `*` wildcard      | Regex `.*?` — spans `/` and matches mid-token substrings | Strict prefix on the tag's short form — anchored to start                           |
| No-operator `A B` | Both present anywhere (implicit `@@`)                    | Parse error — `&&` required                                                         |

______________________________________________________________________

## Performance

*Performance benchmarks will be added here.*

Preliminary guidance:

- For large-scale row filtering on raw strings where schema awareness is not needed, `basic_search` is likely fastest due to vectorised regex on the full series with no per-row parsing.
- `StringQueryHandler` trades some throughput for full query-language support and optional ancestor matching; parse cost per row is a lightweight recursive split.
- `QueryHandler` has the highest per-string cost because it requires a pre-parsed `HedString` (including schema tag resolution), but provides the richest result objects.
