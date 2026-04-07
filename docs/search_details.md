---
html_meta:
  description: HED search details — implementation comparison and performance benchmarks for basic_search, QueryHandler, and StringQueryHandler in hedtools
  keywords: HED search, string search, query handler, basic search, performance, benchmarks, hedtools, pattern matching
---

```{index} search, string search, query, QueryHandler, StringQueryHandler, basic_search
```

# HED search details

HEDtools provides three distinct mechanisms for searching HED-annotated data. This page covers their design and query languages ({ref}`implementations <hed-search-implementations>`) and measured performance characteristics ({ref}`performance <hed-search-performance>`).

(hed-search-implementations)=

## HED search implementations

The three implementations share a common goal — "does this HED string match this query?" — but differ substantially in their inputs, capabilities, schema requirements, and performance characteristics. Choosing the right implementation depends on whether you need schema-aware ancestor matching, full group-structural queries, or raw throughput on unannotated strings.

### Overview of the three implementations

#### `basic_search` — regex-based flat matching

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

#### `QueryHandler` — schema-backed object search

Located in {mod}`hed.models.query_handler`, `QueryHandler` is the full-featured search engine. It compiles a query string into an expression tree once, then evaluates that tree against `HedString` objects that have already been parsed against a loaded `HedSchema`.

Key characteristics:

- Input is a `HedString` object; a full `HedSchema` is required.
- Output is a `list[SearchResult]` containing `HedTag` / `HedGroup` object references, useful for tag-level introspection (not just row filtering).
- Supports the complete query language: `&&`, `||`, `~`, `@`, `{}`, `[]`, `{:}`, `?`, `??`, `???`.
- `@A` means A must **not** appear anywhere in the string.
- Ancestor matching is exact — the schema normalises both query and string tags to short form, so `Event` matches `Sensory-event` because the schema knows `Sensory-event` descends from `Event`.
- Per-string cost includes a full HedString parse and schema tag resolution.

Use `QueryHandler` when you need schema-aware ancestor matching, or when you want object references (e.g., to retrieve the matched group for further processing). See {class}`hed.models.query_handler.QueryHandler`.

#### `StringQueryHandler` — tree-based schema-optional search

Located in {mod}`hed.models.string_search`, `StringQueryHandler` is a new middle-ground implementation that inherits from `QueryHandler` and reuses the full expression-tree compiler, but operates on raw strings rather than pre-parsed `HedString` objects.

It parses each raw HED string into a lightweight {class}`~hed.models.string_search.StringNode` tree that duck-types the `HedGroup`/`HedTag` interfaces expected by the existing expression evaluators — so all `QueryHandler` query syntax works unchanged.

Key characteristics:

- Input is a raw string (or a `pd.Series` via {func}`~hed.models.string_search.search_series`).
- Schema is **optional**: pass a `schema_lookup` dict (see {mod}`hed.models.schema_lookup`) to enable ancestor matching for short-form strings (e.g. `Event` matching `Sensory-event`); omit it for purely literal matching.
- Output is a list (truthy/falsy) — row-filtering only, no object references.
- Supports the same full query syntax as `QueryHandler` (`&&`, `||`, `~`, `@`, `{}`, etc.).
- `@A` carries the same semantics as `QueryHandler` — A must **not** be present.
- Long-form strings (`Event/Sensory-event`) support ancestor matching via slash-splitting even without a lookup. Short-form strings (`Sensory-event`) require a `schema_lookup` for ancestor matching; without one, matching is purely literal.
- Parse cost is a lightweight recursive split — much cheaper than a full HedString + schema parse.

Use `StringQueryHandler` when you have raw strings (not `HedString` objects), need the full `QueryHandler` query syntax, and either don't have a schema available or want faster processing at the cost of losing full schema-aware ancestor matching. See {class}`hed.models.string_search.StringQueryHandler`.

#### Generating a schema lookup

If you want `StringQueryHandler` to resolve ancestors for short-form strings (e.g. query `Event` matching `Sensory-event`) without a full schema parse per row, you can pre-generate a lookup dictionary from a `HedSchema`:

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

### Comparison tables

#### Core characteristics

| Property              | `basic_search`             | `QueryHandler`                                     | `StringQueryHandler`                            |
| --------------------- | -------------------------- | -------------------------------------------------- | ----------------------------------------------- |
| **Input**             | `pd.Series` of raw strings | `HedString` object                                 | Raw string or `pd.Series` (via `search_series`) |
| **Schema required**   | No                         | Yes — full `HedSchema` for tag parsing             | No; optional `schema_lookup` dict               |
| **Output**            | `pd.Series[bool]` mask     | `list[SearchResult]` with `HedTag`/`HedGroup` refs | `list` (truthy/falsy); `StringNode` refs        |
| **Result usable for** | Row filtering              | Row filtering + tag/group introspection            | Row filtering only                              |
| **Batch API**         | Native (`series`)          | Manual loop                                        | `search_series(series, query)`                  |
| **Parse cost**        | Regex compilation once     | Full `HedString` + schema parse per string         | Lightweight tree parse per string               |
| **Unrecognised tags** | Matched literally          | Silent match failure (`tag_terms = ()`)            | Matched literally                               |

#### Query syntax

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

#### Group / structural operators

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

#### Ancestor / cross-form search

| Scenario                                                | `basic_search`                                    | `QueryHandler`                          | `StringQueryHandler`                                             |
| ------------------------------------------------------- | ------------------------------------------------- | --------------------------------------- | ---------------------------------------------------------------- |
| Query `Event`, string `Sensory-event` (short form)      | ❌ literal only                                   | ✅ `tag_terms` from schema              | ✅ with `schema_lookup`; ❌ without                              |
| Query `Event`, string `Event/Sensory-event` (long form) | ❌ `Event` ≠ `Event/Sensory-event`                | ✅ schema normalises                    | ✅ slash-split produces `tag_terms = ("event", "sensory-event")` |
| Query `Event/Sensory-event`, string `Sensory-event`     | ❌                                                | ✅ schema normalises both to short form | ❌ no schema to normalise                                        |
| Schema-free ancestor search                             | `convert_query()` + long-form series (workaround) | N/A — schema always required            | ✅ works natively for long-form strings                          |
| Tag `Def/Name` matched by query `Def`                   | ❌ literal prefix mismatch                        | ✅ `short_base_tag = "Def"`             | ✅ `tag_terms` contains `"def"`                                  |

#### Critical semantic traps

These differences are silent — no error, just wrong answers if you mix up query strings across implementations:

| Operator          | `basic_search`                                           | `QueryHandler` / `StringQueryHandler`                                               |
| ----------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `@A`              | A **must** appear anywhere in the string                 | A must **not** appear anywhere in the string                                        |
| `~A`              | A must not appear **anywhere** (global)                  | A must not appear in any group that also matches the rest of the expression (local) |
| `*` wildcard      | Regex `.*?` — spans `/` and matches mid-token substrings | Strict prefix on the tag's short form — anchored to start                           |
| No-operator `A B` | Both present anywhere (implicit `@@`)                    | Parse error — `&&` required                                                         |

______________________________________________________________________

(hed-search-performance)=

## HED search performance

Benchmarks were run using HED 8.4.0 with `timeit` on both synthetic strings and real BIDS event data. All times are medians in milliseconds. Relative ratios between engines are more meaningful than absolute values, which depend on hardware.

### Key findings

- **Series throughput:** `basic_search` is roughly 14–20× faster than a `QueryHandler` row-by-row loop at 5 000 rows because it leverages vectorised pandas `str.contains` regex matching.
- **Single-string speed:** `StringQueryHandler` (no lookup) is ~40 % faster than `QueryHandler` per string because it avoids schema-based `HedString` construction.
- **Schema-lookup overhead:** Enabling `schema_lookup` in `StringQueryHandler` has negligible overhead for most queries; cost appears only when ancestor matching is actually invoked.
- **Nesting depth:** At depth 20, `QueryHandler` is ~6× slower than on a flat string; `StringQueryHandler` shows similar scaling.
- **Operation coverage:** `basic_search` supports 7 of 18 tested operation types. The remaining 11 (OR, exact groups, logical groups, `?`/`??`/`???` wildcards, quoted terms) require `QueryHandler` or `StringQueryHandler`.

### Series throughput

Whole-series search over a `pd.Series` of HED strings. `basic_search` uses vectorised regex; `search_series` uses `StringQueryHandler.search()` per row; `QueryHandler_loop` constructs a `HedString` per row then searches. Query: `single_bare_term`.

|  Rows | QueryHandler_loop (ms) | basic_search (ms) | search_series (ms) |
| ----: | ---------------------: | ----------------: | -----------------: |
|    10 |                   0.34 |              0.20 |               0.30 |
|   100 |                   3.43 |              0.40 |               2.41 |
|   500 |                   16.7 |              2.25 |               13.1 |
| 1 000 |                   29.8 |              1.91 |               19.5 |
| 5 000 |                    164 |              11.7 |                114 |

All three engines scale linearly with row count. `basic_search` is 14–20× faster than `QueryHandler_loop`; `search_series` is roughly 1.4× faster than `QueryHandler_loop`.

### Single-string timing

Per-string median search time (ms) across string sizes. Tag counts: tiny = 1, small = 5, medium = 10, large = 25, xlarge = 50, xxlarge = 100. Query: `single_bare_term`.

| String size        | QueryHandler (ms) | SQH_no_lookup (ms) | basic_search (ms) |
| ------------------ | ----------------: | -----------------: | ----------------: |
| tiny (1 tag)       |             0.012 |              0.007 |             0.131 |
| small (5 tags)     |             0.020 |              0.014 |             0.197 |
| medium (10 tags)   |             0.041 |              0.021 |             0.123 |
| large (25 tags)    |             0.132 |              0.102 |             0.157 |
| xlarge (50 tags)   |             0.176 |              0.113 |             0.131 |
| xxlarge (100 tags) |             0.329 |              0.248 |             0.154 |

`basic_search` regex overhead dominates on small strings; `QueryHandler` and `StringQueryHandler` dominate on large strings. The crossover occurs around 25–50 tags.

### Operation coverage and cost

Per-operation timing on a 10-tag string. `basic_search` returns no results (not an error) for unsupported constructs, so queries using those operations will silently produce incorrect results.

| Operation                      | QueryHandler (ms) | SQH (ms) | basic_search  |
| ------------------------------ | ----------------: | -------: | ------------- |
| `bare_term`                    |             0.061 |    0.037 | 0.278 ms      |
| `and_2`                        |             0.063 |    0.041 | 0.321 ms      |
| `and_3`                        |             0.067 |    0.045 | 0.355 ms      |
| `negation`                     |             0.083 |    0.043 | 0.160 ms      |
| `wildcard_prefix` (`*` suffix) |             0.046 |    0.037 | 0.204 ms      |
| `nested_group_[]`              |             0.057 |    0.039 | 0.634 ms      |
| `deep_and_chain`               |             0.117 |    0.059 | 0.515 ms      |
| `or`                           |             0.058 |    0.037 | — unsupported |
| `exact_group_{}`               |             0.052 |    0.030 | — unsupported |
| `exact_optional_{:}`           |             0.071 |    0.043 | — unsupported |
| `exact_quoted`                 |             0.062 |    0.030 | — unsupported |
| `wildcard_?`                   |             0.086 |    0.047 | — unsupported |
| `wildcard_??`                  |             0.068 |    0.041 | — unsupported |
| `wildcard_???`                 |             0.074 |    0.041 | — unsupported |
| `descendant_nested`            |             0.138 |    0.086 | — unsupported |
| `double_negation`              |             0.057 |    0.035 | — unsupported |
| `complex_onset_def`            |             0.113 |    0.068 | — unsupported |
| `nested_or_and`                |             0.080 |    0.057 | — unsupported |

`StringQueryHandler` supports all 18 operation types.

### Nesting depth

Parenthesisation depth from 0 (flat) to 20. Deeper nesting increases the tree walk for `QueryHandler` and `StringQueryHandler`. `basic_search` shows no consistent depth trend because its cost depends on delimiter count, not recursion depth.

| Depth | QueryHandler (ms) | SQH_no_lookup (ms) | basic_search (ms) |
| ----: | ----------------: | -----------------: | ----------------: |
|     0 |             0.026 |              0.017 |             0.125 |
|     1 |             0.022 |              0.013 |             0.256 |
|     5 |             0.058 |              0.039 |             0.274 |
|    10 |             0.102 |              0.058 |             0.256 |
|    20 |             0.155 |              0.108 |             0.234 |

At depth 20, `QueryHandler` is ~6× slower than at depth 0; `SQH` is ~6× slower.

### Repeated tags

Repeating a target tag N times in the string. `basic_search`'s `verify_search_delimiters` uses `itertools.product` over delimiter positions; repeated instances multiply the internal search space. Tree-based engines are linear in the number of candidates and are not affected.

| Occurrences | QueryHandler (ms) | SQH_no_lookup (ms) | basic_search (ms) |
| ----------: | ----------------: | -----------------: | ----------------: |
|           0 |             0.034 |              0.022 |             0.544 |
|           5 |             0.151 |              0.084 |             0.791 |
|          10 |             0.093 |              0.073 |             0.940 |
|          20 |             0.182 |              0.138 |             0.668 |
|          40 |             0.200 |              0.195 |             0.654 |

### Compile vs. search

Query compilation is a one-time cost; subsequent searches against different strings reuse the compiled expression. Reusing a compiled handler across many strings amortises compilation cost to near zero.

| Phase   | QueryHandler (ms) | StringQueryHandler (ms) |
| ------- | ----------------: | ----------------------: |
| Compile |             0.004 |                   0.005 |
| Search  |             0.053 |                   0.036 |

### Real BIDS data

Search over 200 rows of the `eeg_ds003645s_hed` BIDS test dataset.

| Query                  | QueryHandler_loop (ms) | basic_search (ms) | search_series (ms) |
| ---------------------- | ---------------------: | ----------------: | -----------------: |
| `single_bare_term`     |                    9.0 |               2.5 |                6.5 |
| `single_wildcard`      |                    8.2 |               0.6 |                4.9 |
| `negation`             |                    8.0 |               0.9 |                6.8 |
| `two_term_and`         |                    8.8 |               1.2 |                4.9 |
| `three_term_and`       |                    8.5 |               1.9 |                5.1 |
| `group_nesting`        |                    7.9 |               0.3 |                7.8 |
| `two_term_or`          |                    7.9 |                 — |                6.8 |
| `exact_group`          |                    9.3 |                 — |                6.6 |
| `exact_group_optional` |                   11.7 |                 — |                5.8 |
| `single_exact_term`    |                    8.1 |                 — |                5.5 |
| `wildcard_child`       |                   12.6 |                 — |                8.9 |
| `complex_composite`    |                   14.2 |                 — |                9.5 |

### Choosing an implementation

**Use `basic_search`** when you need the fastest possible series-level filter, your queries can be expressed with simple terms, AND, negation, or descendant wildcards (`*`), and schema-aware ancestor matching is not required. Ideal for quick event file filtering when query simplicity is acceptable.

**Use `StringQueryHandler`** (via `search_series()`) when you need the full query language (OR, exact groups, logical groups, `?`/`??`/`???` wildcards) and are working with raw strings from tabular files or sidecars. This is the best general-purpose choice — it is ~40 % faster than a `QueryHandler` loop per string and close to `basic_search` on large strings.

**Use `QueryHandler`** when you already have parsed `HedString` objects (for example from a validation pipeline), or when you need results as structured `HedString`/`HedTag` objects rather than boolean matches. The additional overhead relative to `StringQueryHandler` comes from `HedString` construction, not from search expression evaluation, so reusing pre-parsed objects avoids the cost entirely.

### Benchmark methodology

- **Timing:** `timeit` — 20 iterations (single-string), 5 iterations (series), 10 iterations (sweeps). Median reported.
- **Schema:** HED 8.4.0, loaded once and reused.
- **Synthetic data:** Strings built from real schema tags with controlled tag count, nesting depth, group count, and tag repetition.
- **`schema_lookup`:** Generated via `generate_schema_lookup(schema)` — a dict mapping each short tag to its ancestor tuple, enabling ancestor-based matching in `StringQueryHandler` without a full schema load per string.
- **Hardware note:** Absolute timings depend on hardware; relative ratios between engines are the meaningful comparison.
