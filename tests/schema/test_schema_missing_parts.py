"""Schema files with missing parts or unknown header attributes.

- A TSV schema with a missing file of its layout, or a last row cut short, fails to load (issue #1513;
  specification Appendix A.5.1, Appendix B SCHEMA_LOAD_FAILED f). Standard schema 8.3.0 and its partnered libraries
  have no Sources, Prefixes, or AnnotationPropertyExternal files (Appendix B.3).
- A JSON schema with an absent section loads it as empty, records it in ``missing_sections``, and fails
  compliance with SCHEMA_SECTION_MISSING (issue #1466; specification 3.1.4.10, Appendix A.4.1).
- An unrecognized header attribute loads, is written back by every writer, and fails compliance with
  SCHEMA_HEADER_INVALID (issue #1510; specification 3.1.4.1, Appendix B SCHEMA_HEADER_INVALID b).
"""

import json
import os
import shutil
import tempfile
import unittest

from hed.errors.exceptions import HedExceptions, HedFileError
from hed.schema import from_string, load_schema, load_schema_version
from hed.schema.schema_io import df_constants, json_constants

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests")
SCHEMAS_830_TSV = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../../spec_tests/hed-schemas/standard_schema/hedtsv/HED8.3.0"
)


def _codes(schema):
    return [issue["code"] for issue in schema.check_compliance()]


class TestTsvMissingFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_tsv_missing_")
        cls.base = os.path.join(cls.temp_dir, "source", "HED8.5.0")
        load_schema_version("8.5.0").save_as_dataframes(cls.base)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)

    def _copy(self, label, source=None):
        source = source or self.base
        target = os.path.join(self.temp_dir, label, os.path.basename(source))
        shutil.copytree(source, target)
        return target

    @staticmethod
    def _file(directory, suffix):
        return os.path.join(directory, f"{os.path.basename(directory)}_{suffix}.tsv")

    def test_complete_layout_loads(self):
        schema = load_schema(self._copy("complete"))
        self.assertEqual(len(schema.tags.all_names), len(load_schema_version("8.5.0").tags.all_names))

    def test_each_missing_file_raises(self):
        # Before the fix: Tag or ValueClass removed loaded with an empty section; UnitClass removed raised
        # AttributeError.
        for suffix in sorted(df_constants.DF_SUFFIXES):
            with self.subTest(suffix=suffix):
                directory = self._copy(f"no_{suffix}")
                os.remove(self._file(directory, suffix))
                with self.assertRaises(HedFileError) as context:
                    load_schema(directory)
                self.assertEqual(context.exception.code, HedExceptions.SCHEMA_LOAD_FAILED)
                self.assertIn(f"_{suffix}.tsv", context.exception.message)

    def test_only_structure_lists_every_missing_file(self):
        directory = self._copy("only_structure")
        for suffix in df_constants.DF_SUFFIXES - {df_constants.STRUCT_KEY}:
            os.remove(self._file(directory, suffix))
        with self.assertRaises(HedFileError) as context:
            load_schema(directory)
        self.assertIn(f"missing {len(df_constants.DF_SUFFIXES) - 1} file(s)", context.exception.message)

    def test_last_row_cut_inside_a_column_raises(self):
        directory = self._copy("cut_row")
        path = self._file(directory, df_constants.TAG_KEY)
        with open(path, encoding="utf-8") as fp:
            data = fp.read()
        row_start = data.rfind("\n", 0, len(data) // 2) + 1
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(data[: data.index("\t", row_start) + 3])
        with self.assertRaises(HedFileError) as context:
            load_schema(directory)
        self.assertEqual(context.exception.code, HedExceptions.SCHEMA_LOAD_FAILED)
        self.assertIn("cut short", context.exception.message)

    def test_cut_at_row_boundary_cannot_be_detected(self):
        directory = self._copy("cut_boundary")
        path = self._file(directory, df_constants.TAG_KEY)
        with open(path, encoding="utf-8") as fp:
            data = fp.read()
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(data[: data.rfind("\n", 0, len(data) // 2) + 1])
        schema = load_schema(directory)
        self.assertLess(len(schema.tags.all_names), len(load_schema_version("8.5.0").tags.all_names))

    @unittest.skipUnless(os.path.isdir(SCHEMAS_830_TSV), "hed-schemas submodule not checked out")
    def test_830_without_extras_files_loads(self):
        directory = self._copy("v830", SCHEMAS_830_TSV)
        for suffix in df_constants.DF_EXTRAS:
            self.assertFalse(os.path.exists(self._file(directory, suffix)))
        self.assertEqual(load_schema(directory).version_number, "8.3.0")
        os.remove(self._file(directory, df_constants.TAG_KEY))
        with self.assertRaises(HedFileError) as context:
            load_schema(directory)
        self.assertEqual(context.exception.code, HedExceptions.SCHEMA_LOAD_FAILED)


class TestJsonMissingSections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = json.loads(load_schema_version("8.4.0").get_as_json_string())

    def test_writer_writes_every_section(self):
        self.assertEqual(set(json_constants.REQUIRED_SECTION_KEYS) - set(self.full), set())
        empty = from_string('{"version": "8.4.0"}', schema_format=".json")
        written = json.loads(empty.get_as_json_string())
        self.assertEqual(set(json_constants.REQUIRED_SECTION_KEYS) - set(written), set())
        self.assertEqual(written[json_constants.PROLOGUE_KEY], "")
        self.assertEqual(written[json_constants.EPILOGUE_KEY], "")

    def test_complete_file_has_no_missing_sections(self):
        schema = from_string(json.dumps(self.full), schema_format=".json")
        self.assertEqual(schema.missing_sections, [])
        self.assertNotIn("SCHEMA_SECTION_MISSING", _codes(schema))

    def test_each_absent_key(self):
        for key, section in json_constants.REQUIRED_SECTION_KEYS.items():
            with self.subTest(key=key):
                data = dict(self.full)
                del data[key]
                schema = from_string(json.dumps(data), schema_format=".json")
                self.assertEqual(schema.missing_sections, [section])
                issues = [i for i in schema.check_compliance() if i["code"] == "SCHEMA_SECTION_MISSING"]
                self.assertEqual(len(issues), 1)
                self.assertIn(f"'{section}'", issues[0]["message"])

    def test_version_only(self):
        # Issue #1466: this loaded with no sign of the absent sections.
        schema = from_string('{"version": "8.4.0"}', schema_format=".json")
        self.assertEqual(schema.missing_sections, list(json_constants.REQUIRED_SECTION_KEYS.values()))
        self.assertEqual(_codes(schema).count("SCHEMA_SECTION_MISSING"), len(json_constants.REQUIRED_SECTION_KEYS))

    def test_missing_sections_not_compared(self):
        data = dict(self.full)
        del data[json_constants.EPILOGUE_KEY]
        data[json_constants.PROLOGUE_KEY] = self.full[json_constants.PROLOGUE_KEY]
        without = from_string(json.dumps(data), schema_format=".json")
        with_epilogue = from_string(json.dumps({**data, json_constants.EPILOGUE_KEY: ""}), schema_format=".json")
        self.assertEqual(without.missing_sections, ["epilogue"])
        self.assertEqual(without, with_epilogue)

    def test_other_formats_record_nothing(self):
        schema = load_schema_version("8.4.0")
        self.assertEqual(schema.missing_sections, [])
        self.assertEqual(from_string(schema.get_as_mediawiki_string(), schema_format=".mediawiki").missing_sections, [])


class TestUnknownHeaderAttribute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="hed_header_unknown_")
        wiki = load_schema_version("8.5.0").get_as_mediawiki_string()
        cls.schema = from_string(
            wiki.replace('HED version="8.5.0"', 'HED version="8.5.0" unknownAttribute="other"', 1),
            schema_format=".mediawiki",
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)

    def test_loads_and_fails_compliance(self):
        # Issue #1510: loading raised SCHEMA_HEADER_INVALID.
        self.assertEqual(self.schema.header_attributes["unknownAttribute"], "other")
        issues = [i for i in self.schema.check_compliance() if i["code"] == "SCHEMA_HEADER_INVALID"]
        self.assertEqual(len(issues), 1)
        self.assertIn('unknownAttribute="other"', issues[0]["message"])

    def test_fixture_file(self):
        schema = load_schema(os.path.join(DATA_DIR, "wiki_tests", "HED_header_unknown_attribute.mediawiki"))
        self.assertIn("SCHEMA_HEADER_INVALID", _codes(schema))

    def test_known_attributes_pass(self):
        self.assertNotIn("SCHEMA_HEADER_INVALID", _codes(load_schema_version("8.5.0")))
        self.assertNotIn("SCHEMA_HEADER_INVALID", _codes(load_schema_version("score_2.1.0")))

    def test_written_back_by_every_writer(self):
        written = {
            ".mediawiki": self.schema.get_as_mediawiki_string(),
            ".xml": self.schema.get_as_xml_string(),
            ".json": self.schema.get_as_json_string(),
        }
        for schema_format, text in written.items():
            with self.subTest(schema_format=schema_format):
                reloaded = from_string(text, schema_format=schema_format)
                self.assertEqual(reloaded.header_attributes.get("unknownAttribute"), "other")
        tsv_dir = os.path.join(self.temp_dir, "HED8.5.0")
        self.schema.save_as_dataframes(tsv_dir)
        self.assertEqual(load_schema(tsv_dir).header_attributes.get("unknownAttribute"), "other")

    def test_malformed_header_still_raises(self):
        wiki = self.schema.get_as_mediawiki_string()
        header = wiki.split("\n", 1)[0]
        for bad_header, code in (
            ('HED version="8.5.0" unknownAttribute=other', HedExceptions.SCHEMA_HEADER_INVALID),
            ('HED version="8.5.0" library="Bad1"', HedExceptions.SCHEMA_LIBRARY_INVALID),
            ('HED unknownAttribute="other"', HedExceptions.SCHEMA_VERSION_INVALID),
        ):
            with self.subTest(header=bad_header):
                with self.assertRaises(HedFileError) as context:
                    from_string(wiki.replace(header, bad_header, 1), schema_format=".mediawiki")
                self.assertEqual(context.exception.code, code)


if __name__ == "__main__":
    unittest.main()
