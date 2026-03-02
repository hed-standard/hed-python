import unittest
import copy

import pandas as pd

from hed.schema import HedKey, HedSectionKey
from hed.schema.schema_comparer import SchemaComparer
from hed import load_schema_version, load_schema
from hed.schema.schema_io.df_constants import SOURCES_KEY, PREFIXES_KEY, EXTERNAL_ANNOTATION_KEY

from tests.schema import util_create_schemas
import os


class TestSchemaComparerConstants(unittest.TestCase):
    """Verify class-level constant dictionaries are complete."""

    def test_section_entry_names_includes_all_extras(self):
        """SECTION_ENTRY_NAMES must contain all three extras string keys."""
        for key in (SchemaComparer.SOURCES, SchemaComparer.PREFIXES, SchemaComparer.ANNOTATION_PROPERTY_EXTERNAL):
            self.assertIn(key, SchemaComparer.SECTION_ENTRY_NAMES, f"Missing key: {key}")

    def test_section_entry_names_plural_includes_all_extras(self):
        """SECTION_ENTRY_NAMES_PLURAL must contain all three extras string keys."""
        for key in (SchemaComparer.SOURCES, SchemaComparer.PREFIXES, SchemaComparer.ANNOTATION_PROPERTY_EXTERNAL):
            self.assertIn(key, SchemaComparer.SECTION_ENTRY_NAMES_PLURAL, f"Missing key: {key}")

    def test_section_entry_names_plural_includes_misc_and_hed_id(self):
        """SECTION_ENTRY_NAMES_PLURAL must contain MISC_SECTION and HED_ID_SECTION."""
        self.assertIn(SchemaComparer.MISC_SECTION, SchemaComparer.SECTION_ENTRY_NAMES_PLURAL)
        self.assertIn(SchemaComparer.HED_ID_SECTION, SchemaComparer.SECTION_ENTRY_NAMES_PLURAL)

    def test_section_entry_names_plural_includes_all_hed_section_keys(self):
        """SECTION_ENTRY_NAMES_PLURAL must cover every HedSectionKey member."""
        for key in HedSectionKey:
            self.assertIn(key, SchemaComparer.SECTION_ENTRY_NAMES_PLURAL, f"Missing HedSectionKey: {key}")


class TestFindMatchingTags(unittest.TestCase):
    """Tests for find_matching_tags."""

    @classmethod
    def setUpClass(cls):
        cls.schema1 = util_create_schemas.load_schema1()
        cls.schema2 = util_create_schemas.load_schema2()
        cls.comp = SchemaComparer(cls.schema1, cls.schema2)

    def test_returns_dict_with_correct_tags(self):
        result = self.comp.find_matching_tags(return_string=False)
        self.assertEqual(len(result[HedSectionKey.Tags]), 3)
        self.assertIn("TestNode", result[HedSectionKey.Tags])
        self.assertIn("TestNode2", result[HedSectionKey.Tags])
        self.assertIn("TestNode3", result[HedSectionKey.Tags])
        self.assertNotIn("TestNode4", result[HedSectionKey.Tags])
        self.assertNotIn("TestNode5", result[HedSectionKey.Tags])

    def test_returns_string_with_section_label(self):
        result = self.comp.find_matching_tags(return_string=True)
        self.assertIsInstance(result, str)
        self.assertIn("Tags:", result)


class TestCompareSchemas(unittest.TestCase):
    """Tests for compare_schemas."""

    @classmethod
    def setUpClass(cls):
        cls.schema1 = util_create_schemas.load_schema1()
        cls.schema2 = util_create_schemas.load_schema2()

    def test_basic_tag_categorisation(self):
        """Tags are correctly sorted into matches, missing-schema1, missing-schema2, unequal."""
        comp = SchemaComparer(self.schema1, self.schema2)
        matches, not_in_1, not_in_2, unequal = comp.compare_schemas()

        self.assertEqual(len(matches[HedSectionKey.Tags]), 2)
        self.assertIn("TestNode", matches[HedSectionKey.Tags])
        self.assertIn("TestNode2", matches[HedSectionKey.Tags])

        self.assertEqual(len(not_in_2[HedSectionKey.Tags]), 1)
        self.assertIn("TestNode4", not_in_2[HedSectionKey.Tags])

        self.assertEqual(len(not_in_1[HedSectionKey.Tags]), 1)
        self.assertIn("TestNode5", not_in_1[HedSectionKey.Tags])

        self.assertEqual(len(unequal[HedSectionKey.Tags]), 1)
        self.assertIn("TestNode3", unequal[HedSectionKey.Tags])

    def test_sections_none_includes_misc_key(self):
        """sections=None causes the MISC_SECTION key to appear in unequal_entries."""
        schema1 = copy.deepcopy(self.schema1)
        schema2 = copy.deepcopy(self.schema1)
        schema2.prologue = "Changed"
        comp = SchemaComparer(schema1, schema2)
        _, _, _, unequal = comp.compare_schemas(attribute_filter=None, sections=None)
        self.assertIn(SchemaComparer.MISC_SECTION, unequal)

    def test_prologue_difference_detected(self):
        """A prologue change produces an entry in MISC_SECTION."""
        schema1 = copy.deepcopy(self.schema1)
        schema2 = copy.deepcopy(self.schema1)
        schema2.prologue = "New prologue"
        comp = SchemaComparer(schema1, schema2)
        _, _, _, unequal = comp.compare_schemas(attribute_filter=None, sections=None)
        self.assertIn("prologue", unequal[SchemaComparer.MISC_SECTION])

    def test_epilogue_difference_detected(self):
        """An epilogue change produces an entry in MISC_SECTION."""
        schema1 = copy.deepcopy(self.schema1)
        schema2 = copy.deepcopy(self.schema1)
        schema2.epilogue = "New epilogue"
        comp = SchemaComparer(schema1, schema2)
        _, _, _, unequal = comp.compare_schemas(attribute_filter=None, sections=None)
        self.assertIn("epilogue", unequal[SchemaComparer.MISC_SECTION])

    def test_header_attributes_difference_detected(self):
        """A header attribute change produces an entry in MISC_SECTION."""
        schema1 = copy.deepcopy(self.schema1)
        schema2 = copy.deepcopy(self.schema1)
        schema2.header_attributes["version"] = "9.9.9"
        comp = SchemaComparer(schema1, schema2)
        _, _, _, unequal = comp.compare_schemas(attribute_filter=None, sections=None)
        self.assertIn("header_attributes", unequal[SchemaComparer.MISC_SECTION])

    def test_attribute_filter_none_includes_all_entries(self):
        """attribute_filter=None compares all entries, not only InLibrary-tagged ones."""
        comp = SchemaComparer(self.schema1, self.schema2)
        matches_filtered, _, _, _ = comp.compare_schemas(attribute_filter=HedKey.InLibrary)
        matches_all, _, _, _ = comp.compare_schemas(attribute_filter=None)
        # Without filter we get at least as many tags (base + library entries visible)
        self.assertGreaterEqual(len(matches_all[HedSectionKey.Tags]), len(matches_filtered[HedSectionKey.Tags]))

    def test_identical_schemas_no_differences(self):
        """Identical schemas produce an empty compare_differences string."""
        schema = load_schema_version("score_1.0.0")
        comp = SchemaComparer(schema, copy.deepcopy(schema))
        self.assertFalse(comp.compare_differences(attribute_filter=HedKey.InLibrary))

    def test_score_lib_version_counts(self):
        """Real-world SCORE 1.0 vs 1.1 produces expected tag-level counts."""
        schema1 = load_schema_version("score_1.0.0")
        schema2 = load_schema_version("score_1.1.0")
        comp = SchemaComparer(schema1, schema2)
        _, not_in_1, not_in_2, unequal = comp.compare_schemas(attribute_filter=HedKey.InLibrary)
        self.assertEqual(len(not_in_1[HedSectionKey.Tags]), 21)
        self.assertEqual(len(not_in_2[HedSectionKey.Tags]), 10)
        self.assertEqual(len(unequal[HedSectionKey.Tags]), 80)


class TestGatherSchemaChanges(unittest.TestCase):
    """Tests for gather_schema_changes — verifying change_type values and section routing."""

    @classmethod
    def setUpClass(cls):
        cls.base_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/")
        cls.base = util_create_schemas.load_schema1()

    @staticmethod
    def _flat_changes(schema1, schema2, **kwargs):
        """Return all change dicts as a flat list."""
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes(**kwargs)
        return [item for items in result.values() for item in items]

    def test_removed_tag_is_major(self):
        """A tag only in schema1 is classified as Major."""
        changes = self._flat_changes(self.base, util_create_schemas.load_schema2())
        removed = [c for c in changes if "TestNode4" in c["tag"]]
        self.assertTrue(removed)
        self.assertTrue(all(c["change_type"] == "Major" for c in removed))

    def test_added_tag_is_minor(self):
        """A tag only in schema2 is classified as Minor."""
        changes = self._flat_changes(self.base, util_create_schemas.load_schema2())
        added = [c for c in changes if "TestNode5" in c["tag"]]
        self.assertTrue(added)
        self.assertTrue(all(c["change_type"] == "Minor" for c in added))

    def test_description_change_is_patch(self):
        """A description change on an existing entry is classified as Patch."""
        schema2 = copy.deepcopy(self.base)
        schema2[HedSectionKey.Tags]["testnode"].description = "Completely different description"
        changes = self._flat_changes(self.base, schema2)
        desc = [c for c in changes if "Description" in c["change"] and "TestNode" in c["tag"]]
        self.assertTrue(desc)
        self.assertTrue(all(c["change_type"] == "Patch" for c in desc))

    def test_prologue_change_appears_in_misc(self):
        """A prologue change appears under MISC_SECTION."""
        schema2 = copy.deepcopy(self.base)
        schema2.prologue = "Changed prologue"
        comp = SchemaComparer(self.base, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(SchemaComparer.MISC_SECTION, result)
        self.assertIn("prologue", [c["tag"] for c in result[SchemaComparer.MISC_SECTION]])

    def test_epilogue_change_appears_in_misc(self):
        """An epilogue change appears under MISC_SECTION."""
        schema2 = copy.deepcopy(self.base)
        schema2.epilogue = "Changed epilogue"
        comp = SchemaComparer(self.base, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(SchemaComparer.MISC_SECTION, result)
        self.assertIn("epilogue", [c["tag"] for c in result[SchemaComparer.MISC_SECTION]])

    def test_header_attributes_change_appears_in_misc(self):
        """A version change appears under MISC_SECTION."""
        schema2 = copy.deepcopy(self.base)
        schema2.header_attributes["version"] = "9.9.9"
        comp = SchemaComparer(self.base, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(SchemaComparer.MISC_SECTION, result)
        self.assertIn("header_attributes", [c["tag"] for c in result[SchemaComparer.MISC_SECTION]])

    def test_mediawiki_comparison_total_count(self):
        """Known mediawiki schemas produce exactly 30 changes."""
        schema1 = load_schema(os.path.join(self.base_data, "schema_compare.mediawiki"), name="Schema1")
        schema2 = load_schema(os.path.join(self.base_data, "schema_compare2.mediawiki"), name="Schema2")
        result = SchemaComparer(schema1, schema2).gather_schema_changes()
        self.assertEqual(sum(len(v) for v in result.values()), 30)

    def test_changes_sorted_by_severity(self):
        """Each section's change list is ordered Major → Minor → Patch → Unknown."""
        schema1 = load_schema_version("score_1.0.0")
        schema2 = load_schema_version("score_1.1.0")
        result = SchemaComparer(schema1, schema2).gather_schema_changes()
        order = {"Major": 1, "Minor": 2, "Patch": 3, "Unknown": 4}
        for section_changes in result.values():
            positions = [order.get(c["change_type"], 4) for c in section_changes]
            self.assertEqual(positions, sorted(positions), "Section not ordered by severity")

    def test_result_keys_subset_of_section_entry_names(self):
        """All keys returned by gather_schema_changes are in SECTION_ENTRY_NAMES."""
        schema1 = load_schema_version("score_1.0.0")
        schema2 = load_schema_version("score_1.1.0")
        result = SchemaComparer(schema1, schema2).gather_schema_changes()
        for key in result:
            self.assertIn(key, SchemaComparer.SECTION_ENTRY_NAMES)


class TestExtrasChanges(unittest.TestCase):
    """Tests for _add_extras_changes — all diff message types and the in_library guard."""

    @staticmethod
    def _make_schema(extras_dict):
        schema = copy.deepcopy(util_create_schemas.load_schema1())
        schema.extras = extras_dict
        return schema

    @staticmethod
    def _extras_result(schema1, schema2):
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes()
        extras_keys = {SOURCES_KEY, PREFIXES_KEY, EXTERNAL_ANNOTATION_KEY}
        return {k: v for k, v in result.items() if k in extras_keys}

    def test_identical_extras_no_changes(self):
        """Identical extras DataFrames produce zero changes."""
        df = pd.DataFrame({"source": ["src1"], "link": ["http://a.org"], "description": ["d"]})
        schema1 = self._make_schema({SOURCES_KEY: df.copy()})
        schema2 = self._make_schema({SOURCES_KEY: df.copy()})
        changes = self._extras_result(schema1, schema2)
        self.assertEqual(sum(len(v) for v in changes.values()), 0)

    def test_empty_extras_no_changes(self):
        """Both schemas with empty extras dicts produce no extras changes."""
        schema1 = self._make_schema({})
        schema2 = self._make_schema({})
        changes = self._extras_result(schema1, schema2)
        self.assertEqual(sum(len(v) for v in changes.values()), 0)

    def test_section_missing_in_schema1_is_minor(self):
        """An extras section present only in schema2 is Minor."""
        df = pd.DataFrame({"source": ["src1"], "link": ["http://a.org"], "description": ["d"]})
        schema1 = self._make_schema({})
        schema2 = self._make_schema({SOURCES_KEY: df})
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(SOURCES_KEY, result)
        self.assertEqual(result[SOURCES_KEY][0]["change_type"], "Minor")
        self.assertIn("missing in first schema", result[SOURCES_KEY][0]["change"])

    def test_section_missing_in_schema2_is_minor(self):
        """An extras section present only in schema1 is Minor."""
        df = pd.DataFrame({"source": ["src1"], "link": ["http://a.org"], "description": ["d"]})
        schema1 = self._make_schema({SOURCES_KEY: df})
        schema2 = self._make_schema({})
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(SOURCES_KEY, result)
        self.assertEqual(result[SOURCES_KEY][0]["change_type"], "Minor")
        self.assertIn("missing in second schema", result[SOURCES_KEY][0]["change"])

    def test_row_added_to_schema2_is_minor(self):
        """A row present in schema2 but not schema1 is Minor."""
        df1 = pd.DataFrame({"source": ["s1"], "link": ["http://a.org"], "description": ["d"]})
        df2 = pd.DataFrame({"source": ["s1", "s2"], "link": ["http://a.org", "http://b.org"], "description": ["d", "e"]})
        schema1 = self._make_schema({SOURCES_KEY: df1})
        schema2 = self._make_schema({SOURCES_KEY: df2})
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(SOURCES_KEY, result)
        added = [c for c in result[SOURCES_KEY] if "missing in first schema" in c["change"]]
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]["change_type"], "Minor")

    def test_row_removed_from_schema2_is_minor(self):
        """A row present in schema1 but not schema2 is Minor."""
        df1 = pd.DataFrame({"source": ["s1", "s2"], "link": ["http://a.org", "http://b.org"], "description": ["d", "e"]})
        df2 = pd.DataFrame({"source": ["s1"], "link": ["http://a.org"], "description": ["d"]})
        schema1 = self._make_schema({SOURCES_KEY: df1})
        schema2 = self._make_schema({SOURCES_KEY: df2})
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(SOURCES_KEY, result)
        removed = [c for c in result[SOURCES_KEY] if "missing in second schema" in c["change"]]
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["change_type"], "Minor")

    def test_column_value_differs_is_patch(self):
        """Same key row but different non-key column value is Patch."""
        df1 = pd.DataFrame({"source": ["s1"], "link": ["http://a.org"], "description": ["old"]})
        df2 = pd.DataFrame({"source": ["s1"], "link": ["http://a.org"], "description": ["new"]})
        schema1 = self._make_schema({SOURCES_KEY: df1})
        schema2 = self._make_schema({SOURCES_KEY: df2})
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(SOURCES_KEY, result)
        diffs = [c for c in result[SOURCES_KEY] if "columns differ" in c["change"]]
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["change_type"], "Patch")

    def test_in_library_column_difference_ignored(self):
        """Differing in_library values do not produce any change entries."""
        df1 = pd.DataFrame({"source": ["s1"], "link": ["http://a.org"], "description": ["d"], "in_library": ["lib"]})
        df2 = pd.DataFrame({"source": ["s1"], "link": ["http://a.org"], "description": ["d"], "in_library": [None]})
        schema1 = self._make_schema({SOURCES_KEY: df1})
        schema2 = self._make_schema({SOURCES_KEY: df2})
        changes = self._extras_result(schema1, schema2)
        self.assertEqual(sum(len(v) for v in changes.values()), 0)

    def test_duplicate_keys_is_unknown(self):
        """Duplicate key rows in an extras DataFrame are reported as Unknown."""
        df1 = pd.DataFrame({"source": ["s1", "s1"], "link": ["http://a.org", "http://b.org"], "description": ["d1", "d2"]})
        df2 = pd.DataFrame({"source": ["s1"], "link": ["http://a.org"], "description": ["d1"]})
        schema1 = self._make_schema({SOURCES_KEY: df1})
        schema2 = self._make_schema({SOURCES_KEY: df2})
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes()
        all_changes = [c for v in result.values() for c in v]
        dup = [c for c in all_changes if c["change_type"] == "Unknown" and "Duplicate" in c["change"]]
        self.assertTrue(dup)

    def test_prefixes_extras_compared(self):
        """Prefixes extras section is diffed like Sources."""
        df1 = pd.DataFrame({"prefix": ["hed"], "namespace": ["http://hed.org/"], "description": ["HED"]})
        df2 = pd.DataFrame(
            {
                "prefix": ["hed", "score"],
                "namespace": ["http://hed.org/", "http://score.org/"],
                "description": ["HED", "SCORE"],
            }
        )
        schema1 = self._make_schema({PREFIXES_KEY: df1})
        schema2 = self._make_schema({PREFIXES_KEY: df2})
        comp = SchemaComparer(schema1, schema2)
        result = comp.gather_schema_changes()
        self.assertIn(PREFIXES_KEY, result)
        added = [c for c in result[PREFIXES_KEY] if "missing in first schema" in c["change"]]
        self.assertEqual(len(added), 1)


class TestCompareDataFrames(unittest.TestCase):
    """Unit tests for the static _compare_dataframes helper."""

    def test_identical_produces_no_diffs(self):
        df = pd.DataFrame({"key": ["a", "b"], "val": ["x", "y"]})
        self.assertEqual(SchemaComparer._compare_dataframes(df, df.copy(), ["key"]), [])

    def test_row_missing_in_first(self):
        df1 = pd.DataFrame({"key": ["a"], "val": ["x"]})
        df2 = pd.DataFrame({"key": ["a", "b"], "val": ["x", "y"]})
        results = SchemaComparer._compare_dataframes(df1, df2, ["key"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["message"], "Row missing in first schema")

    def test_row_missing_in_second(self):
        df1 = pd.DataFrame({"key": ["a", "b"], "val": ["x", "y"]})
        df2 = pd.DataFrame({"key": ["a"], "val": ["x"]})
        results = SchemaComparer._compare_dataframes(df1, df2, ["key"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["message"], "Row missing in second schema")

    def test_column_value_differs(self):
        df1 = pd.DataFrame({"key": ["a"], "val": ["x"]})
        df2 = pd.DataFrame({"key": ["a"], "val": ["z"]})
        results = SchemaComparer._compare_dataframes(df1, df2, ["key"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["message"], "Column values differ")
        self.assertIn("val", results[0]["cols"])

    def test_duplicate_keys(self):
        df1 = pd.DataFrame({"key": ["a", "a"], "val": ["x", "y"]})
        df2 = pd.DataFrame({"key": ["a"], "val": ["x"]})
        results = SchemaComparer._compare_dataframes(df1, df2, ["key"])
        dup = [r for r in results if r["message"] == "Duplicate keys found"]
        self.assertTrue(dup)

    def test_multiple_key_columns(self):
        """Multi-column composite keys work correctly."""
        df1 = pd.DataFrame({"k1": ["a", "a"], "k2": ["1", "2"], "val": ["x", "y"]})
        df2 = pd.DataFrame({"k1": ["a", "a", "b"], "k2": ["1", "2", "3"], "val": ["x", "changed", "z"]})
        results = SchemaComparer._compare_dataframes(df1, df2, ["k1", "k2"])
        messages = [r["message"] for r in results]
        self.assertIn("Row missing in first schema", messages)
        self.assertIn("Column values differ", messages)


class TestPrettyPrintChangeDict(unittest.TestCase):
    """Tests for pretty_print_change_dict and compare_differences formatting."""

    @classmethod
    def setUpClass(cls):
        cls.schema1 = util_create_schemas.load_schema1()
        cls.schema2 = util_create_schemas.load_schema2()
        cls.comp = SchemaComparer(cls.schema1, cls.schema2)
        cls.changes = cls.comp.gather_schema_changes()

    def test_empty_dict_returns_empty_string(self):
        self.assertEqual(self.comp.pretty_print_change_dict({}), "")

    def test_markdown_uses_bold_headers_and_bullets(self):
        result = self.comp.pretty_print_change_dict(self.changes, use_markdown=True)
        self.assertIn("**", result)
        self.assertIn(" - ", result)
        self.assertNotIn("\t", result)

    def test_plain_text_uses_tabs_no_bold(self):
        result = self.comp.pretty_print_change_dict(self.changes, use_markdown=False)
        self.assertNotIn("**", result)
        self.assertIn("\t", result)

    def test_change_count_matches_parentheses_pattern(self):
        """Every change line ends with '(<type>): <desc>' — count should equal total changes."""
        result = self.comp.pretty_print_change_dict(self.changes)
        total = sum(len(v) for v in self.changes.values())
        self.assertEqual(result.count("):"), total)

    def test_extras_section_uses_human_readable_name(self):
        """Sources/Prefixes/AnnotationPropertyExternal appear with their display names."""
        schema2 = copy.deepcopy(self.schema1)
        schema2.extras = {SOURCES_KEY: pd.DataFrame({"source": ["s1"], "link": ["http://a.org"], "description": ["d"]})}
        comp = SchemaComparer(self.schema1, schema2)
        changes = comp.gather_schema_changes()
        result = comp.pretty_print_change_dict(changes)
        # Key "Sources" should appear as section header "Sources:", not raw dict key
        self.assertIn("Sources:", result)

    def test_custom_title_appears_in_output(self):
        result = self.comp.compare_differences(title="My Special Title")
        self.assertIn("My Special Title", result)

    def test_auto_generated_title_uses_schema_names(self):
        schema1 = load_schema_version("score_1.0.0")
        schema2 = load_schema_version("score_1.1.0")
        comp = SchemaComparer(schema1, schema2)
        result = comp.compare_differences(attribute_filter=HedKey.InLibrary)
        self.assertIn(schema1.name, result)
        self.assertIn(schema2.name, result)

    def test_compare_differences_score_versions_output(self):
        """compare_differences output contains all missing/added tag names."""
        schema1 = load_schema_version("score_1.0.0")
        schema2 = load_schema_version("score_1.1.0")
        comp = SchemaComparer(schema1, schema2)
        _, not_in_1, not_in_2, _ = comp.compare_schemas(attribute_filter=HedKey.InLibrary)
        diff_string = comp.compare_differences(attribute_filter=HedKey.InLibrary)
        self.assertTrue(diff_string)
        for item in not_in_1[HedSectionKey.Tags]:
            self.assertIn(item, diff_string)
        for item in not_in_2[HedSectionKey.Tags]:
            self.assertIn(item, diff_string)
