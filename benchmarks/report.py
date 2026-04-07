"""Generate analysis report from benchmark results.

Reads the latest JSON results file and produces:
  - Console summary tables
  - Matplotlib figures saved to benchmarks/figures/{stem}/
  - A Markdown report in benchmarks/results/

Usage::

    python report.py                         # latest results
    python report.py results/benchmark_20260407_120000.json  # specific file
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # must be set before importing pyplot
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd

RESULTS_DIR = Path(__file__).parent / "results"
_FIGURES_BASE = Path(__file__).parent / "figures"
_FIGURES_BASE.mkdir(exist_ok=True)

# Consistent colours per engine
ENGINE_COLORS = {
    "basic_search": "#1f77b4",
    "QueryHandler": "#ff7f0e",
    "QueryHandler_loop": "#ff7f0e",
    "SQH_no_lookup": "#2ca02c",
    "SQH_with_lookup": "#d62728",
    "search_series_no_lookup": "#2ca02c",
    "search_series_with_lookup": "#d62728",
    "StringQueryHandler": "#9467bd",
    "search_series": "#8c564b",
    "StringQueryHandler_no_lookup": "#2ca02c",
    "StringQueryHandler_with_lookup": "#d62728",
}


def load_results(path=None):
    """Load benchmark results from JSON."""
    if path is None:
        files = sorted(RESULTS_DIR.glob("benchmark_*.json"))
        if not files:
            print("No results files found in", RESULTS_DIR)
            sys.exit(1)
        path = files[-1]
    else:
        path = Path(path)
    print(f"Loading results from {path}")
    return json.loads(path.read_text(encoding="utf-8")), path.stem


# ======================================================================
# Console summary
# ======================================================================


def print_single_string_summary(data):
    """Print a pivoted summary table of single-string results."""
    records = data.get("single_string", [])
    if not records:
        return
    df = pd.DataFrame(records)
    print("\n" + "=" * 80)
    print("SINGLE-STRING BENCHMARK SUMMARY (median seconds)")
    print("=" * 80)
    pivot = df.pivot_table(
        index=["config_label", "query_label"],
        columns="engine",
        values="total_time",
        aggfunc="first",
    )
    # Convert to milliseconds for readability
    pivot_ms = pivot * 1000
    pd.set_option("display.float_format", "{:.4f}".format)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.width", 200)
    print(pivot_ms.to_string())
    print()


def print_series_summary(data):
    """Print series-level benchmark summary."""
    records = data.get("series", [])
    if not records:
        return
    df = pd.DataFrame(records)
    print("\n" + "=" * 80)
    print("SERIES BENCHMARK SUMMARY (median seconds)")
    print("=" * 80)
    pivot = df.pivot_table(
        index=["config_label", "query_label"],
        columns="engine",
        values="total_time",
        aggfunc="first",
    )
    pivot_ms = pivot * 1000
    print(pivot_ms.to_string())
    print()


def print_sweep_summary(data):
    """Print factor sweep summary."""
    records = data.get("factor_sweeps", [])
    if not records:
        return
    df = pd.DataFrame(records)
    print("\n" + "=" * 80)
    print("FACTOR SWEEP SUMMARY")
    print("=" * 80)
    for factor in df["factor"].unique():
        sub = df[df["factor"] == factor]
        pivot = sub.pivot_table(index="level", columns="engine", values="time", aggfunc="first")
        pivot_ms = pivot * 1000
        print(f"\n--- {factor} (ms) ---")
        print(pivot_ms.to_string())


def print_real_data_summary(data):
    """Print real-data benchmark summary."""
    records = data.get("real_data", [])
    if not records:
        return
    df = pd.DataFrame(records)
    print("\n" + "=" * 80)
    print(f"REAL DATA BENCHMARK ({records[0].get('n_rows', '?')} rows)")
    print("=" * 80)
    pivot = df.pivot_table(index="query_label", columns="engine", values="total_time", aggfunc="first")
    pivot_ms = pivot * 1000
    print(pivot_ms.to_string())
    print()


# ======================================================================
# Plots
# ======================================================================


def _color(engine):
    return ENGINE_COLORS.get(engine, "#333333")


def plot_factor_sweep(data, stem):
    """One figure per factor sweep with engines as separate lines."""
    records = data.get("factor_sweeps", [])
    if not records:
        return
    df = pd.DataFrame(records)

    for factor in df["factor"].unique():
        sub = df[df["factor"] == factor].copy()

        fig, ax = plt.subplots(figsize=(8, 5))
        for engine in sub["engine"].unique():
            edf = sub[sub["engine"] == engine].sort_values("level")
            ax.plot(range(len(edf)), edf["time"].values * 1000, marker="o", label=engine, color=_color(engine))
            ax.set_xticks(range(len(edf)))
            ax.set_xticklabels(edf["level"].astype(str), rotation=45, ha="right")

        ax.set_xlabel(factor)
        ax.set_ylabel("Time (ms)")
        ax.set_title(f"Factor sweep: {factor}")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(_figures_dir(stem) / f"benchmark_sweep_{factor}.png", dpi=150)
        plt.close(fig)
        print(f"  Saved figures/{stem}/benchmark_sweep_{factor}.png")


def plot_series_scaling(data, stem):
    """Plot total time vs series size for each engine."""
    records = data.get("factor_sweeps", [])
    if not records:
        return
    df = pd.DataFrame(records)
    sub = df[df["factor"] == "series_size"]
    if sub.empty:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Total time
    ax = axes[0]
    for engine in sub["engine"].unique():
        edf = sub[sub["engine"] == engine].sort_values("level")
        ax.plot(edf["level"], edf["time"] * 1000, marker="o", label=engine, color=_color(engine))
    ax.set_xlabel("Series size (rows)")
    ax.set_ylabel("Total time (ms)")
    ax.set_title("Series search: total time")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Per-row time
    ax = axes[1]
    for engine in sub["engine"].unique():
        edf = sub[sub["engine"] == engine].sort_values("level")
        if "per_row" in edf.columns:
            ax.plot(edf["level"], edf["per_row"] * 1000, marker="o", label=engine, color=_color(engine))
    ax.set_xlabel("Series size (rows)")
    ax.set_ylabel("Per-row time (ms)")
    ax.set_title("Series search: per-row amortized cost")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(_figures_dir(stem) / "benchmark_series_scaling.png", dpi=150)
    plt.close(fig)
    print(f"  Saved figures/{stem}/benchmark_series_scaling.png")


def plot_compile_vs_search(data, stem):
    """Bar chart comparing compilation time to per-search time."""
    records = data.get("factor_sweeps", [])
    if not records:
        return
    df = pd.DataFrame(records)
    sub = df[df["factor"] == "compile_vs_search"]
    if sub.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    engines = sub["engine"].unique()
    levels = sub["level"].unique()  # compile, search
    x = range(len(engines))
    width = 0.35

    for i, level in enumerate(levels):
        vals = []
        for eng in engines:
            row = sub[(sub["engine"] == eng) & (sub["level"] == level)]
            vals.append(row["time"].values[0] * 1000 if len(row) else 0)
        offset = (i - 0.5) * width
        ax.bar([xi + offset for xi in x], vals, width, label=level)

    ax.set_xticks(x)
    ax.set_xticklabels(engines, rotation=15)
    ax.set_ylabel("Time (ms)")
    ax.set_title("Compilation vs per-search cost")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(_figures_dir(stem) / "benchmark_compile_vs_search.png", dpi=150)
    plt.close(fig)
    print(f"  Saved figures/{stem}/benchmark_compile_vs_search.png")


def plot_query_complexity_heatmap(data, stem):
    """Heatmap of query complexity vs engine (single-string results)."""
    records = data.get("single_string", [])
    if not records:
        return
    df = pd.DataFrame(records)
    # Pick one config for clarity
    config = df["config_label"].unique()[len(df["config_label"].unique()) // 2]
    sub = df[df["config_label"] == config]

    pivot = sub.pivot_table(index="query_label", columns="engine", values="total_time", aggfunc="first")
    pivot_ms = pivot * 1000

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(pivot_ms.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(pivot_ms.columns)))
    ax.set_xticklabels(pivot_ms.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(pivot_ms.index)))
    ax.set_yticklabels(pivot_ms.index, fontsize=8)
    ax.set_title(f"Query × Engine time (ms) — config: {config}")
    fig.colorbar(im, ax=ax, label="Time (ms)")

    # Annotate cells
    for i in range(len(pivot_ms.index)):
        for j in range(len(pivot_ms.columns)):
            val = pivot_ms.values[i, j]
            if pd.notna(val):
                ax.text(
                    j,
                    i,
                    f"{val:.2f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if val > pivot_ms.values[pd.notna(pivot_ms.values)].mean() else "black",
                )

    fig.tight_layout()
    fig.savefig(_figures_dir(stem) / "benchmark_query_heatmap.png", dpi=150)
    plt.close(fig)
    print(f"  Saved figures/{stem}/benchmark_query_heatmap.png")


def plot_real_data(data, stem):
    """Bar chart of real-data results."""
    records = data.get("real_data", [])
    if not records:
        return
    df = pd.DataFrame(records)

    pivot = df.pivot_table(index="query_label", columns="engine", values="total_time", aggfunc="first")
    pivot_ms = pivot * 1000

    fig, ax = plt.subplots(figsize=(10, 5))
    pivot_ms.plot(kind="bar", ax=ax, color=[_color(c) for c in pivot_ms.columns])
    ax.set_ylabel("Total time (ms)")
    ax.set_title(f"Real BIDS data ({records[0].get('n_rows', '?')} rows)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(_figures_dir(stem) / "benchmark_real_data.png", dpi=150)
    plt.close(fig)
    print(f"  Saved figures/{stem}/benchmark_real_data.png")


# ======================================================================
# Markdown report
# ======================================================================


def _pivot_to_md(pivot_ms, float_fmt=".3f"):
    """Convert a pandas pivot table (in ms) to a Markdown table string."""
    lines = []
    headers = [""] + [str(c) for c in pivot_ms.columns]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for idx, row in pivot_ms.iterrows():
        label = str(idx) if not isinstance(idx, tuple) else " / ".join(str(x) for x in idx)
        cells = [label]
        for v in row:
            cells.append(f"{v:{float_fmt}}" if pd.notna(v) else "—")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _engine_summary_table(data):
    """Build a comparison table of the three search engines."""
    return (
        "| Feature | basic_search | QueryHandler | StringQueryHandler |\n"
        "| --- | --- | --- | --- |\n"
        "| Input type | `pd.Series[str]` | `HedString` objects | Raw strings (`str`) |\n"
        "| Schema required | No | Yes | Optional (via `schema_lookup`) |\n"
        "| Series-native | Yes (`find_matching`) | No (manual loop) | Yes (`search_series`) |\n"
        "| Boolean AND | `word1, word2` | `term1 && term2` | same as QH |\n"
        "| Boolean OR | — | `term1 || term2` | same as QH |\n"
        "| Negation | `~word` | `~term` | same as QH |\n"
        "| Exact group `{}` | — | `{term1, term2}` | same as QH |\n"
        "| Optional exact `{:}` | — | `{term1, term2:}` | same as QH |\n"
        "| Logical group `[]` | — | `[term1, term2]` | same as QH |\n"
        "| Wildcard `?/?? /???` | — | Yes | same as QH |\n"
        "| Descendant wildcard | `*` suffix | `*` suffix | same as QH |\n"
        '| Quoted exact match | — | `"Exact-tag"` | same as QH |\n'
        "| Implementation | Regex on text | Recursive tree on parsed nodes | Recursive tree on StringNode |\n"
    )


def _figures_dir(stem: str) -> Path:
    """Return (and create) the per-run figures subdirectory."""
    d = _FIGURES_BASE / stem
    d.mkdir(parents=True, exist_ok=True)
    return d


def generate_markdown_report(data, stem):
    """Write a comprehensive Markdown report with tables, plots, and analysis."""
    mode = "quick" if data.get("quick") else "full"
    lines = []

    def h1(t):
        lines.extend([f"# {t}", ""])

    def h2(t):
        lines.extend([f"## {t}", ""])

    def h3(t):
        lines.extend([f"### {t}", ""])

    def p(t):
        lines.extend([t, ""])

    def img(alt, path):
        lines.extend([f"![{alt}]({path})", ""])

    def table(md):
        lines.extend([md, ""])

    # ------------------------------------------------------------------
    # Title and overview
    # ------------------------------------------------------------------
    h1("HED search benchmark report")
    p(f"**Run:** {data.get('timestamp', 'unknown')}  ")
    p(f"**Mode:** {mode}")

    h2("Overview")
    p("This report compares the performance of the three HED string search engines provided by the `hedtools` package:")
    p(
        "1. **basic_search** (`hed.models.basic_search.find_matching`) — regex-based pattern matching "
        "that operates directly on a `pd.Series` of raw HED strings. No schema required. "
        "Supports simple boolean AND (`@`), negation (`~`), wildcards (`*`), and parenthesised groups.\n"
        "2. **QueryHandler** (`hed.models.query_handler.QueryHandler`) — full expression-tree search "
        "that operates on parsed `HedString` objects. Requires a loaded HED schema. "
        "Supports AND, OR, negation, exact groups `{}`, optional exact `{:}`, logical groups `[]`, "
        "wildcard child `?`/`??`/`???`, descendant wildcards, and quoted exact matches.\n"
        "3. **StringQueryHandler** (`hed.models.string_search.StringQueryHandler`) — lightweight "
        "tree-based search that operates on raw strings via `StringNode` duck-typing. Schema is "
        "optional (via `schema_lookup` dict for ancestor queries). Provides `search_series()` "
        "convenience function for `pd.Series` input. Same query syntax as QueryHandler."
    )

    h3("Engine capability matrix")
    table(_engine_summary_table(data))

    # ------------------------------------------------------------------
    # Key findings (populated from data)
    # ------------------------------------------------------------------
    h2("Key findings")
    findings = []

    # Series speed — use series_size sweep so query and config are consistent;
    # report ratio at the largest row count tested.
    series_recs = data.get("series", [])
    _sweep_recs = data.get("factor_sweeps", [])
    if _sweep_recs:
        swdf_series = pd.DataFrame(_sweep_recs)
        ss = swdf_series[swdf_series["factor"] == "series_size"]
        if not ss.empty:
            max_level = ss["level"].max()
            at_max = ss[ss["level"] == max_level]
            bs_row = at_max[at_max["engine"] == "basic_search"]["time"]
            qh_row = at_max[at_max["engine"] == "QueryHandler_loop"]["time"]
            if not bs_row.empty and not qh_row.empty and bs_row.values[0] > 0:
                ratio = qh_row.values[0] / bs_row.values[0]
                findings.append(
                    f"**Series throughput:** `basic_search` is ~{ratio:.0f}× faster than "
                    f"`QueryHandler` in a row-by-row loop at {max_level:,} rows, "
                    f"because it leverages vectorised pandas `str.contains` regex matching."
                )
    elif series_recs:
        sdf = pd.DataFrame(series_recs)
        # Group by engine + n_rows, then take the median across queries at each row count;
        # report the ratio at the largest row count to avoid mixing incomparable workloads.
        per_nrows = sdf.groupby(["engine", "n_rows"])["total_time"].median().reset_index()
        max_nrows = per_nrows["n_rows"].max()
        at_max = per_nrows[per_nrows["n_rows"] == max_nrows]
        bs_row = at_max[at_max["engine"] == "basic_search"]["total_time"]
        qh_row = at_max[at_max["engine"] == "QueryHandler_loop"]["total_time"]
        if not bs_row.empty and not qh_row.empty and bs_row.values[0] > 0:
            ratio = qh_row.values[0] / bs_row.values[0]
            findings.append(
                f"**Series throughput:** `basic_search` is ~{ratio:.0f}× faster than "
                f"`QueryHandler` in a row-by-row loop at {max_nrows:,} rows, "
                f"because it leverages vectorised pandas `str.contains` regex matching."
            )

    # SQH vs QH per string
    single_recs = data.get("single_string", [])
    if single_recs:
        ssdf = pd.DataFrame(single_recs)
        qh_avg = ssdf[ssdf["engine"] == "QueryHandler"]["total_time"].mean()
        sqh_avg = ssdf[ssdf["engine"] == "StringQueryHandler_no_lookup"]["total_time"].mean()
        if qh_avg > 0 and sqh_avg > 0:
            pct = (1 - sqh_avg / qh_avg) * 100
            findings.append(
                f"**Single-string speed:** `StringQueryHandler` (no lookup) is ~{pct:.0f}% "
                f"faster than `QueryHandler` per string because it avoids schema-based "
                f"`HedString` construction and uses lightweight string parsing."
            )

    # Schema lookup cost
    sweeps = data.get("factor_sweeps", [])
    if sweeps:
        swdf = pd.DataFrame(sweeps)
        lu = swdf[swdf["factor"] == "schema_lookup"]
        if not lu.empty:
            with_lu = lu[lu["level"] == "with_lookup"]["time"].mean()
            no_lu = lu[lu["level"] == "no_lookup"]["time"].mean()
            if no_lu > 0:
                lu_pct = ((with_lu / no_lu) - 1) * 100
                if abs(lu_pct) < 5:
                    findings.append(
                        "**Schema-lookup overhead:** Enabling `schema_lookup` in "
                        "`StringQueryHandler` has negligible overhead for simple queries "
                        "(cost comes from queries that actually use ancestor matching)."
                    )
                else:
                    findings.append(
                        f"**Schema-lookup overhead:** Enabling `schema_lookup` in "
                        f"`StringQueryHandler` adds ~{lu_pct:.0f}% overhead for "
                        f"ancestor-based queries."
                    )

    # Deep nesting
    if sweeps:
        nest_df = swdf[swdf["factor"] == "nesting_depth"]
        if not nest_df.empty:
            for eng in ["QueryHandler", "SQH_with_lookup"]:
                edf = nest_df[nest_df["engine"] == eng].sort_values("level")
                if len(edf) >= 2:
                    t0 = edf.iloc[0]["time"]
                    t_last = edf.iloc[-1]["time"]
                    if t0 > 0:
                        ratio = t_last / t0
                        findings.append(
                            f"**Nesting depth ({eng}):** At depth {edf.iloc[-1]['level']}, "
                            f"search time is ~{ratio:.1f}× the flat-string time."
                        )

    # basic_search operation limitations
    if sweeps:
        po = swdf[swdf["factor"] == "per_operation"]
        if not po.empty:
            total = po["level"].nunique()
            bs_supported = po[po["engine"] == "basic_search"]["level"].nunique()
            unsupported = total - bs_supported
            if unsupported > 0:
                findings.append(
                    f"**Operation coverage:** `basic_search` supports "
                    f"{bs_supported} of {total} tested operations. "
                    f"The remaining {unsupported} operations (OR, exact groups, logical groups, "
                    f"wildcards `?`/`??`/`???`, quoted terms) require `QueryHandler` or "
                    f"`StringQueryHandler`."
                )

    for f in findings:
        p(f"- {f}")

    # ------------------------------------------------------------------
    # Single-string results
    # ------------------------------------------------------------------
    if single_recs:
        h2("Single-string performance")
        p(
            "Each query was applied to a single HED string of varying complexity. "
            "Times are medians of repeated runs, in milliseconds."
        )
        ssdf = pd.DataFrame(single_recs)
        pivot = (
            ssdf.pivot_table(
                index=["config_label", "query_label"], columns="engine", values="total_time", aggfunc="first"
            )
            * 1000
        )
        table(_pivot_to_md(pivot))

        img("Query × Engine heatmap", f"../figures/{stem}/benchmark_query_heatmap.png")

    # ------------------------------------------------------------------
    # Series results
    # ------------------------------------------------------------------
    if series_recs:
        h2("Series performance")
        p(
            "Whole-series search: each engine processes all rows of a `pd.Series` for a "
            "given query. `basic_search` uses vectorised regex; `search_series` uses "
            "`StringQueryHandler.search()` per row; `QueryHandler_loop` parses each row "
            "into a `HedString` then searches. Times in milliseconds."
        )
        sdf = pd.DataFrame(series_recs)
        pivot = (
            sdf.pivot_table(
                index=["config_label", "query_label"], columns="engine", values="total_time", aggfunc="first"
            )
            * 1000
        )
        table(_pivot_to_md(pivot))

        img("Series scaling", f"../figures/{stem}/benchmark_series_scaling.png")

    # ------------------------------------------------------------------
    # Factor sweeps
    # ------------------------------------------------------------------
    h2("Factor sweeps")
    p("Each sweep varies a single factor while holding others constant, measuring how performance degrades.")

    factor_descriptions = {
        "tag_count": (
            "Number of tags in the HED string (1 to 100). basic_search time is dominated by "
            "regex compilation overhead and stays roughly constant; tree-based engines scale "
            "linearly with the number of nodes to traverse."
        ),
        "nesting_depth": (
            "Parenthesisation depth from 0 (flat) to 20. Deeper nesting increases the tree "
            "walk for QueryHandler/StringQueryHandler. basic_search sees variable cost because "
            "deeper nesting means more delimiter positions for its cartesian-product verification."
        ),
        "repeated_tags": (
            "Repetitions of a target tag (0 to 40). basic_search's `verify_search_delimiters` "
            "uses `itertools.product` over delimiter positions; repeated tags multiply the "
            "search space. Tree-based engines are unaffected."
        ),
        "group_count": (
            "Number of parenthesised groups (1 to 20). More groups mean more children at the "
            "top level for tree traversal."
        ),
        "series_size": (
            "Number of rows in the Series (10 to 5000). basic_search scales sub-linearly "
            "thanks to vectorised pandas regex. All other engines scale linearly (per-row cost "
            "is fixed)."
        ),
        "query_complexity": (
            "Query expression complexity from a bare term to a multi-clause composite. "
            "More clauses = more expression-tree nodes to evaluate per candidate."
        ),
        "schema_lookup": (
            "StringQueryHandler with vs without the `schema_lookup` dictionary. The lookup "
            "enables ancestor-based matching (e.g. `Event` matches `Sensory-event`) at a cost."
        ),
        "string_form": (
            "Short-form vs long-form HED strings. Long-form strings have fully expanded "
            "paths (e.g. `Event/Sensory-event`) and are longer, increasing regex and parse cost."
        ),
        "compile_vs_search": (
            "Decomposition of one-time query compilation cost vs per-string search cost. "
            "Compilation is cheap for both engines; the per-search cost dominates."
        ),
        "per_operation": (
            "Individual operation types tested in isolation. Shows which operations are "
            "expensive for each engine. basic_search shows NaN/— for unsupported operations."
        ),
    }

    # Deep nesting sub-sweeps
    for rec in sweeps:
        factor = rec["factor"]
        if factor.startswith("deep_nest_") and factor not in factor_descriptions:
            query_type = factor.replace("deep_nest_", "").replace("_", " ")
            factor_descriptions[factor] = (
                f"Deep nesting sweep for *{query_type}* queries at depths 1–20. "
                f"Shows how nesting interacts with specific query patterns."
            )

    factors = sorted({rec["factor"] for rec in sweeps})
    for factor in factors:
        h3(factor.replace("_", " ").title())
        desc = factor_descriptions.get(factor, "")
        if desc:
            p(desc)

        # Inline table for this factor
        sub = pd.DataFrame([r for r in sweeps if r["factor"] == factor])
        pivot = sub.pivot_table(index="level", columns="engine", values="time", aggfunc="first") * 1000
        table(_pivot_to_md(pivot))

        img(factor, f"../figures/{stem}/benchmark_sweep_{factor}.png")

    # ------------------------------------------------------------------
    # Real data
    # ------------------------------------------------------------------
    real_recs = data.get("real_data", [])
    if real_recs:
        h2("Real BIDS data")
        n_rows = real_recs[0].get("n_rows", "?")
        p(
            f"Search over {n_rows} rows of real BIDS event data "
            f"(`eeg_ds003645s_hed` test dataset, HED_column values). "
            f"Times in milliseconds."
        )
        rdf = pd.DataFrame(real_recs)
        pivot = rdf.pivot_table(index="query_label", columns="engine", values="total_time", aggfunc="first") * 1000
        table(_pivot_to_md(pivot))
        img("Real BIDS data", f"../figures/{stem}/benchmark_real_data.png")

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------
    h2("Recommendations")
    p(
        "**Choose `basic_search` when:** You need the fastest possible series-level search, "
        "your queries use only simple terms, AND, negation, or descendant wildcards (`*`), "
        "and you don't need schema-aware matching. Ideal for filtering event files where "
        "speed matters and queries are simple."
    )
    p(
        "**Choose `StringQueryHandler` when:** You need the full query language (OR, exact "
        "groups, logical groups, wildcards) but want to avoid the overhead of parsing every "
        "HED string through the schema. `search_series()` is the best general-purpose "
        "option when operating on raw strings from tabular files."
    )
    p(
        "**Choose `QueryHandler` when:** You already have parsed `HedString` objects (e.g. "
        "from validation pipelines), or you need exact schema-validated matching. The "
        "additional overhead comes from `HedString` construction, not the search itself."
    )

    # ------------------------------------------------------------------
    # Methodology
    # ------------------------------------------------------------------
    h2("Methodology")
    p(
        f"- **Timing:** `timeit` with {20 if not data.get('quick') else 10} iterations "
        f"(single-string), {5 if not data.get('quick') else 3} iterations (series), "
        f"{10 if not data.get('quick') else 5} iterations (sweeps). Median of all iterations reported.\n"
        f"- **Schema:** HED 8.4.0 loaded once and reused across all benchmarks.\n"
        f"- **Data generation:** Synthetic strings built from real schema tags with controlled "
        f"tag count, nesting depth, group count, and tag repetition.\n"
        f"- **schema_lookup:** Generated via `generate_schema_lookup(schema)` — a dict mapping "
        f"each short tag to its ancestor tuple.\n"
        f"- **Environment:** Results depend on hardware; relative ratios between engines are "
        f"the meaningful comparison."
    )

    # Write
    report_path = RESULTS_DIR / f"{stem}_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Saved {report_path}")


# ======================================================================
# Main
# ======================================================================


def main(path=None):
    data, stem = load_results(path)

    # Console summaries
    print_single_string_summary(data)
    print_series_summary(data)
    print_sweep_summary(data)
    print_real_data_summary(data)

    # Plots
    print("\nGenerating plots…")
    plot_factor_sweep(data, stem)
    plot_series_scaling(data, stem)
    plot_compile_vs_search(data, stem)
    plot_query_complexity_heatmap(data, stem)
    plot_real_data(data, stem)

    # Markdown
    print("\nGenerating Markdown report…")
    generate_markdown_report(data, stem)

    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate benchmark report")
    parser.add_argument("results_file", nargs="?", default=None, help="Path to results JSON")
    args = parser.parse_args()
    main(args.results_file)
