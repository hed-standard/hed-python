"""
Unit tests for schema extras sections XML I/O with in_library tracking.

Tests that extras (Sources, Prefixes, AnnotationPropertyExternal) are correctly:
1. Read from XML with in_library column added for library schemas
2. Merged correctly when loading withStandard schemas
3. Written to XML with proper filtering for unmerged/merged saves
4. Round-trip correctly (read -> write -> read)
"""

import unittest
import os
import tempfile
import shutil
from hed.schema import load_schema
from hed.schema.schema_io import df_constants


class TestSchemaExtrasXMLRoundtrip(unittest.TestCase):
    """Test extras sections XML I/O with in_library tracking."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_extras_test_")

        # Path to testlib 4.0.0 which has all three extras sections
        cls.testlib_4_path = os.path.join(os.path.dirname(__file__), "../data/schema_tests/test_merge/HED_testlib_4.0.0.xml")

        # Normalize path
        cls.testlib_4_path = os.path.normpath(cls.testlib_4_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def test_read_unmerged_library_extras_has_in_library_column(self):
        """Test that reading unmerged library schema adds in_library column to extras."""
        schema = load_schema(self.testlib_4_path)

        # Verify schema properties
        self.assertEqual(schema.library, "testlib")
        self.assertEqual(schema.version_number, "4.0.0")
        self.assertEqual(schema.with_standard, "8.4.0")
        self.assertFalse(schema.merged)  # unmerged=True in XML

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
        # Load as merged (this happens automatically because withStandard is set)
        schema = load_schema(self.testlib_4_path)

        # The schema loads the standard 8.4.0 first, then merges in library
        # So it should have entries from both (if standard 8.4.0 has extras)

        # Check if any extras exist
        sources_df = schema.get_extras(df_constants.SOURCES_KEY)
        prefixes_df = schema.get_extras(df_constants.PREFIXES_KEY)
        external_df = schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)

        # At minimum, library entries should be present with in_library column
        if sources_df is not None and not sources_df.empty:
            self.assertIn(df_constants.in_library, sources_df.columns)
            # Should have at least one library entry
            library_entries = sources_df[sources_df[df_constants.in_library].notna()]
            self.assertGreater(len(library_entries), 0, "Should have at least one library Source")

        if prefixes_df is not None and not prefixes_df.empty:
            self.assertIn(df_constants.in_library, prefixes_df.columns)
            library_entries = prefixes_df[prefixes_df[df_constants.in_library].notna()]
            self.assertGreater(len(library_entries), 0, "Should have at least one library Prefix")

        if external_df is not None and not external_df.empty:
            self.assertIn(df_constants.in_library, external_df.columns)
            library_entries = external_df[external_df[df_constants.in_library].notna()]
            self.assertGreater(len(library_entries), 0, "Should have at least one library External annotation")

    def test_write_unmerged_only_outputs_library_extras(self):
        """Test that saving unmerged only outputs extras with in_library column (merged schema saved as unmerged)."""
        # Load schema - it will auto-merge with standard 8.4.0
        merged_schema = load_schema(self.testlib_4_path)

        # Save the MERGED schema as unmerged - should only output library entries
        output_path = os.path.join(self.temp_dir, "testlib_merged_saved_as_unmerged.xml")
        merged_schema.save_as_xml(output_path, save_merged=False)

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
        """Test that saving merged outputs all extras (library and standard)."""
        # Load schema - auto-merges with standard 8.4.0
        merged_schema = load_schema(self.testlib_4_path)

        # Get counts before saving
        sources_before = merged_schema.get_extras(df_constants.SOURCES_KEY)
        prefixes_before = merged_schema.get_extras(df_constants.PREFIXES_KEY)
        external_before = merged_schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)

        sources_count_before = len(sources_before) if sources_before is not None else 0
        prefixes_count_before = len(prefixes_before) if prefixes_before is not None else 0
        external_count_before = len(external_before) if external_before is not None else 0

        # Get library entry count
        library_sources = (
            len(sources_before[sources_before[df_constants.in_library].notna()]) if sources_before is not None else 0
        )
        library_prefixes = (
            len(prefixes_before[prefixes_before[df_constants.in_library].notna()]) if prefixes_before is not None else 0
        )
        library_external = (
            len(external_before[external_before[df_constants.in_library].notna()]) if external_before is not None else 0
        )

        # Save as merged
        output_path = os.path.join(self.temp_dir, "testlib_merged.xml")
        merged_schema.save_as_xml(output_path, save_merged=True)

        # Reload - should auto-merge again with standard
        reloaded_schema = load_schema(output_path)

        sources_after = reloaded_schema.get_extras(df_constants.SOURCES_KEY)
        prefixes_after = reloaded_schema.get_extras(df_constants.PREFIXES_KEY)
        external_after = reloaded_schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)

        sources_count_after = len(sources_after) if sources_after is not None else 0
        prefixes_count_after = len(prefixes_after) if prefixes_after is not None else 0
        external_count_after = len(external_after) if external_after is not None else 0

        # Counts should match
        self.assertEqual(sources_count_before, sources_count_after, "Sources count should match after merged round-trip")
        self.assertEqual(prefixes_count_before, prefixes_count_after, "Prefixes count should match after merged round-trip")
        self.assertEqual(
            external_count_before, external_count_after, "External annotations count should match after merged round-trip"
        )

        # Verify library entries are still present in merged save
        if sources_after is not None and not sources_after.empty:
            library_sources_after = len(sources_after[sources_after[df_constants.in_library].notna()])
            self.assertEqual(
                library_sources, library_sources_after, "Library sources should be preserved in merged round-trip"
            )

        if prefixes_after is not None and not prefixes_after.empty:
            library_prefixes_after = len(prefixes_after[prefixes_after[df_constants.in_library].notna()])
            self.assertEqual(
                library_prefixes, library_prefixes_after, "Library prefixes should be preserved in merged round-trip"
            )

        if external_after is not None and not external_after.empty:
            library_external_after = len(external_after[external_after[df_constants.in_library].notna()])
            self.assertEqual(
                library_external,
                library_external_after,
                "Library external annotations should be preserved in merged round-trip",
            )

    def test_roundtrip_unmerged_preserves_library_extras(self):
        """Test round-trip with unmerged: read merged -> save unmerged -> read -> save unmerged -> verify identical."""
        # Load original (auto-merges with standard)
        schema1 = load_schema(self.testlib_4_path)

        # Save as unmerged (filters to library only)
        path1 = os.path.join(self.temp_dir, "testlib_roundtrip_unmerged1.xml")
        schema1.save_as_xml(path1, save_merged=False)

        # Reload (will auto-merge again)
        schema2 = load_schema(path1)

        # Save as unmerged again
        path2 = os.path.join(self.temp_dir, "testlib_roundtrip_unmerged2.xml")
        schema2.save_as_xml(path2, save_merged=False)

        # Reload final
        schema3 = load_schema(path2)

        # Get final extras (library only)
        sources3 = schema3.get_extras(df_constants.SOURCES_KEY)
        prefixes3 = schema3.get_extras(df_constants.PREFIXES_KEY)
        external3 = schema3.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)

        # All should still be library entries only
        if sources3 is not None and not sources3.empty:
            self.assertTrue(
                (sources3[df_constants.in_library] == "testlib").all(), "All Sources should be library entries after roundtrip"
            )
        if prefixes3 is not None and not prefixes3.empty:
            self.assertTrue(
                (prefixes3[df_constants.in_library] == "testlib").all(),
                "All Prefixes should be library entries after roundtrip",
            )
        if external3 is not None and not external3.empty:
            self.assertTrue(
                (external3[df_constants.in_library] == "testlib").all(),
                "All External annotations should be library entries after roundtrip",
            )

    def test_roundtrip_merged_preserves_all_extras(self):
        """Test round-trip with merged: read -> save merged -> read -> save merged -> verify identical."""
        # Load original (auto-merges)
        schema1 = load_schema(self.testlib_4_path)

        # Get original counts
        sources1 = schema1.get_extras(df_constants.SOURCES_KEY)
        prefixes1 = schema1.get_extras(df_constants.PREFIXES_KEY)
        external1 = schema1.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)

        count1_sources = len(sources1) if sources1 is not None else 0
        count1_prefixes = len(prefixes1) if prefixes1 is not None else 0
        count1_external = len(external1) if external1 is not None else 0

        # Save as merged
        path1 = os.path.join(self.temp_dir, "testlib_roundtrip_merged1.xml")
        schema1.save_as_xml(path1, save_merged=True)

        # Reload
        schema2 = load_schema(path1)

        # Get reloaded counts
        sources2 = schema2.get_extras(df_constants.SOURCES_KEY)
        prefixes2 = schema2.get_extras(df_constants.PREFIXES_KEY)
        external2 = schema2.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)

        len(sources2) if sources2 is not None else 0
        len(prefixes2) if prefixes2 is not None else 0
        len(external2) if external2 is not None else 0

        # Save as merged again
        path2 = os.path.join(self.temp_dir, "testlib_roundtrip_merged2.xml")
        schema2.save_as_xml(path2, save_merged=True)

        # Reload again
        schema3 = load_schema(path2)

        sources3 = schema3.get_extras(df_constants.SOURCES_KEY)
        prefixes3 = schema3.get_extras(df_constants.PREFIXES_KEY)
        external3 = schema3.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)

        count3_sources = len(sources3) if sources3 is not None else 0
        count3_prefixes = len(prefixes3) if prefixes3 is not None else 0
        count3_external = len(external3) if external3 is not None else 0

        # Counts should match
        self.assertEqual(count1_sources, count3_sources, "Sources count should be preserved in merged roundtrip")
        self.assertEqual(count1_prefixes, count3_prefixes, "Prefixes count should be preserved in merged roundtrip")
        self.assertEqual(count1_external, count3_external, "External count should be preserved in merged roundtrip")

    def test_in_library_column_not_in_xml_output(self):
        """Test that in_library column is not serialized to XML output, but inLibrary attributes are correctly written."""
        schema = load_schema(self.testlib_4_path)

        # Check that extras have the in_library column
        sources_df = schema.get_extras(df_constants.SOURCES_KEY)
        if sources_df is not None:
            self.assertIn(df_constants.in_library, sources_df.columns, "Extras should have in_library column in memory")

        # Save as XML (both merged and unmerged)
        unmerged_path = os.path.join(self.temp_dir, "testlib_check_in_library_unmerged.xml")
        merged_path = os.path.join(self.temp_dir, "testlib_check_in_library_merged.xml")

        schema.save_as_xml(unmerged_path, save_merged=False)
        schema.save_as_xml(merged_path, save_merged=True)

        # Read the raw XML text for both
        with open(unmerged_path, "r", encoding="utf-8") as f:
            unmerged_content = f.read()
        with open(merged_path, "r", encoding="utf-8") as f:
            merged_content = f.read()

        # Verify in_library column name does not appear in either XML (this is the internal column name)
        self.assertNotIn("in_library", unmerged_content, "in_library column name should not appear in unmerged XML")
        self.assertNotIn("in_library", merged_content, "in_library column name should not appear in merged XML")
        self.assertNotIn("<in_library>", unmerged_content, "in_library element should not appear in unmerged XML")
        self.assertNotIn("<in_library>", merged_content, "in_library element should not appear in merged XML")

        # Parse XML to check for inLibrary attributes in extras sections
        import xml.etree.ElementTree as ET

        unmerged_tree = ET.parse(unmerged_path)
        merged_tree = ET.parse(merged_path)

        # Check unmerged: should have NO inLibrary attributes in extras sections
        # (Because unmerged only includes library entries, and library attributes are stripped)
        unmerged_root = unmerged_tree.getroot()
        for section_name in ["schemaSources", "schemaPrefix", "schemaAnnotationPropertyExternal"]:
            section = unmerged_root.find(f".//{section_name}")
            if section is not None:
                for entry in section:
                    # Check for inLibrary attribute elements
                    attrs = entry.findall(".//attribute")
                    for attr in attrs:
                        name_elem = attr.find("name")
                        if name_elem is not None:
                            self.assertNotEqual(
                                name_elem.text,
                                "inLibrary",
                                f"Unmerged XML should not have inLibrary attributes in {section_name}",
                            )

        # Check merged: should HAVE inLibrary attributes for library entries in extras sections
        # At least one inLibrary attribute should be found in extras (since testlib has all three types)
        merged_root = merged_tree.getroot()
        found_in_library_attr = False
        for section_name in ["schemaSources", "schemaPrefix", "schemaAnnotationPropertyExternal"]:
            section = merged_root.find(f".//{section_name}")
            if section is not None:
                for entry in section:
                    attrs = entry.findall(".//attribute")
                    for attr in attrs:
                        name_elem = attr.find("name")
                        if name_elem is not None and name_elem.text == "inLibrary":
                            found_in_library_attr = True
                            # Verify it has a value
                            value_elem = attr.find("value")
                            self.assertIsNotNone(value_elem, "inLibrary attribute should have value element")
                            self.assertEqual(value_elem.text, "testlib", "inLibrary attribute value should be library name")

        self.assertTrue(found_in_library_attr, "Merged XML should have at least one inLibrary attribute in extras sections")


if __name__ == "__main__":
    unittest.main()
