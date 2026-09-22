"""
Comprehensive tests for schema extras sections across all formats.

Tests that extras (Sources, Prefixes, ExternalAnnotations) are correctly:
1. Read from all formats (XML, JSON, MediaWiki, TSV) with in_library tracking
2. Have consistent internal representation across formats
3. Round-trip correctly (read → write → read)
4. Properly separate library-specific entries from base-schema entries
"""

import json
import os
import shutil
import tempfile
import unittest

import pandas as pd

from hed.schema import from_string, load_schema, load_schema_version
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

    def _partner_rows_present(self, df, library_rows, label):
        """Check that every row beyond the library's own is a partner row with an empty in_library stamp.

        The number of partner rows is not pinned. The fixture partners with the 8.5.0 prerelease, which a
        save or a reload of an unmerged file fetches as it is today, and hed-schemas edits that prerelease
        (2026-09-17 added a Sources row and two ExternalAnnotations rows, which broke the pinned counts).
        Until 8.5.0 is released, these tests check the shape of the partner's rows, not their number.
        """
        partner_rows = (df[df_constants.in_library] == "").sum()
        self.assertGreater(partner_rows, 0, f"{label}: the partner's rows are present")
        self.assertEqual(partner_rows, len(df) - library_rows, f"{label}: partner rows carry an empty stamp")

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
        """After saving merged -> unmerged and reloading, the library rows are the same and the partner's are back.

        The unmerged file holds only the library's rows; loading it combines them with the partner's
        again (schema_merge._merge_extras), so the reloaded schema has the same rows as the original,
        with the library's still stamped and the partner's carrying an empty stamp.
        """
        for key, label in [
            (df_constants.SOURCES_KEY, "Sources"),
            (df_constants.PREFIXES_KEY, "Prefixes"),
            (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
        ]:
            lib_only = self._library_extras_only(original_schema.get_extras(key), self.library_name)
            reloaded_lib_only = self._library_extras_only(reloaded_schema.get_extras(key), self.library_name)
            pd.testing.assert_frame_equal(
                lib_only, reloaded_lib_only, check_dtype=False, obj=f"{label}: library_only vs reloaded library_only"
            )
            # The partner's rows are not compared row for row: the fixture holds the partner's rows as they
            # were when it was made, while a save or reload takes them from the 8.5.0 prerelease as it is
            # today, and that prerelease changes (see _partner_rows_present).
            self._partner_rows_present(reloaded_schema.get_extras(key), len(lib_only), label)

    def test_03_xml_roundtrip_unmerged(self):
        """Load merged XML -> save unmerged -> reload: library rows survive and the partner's come back."""
        schema = load_schema(self.xml_path)
        temp_xml = os.path.join(self.temp_dir, "roundtrip_unmerged.xml")
        schema.save_as_xml(temp_xml, save_merged=False)
        schema_reloaded = load_schema(temp_xml)
        self._check_unmerged_roundtrip(schema, schema_reloaded)

    def test_04_json_roundtrip_unmerged(self):
        """Load merged JSON -> save unmerged -> reload: library rows survive and the partner's come back."""
        schema = load_schema(self.json_path)
        temp_json = os.path.join(self.temp_dir, "roundtrip_unmerged.json")
        schema.save_as_json(temp_json, save_merged=False)
        schema_reloaded = load_schema(temp_json)
        self._check_unmerged_roundtrip(schema, schema_reloaded)

    def test_05_mediawiki_roundtrip_unmerged(self):
        """Load merged MediaWiki -> save unmerged -> reload: library rows survive and the partner's come back."""
        schema = load_schema(self.wiki_path)
        temp_wiki = os.path.join(self.temp_dir, "roundtrip_unmerged.mediawiki")
        schema.save_as_mediawiki(temp_wiki, save_merged=False)
        schema_reloaded = load_schema(temp_wiki)
        self._check_unmerged_roundtrip(schema, schema_reloaded)

    def test_06_tsv_roundtrip_unmerged(self):
        """Load merged TSV -> save unmerged -> reload: library rows survive and the partner's come back."""
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
                    # A merged save writes the partner's rows as they are today, so only the library's own
                    # rows are compared with the fixture; see _partner_rows_present.
                    df1 = self._library_extras_only(schema.get_extras(key), self.library_name)
                    df2 = self._library_extras_only(schema2.get_extras(key), self.library_name)
                    pd.testing.assert_frame_equal(
                        df1, df2, check_dtype=False, obj=f"{label}: {fmt_name} merged roundtrip"
                    )
                    self._partner_rows_present(schema2.get_extras(key), len(df1), f"{label}: {fmt_name}")

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
                    # Against the fixture only the library's rows can match (see _partner_rows_present); the
                    # three saved formats were written from the same schema, so they match each other in full.
                    df1 = self._library_extras_only(schema.get_extras(key), self.library_name)
                    df2 = self._library_extras_only(schema_fmt.get_extras(key), self.library_name)
                    pd.testing.assert_frame_equal(df1, df2, check_dtype=False, obj=f"{label}: XML vs {fmt_name}")
                    all_json = self._extras_without_in_library(schema_json.get_extras(key))
                    all_fmt = self._extras_without_in_library(schema_fmt.get_extras(key))
                    pd.testing.assert_frame_equal(
                        all_json, all_fmt, check_dtype=False, obj=f"{label}: JSON vs {fmt_name}, all rows"
                    )

    def test_09_base_extras_preserve_empty_in_library_after_merged_save(self):
        """After merged save, base-schema extras retain empty-string in_library (not rewritten to lib name).

        This test validates the fix for schema2base.py line 293-305 where empty-string in_library
        (the explicit marker for base-schema rows) must NOT be rewritten to the library name.
        If this bug exists, base extras get serialized with inLibrary attribute and break
        future unmerge operations.

        Note: Loaders normalize in_library to strings with no NaN (see tests 10-12).
        Base rows are marked with empty string, not NaN.
        """

        schema = load_schema(self.xml_path)
        temp_xml = os.path.join(self.temp_dir, "merged_preserve_base.xml")

        # Save as merged (this is where the bug manifests)
        schema.save_as_xml(temp_xml, save_merged=True)
        schema_reloaded = load_schema(temp_xml)

        for key, label in [
            (df_constants.SOURCES_KEY, "Sources"),
            (df_constants.PREFIXES_KEY, "Prefixes"),
            (df_constants.EXTERNAL_ANNOTATION_KEY, "ExternalAnnotations"),
        ]:
            with self.subTest(section=label):
                df = schema_reloaded.get_extras(key)
                self.assertIsNotNone(df, f"{label} should exist after merged roundtrip")
                self.assertIn(df_constants.in_library, df.columns, f"{label} should have in_library column")

                # After merged save, merged schema contains ALL rows: library + base. The base rows are the
                # partner's as it is today, so their number is not pinned (see _partner_rows_present); what
                # matters here is that every one of them kept the empty stamp.
                lib_rows = (df[df_constants.in_library] == self.library_name).sum()
                self.assertEqual(lib_rows, 1, f"{label}: should have 1 library row (in_library={self.library_name})")
                self._partner_rows_present(df, 1, label)
                # Base rows have empty string as the marker (never NaN due to normalization)
                expected_base_count = (df[df_constants.in_library] == "").sum()

                # Verify unmerge behavior: the unmerged file holds only the library's row, and loading it
                # brings the partner's rows back with an empty stamp.
                temp_xml_unmerged = os.path.join(self.temp_dir, f"check_unmerge_{label}.xml")
                schema_reloaded.save_as_xml(temp_xml_unmerged, save_merged=False)
                with open(temp_xml_unmerged, encoding="utf-8") as fp:
                    xml_text = fp.read()
                element = {
                    "Sources": "schemaSource",
                    "Prefixes": "schemaPrefix",
                    "ExternalAnnotations": "externalAnnotation",
                }
                self.assertEqual(xml_text.count(f"<{element[label]}>"), 1, f"{label}: unmerged file has one row")
                schema_unmerged = load_schema(temp_xml_unmerged)

                df_unmerged = schema_unmerged.get_extras(key)
                self.assertEqual((df_unmerged[df_constants.in_library] == self.library_name).sum(), 1, label)
                self.assertEqual((df_unmerged[df_constants.in_library] == "").sum(), expected_base_count, label)
                self.assertEqual(len(df_unmerged), len(df), f"{label}: reloaded unmerged has library + partner rows")

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


class TestEmptyExtrasSections(unittest.TestCase):
    """The Sources, Prefixes, and External annotations sections are always written and may be omitted on read.

    Fixtures: tests/data/schema_tests/empty_extras/ (mouse 1.0.0, partnered with 8.5.0, no extras of its own).
    """

    EXTRAS_KEYS = (df_constants.SOURCES_KEY, df_constants.PREFIXES_KEY, df_constants.EXTERNAL_ANNOTATION_KEY)
    WIKI_HEADERS = ("'''Sources'''", "'''Prefixes'''", "'''External annotations'''")
    XML_ELEMENTS = ("<schemaSources/>", "<schemaPrefixes/>", "<externalAnnotations/>")
    JSON_KEYS = ("sources", "prefixes", "external_annotations")
    TSV_SUFFIXES = ("_Sources.tsv", "_Prefixes.tsv", "_AnnotationPropertyExternal.tsv")

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_empty_extras_")
        base = os.path.normpath(os.path.join(os.path.dirname(__file__), "../data/schema_tests/empty_extras"))
        cls.no_sections_dir = os.path.join(base, "no_sections")
        cls.empty_sections_dir = os.path.join(base, "empty_sections")
        cls.library_name = "mouse"

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    @staticmethod
    def _fixture_paths(fixture_dir):
        """Return {format_name: path} for the four formats of the mouse fixture in fixture_dir."""
        stem = os.path.join(fixture_dir, "HED_mouse_1.0.0")
        return {"XML": stem + ".xml", "JSON": stem + ".json", "MEDIAWIKI": stem + ".mediawiki", "TSV": stem}

    def _library_rows(self, schema, key):
        """Return the rows of one extras section that belong to the library itself (never the partner's)."""
        df = schema.get_extras(key)
        if df is None or df.empty:
            return 0
        if df_constants.in_library in df.columns:
            return int((df[df_constants.in_library] == self.library_name).sum())
        # Readers stamp in_library on every library-owned row (unmerged load) or keep the file's inLibrary
        # attribute (merged load); rows without the column are the partner's.
        return 0

    @staticmethod
    def _read_text(path):
        with open(path, encoding="utf-8") as fp:
            return fp.read().replace("\r\n", "\n")

    def test_readers_accept_files_without_the_sections(self):
        """A file without the three sections loads and the library adds no extras rows (R1)."""
        for format_name, path in self._fixture_paths(self.no_sections_dir).items():
            with self.subTest(format=format_name):
                schema = load_schema(path)
                self.assertEqual(schema.library, self.library_name)
                for key in self.EXTRAS_KEYS:
                    self.assertEqual(self._library_rows(schema, key), 0, f"{format_name} {key}")
                extras_issues = [
                    issue for issue in schema.check_compliance() if issue["code"].startswith("SCHEMA_MISSING_EXTRA")
                ]
                self.assertEqual(extras_issues, [], f"{format_name}: empty extras must not be a compliance issue")

    def test_files_with_and_without_the_sections_load_identically(self):
        """The regenerated file (sections present and empty) loads to the same schema as the old one (R1)."""
        without = self._fixture_paths(self.no_sections_dir)
        with_empty = self._fixture_paths(self.empty_sections_dir)
        for format_name in without:
            with self.subTest(format=format_name):
                schema_without = load_schema(without[format_name])
                schema_with = load_schema(with_empty[format_name])
                self.assertEqual(schema_without, schema_with, f"{format_name}: schemas differ")
                for key in self.EXTRAS_KEYS:
                    df_without = schema_without.get_extras(key)
                    df_with = schema_with.get_extras(key)
                    if df_without is None or df_without.empty:
                        # TSV: a folder without the file has no entry; a header-only file gives an empty frame.
                        self.assertTrue(df_with is None or df_with.empty, f"{format_name} {key}")
                        continue
                    pd.testing.assert_frame_equal(df_without, df_with, check_dtype=False, obj=f"{format_name} {key}")

    def test_unmerged_save_writes_the_empty_sections(self):
        """Every writer emits the three sections, empty and in order, for a library with no extras (W1-W4)."""
        schema = load_schema(self._fixture_paths(self.no_sections_dir)["MEDIAWIKI"])
        out = os.path.join(self.temp_dir, "unmerged")
        os.makedirs(out, exist_ok=True)
        wiki_path = os.path.join(out, "HED_mouse_1.0.0.mediawiki")
        xml_path = os.path.join(out, "HED_mouse_1.0.0.xml")
        json_path = os.path.join(out, "HED_mouse_1.0.0.json")
        tsv_dir = os.path.join(out, "HED_mouse_1.0.0")
        schema.save_as_mediawiki(wiki_path, save_merged=False)
        schema.save_as_xml(xml_path, save_merged=False)
        schema.save_as_json(json_path, save_merged=False)
        schema.save_as_dataframes(tsv_dir, save_merged=False)

        wiki_text = self._read_text(wiki_path)
        positions = [wiki_text.index(header) for header in self.WIKI_HEADERS]
        self.assertEqual(positions, sorted(positions), "MediaWiki sections out of order")
        self.assertGreater(positions[0], wiki_text.index("'''Epilogue'''"))
        self.assertLess(positions[-1], wiki_text.index("!# end hed"))
        for header in self.WIKI_HEADERS:
            self.assertEqual(wiki_text.count(header), 1, header)
        self.assertNotIn("\n*", wiki_text[positions[0] :], "empty MediaWiki sections must have no rows")

        xml_text = self._read_text(xml_path)
        positions = [xml_text.index(element) for element in self.XML_ELEMENTS]
        self.assertEqual(positions, sorted(positions), "XML sections out of order")
        self.assertGreater(positions[0], xml_text.index("<propertyDefinitions/>"))

        with open(json_path, encoding="utf-8") as fp:
            json_data = json.load(fp)
        for key in self.JSON_KEYS:
            self.assertEqual(json_data.get(key), [], key)
        json_keys = list(json_data.keys())
        self.assertEqual(json_keys[-3:], list(self.JSON_KEYS), "JSON sections must come last, in order")

        for suffix in self.TSV_SUFFIXES:
            tsv_path = os.path.join(tsv_dir, "HED_mouse_1.0.0" + suffix)
            self.assertTrue(os.path.exists(tsv_path), tsv_path)
            lines = self._read_text(tsv_path).strip("\n").split("\n")
            self.assertEqual(len(lines), 1, f"{suffix} must be header-only")

        # The committed empty_sections fixtures are exactly this output; regenerate them if this fails.
        for format_name, fixture in self._fixture_paths(self.empty_sections_dir).items():
            if format_name == "TSV":
                continue
            produced = {"XML": xml_path, "JSON": json_path, "MEDIAWIKI": wiki_path}[format_name]
            self.assertEqual(self._read_text(produced), self._read_text(fixture), f"{format_name} fixture drifted")

    def test_merged_save_keeps_partner_rows_and_marks_none_as_library(self):
        """A merged save still carries the partner's extras rows, none of them attributed to the library (T1)."""
        schema = load_schema(self._fixture_paths(self.no_sections_dir)["MEDIAWIKI"])
        partner = load_schema_version("8.5.0")
        for format_name, save in (
            ("XML", lambda p: schema.save_as_xml(p, save_merged=True)),
            ("JSON", lambda p: schema.save_as_json(p, save_merged=True)),
            ("MEDIAWIKI", lambda p: schema.save_as_mediawiki(p, save_merged=True)),
        ):
            with self.subTest(format=format_name):
                path = os.path.join(
                    self.temp_dir,
                    "merged_" + format_name + {"XML": ".xml", "JSON": ".json"}.get(format_name, ".mediawiki"),
                )
                save(path)
                reloaded = load_schema(path)
                for key in self.EXTRAS_KEYS:
                    partner_df = partner.get_extras(key)
                    expected = 0 if partner_df is None else len(partner_df)
                    reloaded_df = reloaded.get_extras(key)
                    self.assertEqual(0 if reloaded_df is None else len(reloaded_df), expected, f"{format_name} {key}")
                    self.assertEqual(self._library_rows(reloaded, key), 0, f"{format_name} {key}")


class TestPartnerExtrasAvailableToLibrary(unittest.TestCase):
    """An unmerged partnered library may use everything its partner defines, the extras rows included.

    Loading an unmerged file combines the library's Sources, Prefixes, and External annotations rows
    with the partner's (schema_merge._merge_extras), so annotations written with the standard's
    prefixes (dc:, rdfs:, ...) validate without the library restating those sections.
    """

    LIBRARY = """HED library="testpartner" version="1.0.0" withStandard="8.5.0" unmerged="True"

'''Prologue'''

!# start schema

'''Own-thing''' <nowiki>{rooted=Item, annotation=dc:source Wikipedia, annotation=rdfs:comment A comment.} [A tag.]</nowiki>
* Own-child <nowiki>{annotation=own:C1} [A child tag.]</nowiki>

!# end schema

'''Unit classes'''

'''Unit modifiers'''

'''Value classes'''

'''Schema attributes'''

'''Properties'''

'''Epilogue'''

'''Sources'''

'''Prefixes'''
* <nowiki>prefix=own:,namespace=https://example.org/own/#,description=The library's own prefix.</nowiki>

'''External annotations'''
* <nowiki>prefix=own:,id=C1,iri=https://example.org/own/#C1,description=A term of the library's own.</nowiki>

!# end hed
"""

    @classmethod
    def setUpClass(cls):
        cls.schema = from_string(cls.LIBRARY, ".mediawiki")
        cls.partner = load_schema_version("8.5.0")

    def test_partner_rows_are_present_and_unstamped(self):
        """Every partner row is loaded with an empty in_library stamp; the library's rows keep theirs."""
        for key, own_rows in (
            (df_constants.SOURCES_KEY, 0),
            (df_constants.PREFIXES_KEY, 1),
            (df_constants.EXTERNAL_ANNOTATION_KEY, 1),
        ):
            with self.subTest(section=key):
                df = self.schema.get_extras(key)
                partner_df = self.partner.get_extras(key)
                self.assertEqual(len(df), len(partner_df) + own_rows, key)
                self.assertEqual((df[df_constants.in_library] == "testpartner").sum(), own_rows, key)
                self.assertEqual((df[df_constants.in_library] == "").sum(), len(partner_df), key)
        prefixes = set(self.schema.get_extras(df_constants.PREFIXES_KEY)[df_constants.prefix])
        self.assertIn("dc:", prefixes)
        self.assertIn("own:", prefixes)

    def test_annotations_with_partner_prefixes_are_compliant(self):
        """dc:source and rdfs:comment resolve through the partner's rows; own: through the library's."""
        issues = self.schema.check_compliance()
        annotation_issues = [issue for issue in issues if issue["code"].startswith("SCHEMA_ANNOTATION")]
        self.assertEqual(annotation_issues, [])
        self.assertEqual({issue["code"] for issue in issues}, {"SCHEMA_PRERELEASE_VERSION_USED"})

    def test_every_group_member_contributes_its_rows(self):
        """A group of two unmerged libraries holds the partner's rows plus each library's own, stamped."""
        from hed.schema.hed_schema_io import _load_schema_version

        second = (
            self.LIBRARY.replace('library="testpartner"', 'library="testsecond"')
            .replace("Own-thing", "Other-thing")
            .replace("Own-child", "Other-child")
            .replace("own:", "other:")
            .replace("https://example.org/own/", "https://example.org/other/")
        )
        folder = tempfile.mkdtemp(prefix="hed_group_extras_")
        try:
            self.schema.save_as_xml(os.path.join(folder, "HED_testpartner_1.0.0.xml"), save_merged=False)
            from_string(second, ".mediawiki").save_as_xml(
                os.path.join(folder, "HED_testsecond_1.0.0.xml"), save_merged=False
            )
            _load_schema_version.cache_clear()
            group = load_schema_version(["testpartner_1.0.0", "testsecond_1.0.0"], xml_folder=folder)
        finally:
            _load_schema_version.cache_clear()
            shutil.rmtree(folder, ignore_errors=True)
        for key, own_rows in (
            (df_constants.SOURCES_KEY, 0),
            (df_constants.PREFIXES_KEY, 1),
            (df_constants.EXTERNAL_ANNOTATION_KEY, 1),
        ):
            with self.subTest(section=key):
                df = group.get_extras(key)
                partner_df = self.partner.get_extras(key)
                self.assertEqual(len(df), len(partner_df) + 2 * own_rows, key)
                stamps = df[df_constants.in_library]
                self.assertEqual((stamps == "testpartner").sum(), own_rows, key)
                self.assertEqual((stamps == "testsecond").sum(), own_rows, key)
                self.assertEqual((stamps == "").sum(), len(partner_df), key)
        prefixes = set(group.get_extras(df_constants.PREFIXES_KEY)[df_constants.prefix])
        self.assertTrue({"dc:", "own:", "other:"} <= prefixes, prefixes)
        annotation_issues = [i for i in group.check_compliance() if i["code"].startswith("SCHEMA_ANNOTATION")]
        self.assertEqual(annotation_issues, [])

    def test_unmerged_save_writes_only_the_library_rows(self):
        """The partner's rows never leak into an unmerged save."""
        temp_dir = tempfile.mkdtemp(prefix="hed_partner_extras_")
        try:
            path = os.path.join(temp_dir, "HED_testpartner_1.0.0.mediawiki")
            self.schema.save_as_mediawiki(path, save_merged=False)
            with open(path, encoding="utf-8") as fp:
                text = fp.read()
            self.assertEqual(text.count("prefix="), 2, "one Prefixes row and one External annotations row")
            self.assertNotIn("prefix=dc:", text)
            reloaded = load_schema(path)
            self.assertEqual(
                len(reloaded.get_extras(df_constants.PREFIXES_KEY)),
                len(self.partner.get_extras(df_constants.PREFIXES_KEY)) + 1,
            )
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
