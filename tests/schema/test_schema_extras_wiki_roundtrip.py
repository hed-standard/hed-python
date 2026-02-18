"""
Unit tests for schema extras sections MediaWiki I/O with in_library tracking.

Tests that extras (Sources, Prefixes, AnnotationPropertyExternal) are correctly:
1. Read from MediaWiki with in_library column added for library schemas
2. Merged correctly when loading withStandard schemas
3. Written to MediaWiki with proper filtering for unmerged/merged saves
4. Round-trip correctly (read -> write -> read)
"""

import unittest
import os
import tempfile
import shutil
from hed.schema import load_schema
from hed.schema.schema_io import df_constants


class TestSchemaExtrasWikiRoundtrip(unittest.TestCase):
    """Test extras sections MediaWiki I/O with in_library tracking."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_extras_wiki_test_")

        # Path to testlib 4.0.0 XML - we'll convert it to MediaWiki for testing
        cls.testlib_4_xml_path = os.path.join(
            os.path.dirname(__file__), "../data/schema_tests/test_merge/HED_testlib_4.0.0.xml"
        )
        cls.testlib_4_xml_path = os.path.normpath(cls.testlib_4_xml_path)

        # Create MediaWiki version for testing
        schema = load_schema(cls.testlib_4_xml_path)
        cls.testlib_4_wiki_path = os.path.join(cls.temp_dir, "HED_testlib_4.0.0.mediawiki")
        schema.save_as_mediawiki(cls.testlib_4_wiki_path, save_merged=False)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def test_read_unmerged_library_extras_has_in_library_column(self):
        """Test that reading unmerged library schema adds in_library column to extras."""
        schema = load_schema(self.testlib_4_wiki_path)

        # Verify schema properties
        self.assertEqual(schema.library, "testlib")
        self.assertEqual(schema.version_number, "4.0.0")
        self.assertEqual(schema.with_standard, "8.4.0")
        self.assertFalse(schema.merged)  # unmerged=True in MediaWiki

        # Check Sources
        sources_df = schema.get_extras(df_constants.SOURCES_KEY)
        self.assertIsNotNone(sources_df, "Sources should not be None")
        self.assertFalse(sources_df.empty, "Sources should not be empty")
        self.assertIn(df_constants.in_library, sources_df.columns, "Sources should have in_library column")
        # Verify all entries have in_library = 'testlib'
        self.assertTrue(
            (sources_df[df_constants.in_library] == "testlib").all(), "All Sources entries should have in_library='testlib'"
        )

        # Check Prefixes
        prefixes_df = schema.get_extras(df_constants.PREFIXES_KEY)
        self.assertIsNotNone(prefixes_df, "Prefixes should not be None")
        self.assertFalse(prefixes_df.empty, "Prefixes should not be empty")
        self.assertIn(df_constants.in_library, prefixes_df.columns, "Prefixes should have in_library column")
        self.assertTrue(
            (prefixes_df[df_constants.in_library] == "testlib").all(), "All Prefixes entries should have in_library='testlib'"
        )

        # Check External Annotations
        external_df = schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        self.assertIsNotNone(external_df, "External annotations should not be None")
        self.assertFalse(external_df.empty, "External annotations should not be empty")
        self.assertIn(df_constants.in_library, external_df.columns, "External annotations should have in_library column")
        self.assertTrue(
            (external_df[df_constants.in_library] == "testlib").all(),
            "All External annotation entries should have in_library='testlib'",
        )

    def test_read_merged_schema_has_mixed_in_library(self):
        """Test that merged library schema properly tracks library entries with in_library column.

        Note: Standard schema 8.4.0 may not have extras sections, so we only verify library entries exist.
        """
        # Load from MediaWiki (auto-merges with standard 8.4.0)
        schema = load_schema(self.testlib_4_wiki_path)

        # Check if any extras exist
        sources_df = schema.get_extras(df_constants.SOURCES_KEY)
        prefixes_df = schema.get_extras(df_constants.PREFIXES_KEY)
        external_df = schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)

        # At minimum, library entries should be present with in_library column
        if sources_df is not None and not sources_df.empty:
            self.assertIn(df_constants.in_library, sources_df.columns)
            # Should have at least one library entry
            library_entries = sources_df[
                sources_df[df_constants.in_library].notna() & (sources_df[df_constants.in_library] != "")
            ]
            self.assertGreater(len(library_entries), 0, "Should have at least one library Source")

        if prefixes_df is not None and not prefixes_df.empty:
            self.assertIn(df_constants.in_library, prefixes_df.columns)
            library_entries = prefixes_df[
                prefixes_df[df_constants.in_library].notna() & (prefixes_df[df_constants.in_library] != "")
            ]
            self.assertGreater(len(library_entries), 0, "Should have at least one library Prefix")

        if external_df is not None and not external_df.empty:
            self.assertIn(df_constants.in_library, external_df.columns)
            library_entries = external_df[
                external_df[df_constants.in_library].notna() & (external_df[df_constants.in_library] != "")
            ]
            self.assertGreater(len(library_entries), 0, "Should have at least one library External annotation")

    def test_write_unmerged_only_outputs_library_extras(self):
        """Test that saving unmerged only outputs extras with in_library column (merged schema saved as unmerged)."""
        # Load schema - it will auto-merge with standard 8.4.0
        merged_schema = load_schema(self.testlib_4_wiki_path)

        # Save the MERGED schema as unmerged - should only output library entries
        output_path = os.path.join(self.temp_dir, "testlib_merged_saved_as_unmerged.mediawiki")
        merged_schema.save_as_mediawiki(output_path, save_merged=False)

        # Reload and verify
        reloaded_schema = load_schema(output_path)

        # Check Sources - should only have library entries
        sources_df = reloaded_schema.get_extras(df_constants.SOURCES_KEY)
        if sources_df is not None and not sources_df.empty:
            # All entries should have in_library column
            self.assertIn(df_constants.in_library, sources_df.columns)
            # All should be library entries (standard entries filtered out)
            self.assertTrue(
                (sources_df[df_constants.in_library] == "testlib").all(), "Unmerged save should only contain library Sources"
            )

        # Check Prefixes
        prefixes_df = reloaded_schema.get_extras(df_constants.PREFIXES_KEY)
        if prefixes_df is not None and not prefixes_df.empty:
            self.assertIn(df_constants.in_library, prefixes_df.columns)
            self.assertTrue(
                (prefixes_df[df_constants.in_library] == "testlib").all(), "Unmerged save should only contain library Prefixes"
            )

        # Check External Annotations
        external_df = reloaded_schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        if external_df is not None and not external_df.empty:
            self.assertIn(df_constants.in_library, external_df.columns)
            self.assertTrue(
                (external_df[df_constants.in_library] == "testlib").all(),
                "Unmerged save should only contain library External annotations",
            )

    def test_write_merged_outputs_all_extras(self):
        """Test that saving merged outputs all extras with inLibrary attributes."""
        # Load schema - auto-merges with standard 8.4.0
        merged_schema = load_schema(self.testlib_4_wiki_path)

        # Save as merged
        output_path = os.path.join(self.temp_dir, "testlib_merged.mediawiki")
        merged_schema.save_as_mediawiki(output_path, save_merged=True)

        # Reload and verify
        reloaded_schema = load_schema(output_path)

        # Should have all extras (library + standard if present)
        sources_df = reloaded_schema.get_extras(df_constants.SOURCES_KEY)
        if sources_df is not None and not sources_df.empty:
            self.assertIn(df_constants.in_library, sources_df.columns)
            # Should have library entries with in_library='testlib'
            library_sources_count = len(sources_df[sources_df[df_constants.in_library] == "testlib"])
            self.assertGreater(library_sources_count, 0, "Merged save should contain library Sources")

        prefixes_df = reloaded_schema.get_extras(df_constants.PREFIXES_KEY)
        if prefixes_df is not None and not prefixes_df.empty:
            self.assertIn(df_constants.in_library, prefixes_df.columns)
            library_prefixes_count = len(prefixes_df[prefixes_df[df_constants.in_library] == "testlib"])
            self.assertGreater(library_prefixes_count, 0, "Merged save should contain library Prefixes")

        external_df = reloaded_schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        if external_df is not None and not external_df.empty:
            self.assertIn(df_constants.in_library, external_df.columns)
            library_externals_count = len(external_df[external_df[df_constants.in_library] == "testlib"])
            self.assertGreater(library_externals_count, 0, "Merged save should contain library External annotations")

    def test_roundtrip_unmerged_preserves_library_extras(self):
        """Test that unmerged roundtrip preserves all library extras."""
        # Load original
        original_schema = load_schema(self.testlib_4_wiki_path)

        # Save as unmerged
        temp_path = os.path.join(self.temp_dir, "roundtrip_unmerged.mediawiki")
        original_schema.save_as_mediawiki(temp_path, save_merged=False)

        # Reload
        roundtrip_schema = load_schema(temp_path)

        # Compare extras
        for extras_key in [df_constants.SOURCES_KEY, df_constants.PREFIXES_KEY, df_constants.EXTERNAL_ANNOTATION_KEY]:
            orig_df = original_schema.get_extras(extras_key)
            roundtrip_df = roundtrip_schema.get_extras(extras_key)

            if orig_df is None or orig_df.empty:
                continue

            self.assertIsNotNone(roundtrip_df, f"{extras_key} should not be None after roundtrip")
            self.assertFalse(roundtrip_df.empty, f"{extras_key} should not be empty after roundtrip")

            # Compare content (drop in_library for comparison as it's set automatically)
            orig_compare = orig_df.drop(columns=[df_constants.in_library], errors="ignore").fillna("")
            roundtrip_compare = roundtrip_df.drop(columns=[df_constants.in_library], errors="ignore").fillna("")

            # Sort for consistent comparison
            orig_compare = orig_compare.sort_values(by=list(orig_compare.columns)).reset_index(drop=True)
            roundtrip_compare = roundtrip_compare.sort_values(by=list(roundtrip_compare.columns)).reset_index(drop=True)

            self.assertTrue(
                orig_compare.equals(roundtrip_compare), f"{extras_key} content should match after unmerged roundtrip"
            )

    def test_roundtrip_merged_preserves_all_extras(self):
        """Test that merged roundtrip preserves all extras with inLibrary tracking."""
        # Load original (auto-merges)
        original_schema = load_schema(self.testlib_4_wiki_path)

        # Save as merged
        temp_path = os.path.join(self.temp_dir, "roundtrip_merged.mediawiki")
        original_schema.save_as_mediawiki(temp_path, save_merged=True)

        # Reload
        roundtrip_schema = load_schema(temp_path)

        # Compare extras
        for extras_key in [df_constants.SOURCES_KEY, df_constants.PREFIXES_KEY, df_constants.EXTERNAL_ANNOTATION_KEY]:
            orig_df = original_schema.get_extras(extras_key)
            roundtrip_df = roundtrip_schema.get_extras(extras_key)

            if orig_df is None or orig_df.empty:
                continue

            self.assertIsNotNone(roundtrip_df, f"{extras_key} should not be None after roundtrip")

            # Compare including in_library column
            orig_compare = orig_df.fillna("").astype(str)
            roundtrip_compare = roundtrip_df.fillna("").astype(str)

            # Sort for consistent comparison
            orig_compare = orig_compare.sort_values(by=list(orig_compare.columns)).reset_index(drop=True)
            roundtrip_compare = roundtrip_compare.sort_values(by=list(roundtrip_compare.columns)).reset_index(drop=True)

            self.assertTrue(
                orig_compare.equals(roundtrip_compare), f"{extras_key} content should match after merged roundtrip"
            )

    def test_merged_wiki_contains_inLibrary_attribute(self):
        """Test that merged MediaWiki output contains inLibrary= in extras sections."""
        # Load and merge
        merged_schema = load_schema(self.testlib_4_wiki_path)

        # Save as merged
        output_path = os.path.join(self.temp_dir, "testlib_merged_check.mediawiki")
        merged_schema.save_as_mediawiki(output_path, save_merged=True)

        # Read file and check for inLibrary in extras sections
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if any extras sections exist and if so, verify they have inLibrary attributes
        if "'''Sources'''" in content:
            # Find the Sources section
            sources_start = content.find("'''Sources'''")
            sources_end = content.find("'''", sources_start + len("'''Sources'''"))
            if sources_end == -1:
                sources_end = len(content)
            sources_section = content[sources_start:sources_end]

            # If there are library entries, they should have inLibrary=testlib
            if "*" in sources_section and "=" in sources_section:
                self.assertIn(
                    "inLibrary=",
                    sources_section,
                    "Expected at least one Sources entry to contain an inLibrary= attribute in merged output",
                )


if __name__ == "__main__":
    unittest.main()
