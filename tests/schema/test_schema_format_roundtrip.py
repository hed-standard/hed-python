"""
Unit tests for schema format I/O roundtrip validation.

Tests that schemas can be loaded, saved in all 4 formats (XML, MediaWiki, TSV, JSON),
and reloaded with perfect fidelity for both standard and library schemas.
"""

import unittest
import os
import tempfile
import shutil
from hed.schema import load_schema_version, load_schema


class TestSchemaFormatRoundtrip(unittest.TestCase):
    """Test that all 4 schema formats (XML, MediaWiki, TSV, JSON) roundtrip correctly."""

    @classmethod
    def setUpClass(cls):
        """Create temporary directory for test files."""
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_schema_test_")

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def _test_format_roundtrip(self, schema, schema_name, save_merged=True):
        """
        Test that a schema can be saved and reloaded in all 4 formats with perfect fidelity.

        Parameters:
            schema: The HedSchema to test
            schema_name: Base name for saved files
            save_merged: Whether to save in merged format (for library schemas)
        """
        # Create file paths for all formats
        basename = f"{schema_name}{'_merged' if save_merged else '_unmerged'}"
        xml_path = os.path.join(self.temp_dir, f"{basename}.xml")
        mediawiki_path = os.path.join(self.temp_dir, f"{basename}.mediawiki")
        tsv_dir = os.path.join(self.temp_dir, "tsv", basename)
        json_path = os.path.join(self.temp_dir, f"{basename}.json")

        # Save schema in all 4 formats
        schema.save_as_xml(xml_path, save_merged=save_merged)
        schema.save_as_mediawiki(mediawiki_path, save_merged=save_merged)
        schema.save_as_dataframes(tsv_dir, save_merged=save_merged)
        schema.save_as_json(json_path, save_merged=save_merged)

        # Verify files were created
        self.assertTrue(os.path.exists(xml_path), f"XML file not created: {xml_path}")
        self.assertTrue(os.path.exists(mediawiki_path), f"MediaWiki file not created: {mediawiki_path}")
        self.assertTrue(os.path.exists(json_path), f"JSON file not created: {json_path}")
        tsv_tag_file = os.path.join(tsv_dir, f"{basename}_Tag.tsv")
        self.assertTrue(os.path.exists(tsv_tag_file), f"TSV Tag file not created: {tsv_tag_file}")

        # Load schemas from all formats
        schema_from_xml = load_schema(xml_path)
        schema_from_mediawiki = load_schema(mediawiki_path)
        schema_from_tsv = load_schema(tsv_dir)
        schema_from_json = load_schema(json_path)

        # Compare all schemas to original
        self.assertEqual(schema, schema_from_xml, f"XML roundtrip failed for {schema_name} (save_merged={save_merged})")
        self.assertEqual(
            schema, schema_from_mediawiki, f"MediaWiki roundtrip failed for {schema_name} (save_merged={save_merged})"
        )
        self.assertEqual(schema, schema_from_tsv, f"TSV roundtrip failed for {schema_name} (save_merged={save_merged})")
        self.assertEqual(schema, schema_from_json, f"JSON roundtrip failed for {schema_name} (save_merged={save_merged})")

        # Compare all formats to each other
        self.assertEqual(
            schema_from_xml, schema_from_mediawiki, f"XML vs MediaWiki mismatch for {schema_name} (save_merged={save_merged})"
        )
        self.assertEqual(
            schema_from_xml, schema_from_tsv, f"XML vs TSV mismatch for {schema_name} (save_merged={save_merged})"
        )
        self.assertEqual(
            schema_from_xml, schema_from_json, f"XML vs JSON mismatch for {schema_name} (save_merged={save_merged})"
        )

    def test_standard_schema_8_4_0(self):
        """Test HED 8.4.0 standard schema roundtrip in all formats."""
        schema = load_schema_version("8.4.0")
        self.assertIsNotNone(schema, "Failed to load HED 8.4.0 schema")
        self.assertEqual(schema.version_number, "8.4.0")
        self.assertEqual(schema.library, "")

        # Test with standard schema (save_merged not applicable but should work)
        self._test_format_roundtrip(schema, "HED8.4.0", save_merged=True)

    def test_library_schema_lang_merged(self):
        """Test lang 1.1.0 library schema roundtrip in merged format."""
        schema = load_schema_version("lang_1.1.0")
        self.assertIsNotNone(schema, "Failed to load lang 1.1.0 schema")
        self.assertEqual(schema.library, "lang")
        self.assertEqual(schema.version_number, "1.1.0")
        self.assertEqual(schema.with_standard, "8.4.0")

        # Test merged format (includes standard schema tags)
        self._test_format_roundtrip(schema, "lang_1.1.0", save_merged=True)

    def test_library_schema_lang_unmerged(self):
        """Test lang 1.1.0 library schema roundtrip in unmerged format."""
        schema = load_schema_version("lang_1.1.0")
        self.assertIsNotNone(schema, "Failed to load lang 1.1.0 schema")

        # Test unmerged format (library tags only)
        self._test_format_roundtrip(schema, "lang_1.1.0", save_merged=False)

    def test_format_compatibility_standard(self):
        """Test that all formats produce identical schemas for standard schema."""
        schema = load_schema_version("8.4.0")

        # Save in all formats
        xml_path = os.path.join(self.temp_dir, "compat_std.xml")
        mediawiki_path = os.path.join(self.temp_dir, "compat_std.mediawiki")
        tsv_dir = os.path.join(self.temp_dir, "tsv", "compat_std")
        json_path = os.path.join(self.temp_dir, "compat_std.json")

        schema.save_as_xml(xml_path)
        schema.save_as_mediawiki(mediawiki_path)
        schema.save_as_dataframes(tsv_dir)
        schema.save_as_json(json_path)

        # Load all formats
        schemas = {
            "XML": load_schema(xml_path),
            "MediaWiki": load_schema(mediawiki_path),
            "TSV": load_schema(tsv_dir),
            "JSON": load_schema(json_path),
        }

        # All formats should be equal to each other
        format_names = list(schemas.keys())
        for i, format1 in enumerate(format_names):
            for format2 in format_names[i + 1 :]:
                self.assertEqual(
                    schemas[format1],
                    schemas[format2],
                    f"{format1} and {format2} formats produced different schemas for standard schema",
                )

    def test_format_compatibility_library_merged(self):
        """Test that all formats produce identical schemas for library schema (merged)."""
        schema = load_schema_version("lang_1.1.0")

        # Save in all formats (merged)
        xml_path = os.path.join(self.temp_dir, "compat_lib_merged.xml")
        mediawiki_path = os.path.join(self.temp_dir, "compat_lib_merged.mediawiki")
        tsv_dir = os.path.join(self.temp_dir, "tsv", "compat_lib_merged")
        json_path = os.path.join(self.temp_dir, "compat_lib_merged.json")

        schema.save_as_xml(xml_path, save_merged=True)
        schema.save_as_mediawiki(mediawiki_path, save_merged=True)
        schema.save_as_dataframes(tsv_dir, save_merged=True)
        schema.save_as_json(json_path, save_merged=True)

        # Load all formats
        schemas = {
            "XML": load_schema(xml_path),
            "MediaWiki": load_schema(mediawiki_path),
            "TSV": load_schema(tsv_dir),
            "JSON": load_schema(json_path),
        }

        # All formats should be equal to each other
        format_names = list(schemas.keys())
        for i, format1 in enumerate(format_names):
            for format2 in format_names[i + 1 :]:
                self.assertEqual(
                    schemas[format1],
                    schemas[format2],
                    f"{format1} and {format2} formats produced different schemas for library (merged)",
                )

    def test_format_compatibility_library_unmerged(self):
        """Test that all formats produce identical schemas for library schema (unmerged)."""
        schema = load_schema_version("lang_1.1.0")

        # Save in all formats (unmerged)
        xml_path = os.path.join(self.temp_dir, "compat_lib_unmerged.xml")
        mediawiki_path = os.path.join(self.temp_dir, "compat_lib_unmerged.mediawiki")
        tsv_dir = os.path.join(self.temp_dir, "tsv", "compat_lib_unmerged")
        json_path = os.path.join(self.temp_dir, "compat_lib_unmerged.json")

        schema.save_as_xml(xml_path, save_merged=False)
        schema.save_as_mediawiki(mediawiki_path, save_merged=False)
        schema.save_as_dataframes(tsv_dir, save_merged=False)
        schema.save_as_json(json_path, save_merged=False)

        # Load all formats
        schemas = {
            "XML": load_schema(xml_path),
            "MediaWiki": load_schema(mediawiki_path),
            "TSV": load_schema(tsv_dir),
            "JSON": load_schema(json_path),
        }

        # All formats should be equal to each other
        format_names = list(schemas.keys())
        for i, format1 in enumerate(format_names):
            for format2 in format_names[i + 1 :]:
                self.assertEqual(
                    schemas[format1],
                    schemas[format2],
                    f"{format1} and {format2} formats produced different schemas for library (unmerged)",
                )

    def test_json_specific_features(self):
        """Test JSON-specific features like multi-value attributes and boolean preservation."""
        schema = load_schema_version("lang_1.1.0")

        # Save as JSON
        json_path = os.path.join(self.temp_dir, "json_features.json")
        schema.save_as_json(json_path, save_merged=True)

        # Reload and verify
        schema_from_json = load_schema(json_path)
        self.assertEqual(schema, schema_from_json, "JSON roundtrip failed")

        # Verify specific tags with multi-value attributes exist
        # (These are in the lang schema and have annotation attributes)
        if "Language-item-property" in schema.tags:
            original_tag = schema.tags["Language-item-property"]
            reloaded_tag = schema_from_json.tags["Language-item-property"]

            # Verify attributes match
            self.assertEqual(
                original_tag.attributes, reloaded_tag.attributes, "Tag attributes don't match after JSON roundtrip"
            )

    def test_library_schema_header_attributes(self):
        """Test that library schema header attributes are preserved correctly."""
        schema = load_schema_version("lang_1.1.0")

        # Test merged
        json_merged = os.path.join(self.temp_dir, "header_merged.json")
        schema.save_as_json(json_merged, save_merged=True)
        schema_merged = load_schema(json_merged)

        self.assertEqual(schema.library, schema_merged.library)
        self.assertEqual(schema.version_number, schema_merged.version_number)
        self.assertEqual(schema.with_standard, schema_merged.with_standard)

        # Test unmerged
        json_unmerged = os.path.join(self.temp_dir, "header_unmerged.json")
        schema.save_as_json(json_unmerged, save_merged=False)
        schema_unmerged = load_schema(json_unmerged)

        self.assertEqual(schema.library, schema_unmerged.library)
        # Version number might be different for unmerged (without library prefix)
        self.assertEqual(schema.with_standard, schema_unmerged.with_standard)


if __name__ == "__main__":
    unittest.main()
