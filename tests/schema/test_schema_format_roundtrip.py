"""
Unit tests for schema format I/O roundtrip validation.

Tests that schemas can be loaded, saved in all 4 formats (XML, MEDIAWIKI, TSV, JSON),
and reloaded with perfect fidelity for both standard and library schemas.
"""

import unittest
import os
import tempfile
import shutil
from hed.schema import load_schema_version, load_schema
from hed.schema.schema_io import df_constants


class TestSchemaFormatRoundtrip(unittest.TestCase):
    """Test that all 4 schema formats (XML, MEDIAWIKI, TSV, JSON) roundtrip correctly."""

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
        self.assertTrue(os.path.exists(mediawiki_path), f"MEDIAWIKI file not created: {mediawiki_path}")
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
            schema, schema_from_mediawiki, f"MEDIAWIKI roundtrip failed for {schema_name} (save_merged={save_merged})"
        )
        self.assertEqual(schema, schema_from_tsv, f"TSV roundtrip failed for {schema_name} (save_merged={save_merged})")
        self.assertEqual(schema, schema_from_json, f"JSON roundtrip failed for {schema_name} (save_merged={save_merged})")

        # Compare all formats to each other
        self.assertEqual(
            schema_from_xml, schema_from_mediawiki, f"XML vs MEDIAWIKI mismatch for {schema_name} (save_merged={save_merged})"
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
            "MEDIAWIKI": load_schema(mediawiki_path),
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
            "MEDIAWIKI": load_schema(mediawiki_path),
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
            "MEDIAWIKI": load_schema(mediawiki_path),
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

    def test_json_empty_list_attributes_omitted(self):
        """Test that empty list attributes (suggestedTag, relatedTag, etc.) are omitted from JSON."""
        import json

        schema = load_schema_version("8.4.0")
        json_path = os.path.join(self.temp_dir, "empty_lists.json")
        schema.save_as_json(json_path)

        # Read the JSON file and check for empty list attributes
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Check ALL tags for empty lists
        tags_with_empty_lists = []

        for tag_name, tag_data in json_data.get("tags", {}).items():
            # Check attributes dict
            attrs = tag_data.get("attributes", {})
            for list_attr in ["suggestedTag", "relatedTag", "valueClass", "unitClass"]:
                if list_attr in attrs and attrs[list_attr] == []:
                    tags_with_empty_lists.append(f"{tag_name}.attributes.{list_attr}")

            # Check explicitAttributes dict
            explicit_attrs = tag_data.get("explicitAttributes", {})
            for list_attr in ["suggestedTag", "relatedTag", "valueClass", "unitClass"]:
                if list_attr in explicit_attrs and explicit_attrs[list_attr] == []:
                    tags_with_empty_lists.append(f"{tag_name}.explicitAttributes.{list_attr}")

        self.assertEqual(
            len(tags_with_empty_lists),
            0,
            f"Found {len(tags_with_empty_lists)} empty list attributes: {tags_with_empty_lists[:5]}",
        )

        # Verify that tags WITH these attributes have non-empty lists
        if "Sensory-event" in json_data.get("tags", {}):
            sensory_attrs = json_data["tags"]["Sensory-event"].get("attributes", {})
            if "suggestedTag" in sensory_attrs:
                self.assertTrue(
                    len(sensory_attrs["suggestedTag"]) > 0, "Sensory-event suggestedTag should be non-empty if present"
                )

    def test_extras_sections_roundtrip(self):
        """Test that extras sections (Sources, Prefixes, AnnotationPropertyExternal) roundtrip correctly."""
        schema = load_schema_version("8.4.0")

        # Check that original has extras
        orig_extras = getattr(schema, "extras", {}) or {}
        self.assertGreater(len(orig_extras), 0, "Schema should have extras sections")

        # Save and reload
        json_path = os.path.join(self.temp_dir, "with_extras.json")
        schema.save_as_json(json_path)
        reloaded = load_schema(json_path)

        # Check reloaded has extras
        reloaded_extras = getattr(reloaded, "extras", {}) or {}

        # Compare each extras section
        self.assertEqual(set(orig_extras.keys()), set(reloaded_extras.keys()), "Extras sections should match")

        for key in orig_extras.keys():
            orig_df = orig_extras[key]
            reloaded_df = reloaded_extras[key]
            # Drop in_library column if present (internal metadata not relevant for comparison)
            orig_compare = orig_df.drop(columns=[df_constants.in_library], errors="ignore")
            reloaded_compare = reloaded_df.drop(columns=[df_constants.in_library], errors="ignore")
            self.assertTrue(orig_compare.equals(reloaded_compare), f"Extras section '{key}' should match after roundtrip")

    def test_library_schema_extras_roundtrip(self):
        """Test that library schema extras (external annotations, etc.) roundtrip correctly."""
        schema = load_schema_version("score_2.1.0")

        # Check that library schema has extras
        orig_extras = getattr(schema, "extras", {}) or {}
        self.assertGreater(len(orig_extras), 0, "Library schema should have extras sections")

        # Check for external annotations specifically
        self.assertIn("AnnotationPropertyExternal", orig_extras, "Library schema should have external annotations")

        # Save and reload
        json_path = os.path.join(self.temp_dir, "library_with_extras.json")
        schema.save_as_json(json_path, save_merged=False)
        reloaded = load_schema(json_path)

        # Check reloaded has all extras
        reloaded_extras = getattr(reloaded, "extras", {}) or {}
        self.assertEqual(set(orig_extras.keys()), set(reloaded_extras.keys()), "Library schema extras sections should match")

        # Verify each extras dataframe matches
        for key in orig_extras.keys():
            orig_df = orig_extras[key]
            reloaded_df = reloaded_extras[key]
            # Drop in_library column if present (internal metadata not relevant for comparison)
            orig_compare = orig_df.drop(columns=[df_constants.in_library], errors="ignore")
            reloaded_compare = reloaded_df.drop(columns=[df_constants.in_library], errors="ignore")
            self.assertTrue(
                orig_compare.equals(reloaded_compare), f"Library schema extras '{key}' should match after roundtrip"
            )

    def test_library_schema_score(self):
        """Test score library schema roundtrip specifically."""
        schema = load_schema_version("score_2.1.0")

        # Test unmerged format
        json_path = os.path.join(self.temp_dir, "score_unmerged.json")
        schema.save_as_json(json_path, save_merged=False)
        reloaded = load_schema(json_path)

        # Verify library attributes
        self.assertEqual(schema.library, reloaded.library)
        self.assertEqual(schema.version, reloaded.version)
        self.assertEqual(schema.with_standard, reloaded.with_standard)

        # Verify tag counts match
        self.assertEqual(len(schema.tags.all_entries), len(reloaded.tags.all_entries))

        # Verify prologue and epilogue
        self.assertEqual(schema.prologue, reloaded.prologue)
        self.assertEqual(schema.epilogue, reloaded.epilogue)

    def test_load_from_string_xml(self):
        """Test loading schema from XML string."""
        from hed.schema import from_string

        schema = load_schema_version("8.4.0")

        # Save as XML to get the string
        xml_path = os.path.join(self.temp_dir, "string_test.xml")
        schema.save_as_xml(xml_path)

        # Read as string
        with open(xml_path, encoding="utf-8") as f:
            xml_string = f.read()

        # Load from string
        schema_from_string = from_string(xml_string)

        # Should match original
        self.assertEqual(schema, schema_from_string, "Loading from XML string should produce identical schema")

    def test_load_from_string_mediawiki(self):
        """Test loading schema from MediaWiki string."""
        from hed.schema import from_string

        schema = load_schema_version("8.4.0")

        # Save as MediaWiki to get the string
        wiki_path = os.path.join(self.temp_dir, "string_test.mediawiki")
        schema.save_as_mediawiki(wiki_path)

        # Read as string
        with open(wiki_path, encoding="utf-8") as f:
            wiki_string = f.read()

        # Load from string
        schema_from_string = from_string(wiki_string, schema_format=".mediawiki")

        # Should match original
        self.assertEqual(schema, schema_from_string, "Loading from MediaWiki string should produce identical schema")

    def test_schema_compliance(self):
        """Test schema compliance checking catches validation issues."""
        # Load a compliant schema
        schema = load_schema_version("8.4.0")
        issues = schema.check_compliance()
        self.assertEqual(len(issues), 0, "Current schemas should have no compliance issues")

        # Load an older schema with known issues (HED8.0.0t has compliance problems)
        old_schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED8.0.0t.xml")
        if os.path.exists(old_schema_path):
            old_schema = load_schema(old_schema_path)
            old_issues = old_schema.check_compliance()
            self.assertGreater(len(old_issues), 0, "Old schema should have compliance issues")

    def test_duplicate_detection(self):
        """Test that duplicate units/unit classes are detected during compliance checking."""
        # Test duplicate unit
        dup_unit_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/duplicate_unit.xml")
        if os.path.exists(dup_unit_path):
            schema = load_schema(dup_unit_path)
            issues = schema.check_compliance()
            self.assertEqual(len(issues), 1, "Should detect exactly 1 duplicate unit issue")

        # Test duplicate unit class
        dup_unitclass_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/duplicate_unit_class.xml"
        )
        if os.path.exists(dup_unitclass_path):
            schema = load_schema(dup_unitclass_path)
            issues = schema.check_compliance()
            self.assertEqual(len(issues), 1, "Should detect exactly 1 duplicate unit class issue")

    def test_saving_with_namespace_prefix(self):
        """Test that schemas loaded with a namespace prefix can be saved correctly."""
        old_schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED8.0.0t.xml")
        if not os.path.exists(old_schema_path):
            self.skipTest("Test schema file not available")

        # Load schema without prefix
        schema_no_prefix = load_schema(old_schema_path)

        # Load same schema with prefix
        schema_with_prefix = load_schema(old_schema_path, schema_namespace="tl:")

        # Save the prefixed schema
        xml_path = os.path.join(self.temp_dir, "with_prefix.xml")
        schema_with_prefix.save_as_xml(xml_path)

        # Reload - should match the non-prefixed version
        reloaded = load_schema(xml_path)
        self.assertEqual(reloaded, schema_no_prefix, "Schema with prefix should save and reload as equivalent")

    def test_edge_case_schemas_roundtrip(self):
        """Test that various edge-case schemas (custom properties, unknown attributes, etc.) roundtrip correctly."""
        # Test schemas with custom properties, unknown attributes, multiple value classes, etc.
        edge_case_schemas = [
            "added_prop.xml",
            "added_prop_with_usage.xml",
            "unknown_attribute.xml",
            "HED8.0.0_2_value_classes.xml",
        ]

        for schema_name in edge_case_schemas:
            schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests", schema_name)
            if not os.path.exists(schema_path):
                continue

            with self.subTest(schema=schema_name):
                original = load_schema(schema_path)

                # Test XML roundtrip
                xml_path = os.path.join(self.temp_dir, f"edge_case_{schema_name}")
                original.save_as_xml(xml_path)
                xml_reloaded = load_schema(xml_path)
                self.assertEqual(original, xml_reloaded, f"XML roundtrip failed for {schema_name}")

                # Test MediaWiki roundtrip
                wiki_path = xml_path.replace(".xml", ".mediawiki")
                original.save_as_mediawiki(wiki_path)
                wiki_reloaded = load_schema(wiki_path)
                self.assertEqual(original, wiki_reloaded, f"MediaWiki roundtrip failed for {schema_name}")

                # Test JSON roundtrip
                json_path = xml_path.replace(".xml", ".json")
                original.save_as_json(json_path)
                json_reloaded = load_schema(json_path)
                self.assertEqual(original, json_reloaded, f"JSON roundtrip failed for {schema_name}")

    def test_prologue_preservation(self):
        """Test that prologue/epilogue are preserved correctly across roundtrips."""
        # Test with schemas that have different prologue formatting
        for schema_name in [
            "prologue_tests/test_extra_blank_line_end.xml",
            "prologue_tests/test_extra_blank_line_middle.xml",
            "prologue_tests/test_extra_blank_line_start.xml",
            "prologue_tests/test_no_blank_line.xml",
        ]:
            schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests", schema_name)
            if not os.path.exists(schema_path):
                continue

            with self.subTest(schema=schema_name):
                original = load_schema(schema_path)
                orig_prologue = original.prologue
                orig_epilogue = original.epilogue

                # Test roundtrip preserves prologue/epilogue
                for format_ext, save_method in [
                    (".xml", "save_as_xml"),
                    (".mediawiki", "save_as_mediawiki"),
                    (".json", "save_as_json"),
                ]:
                    save_path = os.path.join(self.temp_dir, f"prologue_test{format_ext}")
                    getattr(original, save_method)(save_path)
                    reloaded = load_schema(save_path)

                    self.assertEqual(
                        orig_prologue,
                        reloaded.prologue,
                        f"Prologue should be preserved in {format_ext} roundtrip for {schema_name}",
                    )
                    self.assertEqual(
                        orig_epilogue,
                        reloaded.epilogue,
                        f"Epilogue should be preserved in {format_ext} roundtrip for {schema_name}",
                    )


if __name__ == "__main__":
    unittest.main()
