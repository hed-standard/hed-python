"""Generate synthetic and real HED strings/Series for benchmarking.

Usage::

    from data_generator import DataGenerator
    gen = DataGenerator()  # loads schema 8.3.0
    s = gen.make_string(n_tags=10, n_groups=2, depth=1)
    series = gen.make_series(n_rows=1000, n_tags=10, n_groups=2, depth=1)
    real = gen.load_real_data(tile_to=5000)
"""

from __future__ import annotations

import os
import random

import pandas as pd

from hed.schema import load_schema_version
from hed.models.schema_lookup import generate_schema_lookup
from hed.models.tabular_input import TabularInput
from hed.models.df_util import convert_to_form


class DataGenerator:
    """Build synthetic and real HED data for benchmarking."""

    def __init__(self, schema_version="8.3.0", seed=42):
        self.schema = load_schema_version(schema_version)
        self.lookup = generate_schema_lookup(self.schema)
        self._rng = random.Random(seed)

        # Collect real tag short names from the schema for realistic generation
        self._all_tags = []
        for name, entry in self.schema.tags.items():
            if name.endswith("/#"):
                continue
            short = getattr(entry, "short_tag_name", name.rsplit("/", 1)[-1])
            self._all_tags.append(short)

        # Separate leaf vs non-leaf for variety
        self._tags = list(self._all_tags)

    # ------------------------------------------------------------------
    # Single string generation
    # ------------------------------------------------------------------

    def _pick_tags(self, n, repeats=0):
        """Pick *n* unique tags, then append *repeats* duplicates of the first."""
        chosen = self._rng.sample(self._tags, min(n, len(self._tags)))
        if repeats and chosen:
            chosen.extend([chosen[0]] * repeats)
        return chosen

    def make_string(self, n_tags=5, n_groups=0, depth=0, repeats=0, form="short"):
        """Build a single synthetic HED string.

        Parameters:
            n_tags: Total number of tag tokens (spread across top-level and groups).
            n_groups: Number of parenthesised groups to create.
            depth: Maximum nesting depth inside groups.
            repeats: Number of duplicate copies of the first tag to append.
            form: 'short' | 'long' — tag form.

        Returns:
            str: A raw HED string.
        """
        tags = self._pick_tags(n_tags, repeats=repeats)
        if form == "long":
            tags = self._to_long(tags)

        if n_groups == 0 or depth == 0:
            return ", ".join(tags)

        # Distribute tags across top-level and groups
        top_count = max(1, n_tags - n_groups * 2)
        top_tags = tags[:top_count]
        remaining = tags[top_count:]

        parts = list(top_tags)
        for i in range(n_groups):
            group_tags = remaining[i * 2 : i * 2 + 2] if i * 2 + 2 <= len(remaining) else remaining[i * 2 :]
            if not group_tags:
                group_tags = [self._rng.choice(self._tags)]
            parts.append(self._wrap_group(group_tags, depth))

        return ", ".join(parts)

    def _wrap_group(self, tags, depth):
        """Recursively nest *tags* to the given *depth*."""
        inner = ", ".join(tags)
        result = f"({inner})"
        for _ in range(depth - 1):
            extra = self._rng.choice(self._tags)
            result = f"({extra}, {result})"
        return result

    def make_deeply_nested_string(self, depth, tags_per_level=2):
        """Build a string with deep nesting: (A, (B, (C, ...))).

        Parameters:
            depth: Number of nesting levels.
            tags_per_level: Tags at each level.

        Returns:
            str: Deeply nested HED string.
        """
        tags = self._pick_tags(depth * tags_per_level + 2)
        # Build inside-out
        inner = ", ".join(tags[:tags_per_level])
        for i in range(depth):
            level_tags = tags[tags_per_level + i * tags_per_level : tags_per_level + (i + 1) * tags_per_level]
            if not level_tags:
                level_tags = [self._rng.choice(self._tags)]
            inner = f"({', '.join(level_tags)}, ({inner}))"
        return f"Event, Action, {inner}"

    def make_string_with_specific_tags(self, target_tags, n_extra=5, n_groups=2, depth=1, repeats=0):
        """Build a string guaranteed to contain specific tags.

        Parameters:
            target_tags: List of tag names to include.
            n_extra: Number of random extra tags.
            n_groups: Number of groups.
            depth: Nesting depth.
            repeats: How many times to repeat the first target tag.

        Returns:
            str: HED string containing the target tags.
        """
        extra = self._pick_tags(n_extra)
        all_tags = list(target_tags) + extra + [target_tags[0]] * repeats
        self._rng.shuffle(all_tags)

        if n_groups == 0 or depth == 0:
            return ", ".join(all_tags)

        top_count = max(1, len(all_tags) - n_groups * 2)
        top_tags = all_tags[:top_count]
        remaining = all_tags[top_count:]

        parts = list(top_tags)
        for i in range(n_groups):
            group_tags = remaining[i * 2 : i * 2 + 2] if i * 2 + 2 <= len(remaining) else remaining[i * 2 :]
            if not group_tags:
                group_tags = [self._rng.choice(self._tags)]
            parts.append(self._wrap_group(group_tags, depth))

        return ", ".join(parts)

    def _to_long(self, short_tags):
        """Convert short tag names to long form via the schema."""
        from hed.models.hed_tag import HedTag

        out = []
        for t in short_tags:
            try:
                out.append(HedTag(t, self.schema).long_tag)
            except Exception:
                out.append(t)
        return out

    # ------------------------------------------------------------------
    # Series generation
    # ------------------------------------------------------------------

    def make_series(self, n_rows, *, n_tags=5, n_groups=0, depth=0, repeats=0, form="short", heterogeneous=False):
        """Build a pd.Series of HED strings.

        Parameters:
            n_rows: Number of rows.
            n_tags, n_groups, depth, repeats, form: Passed to make_string.
            heterogeneous: If True, randomise parameters per row.
        """
        if heterogeneous:
            rows = []
            for _ in range(n_rows):
                nt = self._rng.choice([3, 5, 10, 15, 25])
                ng = self._rng.choice([0, 1, 2, 5])
                d = self._rng.choice([0, 1, 2])
                rows.append(self.make_string(n_tags=nt, n_groups=ng, depth=d, form=form))
            return pd.Series(rows)
        else:
            # Homogeneous: one template, tiled
            template = self.make_string(n_tags=n_tags, n_groups=n_groups, depth=depth, repeats=repeats, form=form)
            return pd.Series([template] * n_rows)

    # ------------------------------------------------------------------
    # Real data
    # ------------------------------------------------------------------

    def load_real_data(self, tile_to=None, form="short"):
        """Load the FacePerception BIDS events and return a HED Series.

        Parameters:
            tile_to: If set, tile the series up to this many rows.
            form: 'short' | 'long'.

        Returns:
            pd.Series of HED strings.
        """
        bids_root = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "..", "tests", "data", "bids_tests", "eeg_ds003645s_hed")
        )
        sidecar = os.path.join(bids_root, "task-FacePerception_events.json")
        events = os.path.join(bids_root, "sub-002", "eeg", "sub-002_task-FacePerception_run-1_events.tsv")
        tab = TabularInput(events, sidecar)
        series = tab.series_filtered

        if form == "long":
            df = series.copy()
            convert_to_form(df, self.schema, "long_tag")
            series = df

        if tile_to and tile_to > len(series):
            reps = (tile_to // len(series)) + 1
            series = pd.Series(list(series) * reps).iloc[:tile_to].reset_index(drop=True)

        return series


# Quick self-test
if __name__ == "__main__":
    gen = DataGenerator()
    print(f"Schema tags available: {len(gen._tags)}")
    print(f"Sample string (5 tags):  {gen.make_string(5)}")
    print(f"Sample string (10 tags, 2 groups, depth 2): {gen.make_string(10, 2, 2)}")
    print(f"Sample string (5 tags, 3 repeats): {gen.make_string(5, repeats=3)}")
    print(f"Real data rows: {len(gen.load_real_data())}")
    print(f"Tiled to 500:   {len(gen.load_real_data(tile_to=500))}")
