"""
Unit tests for schema extras sections TSV I/O with in_library tracking.

Tests that extras (Sources, Prefixes, AnnotationPropertyExternal) are correctly:
1. Read from TSV with in_library column added for library schemas
2. Merged correctly when loading withStandard schemas
3. Written to TSV with proper filtering for unmerged/merged saves
4. Round-trip correctly (read -> write -> read)

Note: TSV format does NOT serialize the in_library column (it's internal metadata only).
However, df2schema reconstructs in_library on load by comparing TSV extras against the
partnered standard schema's extras, allowing proper provenance tracking even for merged TSVs.
"""

import unittest
import os
import tempfile
import shutil
from hed.schema import load_schema
from hed.schema.schema_io import df_constants


class TestSchemaExtrasTSVRoundtrip(unittest.TestCase):
    """Test extras sections TSV I/O with in_library tracking."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_extras_tsv_test_")

        # Path to testlib 4.0.0 XML - we'll convert it to TSV for testing
        cls.testlib_4_xml_path = os.path.join(
            os.path.dirname(__file__), "../data/schema_tests/test_merge/HED_testlib_4.0.0.xml"
        )
        cls.testlib_4_xml_path = os.path.normpath(cls.testlib_4_xml_path)

        # Create TSV version for testing
        schema = load_schema(cls.testlib_4_xml_path)
        cls.testlib_4_tsv_dir = os.path.join(cls.temp_dir, "HED_testlib_4.0.0_tsv")
        schema.save_as_dataframes(cls.testlib_4_tsv_dir, save_merged=False)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def test_read_unmerged_library_extras_has_in_library_column(self):
        """Test that reading unmerged library schema adds in_library column to extras.

        Note: Unmerged library schemas with withStandard auto-merge, so extras will contain
        both library entries (in_library='testlib') and standard entries (in_library=None).
        """
        schema = load_schema(self.testlib_4_tsv_dir)

        # Verify schema properties
        self.assertEqual(schema.library, "testlib")
        self.assertEqual(schema.version_number, "4.0.0")
        self.assertEqual(schema.with_standard, "8.4.0")
        self.assertFalse(schema.merged)  # unmerged

        # Check Sources - should have in_library column and at least one library entry
        sources_df = schema.get_extras(df_constants.SOURCES_KEY)
        self.assertIsNotNone(sources_df, "Sources should not be None")
        self.assertFalse(sources_df.empty, "Sources should not be empty")
        self.assertIn(df_constants.in_library, sources_df.columns, "Sources should have in_library column")
        # Verify at least one library entry exists
        library_sources = sources_df[sources_df[df_constants.in_library] == "testlib"]
        self.assertGreater(len(library_sources), 0, "Should have at least one library Source")

        # Check Prefixes - should have in_library column and at least one library entry
        prefixes_df = schema.get_extras(df_constants.PREFIXES_KEY)
        self.assertIsNotNone(prefixes_df, "Prefixes should not be None")
        self.assertFalse(prefixes_df.empty, "Prefixes should not be empty")
        self.assertIn(df_constants.in_library, prefixes_df.columns, "Prefixes should have in_library column")
        library_prefixes = prefixes_df[prefixes_df[df_constants.in_library] == "testlib"]
        self.assertGreater(len(library_prefixes), 0, "Should have at least one library Prefix")

        # Check External Annotations - should have in_library column and at least one library entry
        external_df = schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        self.assertIsNotNone(external_df, "External annotations should not be None")
        self.assertFalse(external_df.empty, "External annotations should not be empty")
        self.assertIn(df_constants.in_library, external_df.columns, "External annotations should have in_library column")
        library_external = external_df[external_df[df_constants.in_library] == "testlib"]
        self.assertGreater(len(library_external), 0, "Should have at least one library External annotation")

    def test_read_merged_schema_has_mixed_in_library(self):
        """Test that merged library schema properly tracks library entries with in_library column.

        Note: Standard schema 8.4.0 may not have extras sections, so we only verify library entries exist.
        """
        # Load from TSV (auto-merges with standard 8.4.0)
        schema = load_schema(self.testlib_4_tsv_dir)

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
        """Test that saving unmerged only outputs library-specific extras to TSV files.

        Note: When reloaded, the schema auto-merges with standard, so the reloaded schema
        will have both library and standard entries. This test verifies the TSV files
        themselves only contain library entries.
        """
        # Load schema - it will auto-merge with standard 8.4.0
        merged_schema = load_schema(self.testlib_4_tsv_dir)

        # Save the MERGED schema as unmerged - should only output library entries
        output_base = "testlib_merged_saved_as_unmerged_tsv"
        output_path = os.path.join(self.temp_dir, output_base)
        merged_schema.save_as_dataframes(output_path, save_merged=False)

        # Check the actual TSV files directly (before reloading)
        # File naming follows: {output_base}/{output_base}_{suffix}.tsv
        import pandas as pd

        sources_file = os.path.join(output_path, f"{output_base}_{df_constants.SOURCES_KEY}.tsv")
        if os.path.exists(sources_file):
            df = pd.read_csv(sources_file, sep="\t", dtype=str, na_filter=False)
            # TSV file should not have in_library column (internal metadata)
            self.assertNotIn(df_constants.in_library, df.columns, "TSV file should not contain in_library column")
            # Should only have library sources (FoodDB from testlib), not standard sources (Wikipedia)
            source_names = df[df_constants.source].tolist()
            self.assertIn("FoodDB", source_names, "Should have library source FoodDB")
            self.assertNotIn("Wikipedia", source_names, "Should not have standard source Wikipedia (unmerged save)")
        else:
            self.fail(f"Sources file not found: {sources_file}")

        prefixes_file = os.path.join(output_path, f"{output_base}_{df_constants.PREFIXES_KEY}.tsv")
        if os.path.exists(prefixes_file):
            df = pd.read_csv(prefixes_file, sep="\t", dtype=str, na_filter=False)
            self.assertNotIn(df_constants.in_library, df.columns, "TSV file should not contain in_library column")

        external_file = os.path.join(output_path, f"{output_base}_{df_constants.EXTERNAL_ANNOTATION_KEY}.tsv")
        if os.path.exists(external_file):
            df = pd.read_csv(external_file, sep="\t", dtype=str, na_filter=False)
            self.assertNotIn(df_constants.in_library, df.columns, "TSV file should not contain in_library column")

    def test_write_merged_outputs_all_extras(self):
        """Test that saving merged outputs all extras data.

        Note: TSV format cannot encode in_library provenance. When a merged TSV is reloaded,
        without partnering to standard schema, we cannot determine which entries are library vs standard.
        This test verifies the data is preserved, not the in_library metadata.
        """
        # Load schema - auto-merges with standard 8.4.0
        merged_schema = load_schema(self.testlib_4_tsv_dir)

        # Save as merged
        output_path = os.path.join(self.temp_dir, "testlib_merged_tsv")
        merged_schema.save_as_dataframes(output_path, save_merged=True)

        # Reload and verify - compare data content (not in_library tracking)
        reloaded_schema = load_schema(output_path)

        # Should have all extras data
        orig_sources = merged_schema.get_extras(df_constants.SOURCES_KEY)
        reload_sources = reloaded_schema.get_extras(df_constants.SOURCES_KEY)
        if orig_sources is not None and not orig_sources.empty:
            self.assertIsNotNone(reload_sources)
            # Compare data columns (excluding in_library)
            orig_data = orig_sources.drop(columns=[df_constants.in_library], errors="ignore")
            reload_data = reload_sources.drop(columns=[df_constants.in_library], errors="ignore")
            self.assertEqual(len(orig_data), len(reload_data), "Merged save should preserve all Sources entries")

        orig_prefixes = merged_schema.get_extras(df_constants.PREFIXES_KEY)
        reload_prefixes = reloaded_schema.get_extras(df_constants.PREFIXES_KEY)
        if orig_prefixes is not None and not orig_prefixes.empty:
            self.assertIsNotNone(reload_prefixes)
            orig_data = orig_prefixes.drop(columns=[df_constants.in_library], errors="ignore")
            reload_data = reload_prefixes.drop(columns=[df_constants.in_library], errors="ignore")
            self.assertEqual(len(orig_data), len(reload_data), "Merged save should preserve all Prefixes entries")

        orig_external = merged_schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        reload_external = reloaded_schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        if orig_external is not None and not orig_external.empty:
            self.assertIsNotNone(reload_external)
            orig_data = orig_external.drop(columns=[df_constants.in_library], errors="ignore")
            reload_data = reload_external.drop(columns=[df_constants.in_library], errors="ignore")
            self.assertEqual(len(orig_data), len(reload_data), "Merged save should preserve all External annotation entries")

    def test_roundtrip_unmerged_preserves_library_extras(self):
        """Test that unmerged roundtrip preserves all library extras.

        Note: We compare only library entries (in_library='testlib') since auto-merging
        adds standard schema entries that may vary.
        """
        # Load original
        original_schema = load_schema(self.testlib_4_tsv_dir)

        # Save as unmerged
        temp_path = os.path.join(self.temp_dir, "roundtrip_unmerged_tsv")
        original_schema.save_as_dataframes(temp_path, save_merged=False)

        # Reload
        roundtrip_schema = load_schema(temp_path)

        # Compare extras - filter to library entries only
        for extras_key in [df_constants.SOURCES_KEY, df_constants.PREFIXES_KEY, df_constants.EXTERNAL_ANNOTATION_KEY]:
            orig_df = original_schema.get_extras(extras_key)
            roundtrip_df = roundtrip_schema.get_extras(extras_key)

            if orig_df is None or orig_df.empty:
                continue

            self.assertIsNotNone(roundtrip_df, f"{extras_key} should not be None after roundtrip")
            self.assertFalse(roundtrip_df.empty, f"{extras_key} should not be empty after roundtrip")

            # Filter to library entries only for comparison (auto-merge adds standard entries)
            orig_lib = orig_df[orig_df[df_constants.in_library] == "testlib"].copy()
            roundtrip_lib = roundtrip_df[roundtrip_df[df_constants.in_library] == "testlib"].copy()

            # Drop in_library for comparison as it's set automatically
            orig_compare = orig_lib.drop(columns=[df_constants.in_library], errors="ignore").fillna("")
            roundtrip_compare = roundtrip_lib.drop(columns=[df_constants.in_library], errors="ignore").fillna("")

            # Sort for consistent comparison
            orig_compare = orig_compare.sort_values(by=list(orig_compare.columns)).reset_index(drop=True)
            roundtrip_compare = roundtrip_compare.sort_values(by=list(roundtrip_compare.columns)).reset_index(drop=True)

            self.assertTrue(
                orig_compare.equals(roundtrip_compare), f"{extras_key} library content should match after unmerged roundtrip"
            )

    def test_roundtrip_merged_preserves_all_extras(self):
        """Test that merged roundtrip preserves all extras data and reconstructs in_library.

        Note: TSV format does not encode in_library in the file, but df2schema reconstructs it
        by loading the partnered standard schema and comparing extras to determine provenance.
        """
        # Load original (auto-merges)
        original_schema = load_schema(self.testlib_4_tsv_dir)

        # Save as merged
        temp_path = os.path.join(self.temp_dir, "roundtrip_merged_tsv")
        original_schema.save_as_dataframes(temp_path, save_merged=True)

        # Reload
        roundtrip_schema = load_schema(temp_path)

        # Compare extras (including in_library which should be reconstructed)
        for extras_key in [df_constants.SOURCES_KEY, df_constants.PREFIXES_KEY, df_constants.EXTERNAL_ANNOTATION_KEY]:
            orig_df = original_schema.get_extras(extras_key)
            roundtrip_df = roundtrip_schema.get_extras(extras_key)

            if orig_df is None or orig_df.empty:
                continue

            self.assertIsNotNone(roundtrip_df, f"{extras_key} should not be None after roundtrip")

            # For merged roundtrip, we should have reconstructed in_library correctly
            # by comparing against the standard schema's extras
            orig_compare = orig_df.fillna("").astype(str)
            roundtrip_compare = roundtrip_df.fillna("").astype(str)

            # Sort for consistent comparison
            orig_compare = orig_compare.sort_values(by=list(orig_compare.columns)).reset_index(drop=True)
            roundtrip_compare = roundtrip_compare.sort_values(by=list(roundtrip_compare.columns)).reset_index(drop=True)

            self.assertTrue(
                orig_compare.equals(roundtrip_compare),
                f"{extras_key} should match after merged roundtrip (including in_library)",
            )

    def test_in_library_column_not_in_tsv_output(self):
        """Test that in_library column is not serialized to TSV output (internal metadata)."""
        # Load schema
        schema = load_schema(self.testlib_4_tsv_dir)

        # Save as TSV (both merged and unmerged)
        merged_base = "check_column_name_merged_tsv"
        unmerged_base = "check_column_name_unmerged_tsv"
        merged_path = os.path.join(self.temp_dir, merged_base)
        unmerged_path = os.path.join(self.temp_dir, unmerged_base)
        schema.save_as_dataframes(merged_path, save_merged=True)
        schema.save_as_dataframes(unmerged_path, save_merged=False)

        # Check merged and unmerged TSVs - read the raw files to verify column names
        import pandas as pd

        # Use actual TSV naming convention: {base}_{suffix}.tsv
        extras_keys = [df_constants.SOURCES_KEY, df_constants.PREFIXES_KEY, df_constants.EXTERNAL_ANNOTATION_KEY]

        for extras_key in extras_keys:
            # Check merged TSV
            merged_file = os.path.join(merged_path, f"{merged_base}_{extras_key}.tsv")
            if os.path.exists(merged_file):
                df = pd.read_csv(merged_file, sep="\t", dtype=str, na_filter=False)
                self.assertNotIn(
                    df_constants.in_library, df.columns, f"Merged TSV should not contain in_library column in {extras_key}"
                )
            else:
                # Only fail if we expect this file to exist (Sources should always exist for testlib)
                if extras_key == df_constants.SOURCES_KEY:
                    self.fail(f"Expected merged TSV file not found: {merged_file}")

            # Check unmerged TSV
            unmerged_file = os.path.join(unmerged_path, f"{unmerged_base}_{extras_key}.tsv")
            if os.path.exists(unmerged_file):
                df = pd.read_csv(unmerged_file, sep="\t", dtype=str, na_filter=False)
                self.assertNotIn(
                    df_constants.in_library,
                    df.columns,
                    f"Unmerged TSV should not contain in_library column in {extras_key}",
                )
            else:
                # Only fail if we expect this file to exist (Sources should always exist for testlib)
                if extras_key == df_constants.SOURCES_KEY:
                    self.fail(f"Expected unmerged TSV file not found: {unmerged_file}")


if __name__ == "__main__":
    unittest.main()
