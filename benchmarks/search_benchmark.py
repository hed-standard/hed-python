"""HED search performance benchmark harness.

Measures compilation time, single-string search time, and series search time
for all three HED search engines across a matrix of query types + data configs.

Usage::

    python search_benchmark.py              # full benchmark
    python search_benchmark.py --quick      # fast smoke-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import timeit
import tracemalloc
from datetime import datetime
from pathlib import Path

import pandas as pd

# Ensure the repo root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hed import HedString, QueryHandler
from hed.models.basic_search import find_matching
from hed.models.string_search import StringQueryHandler, search_series

from data_generator import DataGenerator

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ======================================================================
# Timing helpers
# ======================================================================


def time_it(func, n_runs=5, min_time=0.0):
    """Return (median_seconds, all_times) for calling *func* n_runs times."""
    times = []
    for _ in range(n_runs):
        t = timeit.timeit(func, number=1)
        times.append(t)
    times.sort()
    median = times[len(times) // 2]
    return median, times


def measure_memory(func):
    """Return peak memory (bytes) used by *func*."""
    tracemalloc.start()
    func()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


# ======================================================================
# Query definitions  — (label, basic_search_query, qh_query)
#   basic_search_query = None means "not supported by basic_search"
# ======================================================================

QUERIES = [
    # --- Simple terms ---
    ("single_bare_term", "@Event", "Event"),
    ("single_exact_term", None, '"Event"'),
    ("single_wildcard", "Def/*", "Def/*"),
    # --- Boolean ---
    ("two_term_and", "@Event, @Action", "Event && Action"),
    ("two_term_or", None, "Event || Action"),
    ("negation", "~Event", "~Event"),
    # --- Groups ---
    ("group_nesting", "(Event, Action)", "[Event && Action]"),
    ("exact_group", None, "{Event && Action}"),
    ("exact_group_optional", None, "{Event && Action: Agent}"),
    ("wildcard_child", None, "{Event, ?}"),
    # --- Complex ---
    ("three_term_and", "@Event, @Action, @Agent", "Event && Action && Agent"),
    ("complex_composite", None, "{(Onset || Offset), (Def || {Def-expand}): ???}"),
]


# ======================================================================
# Single-string benchmarks
# ======================================================================


class SingleStringBenchmark:
    """Benchmark each engine on a single HED string."""

    def __init__(self, gen: DataGenerator, n_runs=20):
        self.gen = gen
        self.schema = gen.schema
        self.lookup = gen.lookup
        self.n_runs = n_runs

    def run_all(self, string_configs):
        """Run all queries against all string configurations.

        Parameters:
            string_configs: list of dicts with keys matching DataGenerator.make_string params
                plus a 'label' key for identification.

        Returns:
            list[dict]: One record per (query, config, engine) combination.
        """
        records = []
        for cfg in string_configs:
            label = cfg.pop("label")
            raw = self.gen.make_string(**cfg)
            cfg["label"] = label  # restore

            for q_label, bs_query, qh_query in QUERIES:
                # --- basic_search ---
                if bs_query is not None:
                    rec = self._bench_basic(raw, bs_query, label, q_label)
                    records.append(rec)

                # --- QueryHandler ---
                rec = self._bench_query_handler(raw, qh_query, label, q_label)
                records.append(rec)

                # --- StringQueryHandler (no lookup) ---
                rec = self._bench_string_qh(raw, qh_query, label, q_label, schema_lookup=None, suffix="no_lookup")
                records.append(rec)

                # --- StringQueryHandler (with lookup) ---
                rec = self._bench_string_qh(
                    raw, qh_query, label, q_label, schema_lookup=self.lookup, suffix="with_lookup"
                )
                records.append(rec)

        return records

    def _bench_basic(self, raw, query, cfg_label, q_label):
        series = pd.Series([raw])
        # Compilation (regex build is inside find_matching, not separable easily)
        med, _ = time_it(lambda: find_matching(series, query), self.n_runs)
        matches = int(find_matching(series, query).sum())
        return {
            "engine": "basic_search",
            "query_label": q_label,
            "config_label": cfg_label,
            "query": query,
            "compile_time": None,  # not separable
            "search_time": med,
            "total_time": med,
            "matches": matches,
        }

    def _bench_query_handler(self, raw, query, cfg_label, q_label):
        # Compilation
        comp_med, _ = time_it(lambda: QueryHandler(query), self.n_runs)
        qh = QueryHandler(query)

        # Need to parse HedString each time (part of the cost)
        def do_search():
            hs = HedString(raw, self.schema)
            return qh.search(hs)

        search_med, _ = time_it(do_search, self.n_runs)
        result = do_search()
        return {
            "engine": "QueryHandler",
            "query_label": q_label,
            "config_label": cfg_label,
            "query": query,
            "compile_time": comp_med,
            "search_time": search_med,
            "total_time": comp_med + search_med,
            "matches": len(result),
        }

    def _bench_string_qh(self, raw, query, cfg_label, q_label, schema_lookup, suffix):
        comp_med, _ = time_it(lambda: StringQueryHandler(query), self.n_runs)
        sqh = StringQueryHandler(query)
        search_med, _ = time_it(lambda: sqh.search(raw, schema_lookup=schema_lookup), self.n_runs)
        result = sqh.search(raw, schema_lookup=schema_lookup)
        return {
            "engine": f"StringQueryHandler_{suffix}",
            "query_label": q_label,
            "config_label": cfg_label,
            "query": query,
            "compile_time": comp_med,
            "search_time": search_med,
            "total_time": comp_med + search_med,
            "matches": len(result),
        }


# ======================================================================
# Series benchmarks
# ======================================================================


class SeriesBenchmark:
    """Benchmark each engine on a pd.Series of HED strings."""

    def __init__(self, gen: DataGenerator, n_runs=5):
        self.gen = gen
        self.schema = gen.schema
        self.lookup = gen.lookup
        self.n_runs = n_runs

    def run_all(self, series_configs):
        """Run selected queries against series of varying size.

        Parameters:
            series_configs: list of dicts with keys 'label', 'n_rows', plus
                DataGenerator.make_series params.

        Returns:
            list[dict]: One record per (query, config, engine) combination.
        """
        records = []
        for cfg in series_configs:
            label = cfg.pop("label")
            n_rows = cfg["n_rows"]
            series = self.gen.make_series(**cfg)
            cfg["label"] = label  # restore

            # Use a subset of queries for series (too slow to run all × all)
            # For small series test all; for large ones test representative subset
            queries_to_test = QUERIES if n_rows <= 500 else QUERIES[:6]
            for q_label, bs_query, qh_query in queries_to_test:
                print(f"  Series {label} | {q_label} ({n_rows} rows)…")

                # --- basic_search ---
                if bs_query is not None:
                    rec = self._bench_basic_series(series, bs_query, label, q_label, n_rows)
                    records.append(rec)

                # --- search_series (StringQueryHandler) no lookup ---
                rec = self._bench_search_series(series, qh_query, label, q_label, n_rows, None, "no_lookup")
                records.append(rec)

                # --- search_series (StringQueryHandler) with lookup ---
                rec = self._bench_search_series(series, qh_query, label, q_label, n_rows, self.lookup, "with_lookup")
                records.append(rec)

                # --- QueryHandler loop ---
                rec = self._bench_qh_loop(series, qh_query, label, q_label, n_rows)
                records.append(rec)

        return records

    def _bench_basic_series(self, series, query, cfg_label, q_label, n_rows):
        med, _ = time_it(lambda: find_matching(series, query), self.n_runs)
        matches = int(find_matching(series, query).sum())
        return {
            "engine": "basic_search",
            "query_label": q_label,
            "config_label": cfg_label,
            "n_rows": n_rows,
            "total_time": med,
            "per_row": med / n_rows,
            "matches": matches,
        }

    def _bench_search_series(self, series, query, cfg_label, q_label, n_rows, lookup, suffix):
        med, _ = time_it(lambda: search_series(series, query, schema_lookup=lookup), self.n_runs)
        matches = int(search_series(series, query, schema_lookup=lookup).sum())
        return {
            "engine": f"search_series_{suffix}",
            "query_label": q_label,
            "config_label": cfg_label,
            "n_rows": n_rows,
            "total_time": med,
            "per_row": med / n_rows,
            "matches": matches,
        }

    def _bench_qh_loop(self, series, query, cfg_label, q_label, n_rows):
        qh = QueryHandler(query)
        schema = self.schema

        def do_all():
            for s in series:
                if pd.notna(s) and s:
                    hs = HedString(s, schema)
                    qh.search(hs)

        med, _ = time_it(do_all, self.n_runs)
        # count matches
        count = 0
        for s in series:
            if pd.notna(s) and s:
                hs = HedString(s, schema)
                if qh.search(hs):
                    count += 1
        return {
            "engine": "QueryHandler_loop",
            "query_label": q_label,
            "config_label": cfg_label,
            "n_rows": n_rows,
            "total_time": med,
            "per_row": med / n_rows,
            "matches": count,
        }


# ======================================================================
# Factor sweeps
# ======================================================================


class FactorSweep:
    """Isolate the effect of one variable on performance."""

    def __init__(self, gen: DataGenerator, n_runs=10):
        self.gen = gen
        self.schema = gen.schema
        self.lookup = gen.lookup
        self.n_runs = n_runs

    def sweep_tag_count(self, tag_counts=(1, 5, 10, 25, 50, 100)):
        """Vary number of tags per string, fixed simple query."""
        query = "Event"
        bs_query = "@Event"
        records = []
        for nt in tag_counts:
            raw = self.gen.make_string(n_tags=nt)
            for engine, med in self._bench_all_engines(raw, query, bs_query):
                records.append({"factor": "tag_count", "level": nt, "engine": engine, "time": med})
        return records

    def sweep_nesting_depth(self, depths=(0, 1, 2, 3, 5, 10, 15, 20)):
        """Vary nesting depth using deeply nested strings."""
        query = "Event"
        bs_query = "@Event"
        records = []
        for d in depths:
            if d == 0:
                raw = self.gen.make_string(n_tags=10)
            else:
                raw = self.gen.make_deeply_nested_string(depth=d, tags_per_level=2)
            for engine, med in self._bench_all_engines(raw, query, bs_query):
                records.append({"factor": "nesting_depth", "level": d, "engine": engine, "time": med})
        return records

    def sweep_repeated_tags(self, repeat_counts=(0, 3, 5, 10, 20, 40)):
        """Vary duplicate tag count — stresses basic_search cartesian product.

        Uses strings that actually contain 'Event' and 'Action' as the repeated
        tags so the group query ``(Event, Action)`` triggers combinatorial matching.
        """
        query = "(Event, Action)"
        bs_query = "(Event, Action)"
        records = []
        for r in repeat_counts:
            raw = self.gen.make_string_with_specific_tags(
                ["Event", "Action"], n_extra=3, n_groups=1, depth=1, repeats=r
            )
            for engine, med in self._bench_all_engines(raw, query, bs_query):
                records.append({"factor": "repeated_tags", "level": r, "engine": engine, "time": med})
        return records

    def sweep_group_count(self, group_counts=(0, 1, 5, 10, 20)):
        """Vary number of groups per string."""
        query = "Event"
        bs_query = "@Event"
        records = []
        for ng in group_counts:
            raw = self.gen.make_string(n_tags=max(10, ng * 2 + 3), n_groups=ng, depth=1)
            for engine, med in self._bench_all_engines(raw, query, bs_query):
                records.append({"factor": "group_count", "level": ng, "engine": engine, "time": med})
        return records

    def sweep_series_size(self, sizes=(10, 100, 500, 1000, 5000)):
        """Vary series length."""
        query = "Event"
        bs_query = "@Event"
        records = []
        for n in sizes:
            series = self.gen.make_series(n_rows=n, n_tags=10, n_groups=2, depth=1)
            for engine, med in self._bench_series_engines(series, query, bs_query, n):
                records.append({"factor": "series_size", "level": n, "engine": engine, "time": med, "per_row": med / n})
        return records

    def sweep_query_complexity(self):
        """Compare queries of increasing complexity."""
        raw = self.gen.make_string(n_tags=20, n_groups=5, depth=2)
        complexity_queries = [
            ("1_single_term", "@Event", "Event"),
            ("2_two_and", "@Event, @Action", "Event && Action"),
            ("3_three_and", "@Event, @Action, @Agent", "Event && Action && Agent"),
            ("4_or", None, "Event || Action"),
            ("5_negation", "~Event", "~Event"),
            ("6_group", "(Event, Action)", "[Event && Action]"),
            ("7_exact", None, "{Event && Action}"),
            ("8_complex", None, "{(Onset || Offset), (Def || {Def-expand}): ???}"),
        ]
        records = []
        for clabel, bs_q, qh_q in complexity_queries:
            for engine, med in self._bench_all_engines(raw, qh_q, bs_q):
                records.append({"factor": "query_complexity", "level": clabel, "engine": engine, "time": med})
        return records

    def sweep_schema_lookup(self):
        """Compare StringQueryHandler with vs without schema_lookup."""
        raw = self.gen.make_string(n_tags=15, n_groups=3, depth=1)
        query = "Event"
        sqh = StringQueryHandler(query)
        records = []
        for with_lookup in [False, True]:
            lk = self.lookup if with_lookup else None
            label = "with_lookup" if with_lookup else "no_lookup"
            med, _ = time_it(lambda lk=lk: sqh.search(raw, schema_lookup=lk), self.n_runs)
            records.append({"factor": "schema_lookup", "level": label, "engine": "StringQueryHandler", "time": med})
        return records

    def sweep_string_form(self):
        """Compare short vs long form strings."""
        query = "Event"
        bs_query = "@Event"
        records = []
        for form in ["short", "long"]:
            raw = self.gen.make_string(n_tags=15, n_groups=3, depth=1, form=form)
            for engine, med in self._bench_all_engines(raw, query, bs_query):
                records.append({"factor": "string_form", "level": form, "engine": engine, "time": med})
        return records

    def sweep_compilation_vs_search(self):
        """Separate compilation cost from per-search cost."""
        raw = self.gen.make_string(n_tags=15, n_groups=3, depth=1)
        query = "Event"
        records = []

        # QueryHandler
        comp, _ = time_it(lambda: QueryHandler(query), self.n_runs)
        qh = QueryHandler(query)

        def qh_search():
            hs = HedString(raw, self.schema)
            qh.search(hs)

        search_med, _ = time_it(qh_search, self.n_runs)
        records.append({"factor": "compile_vs_search", "level": "compile", "engine": "QueryHandler", "time": comp})
        records.append({"factor": "compile_vs_search", "level": "search", "engine": "QueryHandler", "time": search_med})

        # StringQueryHandler
        comp2, _ = time_it(lambda: StringQueryHandler(query), self.n_runs)
        sqh = StringQueryHandler(query)
        search_med2, _ = time_it(lambda: sqh.search(raw, schema_lookup=self.lookup), self.n_runs)
        records.append(
            {"factor": "compile_vs_search", "level": "compile", "engine": "StringQueryHandler", "time": comp2}
        )
        records.append(
            {"factor": "compile_vs_search", "level": "search", "engine": "StringQueryHandler", "time": search_med2}
        )

        return records

    def sweep_per_operation(self):
        """Test every query operation type on the same string.

        Uses a string with enough structure to exercise all operations:
        groups, nested groups, Def tags, Onset, etc.
        """
        # Build a string with structure that can match all query types
        raw = (
            "Sensory-event, Action, Agent, "
            "(Event, (Onset, (Def/MyDef))), "
            "(Offset, Item, (Def-expand/MyDef, (Red, Blue))), "
            "(Visual-presentation, Square, Green)"
        )

        operation_queries = [
            # (label, basic_search_query, qh_query)
            ("bare_term", "@Event", "Event"),
            ("exact_quoted", None, '"Sensory-event"'),
            ("wildcard_prefix", "Def/*", "Def/*"),
            ("and_2", "@Event, @Action", "Event && Action"),
            ("and_3", "@Event, @Action, @Agent", "Event && Action && Agent"),
            ("or", None, "Event || Action"),
            ("negation", "~Event", "~Event"),
            ("nested_group_[]", "(Event, Action)", "[Event && Action]"),
            ("exact_group_{}", None, "{Event && Action}"),
            ("exact_optional_{:}", None, "{Event && Action: Agent}"),
            ("wildcard_?", None, "{Event, ?}"),
            ("wildcard_??", None, "{Event, ??}"),
            ("wildcard_???", None, "{Event, ???}"),
            ("descendant_nested", None, "[Def && Onset]"),
            ("complex_onset_def", None, "{(Onset || Offset), (Def || {Def-expand}): ???}"),
            ("deep_and_chain", "@Event, @Action, @Agent, @Item, @Red", "Event && Action && Agent && Item && Red"),
            ("nested_or_and", None, "(Event || Sensory-event) && (Action || Agent)"),
            ("double_negation", None, "~(~Event)"),
        ]

        records = []
        for op_label, bs_q, qh_q in operation_queries:
            for engine, med in self._bench_all_engines(raw, qh_q, bs_q):
                records.append({"factor": "per_operation", "level": op_label, "engine": engine, "time": med})
        return records

    def sweep_deep_nesting_by_query(self):
        """Test how different query types perform on deeply nested strings."""
        depths = [1, 5, 10, 20]
        queries = [
            ("bare_term", "@Event", "Event"),
            ("two_and", "@Event, @Action", "Event && Action"),
            ("group_match", "(Event, Action)", "[Event && Action]"),
            ("exact_group", None, "{Event && Action}"),
            ("negation", "~Event", "~Event"),
        ]
        records = []
        for d in depths:
            raw = self.gen.make_deeply_nested_string(depth=d, tags_per_level=2)
            for q_label, bs_q, qh_q in queries:
                for engine, med in self._bench_all_engines(raw, qh_q, bs_q):
                    records.append(
                        {
                            "factor": f"deep_nest_{q_label}",
                            "level": d,
                            "engine": engine,
                            "time": med,
                        }
                    )
        return records

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bench_all_engines(self, raw, qh_query, bs_query=None):
        """Yield (engine_name, median_time) for all engines on a single string."""
        series1 = pd.Series([raw])

        # basic_search
        if bs_query is not None:
            med, _ = time_it(lambda: find_matching(series1, bs_query), self.n_runs)
            yield "basic_search", med

        # QueryHandler
        qh = QueryHandler(qh_query)

        def qh_search():
            hs = HedString(raw, self.schema)
            qh.search(hs)

        med, _ = time_it(qh_search, self.n_runs)
        yield "QueryHandler", med

        # StringQueryHandler no lookup
        sqh = StringQueryHandler(qh_query)
        med, _ = time_it(lambda: sqh.search(raw, schema_lookup=None), self.n_runs)
        yield "SQH_no_lookup", med

        # StringQueryHandler with lookup
        med, _ = time_it(lambda: sqh.search(raw, schema_lookup=self.lookup), self.n_runs)
        yield "SQH_with_lookup", med

    def _bench_series_engines(self, series, qh_query, bs_query, n_rows):
        """Yield (engine_name, median_time) for series-level engines."""
        # basic_search
        if bs_query is not None:
            med, _ = time_it(lambda: find_matching(series, bs_query), max(3, self.n_runs // 2))
            yield "basic_search", med

        # search_series no lookup
        med, _ = time_it(lambda: search_series(series, qh_query, schema_lookup=None), max(3, self.n_runs // 2))
        yield "search_series_no_lookup", med

        # search_series with lookup
        med, _ = time_it(lambda: search_series(series, qh_query, schema_lookup=self.lookup), max(3, self.n_runs // 2))
        yield "search_series_with_lookup", med

        # QueryHandler loop
        qh = QueryHandler(qh_query)
        schema = self.schema

        def qh_loop():
            for s in series:
                if pd.notna(s) and s:
                    hs = HedString(s, schema)
                    qh.search(hs)

        med, _ = time_it(qh_loop, max(3, self.n_runs // 2))
        yield "QueryHandler_loop", med


# ======================================================================
# Main orchestrator
# ======================================================================


def run_full_benchmark(quick=False):
    """Run the complete benchmark suite and save results."""
    print("Initialising DataGenerator (loading schema)…")
    gen = DataGenerator()

    n_single = 10 if quick else 20
    n_series = 3 if quick else 5
    n_sweep = 5 if quick else 10

    # ------------------------------------------------------------------
    # 1. Single-string benchmark
    # ------------------------------------------------------------------
    print("\n=== Single-string benchmarks ===")
    ssb = SingleStringBenchmark(gen, n_runs=n_single)

    string_configs = [
        {"label": "tiny_1tag", "n_tags": 1},
        {"label": "small_5tag", "n_tags": 5},
        {"label": "medium_10tag", "n_tags": 10, "n_groups": 2, "depth": 1},
        {"label": "large_25tag", "n_tags": 25, "n_groups": 5, "depth": 2},
        {"label": "xlarge_50tag", "n_tags": 50, "n_groups": 10, "depth": 2},
    ]
    if not quick:
        string_configs.append({"label": "xxlarge_100tag", "n_tags": 100, "n_groups": 15, "depth": 3})
    single_results = ssb.run_all(string_configs)
    print(f"  Collected {len(single_results)} single-string records.")

    # ------------------------------------------------------------------
    # 2. Series benchmark
    # ------------------------------------------------------------------
    print("\n=== Series benchmarks ===")
    sb = SeriesBenchmark(gen, n_runs=n_series)

    if quick:
        series_sizes = [10, 100, 500]
    else:
        series_sizes = [10, 100, 500, 1000, 5000]

    series_configs = []
    for n in series_sizes:
        series_configs.append({"label": f"homo_{n}", "n_rows": n, "n_tags": 10, "n_groups": 2, "depth": 1})
    for n in [100, 1000] if not quick else [100]:
        series_configs.append({"label": f"hetero_{n}", "n_rows": n, "n_tags": 10, "heterogeneous": True})

    series_results = sb.run_all(series_configs)
    print(f"  Collected {len(series_results)} series records.")

    # ------------------------------------------------------------------
    # 3. Factor sweeps
    # ------------------------------------------------------------------
    print("\n=== Factor sweeps ===")
    fs = FactorSweep(gen, n_runs=n_sweep)

    sweep_results = []
    for name, method in [
        ("tag_count", fs.sweep_tag_count),
        ("nesting_depth", fs.sweep_nesting_depth),
        ("repeated_tags", fs.sweep_repeated_tags),
        ("group_count", fs.sweep_group_count),
        ("series_size", fs.sweep_series_size),
        ("query_complexity", fs.sweep_query_complexity),
        ("schema_lookup", fs.sweep_schema_lookup),
        ("string_form", fs.sweep_string_form),
        ("compile_vs_search", fs.sweep_compilation_vs_search),
        ("per_operation", fs.sweep_per_operation),
        ("deep_nesting_by_query", fs.sweep_deep_nesting_by_query),
    ]:
        print(f"  Sweep: {name}")
        sweep_results.extend(method())

    print(f"  Collected {len(sweep_results)} sweep records.")

    # ------------------------------------------------------------------
    # 4. Real data benchmark
    # ------------------------------------------------------------------
    print("\n=== Real data benchmark ===")
    real_series = gen.load_real_data()
    real_n = len(real_series)
    print(f"  Real data: {real_n} rows")

    real_results = []
    for q_label, bs_query, qh_query in QUERIES:
        if bs_query is not None:
            med, _ = time_it(lambda bs_query=bs_query: find_matching(real_series, bs_query), n_series)
            real_results.append(
                {
                    "engine": "basic_search",
                    "query_label": q_label,
                    "total_time": med,
                    "per_row": med / real_n,
                    "n_rows": real_n,
                }
            )

        med, _ = time_it(
            lambda qh_query=qh_query: search_series(real_series, qh_query, schema_lookup=gen.lookup), n_series
        )
        real_results.append(
            {
                "engine": "search_series",
                "query_label": q_label,
                "total_time": med,
                "per_row": med / real_n,
                "n_rows": real_n,
            }
        )

        qh = QueryHandler(qh_query)
        schema = gen.schema

        def qh_loop(qh=qh, schema=schema):
            for s in real_series:
                if pd.notna(s) and s:
                    hs = HedString(s, schema)
                    qh.search(hs)

        med, _ = time_it(qh_loop, n_series)
        real_results.append(
            {
                "engine": "QueryHandler_loop",
                "query_label": q_label,
                "total_time": med,
                "per_row": med / real_n,
                "n_rows": real_n,
            }
        )

    print(f"  Collected {len(real_results)} real-data records.")

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "timestamp": timestamp,
        "quick": quick,
        "single_string": single_results,
        "series": series_results,
        "factor_sweeps": sweep_results,
        "real_data": real_results,
    }
    out_path = RESULTS_DIR / f"benchmark_{timestamp}.json"
    out_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    return output


# ======================================================================
# Entry point
# ======================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HED search benchmark")
    parser.add_argument("--quick", action="store_true", help="Reduced run for smoke testing")
    args = parser.parse_args()
    run_full_benchmark(quick=args.quick)
