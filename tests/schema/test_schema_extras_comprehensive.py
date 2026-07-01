"""
Comprehensive tests for schema extras sections across all formats.

Tests that extras (Sources, Prefixes, ExternalAnnotations) are correctly:
1. Read from all formats (XML, JSON, MediaWiki, TSV) with in_library tracking
2. Have consistent internal representation across formats
3. Round-trip correctly (read → write → read)
4. Properly separate library-specific entries from base-schema entries
"""

import unittest
import os
import tempfile
import shutil
import pandas as pd
from hed.schema import load_schema
from hed.schema.schema_io import df_constants


class TestSchemaExtrasAllFormats(unittest.TestCase):
    """Comprehensive tests for extras sections across all formats."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_extras_all_formats_")
        cls.test_data_dir = os.path.join(os.path.dirname(__file__), "../data/schema_tests/test_merge")
        cls.test_data_dir = os.path.normpath(cls.test_data_dir)

        # Paths to all format versions of HED_testlib_4.0.0
        cls.xml_path = os.path.join(cls.test_data_dir, "HED_testlib_4.0.0.xml")
        cls.json_path = os.path.join(cls.test_data_dir, "HED_testlib_4.0.0.json")
        cls.wiki_path = os.path.join(cls.test_data_dir, "HED_testlib_4.0.0.mediawiki")
        cls.tsv_path = os.path.join(cls.test_data_dir, "HED_testlib_4.0.0")

        # Expected totals for testlib 4.0.0 paired with 8.5.0
        # = library-specific + base-schema entries
        cls.expected_sources = 2  # 1 library + 1 base
        cls.expected_prefixes = 14  # 1 library + 13 base
        cls.expected_externals = 18  # 1 library + 17 base
        cls.library_name = "testlib"
        cls.with_standard = "8.5.0"

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def _verify_extras_count_and_tracking(self, df, expected_total, expected_lib, format_name, section_name):
        """Verify DataFrame row count and that in_library tracks library-specific entries."""
        self.assertIsNotNone(df, f"{format_name} {section_name} should not be None")
        self.assertEqual(
            len(df), expected_total, f"{format_name} {section_name} should have {expected_total} total entries"
        )
        self.assertIn(
            df_constants.in_library,
            df.columns,
            f"{format_name} {section_name} should have in_library column for tracking",
        )
        lib_rows = (df[df_constants.in_library] == self.library_name).sum()
        self.assertEqual(
            lib_rows, expected_lib, f"{format_name} {section_name} should have {expected_lib} library rows"
        )

    def _extras_without_in_library(self, df):
        """Return a copy of df without the in_library column, sorted for comparison."""
        if df is None or df.empty:
            return df
        cols = [c for c in df.columns if c != df_constants.in_library]
        result = df[cols].sort_values(by=cols).reset_index(drop=True)
        return result

    def _library_extras_only(self, df, library_name):
        """Return only library-specific rows (in_library == library_name), without in_library col."""
        if df is None or df.empty:
            return df
        if df_constants.in_library not in df.columns:
            return self._extras_without_in_library(df)
        lib_df = df[df[df_constants.in_library] == library_name].copy()
        cols = [c for c in lib_df.columns if c != df_constants.in_library]
        return lib_df[cols].sort_values(by=cols).reset_index(drop=True)

    def test_01_all_formats_load_extras_correctly(self):
        """All formats load extras with correct total counts and proper in_library tracking."""
        formats = {
            "XML": self.xml_path,
            "JSON": self.json_path,
            "MediaWiki": self.wiki_path,
            "TSV": self.tsv_path,
        }
        # library contributes exactly 1 entry to each section
        lib_sources = 1
        lib_prefixes = 1
        lib_externals = 1

        for format_name, path in formats.items():
            with self.subTest(format=format_name):
                schema = load_schema(path)

                self.assertEqual(schema.library, self.library_name)
                self.assertEqual(schema.version_number, "4.0.0")
                self.assertEqual(schema.with_standard, self.with_standard)
                self.assertTrue(schema.merged)

                self._verify_extras_count_and_tracking(
                    schema.get_extras(df_constants.SOURCES_KEY),
                    self.expected_sources,
                    lib_sources,
                    format_name,
                    "Sources",
                )
                self._verify_extras_count_and_tracking(
                    schema.get_extras(df_constants.PREFIXES_KEY),
                    self.expected_prefixes,
                    lib_prefixes,
                    format_name,
                    "Prefixes",
                )
                self._verify_extras_count_and_tracking(
                    schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
                    self.expected_externals,
                    lib_externals,
                    format_name,
                    "ExternalAnnotations",
                )

    def test_02_all_formats_have_identical_internal_representation(self):
        """All formats produce identical internal DataFrames (ignoring in_library for comparison)."""
        schema_xml = load_schema(self.xml_path)
        schema_json = load_schema(self.json_path)
        schema_wiki = load_schema(self.wiki_path)
        schema_tsv = load_schema(self.tsv_path)

        schemas = {
            "XML": schema_xml,
            "JSON": schema_json,
            "MediaWiki": schema_wiki,
            "TSV": schema_tsv,
        }

        # Compare each pair of formats
        format_pairs = [
            ("XML", "JSON"),
            ("XML", "MediaWiki"),
            ("XML", "TSV"),
            ("JSON", "MediaWiki"),
            ("JSON", "TSV"),
            ("MediaWiki", "TSV"),
        ]

        for fmt1, fmt2 in format_pairs:
            with self.subTest(comparison=f"{fmt1}_vs_{fmt2}"):
                for key, label in [
                    (df_constants.SOURCES_KEY, "Sources"),
                    (df_constants.PREFIXES_KEY, "Prefixes"),
                    (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
                ]:
                    df1 = self._extras_without_in_library(schemas[fmt1].get_extras(key))
                    df2 = self._extras_without_in_library(schemas[fmt2].get_extras(key))
                    pd.testing.assert_frame_equal(df1, df2, check_dtype=False, obj=f"{label}: {fmt1} vs {fmt2}")

    def _check_unmerged_roundtrip(self, original_schema, reloaded_schema):
        """After saving merged→unmerged and reloading, only library entries survive."""
        for key, label in [
            (df_constants.SOURCES_KEY, "Sources"),
            (df_constants.PREFIXES_KEY, "Prefixes"),
            (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
        ]:
            lib_only = self._library_extras_only(original_schema.get_extras(key), self.library_name)
            reloaded = self._extras_without_in_library(reloaded_schema.get_extras(key))
            pd.testing.assert_frame_equal(
                lib_only, reloaded, check_dtype=False, obj=f"{label}: library_only vs reloaded"
            )

    def test_03_xml_roundtrip_unmerged(self):
        """Load merged XML → save unmerged → reload: only library extras survive."""
        schema = load_schema(self.xml_path)
        temp_xml = os.path.join(self.temp_dir, "roundtrip_unmerged.xml")
        schema.save_as_xml(temp_xml, save_merged=False)
        schema_reloaded = load_schema(temp_xml)
        self._check_unmerged_roundtrip(schema, schema_reloaded)

    def test_04_json_roundtrip_unmerged(self):
        """Load merged JSON → save unmerged → reload: only library extras survive."""
        schema = load_schema(self.json_path)
        temp_json = os.path.join(self.temp_dir, "roundtrip_unmerged.json")
        schema.save_as_json(temp_json, save_merged=False)
        schema_reloaded = load_schema(temp_json)
        self._check_unmerged_roundtrip(schema, schema_reloaded)

    def test_05_mediawiki_roundtrip_unmerged(self):
        """Load merged MediaWiki → save unmerged → reload: only library extras survive."""
        schema = load_schema(self.wiki_path)
        temp_wiki = os.path.join(self.temp_dir, "roundtrip_unmerged.mediawiki")
        schema.save_as_mediawiki(temp_wiki, save_merged=False)
        schema_reloaded = load_schema(temp_wiki)
        self._check_unmerged_roundtrip(schema, schema_reloaded)

    def test_06_tsv_roundtrip_unmerged(self):
        """Load merged TSV → save unmerged → reload: only library extras survive."""
        schema = load_schema(self.tsv_path)
        temp_tsv_dir = os.path.join(self.temp_dir, "roundtrip_unmerged_tsv")
        schema.save_as_dataframes(temp_tsv_dir, save_merged=False)
        schema_reloaded = load_schema(temp_tsv_dir)
        self._check_unmerged_roundtrip(schema, schema_reloaded)

    def test_07_merged_roundtrip_same_format(self):
        """Load merged → save merged → reload: extras are identical (all formats)."""
        for fmt_name, path, save_fn, reload_path in [
            (
                "XML",
                self.xml_path,
                lambda s, p: s.save_as_xml(p, save_merged=True),
                os.path.join(self.temp_dir, "rt_merged.xml"),
            ),
            (
                "JSON",
                self.json_path,
                lambda s, p: s.save_as_json(p, save_merged=True),
                os.path.join(self.temp_dir, "rt_merged.json"),
            ),
            (
                "Wiki",
                self.wiki_path,
                lambda s, p: s.save_as_mediawiki(p, save_merged=True),
                os.path.join(self.temp_dir, "rt_merged.mediawiki"),
            ),
            (
                "TSV",
                self.tsv_path,
                lambda s, p: s.save_as_dataframes(p, save_merged=True),
                os.path.join(self.temp_dir, "rt_merged_tsv"),
            ),
        ]:
            with self.subTest(format=fmt_name):
                schema = load_schema(path)
                save_fn(schema, reload_path)
                schema2 = load_schema(reload_path)
                for key, label in [
                    (df_constants.SOURCES_KEY, "Sources"),
                    (df_constants.PREFIXES_KEY, "Prefixes"),
                    (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
                ]:
                    df1 = self._extras_without_in_library(schema.get_extras(key))
                    df2 = self._extras_without_in_library(schema2.get_extras(key))
                    pd.testing.assert_frame_equal(
                        df1, df2, check_dtype=False, obj=f"{label}: {fmt_name} merged roundtrip"
                    )

    def test_08_cross_format_roundtrip(self):
        """Load merged XML → save merged in other formats → reload: extras match."""
        schema = load_schema(self.xml_path)
        temp_json = os.path.join(self.temp_dir, "cross_format.json")
        temp_wiki = os.path.join(self.temp_dir, "cross_format.mediawiki")
        temp_tsv = os.path.join(self.temp_dir, "cross_format_tsv")

        schema.save_as_json(temp_json, save_merged=True)
        schema.save_as_mediawiki(temp_wiki, save_merged=True)
        schema.save_as_dataframes(temp_tsv, save_merged=True)

        schema_json = load_schema(temp_json)
        schema_wiki = load_schema(temp_wiki)
        schema_tsv = load_schema(temp_tsv)

        for fmt_name, schema_fmt in [("JSON", schema_json), ("Wiki", schema_wiki), ("TSV", schema_tsv)]:
            with self.subTest(target_format=fmt_name):
                for key, label in [
                    (df_constants.SOURCES_KEY, "Sources"),
                    (df_constants.PREFIXES_KEY, "Prefixes"),
                    (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
                ]:
                    df1 = self._extras_without_in_library(schema.get_extras(key))
                    df2 = self._extras_without_in_library(schema_fmt.get_extras(key))
                    pd.testing.assert_frame_equal(df1, df2, check_dtype=False, obj=f"{label}: XML vs {fmt_name}")

    def test_09_base_extras_preserve_empty_in_library_after_merged_save(self):
        """After merged save, base-schema extras retain empty/NaN in_library (not rewritten to lib name).

        This test validates the fix for schema2base.py line 293-305 where empty/NaN in_library
        (the explicit marker for base-schema rows) must NOT be rewritten to the library name.
        If this bug exists, base extras get serialized with inLibrary attribute and break
        future unmerge operations.
        """

        schema = load_schema(self.xml_path)
        temp_xml = os.path.join(self.temp_dir, "merged_preserve_base.xml")

        # Save as merged (this is where the bug manifests)
        schema.save_as_xml(temp_xml, save_merged=True)
        schema_reloaded = load_schema(temp_xml)

        for key, label, expected_base_count in [
            (df_constants.SOURCES_KEY, "Sources", self.expected_sources - 1),
            (df_constants.PREFIXES_KEY, "Prefixes", self.expected_prefixes - 1),
            (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations", self.expected_externals - 1),
        ]:
            with self.subTest(section=label):
                df = schema_reloaded.get_extras(key)
                self.assertIsNotNone(df, f"{label} should exist after merged roundtrip")
                self.assertIn(df_constants.in_library, df.columns, f"{label} should have in_library column")

                # After merged save, merged schema contains ALL rows: library + base
                lib_rows = (df[df_constants.in_library] == self.library_name).sum()
                # Base rows have NaN or empty string (both are valid markers for "not a library row")
                not_lib_rows = df[df_constants.in_library].isna().sum() + (df[df_constants.in_library] == "").sum()

                # Verify counts match expected totals (library + base)
                self.assertEqual(lib_rows, 1, f"{label}: should have 1 library row (in_library={self.library_name})")
                self.assertEqual(
                    not_lib_rows,
                    expected_base_count,
                    f"{label}: should have {expected_base_count} base rows with NaN/empty in_library (not rewritten to {self.library_name})",
                )
                self.assertEqual(
                    len(df),
                    self.expected_sources
                    if label == "Sources"
                    else (self.expected_prefixes if label == "Prefixes" else self.expected_externals),
                    f"{label}: total rows should match expected count",
                )

                # Verify unmerge behavior: save unmerged should only have library rows
                temp_xml_unmerged = os.path.join(self.temp_dir, f"check_unmerge_{label}.xml")
                schema_reloaded.save_as_xml(temp_xml_unmerged, save_merged=False)
                schema_unmerged = load_schema(temp_xml_unmerged)

                df_unmerged = schema_unmerged.get_extras(key)
                if df_unmerged is not None and not df_unmerged.empty:
                    # After unmerge, only library rows should remain (base rows dropped)
                    self.assertEqual(
                        len(df_unmerged), 1, f"{label}: unmerged should only have library row, not base rows"
                    )

    def test_10_json_loader_normalizes_in_library_column(self):
        """JSON loader normalizes in_library to string (NaN → empty string) for all extras sections.

        This test validates the fix in json2schema.py _load_extras() where extras DataFrames
        can end up with NaN in the in_library column. Downstream code expects string values,
        not NaN. This test ensures all three extras sections (sources, prefixes, external annotations)
        have in_library as string type with no NaN values after JSON loading.
        """

        schema = load_schema(self.json_path)

        for key, label in [
            (df_constants.SOURCES_KEY, "Sources"),
            (df_constants.PREFIXES_KEY, "Prefixes"),
            (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
        ]:
            with self.subTest(section=label):
                df = schema.get_extras(key)
                self.assertIsNotNone(df, f"JSON: {label} should not be None")
                self.assertIn(df_constants.in_library, df.columns, f"JSON: {label} should have in_library column")

                # Check that there are NO NaN values in in_library
                nan_count = df[df_constants.in_library].isna().sum()
                self.assertEqual(
                    nan_count, 0, f"JSON: {label} in_library should have no NaN values (found {nan_count})"
                )

                # Verify all values are strings
                for idx, val in enumerate(df[df_constants.in_library]):
                    self.assertIsInstance(
                        val,
                        str,
                        f"JSON: {label} in_library[{idx}] should be string, got {type(val).__name__}: {repr(val)}",
                    )

    def test_11_xml_loader_normalizes_in_library_column(self):
        """XML loader normalizes in_library to string (NaN → empty string) for all extras sections."""

        schema = load_schema(self.xml_path)

        for key, label in [
            (df_constants.SOURCES_KEY, "Sources"),
            (df_constants.PREFIXES_KEY, "Prefixes"),
            (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
        ]:
            with self.subTest(section=label):
                df = schema.get_extras(key)
                self.assertIsNotNone(df, f"XML: {label} should not be None")
                self.assertIn(df_constants.in_library, df.columns, f"XML: {label} should have in_library column")

                # Check that there are NO NaN values in in_library
                nan_count = df[df_constants.in_library].isna().sum()
                self.assertEqual(nan_count, 0, f"XML: {label} in_library should have no NaN values (found {nan_count})")

                # Verify all values are strings
                for idx, val in enumerate(df[df_constants.in_library]):
                    self.assertIsInstance(
                        val,
                        str,
                        f"XML: {label} in_library[{idx}] should be string, got {type(val).__name__}: {repr(val)}",
                    )

    def test_12_all_loaders_normalize_in_library_column(self):
        """All loaders (XML, JSON, MediaWiki, TSV) normalize in_library to string with no NaN."""

        formats = {
            "XML": self.xml_path,
            "JSON": self.json_path,
            "MediaWiki": self.wiki_path,
            "TSV": self.tsv_path,
        }

        for format_name, path in formats.items():
            schema = load_schema(path)

            for key, label in [
                (df_constants.SOURCES_KEY, "Sources"),
                (df_constants.PREFIXES_KEY, "Prefixes"),
                (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
            ]:
                with self.subTest(format=format_name, section=label):
                    df = schema.get_extras(key)
                    self.assertIsNotNone(df, f"{format_name}: {label} should not be None")

                    if df_constants.in_library in df.columns:
                        # No NaN values
                        nan_count = df[df_constants.in_library].isna().sum()
                        self.assertEqual(
                            nan_count, 0, f"{format_name}: {label} in_library should have no NaN (found {nan_count})"
                        )

                        # All values are strings
                        for val in df[df_constants.in_library]:
                            self.assertIsInstance(
                                val,
                                str,
                                f"{format_name}: {label} in_library value should be string, got {type(val).__name__}",
                            )


if __name__ == "__main__":
    unittest.main()
