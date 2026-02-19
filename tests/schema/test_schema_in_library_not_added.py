"""
Unit tests to verify in_library column is only added for library schemas with withStandard.

Tests that in_library column is NOT added for:
1. Standard schemas (no library attribute)
2. Standalone library schemas (library without withStandard) - if they exist

The in_library column is only relevant for library schemas that are partnered with a standard schema.
"""

import unittest
import os
import tempfile
import shutil
from hed.schema import load_schema_version
from hed.schema.schema_io import df_constants


class TestInLibraryNotAdded(unittest.TestCase):
    """Test that in_library column is only added when appropriate."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_in_library_test_")

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def test_standard_schema_no_in_library_column(self):
        """Test that standard schemas do NOT get in_library column in extras.

        Standard schemas (no library attribute) should not have in_library tracking
        since there's no distinction between library vs standard entries.
        """
        # Load a standard schema that has extras sections (8.4.0+)
        schema = load_schema_version("8.4.0")

        # Verify it's a standard schema
        self.assertEqual(schema.library, "", "Should be a standard schema (no library)")
        self.assertEqual(schema.with_standard, "", "Standard schema should not have withStandard")

        # Check that extras do NOT have in_library column
        sources_df = schema.get_extras(df_constants.SOURCES_KEY)
        if sources_df is not None and not sources_df.empty:
            self.assertNotIn(
                df_constants.in_library,
                sources_df.columns,
                "Standard schema Sources should NOT have in_library column",
            )

        prefixes_df = schema.get_extras(df_constants.PREFIXES_KEY)
        if prefixes_df is not None and not prefixes_df.empty:
            self.assertNotIn(
                df_constants.in_library,
                prefixes_df.columns,
                "Standard schema Prefixes should NOT have in_library column",
            )

        external_df = schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        if external_df is not None and not external_df.empty:
            self.assertNotIn(
                df_constants.in_library,
                external_df.columns,
                "Standard schema External annotations should NOT have in_library column",
            )

    def test_standard_schema_tsv_roundtrip_no_in_library(self):
        """Test that standard schema TSV roundtrip doesn't add in_library column."""
        # Load standard schema
        schema = load_schema_version("8.4.0")

        # Save as TSV
        output_path = os.path.join(self.temp_dir, "standard_schema_tsv")
        schema.save_as_dataframes(output_path)

        # Reload using load_schema (not load_schema_version)
        from hed.schema import load_schema

        reloaded_schema = load_schema(output_path)

        # Verify reloaded schema extras still don't have in_library
        sources_df = reloaded_schema.get_extras(df_constants.SOURCES_KEY)
        if sources_df is not None and not sources_df.empty:
            self.assertNotIn(
                df_constants.in_library,
                sources_df.columns,
                "Reloaded standard schema should not have in_library column",
            )

    def test_library_with_standard_has_in_library(self):
        """Test that library schema WITH withStandard DOES get in_library column (positive control)."""
        # Load library schema with withStandard
        schema = load_schema_version("lang_1.1.0")

        # Verify it's a library schema with withStandard
        self.assertEqual(schema.library, "lang")
        self.assertTrue(bool(schema.with_standard), "Should have withStandard attribute")

        # Check that extras DO have in_library column
        sources_df = schema.get_extras(df_constants.SOURCES_KEY)
        if sources_df is not None and not sources_df.empty:
            self.assertIn(
                df_constants.in_library,
                sources_df.columns,
                "Library schema with withStandard SHOULD have in_library column",
            )

        prefixes_df = schema.get_extras(df_constants.PREFIXES_KEY)
        if prefixes_df is not None and not prefixes_df.empty:
            self.assertIn(
                df_constants.in_library,
                prefixes_df.columns,
                "Library schema with withStandard SHOULD have in_library column",
            )


if __name__ == "__main__":
    unittest.main()
