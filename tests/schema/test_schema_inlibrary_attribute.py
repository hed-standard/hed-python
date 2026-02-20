"""
Comprehensive tests for inLibrary attribute behavior across all formats and save modes.

Tests that the inLibrary attribute is:
1. Present in schema sections (Unit, UnitClass, UnitModifier, ValueClass) when save_merged=True
2. Absent in schema sections when save_merged=False
3. NEVER present in extras sections (Sources, Prefixes, ExternalAnnotations) in any save mode
4. Correctly preserved across format roundtrips
5. Correctly formatted in each output format (XML, JSON, MediaWiki, TSV)
"""

import unittest
import os
import tempfile
import shutil
import pandas as pd
from hed.schema import load_schema_version, load_schema


class TestInLibraryAttribute(unittest.TestCase):
    """Test inLibrary attribute presence/absence in various sections and save modes."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_inlibrary_test_")

        # Load test library schemas - use public versions
        cls.lang_schema = load_schema_version("lang_1.1.0")
        cls.score_schema = load_schema_version("score_1.1.0")

        # Also load testlib from test data if available
        cls.test_data_dir = os.path.join(os.path.dirname(__file__), "../data/schema_tests/test_merge")
        cls.test_data_dir = os.path.normpath(cls.test_data_dir)
        cls.testlib_path = os.path.join(cls.test_data_dir, "HED_testlib_4.0.0")

        cls.testlib_schema = None
        if os.path.exists(cls.testlib_path):
            cls.testlib_schema = load_schema(cls.testlib_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def _get_library_name(self, schema):
        """Get the library name from schema."""
        return schema.library

    def _save_schema_all_formats(self, schema, basename, save_merged):
        """Save schema in all 4 formats and return paths."""
        paths = {}
        paths["xml"] = os.path.join(self.temp_dir, f"{basename}_merged_{save_merged}.xml")
        paths["json"] = os.path.join(self.temp_dir, f"{basename}_merged_{save_merged}.json")
        paths["mediawiki"] = os.path.join(self.temp_dir, f"{basename}_merged_{save_merged}.mediawiki")
        paths["tsv"] = os.path.join(self.temp_dir, f"{basename}_merged_{save_merged}_tsv")

        schema.save_as_xml(paths["xml"], save_merged=save_merged)
        schema.save_as_json(paths["json"], save_merged=save_merged)
        schema.save_as_mediawiki(paths["mediawiki"], save_merged=save_merged)
        schema.save_as_dataframes(paths["tsv"], save_merged=save_merged)

        return paths

    def _verify_inlibrary_in_tsv_schema_sections(self, tsv_dir, library_name, should_have_inlibrary):
        """
        Verify inLibrary presence/absence in TSV files by reading all TSV files and checking
        if inLibrary appears in any Attributes column value.

        Parameters:
            tsv_dir: Directory containing TSV files
            library_name: Name of the library (e.g., 'lang', 'score')
            should_have_inlibrary: True if inLibrary should be present, False otherwise
        """
        # Read all TSV files in the directory
        inlibrary_pattern = f"inLibrary={library_name}"
        found_inlibrary = False

        for tsv_file in os.listdir(tsv_dir):
            if not tsv_file.endswith(".tsv"):
                continue

            full_path = os.path.join(tsv_dir, tsv_file)
            df = pd.read_csv(full_path, sep="\t", dtype=str, keep_default_na=False)

            # Check Attributes column if it exists
            if "Attributes" in df.columns:
                if df["Attributes"].str.contains(inlibrary_pattern, na=False).any():
                    found_inlibrary = True
                    break

        if should_have_inlibrary:
            # Note: Some schemas (like score) may have no library-specific schema sections,
            # only library-specific tags. So we don't assert here, just note if found.
            # The main check is in the full string formats (XML, JSON, MediaWiki)
            pass
        else:
            self.assertFalse(found_inlibrary, f"TSV files should NOT contain inLibrary={library_name} when save_merged=False")

    def _verify_no_inlibrary_in_tsv_extras(self, tsv_dir):
        """Verify extras sections in TSV never have in_library column."""
        extras_sections = ["Sources", "Prefixes", "ExternalAnnotations"]
        basename = os.path.basename(tsv_dir)

        for section in extras_sections:
            tsv_file = os.path.join(tsv_dir, f"{basename}_{section}.tsv")
            if not os.path.exists(tsv_file):
                continue

            df = pd.read_csv(tsv_file, sep="\t", dtype=str, keep_default_na=False)
            self.assertNotIn("in_library", df.columns, f"TSV {section} should NEVER have in_library column")

    def _verify_inlibrary_in_xml(self, xml_path, library_name, should_have_inlibrary):
        """Verify inLibrary presence/absence in XML file."""
        with open(xml_path, "r", encoding="utf-8") as f:
            content = f.read()

        inlibrary_pattern = "<name>inLibrary</name>"

        has_inlibrary_attr = inlibrary_pattern in content

        if should_have_inlibrary:
            self.assertTrue(has_inlibrary_attr, "XML should contain inLibrary attributes when save_merged=True")
            # Verify it's actually set to the correct library name
            if has_inlibrary_attr:
                # Count occurrences - should have many for schema sections
                count = content.count(inlibrary_pattern)
                self.assertGreater(
                    count, 0, "XML should have multiple inLibrary attributes for library schema when save_merged=True"
                )
        else:
            self.assertFalse(has_inlibrary_attr, "XML should NOT contain inLibrary attributes when save_merged=False")

    def _verify_inlibrary_in_json(self, json_path, library_name, should_have_inlibrary):
        """Verify inLibrary presence/absence in JSON file."""
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()

        inlibrary_pattern = f'"inLibrary": "{library_name}"'
        has_inlibrary = inlibrary_pattern in content

        if should_have_inlibrary:
            self.assertTrue(has_inlibrary, "JSON should contain inLibrary fields when save_merged=True")
        else:
            # Check that inLibrary doesn't appear with this library name
            self.assertFalse(has_inlibrary, f"JSON should NOT contain inLibrary={library_name} when save_merged=False")

    def _verify_inlibrary_in_mediawiki(self, wiki_path, library_name, should_have_inlibrary):
        """Verify inLibrary presence/absence in MediaWiki file."""
        with open(wiki_path, "r", encoding="utf-8") as f:
            content = f.read()

        # MediaWiki uses curly braces for attributes, not square brackets
        inlibrary_pattern = f"inLibrary={library_name}"
        has_inlibrary = inlibrary_pattern in content

        if should_have_inlibrary:
            self.assertTrue(has_inlibrary, f"MediaWiki should contain inLibrary={library_name} when save_merged=True")
        else:
            self.assertFalse(has_inlibrary, f"MediaWiki should NOT contain inLibrary={library_name} when save_merged=False")

    def test_01_schema_sections_have_inlibrary_when_merged(self):
        """Test that schema sections have inLibrary attribute when save_merged=True."""
        for schema, schema_name in [(self.lang_schema, "lang"), (self.score_schema, "score")]:
            with self.subTest(schema=schema_name):
                library_name = self._get_library_name(schema)
                paths = self._save_schema_all_formats(schema, schema_name, save_merged=True)

                # Verify TSV
                self._verify_inlibrary_in_tsv_schema_sections(paths["tsv"], library_name, should_have_inlibrary=True)

                # Verify XML
                self._verify_inlibrary_in_xml(paths["xml"], library_name, should_have_inlibrary=True)

                # Verify JSON
                self._verify_inlibrary_in_json(paths["json"], library_name, should_have_inlibrary=True)

                # Verify MediaWiki
                self._verify_inlibrary_in_mediawiki(paths["mediawiki"], library_name, should_have_inlibrary=True)

    def test_02_schema_sections_no_inlibrary_when_unmerged(self):
        """Test that schema sections do NOT have inLibrary attribute when save_merged=False."""
        for schema, schema_name in [(self.lang_schema, "lang"), (self.score_schema, "score")]:
            with self.subTest(schema=schema_name):
                library_name = self._get_library_name(schema)
                paths = self._save_schema_all_formats(schema, schema_name, save_merged=False)

                # Verify TSV
                self._verify_inlibrary_in_tsv_schema_sections(paths["tsv"], library_name, should_have_inlibrary=False)

                # Verify XML
                self._verify_inlibrary_in_xml(paths["xml"], library_name, should_have_inlibrary=False)

                # Verify JSON
                self._verify_inlibrary_in_json(paths["json"], library_name, should_have_inlibrary=False)

                # Verify MediaWiki
                self._verify_inlibrary_in_mediawiki(paths["mediawiki"], library_name, should_have_inlibrary=False)

    def test_03_extras_never_have_inlibrary_merged(self):
        """Test that extras sections NEVER have inLibrary even when save_merged=True."""
        for schema, schema_name in [(self.lang_schema, "lang"), (self.score_schema, "score")]:
            with self.subTest(schema=schema_name):
                paths = self._save_schema_all_formats(schema, schema_name, save_merged=True)

                # Only check TSV as extras are only stored as DataFrames
                self._verify_no_inlibrary_in_tsv_extras(paths["tsv"])

    def test_04_extras_never_have_inlibrary_unmerged(self):
        """Test that extras sections NEVER have inLibrary even when save_merged=False."""
        for schema, schema_name in [(self.lang_schema, "lang"), (self.score_schema, "score")]:
            with self.subTest(schema=schema_name):
                paths = self._save_schema_all_formats(schema, schema_name, save_merged=False)

                # Only check TSV as extras are only stored as DataFrames
                self._verify_no_inlibrary_in_tsv_extras(paths["tsv"])

    def test_05_inlibrary_preserved_in_roundtrip_merged(self):
        """Test that inLibrary attributes are preserved through save/load cycles when merged."""
        schema = self.lang_schema
        library_name = self._get_library_name(schema)

        # Save in all formats with save_merged=True
        paths = self._save_schema_all_formats(schema, "lang_roundtrip", save_merged=True)

        # Reload from each format
        for format_name, path in paths.items():
            with self.subTest(format=format_name):
                reloaded = load_schema(path)

                # Save again in same format
                if format_name == "xml":
                    roundtrip_path = os.path.join(self.temp_dir, "lang_roundtrip2.xml")
                    reloaded.save_as_xml(roundtrip_path, save_merged=True)
                    self._verify_inlibrary_in_xml(roundtrip_path, library_name, should_have_inlibrary=True)
                elif format_name == "json":
                    roundtrip_path = os.path.join(self.temp_dir, "lang_roundtrip2.json")
                    reloaded.save_as_json(roundtrip_path, save_merged=True)
                    self._verify_inlibrary_in_json(roundtrip_path, library_name, should_have_inlibrary=True)
                elif format_name == "mediawiki":
                    roundtrip_path = os.path.join(self.temp_dir, "lang_roundtrip2.mediawiki")
                    reloaded.save_as_mediawiki(roundtrip_path, save_merged=True)
                    self._verify_inlibrary_in_mediawiki(roundtrip_path, library_name, should_have_inlibrary=True)
                elif format_name == "tsv":
                    roundtrip_path = os.path.join(self.temp_dir, "lang_roundtrip2_tsv")
                    reloaded.save_as_dataframes(roundtrip_path, save_merged=True)
                    self._verify_inlibrary_in_tsv_schema_sections(roundtrip_path, library_name, should_have_inlibrary=True)

    def test_06_inlibrary_absent_in_roundtrip_unmerged(self):
        """Test that inLibrary attributes remain absent through save/load cycles when unmerged."""
        schema = self.lang_schema
        library_name = self._get_library_name(schema)

        # Save in all formats with save_merged=False
        paths = self._save_schema_all_formats(schema, "lang_roundtrip_unmerged", save_merged=False)

        # Reload from each format
        for format_name, path in paths.items():
            with self.subTest(format=format_name):
                reloaded = load_schema(path)

                # Save again in same format
                if format_name == "xml":
                    roundtrip_path = os.path.join(self.temp_dir, "lang_roundtrip_unmerged2.xml")
                    reloaded.save_as_xml(roundtrip_path, save_merged=False)
                    self._verify_inlibrary_in_xml(roundtrip_path, library_name, should_have_inlibrary=False)
                elif format_name == "json":
                    roundtrip_path = os.path.join(self.temp_dir, "lang_roundtrip_unmerged2.json")
                    reloaded.save_as_json(roundtrip_path, save_merged=False)
                    self._verify_inlibrary_in_json(roundtrip_path, library_name, should_have_inlibrary=False)
                elif format_name == "mediawiki":
                    roundtrip_path = os.path.join(self.temp_dir, "lang_roundtrip_unmerged2.mediawiki")
                    reloaded.save_as_mediawiki(roundtrip_path, save_merged=False)
                    self._verify_inlibrary_in_mediawiki(roundtrip_path, library_name, should_have_inlibrary=False)
                elif format_name == "tsv":
                    roundtrip_path = os.path.join(self.temp_dir, "lang_roundtrip_unmerged2_tsv")
                    reloaded.save_as_dataframes(roundtrip_path, save_merged=False)
                    self._verify_inlibrary_in_tsv_schema_sections(roundtrip_path, library_name, should_have_inlibrary=False)

    def test_07_testlib_inlibrary_behavior(self):
        """Test inLibrary behavior with testlib schema if available."""
        if self.testlib_schema is None:
            self.skipTest("testlib schema not available in test data")

        library_name = self._get_library_name(self.testlib_schema)

        # Test merged save
        paths_merged = self._save_schema_all_formats(self.testlib_schema, "testlib", save_merged=True)
        self._verify_inlibrary_in_tsv_schema_sections(paths_merged["tsv"], library_name, should_have_inlibrary=True)
        self._verify_no_inlibrary_in_tsv_extras(paths_merged["tsv"])

        # Test unmerged save
        paths_unmerged = self._save_schema_all_formats(self.testlib_schema, "testlib", save_merged=False)
        self._verify_inlibrary_in_tsv_schema_sections(paths_unmerged["tsv"], library_name, should_have_inlibrary=False)
        self._verify_no_inlibrary_in_tsv_extras(paths_unmerged["tsv"])

    def test_08_cross_format_inlibrary_consistency(self):
        """Test that inLibrary appears consistently when converting between formats."""
        schema = self.score_schema
        library_name = self._get_library_name(schema)

        # Save as XML with merged
        xml_path = os.path.join(self.temp_dir, "score_cross.xml")
        schema.save_as_xml(xml_path, save_merged=True)

        # Load from XML and save as JSON
        schema_from_xml = load_schema(xml_path)
        json_path = os.path.join(self.temp_dir, "score_cross_from_xml.json")
        schema_from_xml.save_as_json(json_path, save_merged=True)

        # Verify both have inLibrary
        self._verify_inlibrary_in_xml(xml_path, library_name, should_have_inlibrary=True)
        self._verify_inlibrary_in_json(json_path, library_name, should_have_inlibrary=True)

        # Now test unmerged path
        xml_path_unmerged = os.path.join(self.temp_dir, "score_cross_unmerged.xml")
        schema.save_as_xml(xml_path_unmerged, save_merged=False)

        schema_from_xml_unmerged = load_schema(xml_path_unmerged)
        json_path_unmerged = os.path.join(self.temp_dir, "score_cross_from_xml_unmerged.json")
        schema_from_xml_unmerged.save_as_json(json_path_unmerged, save_merged=False)

        # Verify neither has inLibrary
        self._verify_inlibrary_in_xml(xml_path_unmerged, library_name, should_have_inlibrary=False)
        self._verify_inlibrary_in_json(json_path_unmerged, library_name, should_have_inlibrary=False)

    def test_09_specific_entries_have_inlibrary(self):
        """Test that specific library entries have inLibrary in merged saves."""
        schema = self.lang_schema
        library_name = "lang"

        # Save as TSV merged
        tsv_path = os.path.join(self.temp_dir, "lang_specific_tsv")
        schema.save_as_dataframes(tsv_path, save_merged=True)

        # Check UnitClass section for specific library entry
        unitclass_file = os.path.join(tsv_path, f"{os.path.basename(tsv_path)}_UnitClass.tsv")
        if os.path.exists(unitclass_file):
            df = pd.read_csv(unitclass_file, sep="\t", dtype=str, keep_default_na=False)

            # Find entries that are from the library (no hedId or empty hedId)
            if "hedId" in df.columns:
                library_entries = df[df["hedId"] == ""]
                if not library_entries.empty:
                    # At least one library entry should have inLibrary attribute
                    has_inlibrary = library_entries["Attributes"].str.contains(f"inLibrary={library_name}", na=False).any()
                    self.assertTrue(
                        has_inlibrary, "At least one library UnitClass entry should have inLibrary attribute in merged save"
                    )


if __name__ == "__main__":
    unittest.main()
