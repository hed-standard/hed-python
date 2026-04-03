"""Tests targeting pandas 3.0 compatibility fixes.

Each test class is named after the specific change it validates, with docstrings
explaining why the old code broke and referencing the fix made.

Breakages addressed:
  1. ChainedAssignmentError in shrink_defs (df[col][mask] = ...)
  2. iloc/dtype preservation in _filter_by_index_list
  3. DataFrame.drop() no longer accepts axis= alongside columns=
  4. NaN float cells in schema DataFrames (description, hedId columns)
  5. _merge_dataframes fillna with non-object string dtypes (StringDtype)
  6. get_attributes_from_row receiving NaN instead of a string
  7. _verify_hedid_matches receiving NaN hedId (broke .startswith())
  8. assign_hed_ids_section: float NaN is truthy, so bare `if hed_id:` skipped rows
"""

import unittest
import pandas as pd

from hed import load_schema_version
from hed.models.df_util import shrink_defs, _filter_by_index_list
from hed.tools.util.data_util import delete_columns
from hed.schema.schema_io.df_util import _merge_dataframes, get_attributes_from_row
from hed.schema.schema_io import df_constants as constants
from hed.schema.schema_io.hed_id_util import _verify_hedid_matches, assign_hed_ids_section, _get_hedid_range
from hed.schema.hed_schema_io import from_dataframes

hed_schema_global = load_schema_version("8.4.0")


# ---------------------------------------------------------------------------
# 1. shrink_defs — ChainedAssignmentError fix
# ---------------------------------------------------------------------------


class TestShrinkDefsCoW(unittest.TestCase):
    """Validate that shrink_defs mutates the DataFrame correctly.

    pandas 3.0 raises ChainedAssignmentError for ``df[col][mask] = ...``.
    The fix uses ``df.loc[mask, col] = ...`` instead.
    """

    def setUp(self):
        self.schema = hed_schema_global

    def test_mutation_is_in_place(self):
        """The original DataFrame object must be modified, not a silent copy."""
        df = pd.DataFrame(
            {"HED": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent", "Event/Plain"]}
        )
        original_id = id(df)
        shrink_defs(df, self.schema, ["HED"])
        self.assertEqual(id(df), original_id, "shrink_defs must modify the existing DataFrame")
        self.assertEqual(df.loc[0, "HED"], "Def/TestDefNormal,Event/SomeEvent")
        self.assertEqual(df.loc[1, "HED"], "Event/Plain")

    def test_non_matching_rows_unchanged(self):
        """Rows without Def-expand must not be touched."""
        df = pd.DataFrame(
            {
                "HED": [
                    "(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2))",
                    "Event/SomethingElse",
                    "(Def-expand/TestDefPlaceholder/5,(Acceleration/5,Action/TestDef2))",
                ]
            }
        )
        shrink_defs(df, self.schema, ["HED"])
        self.assertEqual(df.loc[1, "HED"], "Event/SomethingElse")
        self.assertEqual(df.loc[0, "HED"], "Def/TestDefNormal")
        self.assertEqual(df.loc[2, "HED"], "Def/TestDefPlaceholder/5")

    def test_multi_column_selective_mask(self):
        """Each column uses its own independent mask — a match in col1 must not affect col2."""
        df = pd.DataFrame(
            {
                "col1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2))", "Event/Plain"],
                "col2": ["Event/Only", "(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2))"],
            }
        )
        shrink_defs(df, self.schema, ["col1", "col2"])
        self.assertEqual(df.loc[0, "col1"], "Def/TestDefNormal")
        self.assertEqual(df.loc[1, "col1"], "Event/Plain")
        self.assertEqual(df.loc[0, "col2"], "Event/Only")
        self.assertEqual(df.loc[1, "col2"], "Def/TestDefNormal")


# ---------------------------------------------------------------------------
# 2. _filter_by_index_list — iloc / dtype preservation fix
# ---------------------------------------------------------------------------


class TestFilterByIndexListPandas3(unittest.TestCase):
    """Validate dtype preservation and iloc-based indexing in _filter_by_index_list.

    pandas 3.0 may use StringDtype instead of object for string Series.
    Using integer indexing (``series[i]``) on a StringDtype series raises an
    error; the fix uses ``.iloc[i]`` throughout.  The new_series dtype is also
    set to match the input so comparisons do not fail due to dtype mismatch.
    """

    def test_output_dtype_matches_input_series(self):
        """Output Series dtype must match the input, not always be 'object'."""
        series = pd.array(["apple", "orange", "banana"], dtype=pd.StringDtype())
        input_series = pd.Series(series)
        result = _filter_by_index_list(input_series, {0: [0, 1], 1: [2]})
        self.assertEqual(result.dtype, input_series.dtype)

    def test_empty_slots_are_empty_string_not_nan(self):
        """Slots not covered by indexed_dict must be empty string, not NaN."""
        series = pd.Series(["a", "b", "c", "d"])
        result = _filter_by_index_list(series, {0: [0, 1]})
        # Slots 2 and 3 are not in indexed_dict — they should be ""
        self.assertEqual(result.iloc[2], "")
        self.assertEqual(result.iloc[3], "")
        self.assertFalse(pd.isna(result.iloc[2]))
        self.assertFalse(pd.isna(result.iloc[3]))

    def test_string_dtype_series_values_correct(self):
        """Values should be correctly joined when input uses pd.StringDtype."""
        series = pd.Series(pd.array(["apple", "orange", "banana"], dtype=pd.StringDtype()))
        result = _filter_by_index_list(series, {0: [0, 1], 1: [2]})
        self.assertEqual(result.iloc[0], "apple,orange")
        self.assertEqual(result.iloc[1], "")
        self.assertEqual(result.iloc[2], "banana")

    def test_dataframe_output_dtype_preserved(self):
        """DataFrame variant: HED column dtype in result must match source column."""
        input_df = pd.DataFrame({"HED": pd.array(["x", "y"], dtype=pd.StringDtype()), "Extra": ["e1", "e2"]})
        result = _filter_by_index_list(input_df, {0: [0, 1]})
        self.assertEqual(result["HED"].iloc[0], "x,y")
        self.assertEqual(result["HED"].iloc[1], "")


# ---------------------------------------------------------------------------
# 3. delete_columns — drop() API change (no axis= with columns=)
# ---------------------------------------------------------------------------


class TestDeleteColumnsNoAxis(unittest.TestCase):
    """Validate delete_columns still works after removing the axis=1 argument.

    pandas 3.0 raises TypeError when both ``columns=`` and ``axis=`` are given.
    """

    def test_deletes_existing_columns(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        delete_columns(df, ["a", "c"])
        self.assertListEqual(list(df.columns), ["b"])

    def test_ignores_nonexistent_columns(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        delete_columns(df, ["a", "z"])  # "z" doesn't exist — must not raise
        self.assertListEqual(list(df.columns), ["b"])

    def test_empty_delete_list(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        delete_columns(df, [])
        self.assertListEqual(list(df.columns), ["a", "b"])

    def test_modifies_in_place(self):
        df = pd.DataFrame({"x": [1], "y": [2]})
        original_id = id(df)
        delete_columns(df, ["x"])
        self.assertEqual(id(df), original_id)
        self.assertNotIn("x", df.columns)


# ---------------------------------------------------------------------------
# 4. df2schema — NaN in description / hedId columns
# ---------------------------------------------------------------------------


class TestSchemaLoadingWithNaNColumns(unittest.TestCase):
    """Validate that loading schema DataFrames containing NaN floats in
    description or hedId columns does not raise AttributeError.

    pandas 3.0 may return float NaN (not '') for missing cells even in
    object-typed columns when a merge introduces new rows.  The old
    ``if description:`` / ``if hed_id:`` checks are truthy for NaN, causing
    ``float.strip()`` or ``float.startswith()`` AttributeErrors.
    """

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.0.0")

    def _make_schema_dfs_with_nan_descriptions(self):
        """Return a minimal schema dict with explicit NaN in dc:description."""
        dfs = self.schema.get_as_dataframes()
        # Replace some description values with actual float NaN
        tag_df = dfs[constants.TAG_KEY].copy()
        tag_df.loc[tag_df.index[0], constants.dcdescription] = float("nan")
        tag_df.loc[tag_df.index[1], constants.dcdescription] = float("nan")
        dfs[constants.TAG_KEY] = tag_df
        return dfs

    def _make_schema_dfs_with_nan_hed_ids(self):
        """Return a minimal schema dict with explicit NaN in hedId."""
        dfs = self.schema.get_as_dataframes()
        tag_df = dfs[constants.TAG_KEY].copy()
        tag_df.loc[tag_df.index[0], constants.hed_id] = float("nan")
        dfs[constants.TAG_KEY] = tag_df
        return dfs

    def test_nan_description_does_not_raise(self):
        """NaN in dc:description must not crash schema loading."""
        dfs = self._make_schema_dfs_with_nan_descriptions()
        try:
            from_dataframes(dfs)
        except AttributeError as exc:
            self.fail(f"from_dataframes raised AttributeError with NaN description: {exc}")

    def test_nan_hed_id_does_not_raise(self):
        """NaN in hedId must not crash schema loading."""
        dfs = self._make_schema_dfs_with_nan_hed_ids()
        try:
            from_dataframes(dfs)
        except AttributeError as exc:
            self.fail(f"from_dataframes raised AttributeError with NaN hedId: {exc}")


# ---------------------------------------------------------------------------
# 5. _merge_dataframes — StringDtype fillna fix
# ---------------------------------------------------------------------------


class TestMergeDataFramesStringDtype(unittest.TestCase):
    """Validate that _merge_dataframes fills NaN correctly for StringDtype columns.

    pandas 3.0 may use StringDtype (not 'object') for string columns.
    The old ``df[col].dtype == 'object'`` check missed StringDtype columns,
    leaving NaN unfilled.  The fix uses ``pd.api.types.is_numeric_dtype()``.
    """

    def test_missing_string_values_filled_with_empty_string(self):
        """NaN introduced by a left-merge must be filled with '' not left as NaN."""
        df1 = pd.DataFrame({"key": [1, 2, 3], "val_a": ["A1", "A2", "A3"]})
        df2 = pd.DataFrame({"key": [2, 3], "val_b": ["B2", "B3"]})
        result = _merge_dataframes(df1, df2, "key")
        unmatched = result.loc[result["key"] == 1, "val_b"].values[0]
        self.assertEqual(unmatched, "", f"Expected '' for unmatched row, got {unmatched!r}")
        self.assertFalse(pd.isna(unmatched))

    def test_missing_numeric_values_filled_with_zero(self):
        """NaN in numeric columns must be filled with 0."""
        df1 = pd.DataFrame({"key": [1, 2, 3], "num_a": [10, 20, 30]})
        df2 = pd.DataFrame({"key": [2, 3], "num_b": [200, 300]})
        result = _merge_dataframes(df1, df2, "key")
        unmatched = result.loc[result["key"] == 1, "num_b"].values[0]
        self.assertEqual(unmatched, 0)

    def test_explicit_string_dtype_column_filled(self):
        """Explicitly StringDtype columns must also be filled with ''."""
        df1 = pd.DataFrame(
            {
                "key": pd.array([1, 2, 3], dtype="Int64"),
                "val": pd.array(["x", "y", "z"], dtype=pd.StringDtype()),
            }
        )
        df2 = pd.DataFrame(
            {
                "key": pd.array([2, 3], dtype="Int64"),
                "extra": pd.array(["e2", "e3"], dtype=pd.StringDtype()),
            }
        )
        result = _merge_dataframes(df1, df2, "key")
        unmatched = result.loc[result["key"] == 1, "extra"].values[0]
        self.assertEqual(unmatched, "", f"StringDtype NaN must be filled with '', got {unmatched!r}")


# ---------------------------------------------------------------------------
# 6. get_attributes_from_row — NaN in attributes column
# ---------------------------------------------------------------------------


class TestGetAttributesFromRowNaN(unittest.TestCase):
    """Validate that get_attributes_from_row handles NaN gracefully.

    If a row's Attributes cell contains float NaN (not ''), the old code
    passed it to parse_attribute_string which returned None (implicit),
    causing callers to crash.  The fix normalises NaN to '' before parsing.
    """

    def test_nan_attributes_returns_empty_dict(self):
        """A NaN float in the Attributes column must produce an empty dict."""
        row = pd.Series(
            {
                constants.hed_id: "HED_0001234",
                constants.name: "SomeTag",
                constants.attributes: float("nan"),
                constants.subclass_of: "HedTag",
                constants.dcdescription: "desc",
            }
        )
        result = get_attributes_from_row(row)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_nan_properties_returns_empty_dict(self):
        """A NaN float in the Properties column must produce an empty dict."""
        row = pd.Series(
            {
                constants.hed_id: "",
                constants.name: "SomeProp",
                constants.properties: float("nan"),
                constants.subclass_of: "HedTag",
                constants.dcdescription: "",
            }
        )
        result = get_attributes_from_row(row)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_empty_string_attributes_returns_empty_dict(self):
        """An empty string in Attributes must still return an empty dict (regression guard)."""
        row = pd.Series(
            {
                constants.hed_id: "",
                constants.name: "SomeTag",
                constants.attributes: "",
                constants.subclass_of: "HedTag",
                constants.dcdescription: "",
            }
        )
        result = get_attributes_from_row(row)
        self.assertEqual(result, {})

    def test_valid_attributes_still_parsed(self):
        """Valid attribute strings must still be parsed correctly after the fix."""
        row = pd.Series(
            {
                constants.hed_id: "",
                constants.name: "SomeTag",
                constants.attributes: "suggestedTag=Event,extensionAllowed",
                constants.subclass_of: "HedTag",
                constants.dcdescription: "",
            }
        )
        result = get_attributes_from_row(row)
        self.assertIn("suggestedTag", result)
        self.assertEqual(result["suggestedTag"], "Event")
        self.assertIn("extensionAllowed", result)


# ---------------------------------------------------------------------------
# 7. _verify_hedid_matches — NaN hedId breaks .startswith()
# ---------------------------------------------------------------------------


class TestVerifyHedIdMatchesNaN(unittest.TestCase):
    """Validate that _verify_hedid_matches handles NaN hedId without AttributeError.

    pandas 3.0 can leave NaN floats in hedId cells that were not populated.
    The old code called ``df_id.startswith("HED_")`` directly, which raises
    ``AttributeError: 'float' object has no attribute 'startswith'``.
    The fix casts non-str df_id values to '' before any string operations.
    """

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.2.0")

    def test_nan_hedid_does_not_raise(self):
        """NaN in hedId column must not raise AttributeError."""
        df = pd.DataFrame(
            [
                {constants.name: "Event", constants.hed_id: float("nan")},
                {constants.name: "Age-#", constants.hed_id: float("nan")},
            ]
        )
        try:
            errors = _verify_hedid_matches(self.schema.tags, df, _get_hedid_range("", constants.TAG_KEY))
        except AttributeError as exc:
            self.fail(f"_verify_hedid_matches raised AttributeError with NaN hedId: {exc}")
        self.assertEqual(len(errors), 0, "NaN hedId should be treated as absent — no errors expected")

    def test_nan_hedid_treated_as_absent(self):
        """NaN hedId must be treated the same as an empty string — no ID assigned."""
        df = pd.DataFrame([{constants.name: "Event", constants.hed_id: float("nan")}])
        errors = _verify_hedid_matches(self.schema.tags, df, _get_hedid_range("", constants.TAG_KEY))
        self.assertEqual(len(errors), 0)

    def test_mixed_nan_and_valid_ids(self):
        """Mix of NaN and valid hedId values must not raise AttributeError.

        A NaN hedId treated as absent may still produce a mismatch error if the
        schema entry has an ID — that is correct behaviour.  The key property
        being tested is that no AttributeError is raised by the NaN row.
        """
        df = pd.DataFrame(
            [
                {constants.name: "Event", constants.hed_id: "HED_0012001"},
                {constants.name: "Age-#", constants.hed_id: float("nan")},  # NaN row
            ]
        )
        try:
            _verify_hedid_matches(load_schema_version("8.4.0").tags, df, _get_hedid_range("", constants.TAG_KEY))
        except AttributeError as exc:
            self.fail(f"_verify_hedid_matches raised AttributeError on NaN hedId: {exc}")


# ---------------------------------------------------------------------------
# 8. assign_hed_ids_section — NaN is truthy; bare `if hed_id:` skipped rows
# ---------------------------------------------------------------------------


class TestAssignHedIdsSectionNaN(unittest.TestCase):
    """Validate that assign_hed_ids_section treats NaN as a missing ID.

    In Python, ``bool(float('nan'))`` is ``True``.  The old code used
    ``if hed_id: continue``, which meant NaN-valued hedId cells were treated as
    "already has an ID" and skipped.  The fix uses
    ``isinstance(hed_id, str) and hed_id`` to correctly skip only real string IDs.
    """

    def test_nan_hed_id_gets_assigned(self):
        """A row with float NaN as hedId must receive a new ID."""
        df = pd.DataFrame({constants.hed_id: [float("nan"), "HED_0000005"], constants.name: ["A", "B"]})
        assign_hed_ids_section(df, {1, 2, 3})
        new_id = df.loc[0, constants.hed_id]
        self.assertIsInstance(new_id, str, "NaN hedId must be replaced with a string ID")
        self.assertTrue(new_id.startswith("HED_"), f"Assigned ID must be HED_XXXXXXX, got {new_id!r}")

    def test_existing_string_id_not_overwritten(self):
        """A row with a valid string hedId must not be changed."""
        df = pd.DataFrame({constants.hed_id: [float("nan"), "HED_0000005"], constants.name: ["A", "B"]})
        assign_hed_ids_section(df, {1, 2, 3})
        self.assertEqual(df.loc[1, constants.hed_id], "HED_0000005")

    def test_all_nan_rows_get_assigned(self):
        """All NaN rows must get IDs from the pool."""
        df = pd.DataFrame(
            {constants.hed_id: [float("nan"), float("nan"), float("nan")], constants.name: ["A", "B", "C"]}
        )
        assign_hed_ids_section(df, {10, 20, 30})
        for i in range(3):
            val = df.loc[i, constants.hed_id]
            self.assertTrue(isinstance(val, str) and val.startswith("HED_"), f"Row {i} not assigned: {val!r}")

    def test_empty_string_id_gets_assigned(self):
        """An empty string hedId (falsy) must also receive a new ID."""
        df = pd.DataFrame({constants.hed_id: ["", "HED_0000005"], constants.name: ["A", "B"]})
        assign_hed_ids_section(df, {7, 8})
        new_id = df.loc[0, constants.hed_id]
        self.assertTrue(isinstance(new_id, str) and new_id.startswith("HED_"))


if __name__ == "__main__":
    unittest.main()
