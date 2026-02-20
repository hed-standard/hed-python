"""
Comprehensive tests for schema extras sections across all formats.

Tests that extras (Sources, Prefixes, ExternalAnnotations) are correctly:
1. Read from all formats (XML, JSON, MediaWiki, TSV) without in_library tracking
2. Have consistent internal representation across formats
3. Round-trip correctly (read → write → read)
4. Save identically for both merged and unmerged modes
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

        # Expected counts for testlib 4.0.0
        cls.expected_sources = 2
        cls.expected_prefixes = 14
        cls.expected_externals = 17

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def _verify_extras_dataframe(self, df, expected_len, expected_columns, format_name, section_name):
        """Helper to verify DataFrame structure and content."""
        self.assertIsNotNone(df, f"{format_name} {section_name} should not be None")
        self.assertEqual(len(df), expected_len, f"{format_name} {section_name} should have {expected_len} entries")
        self.assertEqual(list(df.columns), expected_columns, f"{format_name} {section_name} columns mismatch")
        self.assertNotIn("in_library", df.columns, f"{format_name} {section_name} should NOT have in_library column")

    def _verify_dataframes_equal(self, df1, df2, name1, name2, section):
        """Helper to verify two DataFrames are identical."""
        # Sort both by all columns for comparison
        if df1 is not None and not df1.empty:
            df1_sorted = df1.sort_values(by=list(df1.columns)).reset_index(drop=True)
        else:
            df1_sorted = df1

        if df2 is not None and not df2.empty:
            df2_sorted = df2.sort_values(by=list(df2.columns)).reset_index(drop=True)
        else:
            df2_sorted = df2

        pd.testing.assert_frame_equal(df1_sorted, df2_sorted, check_dtype=False, obj=f"{section}: {name1} vs {name2}")

    def test_01_all_formats_load_extras_correctly(self):
        """Test that all formats load extras with correct counts and no in_library column."""
        formats = {
            "XML": self.xml_path,
            "JSON": self.json_path,
            "MediaWiki": self.wiki_path,
            "TSV": self.tsv_path,
        }

        for format_name, path in formats.items():
            with self.subTest(format=format_name):
                schema = load_schema(path)

                # Verify schema properties
                self.assertEqual(schema.library, "testlib")
                self.assertEqual(schema.version_number, "4.0.0")
                self.assertEqual(schema.with_standard, "8.4.0")
                self.assertFalse(schema.merged)

                # Verify Sources
                sources = schema.get_extras(df_constants.SOURCES_KEY)
                self._verify_extras_dataframe(
                    sources, self.expected_sources, df_constants.source_columns, format_name, "Sources"
                )

                # Verify Prefixes
                prefixes = schema.get_extras(df_constants.PREFIXES_KEY)
                self._verify_extras_dataframe(
                    prefixes, self.expected_prefixes, df_constants.prefix_columns, format_name, "Prefixes"
                )

                # Verify External Annotations
                externals = schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
                self._verify_extras_dataframe(
                    externals,
                    self.expected_externals,
                    df_constants.external_annotation_columns,
                    format_name,
                    "ExternalAnnotations",
                )

    def test_02_all_formats_have_identical_internal_representation(self):
        """Test that all formats produce identical internal DataFrames."""
        # Load all formats
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
                # Compare Sources
                self._verify_dataframes_equal(
                    schemas[fmt1].get_extras(df_constants.SOURCES_KEY),
                    schemas[fmt2].get_extras(df_constants.SOURCES_KEY),
                    fmt1,
                    fmt2,
                    "Sources",
                )

                # Compare Prefixes
                self._verify_dataframes_equal(
                    schemas[fmt1].get_extras(df_constants.PREFIXES_KEY),
                    schemas[fmt2].get_extras(df_constants.PREFIXES_KEY),
                    fmt1,
                    fmt2,
                    "Prefixes",
                )

                # Compare External Annotations
                self._verify_dataframes_equal(
                    schemas[fmt1].get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
                    schemas[fmt2].get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
                    fmt1,
                    fmt2,
                    "ExternalAnnotations",
                )

    def test_03_xml_roundtrip_unmerged(self):
        """Test XML load → save unmerged → reload cycle."""
        schema = load_schema(self.xml_path)
        temp_xml = os.path.join(self.temp_dir, "roundtrip_unmerged.xml")

        # Save as unmerged
        schema.save_as_xml(temp_xml, save_merged=False)

        # Reload
        schema_reloaded = load_schema(temp_xml)

        # Verify extras match
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.SOURCES_KEY),
            schema_reloaded.get_extras(df_constants.SOURCES_KEY),
            "original",
            "reloaded",
            "Sources",
        )
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.PREFIXES_KEY),
            schema_reloaded.get_extras(df_constants.PREFIXES_KEY),
            "original",
            "reloaded",
            "Prefixes",
        )
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            schema_reloaded.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            "original",
            "reloaded",
            "ExternalAnnotations",
        )

    def test_04_json_roundtrip_unmerged(self):
        """Test JSON load → save unmerged → reload cycle."""
        schema = load_schema(self.json_path)
        temp_json = os.path.join(self.temp_dir, "roundtrip_unmerged.json")

        # Save as unmerged
        schema.save_as_json(temp_json, save_merged=False)

        # Reload
        schema_reloaded = load_schema(temp_json)

        # Verify extras match
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.SOURCES_KEY),
            schema_reloaded.get_extras(df_constants.SOURCES_KEY),
            "original",
            "reloaded",
            "Sources",
        )
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.PREFIXES_KEY),
            schema_reloaded.get_extras(df_constants.PREFIXES_KEY),
            "original",
            "reloaded",
            "Prefixes",
        )
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            schema_reloaded.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            "original",
            "reloaded",
            "ExternalAnnotations",
        )

    def test_05_mediawiki_roundtrip_unmerged(self):
        """Test MediaWiki load → save unmerged → reload cycle."""
        schema = load_schema(self.wiki_path)
        temp_wiki = os.path.join(self.temp_dir, "roundtrip_unmerged.mediawiki")

        # Save as unmerged
        schema.save_as_mediawiki(temp_wiki, save_merged=False)

        # Reload
        schema_reloaded = load_schema(temp_wiki)

        # Verify extras match
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.SOURCES_KEY),
            schema_reloaded.get_extras(df_constants.SOURCES_KEY),
            "original",
            "reloaded",
            "Sources",
        )
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.PREFIXES_KEY),
            schema_reloaded.get_extras(df_constants.PREFIXES_KEY),
            "original",
            "reloaded",
            "Prefixes",
        )
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            schema_reloaded.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            "original",
            "reloaded",
            "ExternalAnnotations",
        )

    def test_06_tsv_roundtrip_unmerged(self):
        """Test TSV load → save unmerged → reload cycle."""
        schema = load_schema(self.tsv_path)
        temp_tsv_dir = os.path.join(self.temp_dir, "roundtrip_unmerged_tsv")

        # Save as unmerged
        schema.save_as_dataframes(temp_tsv_dir, save_merged=False)

        # Reload
        schema_reloaded = load_schema(temp_tsv_dir)

        # Verify extras match
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.SOURCES_KEY),
            schema_reloaded.get_extras(df_constants.SOURCES_KEY),
            "original",
            "reloaded",
            "Sources",
        )
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.PREFIXES_KEY),
            schema_reloaded.get_extras(df_constants.PREFIXES_KEY),
            "original",
            "reloaded",
            "Prefixes",
        )
        self._verify_dataframes_equal(
            schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            schema_reloaded.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            "original",
            "reloaded",
            "ExternalAnnotations",
        )

    def test_07_merged_and_unmerged_saves_identical(self):
        """Test that merged and unmerged saves produce identical extras sections."""
        schema = load_schema(self.xml_path)

        # Save as both merged and unmerged
        temp_merged = os.path.join(self.temp_dir, "save_merged.xml")
        temp_unmerged = os.path.join(self.temp_dir, "save_unmerged.xml")

        schema.save_as_xml(temp_merged, save_merged=True)
        schema.save_as_xml(temp_unmerged, save_merged=False)

        # Reload both
        schema_merged = load_schema(temp_merged)
        schema_unmerged = load_schema(temp_unmerged)

        # Verify extras are identical
        self._verify_dataframes_equal(
            schema_merged.get_extras(df_constants.SOURCES_KEY),
            schema_unmerged.get_extras(df_constants.SOURCES_KEY),
            "merged",
            "unmerged",
            "Sources",
        )
        self._verify_dataframes_equal(
            schema_merged.get_extras(df_constants.PREFIXES_KEY),
            schema_unmerged.get_extras(df_constants.PREFIXES_KEY),
            "merged",
            "unmerged",
            "Prefixes",
        )
        self._verify_dataframes_equal(
            schema_merged.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            schema_unmerged.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
            "merged",
            "unmerged",
            "ExternalAnnotations",
        )

    def test_08_cross_format_roundtrip(self):
        """Test loading in one format and saving in another."""
        # Load from XML
        schema = load_schema(self.xml_path)

        # Save in all other formats
        temp_json = os.path.join(self.temp_dir, "cross_format.json")
        temp_wiki = os.path.join(self.temp_dir, "cross_format.mediawiki")
        temp_tsv = os.path.join(self.temp_dir, "cross_format_tsv")

        schema.save_as_json(temp_json, save_merged=False)
        schema.save_as_mediawiki(temp_wiki, save_merged=False)
        schema.save_as_dataframes(temp_tsv, save_merged=False)

        # Reload from each format
        schema_json = load_schema(temp_json)
        schema_wiki = load_schema(temp_wiki)
        schema_tsv = load_schema(temp_tsv)

        # Verify all match the original
        for fmt_name, schema_fmt in [("JSON", schema_json), ("Wiki", schema_wiki), ("TSV", schema_tsv)]:
            with self.subTest(target_format=fmt_name):
                self._verify_dataframes_equal(
                    schema.get_extras(df_constants.SOURCES_KEY),
                    schema_fmt.get_extras(df_constants.SOURCES_KEY),
                    "XML_original",
                    fmt_name,
                    "Sources",
                )
                self._verify_dataframes_equal(
                    schema.get_extras(df_constants.PREFIXES_KEY),
                    schema_fmt.get_extras(df_constants.PREFIXES_KEY),
                    "XML_original",
                    fmt_name,
                    "Prefixes",
                )
                self._verify_dataframes_equal(
                    schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
                    schema_fmt.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY),
                    "XML_original",
                    fmt_name,
                    "ExternalAnnotations",
                )


if __name__ == "__main__":
    unittest.main()
