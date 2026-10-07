import contextlib
import copy
import io
import json
import os
import shutil
import unittest

from hed import load_schema, load_schema_version
from hed.schema import HedKey, HedSectionKey
from hed.scripts.hed_convert_schema import convert_and_update, format_removed_row
from hed.scripts.schema_script_util import add_extension


class TestConvertAndUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary directory for schema files
        cls.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas_update", "prerelease")
        if not os.path.exists(cls.base_path):
            os.makedirs(cls.base_path)

    def test_schema_conversion_and_update(self):
        # Load a known schema, modify it if necessary, and save it
        schema = load_schema_version("8.3.0")
        original_name = os.path.join(self.base_path, "test_schema.mediawiki")
        schema.save_as_mediawiki(original_name)

        # Assume filenames updated includes just the original schema file for simplicity
        filenames = [original_name]
        with contextlib.redirect_stdout(io.StringIO()):
            result = convert_and_update(filenames, set_ids=False)

        # Verify no error from convert_and_update and the correct schema version was saved
        self.assertEqual(result, 0)

        tsv_filename = add_extension(os.path.join(self.base_path, "test_schema"), ".tsv")
        schema_reload1 = load_schema(tsv_filename)
        schema_reload2 = load_schema(os.path.join(self.base_path, "test_schema.xml"))

        self.assertEqual(schema, schema_reload1)
        self.assertEqual(schema, schema_reload2)

        # Now verify after doing this again with a new schema, they're still the same.
        schema = load_schema_version("8.3.0")
        schema.save_as_dataframes(tsv_filename)

        filenames = [os.path.join(tsv_filename, "test_schema_Tag.tsv")]
        with contextlib.redirect_stdout(io.StringIO()):
            result = convert_and_update(filenames, set_ids=False)

        # Verify no error from convert_and_update and the correct schema version was saved
        self.assertEqual(result, 0)

        schema_reload1 = load_schema(os.path.join(self.base_path, "test_schema.mediawiki"))
        schema_reload2 = load_schema(os.path.join(self.base_path, "test_schema.xml"))

        self.assertEqual(schema, schema_reload1)
        self.assertEqual(schema, schema_reload2)

    def test_schema_adding_tag(self):
        schema = load_schema_version("8.4.0")
        basename = os.path.join(self.base_path, "test_schema_edited")
        schema.save_as_mediawiki(add_extension(basename, ".mediawiki"))
        schema.save_as_xml(add_extension(basename, ".xml"))
        schema.save_as_dataframes(add_extension(basename, ".tsv"))
        schema.save_as_json(add_extension(basename, ".json"))

        schema_edited = copy.deepcopy(schema)
        test_tag_name = "NewTagWithoutID"
        new_entry = schema_edited._create_tag_entry(test_tag_name, HedSectionKey.Tags)
        schema_edited._add_tag_to_dict(test_tag_name, new_entry, HedSectionKey.Tags)

        schema_edited.save_as_mediawiki(add_extension(basename, ".mediawiki"))

        # Assume filenames updated includes just the original schema file for simplicity
        filenames = [add_extension(basename, ".mediawiki")]
        with contextlib.redirect_stdout(io.StringIO()):
            result = convert_and_update(filenames, set_ids=False)
        self.assertEqual(result, 0)

        schema_reloaded = load_schema(add_extension(basename, ".xml"))
        x = schema_reloaded == schema_edited
        self.assertTrue(x)
        self.assertEqual(schema_reloaded, schema_edited)

        with contextlib.redirect_stdout(io.StringIO()):
            result = convert_and_update(filenames, set_ids=True)
        self.assertEqual(result, 0)

        schema_reloaded = load_schema(add_extension(basename, ".xml"))

        reloaded_entry = schema_reloaded.tags[test_tag_name]
        self.assertTrue(reloaded_entry.has_attribute(HedKey.HedID))

    def test_schema_removing_retired_unit(self):
        # Mimic the 8.5.0 edit: uV leaves the mediawiki while the TSV still carries its retired id
        # HED_0011644. The converter drops that row, says so, and the formats agree afterwards.
        schema = load_schema_version("8.4.0")
        basename = os.path.join(self.base_path, "test_schema_retired")
        schema.save_as_mediawiki(add_extension(basename, ".mediawiki"))
        schema.save_as_dataframes(add_extension(basename, ".tsv"))

        with open(add_extension(basename, ".mediawiki"), encoding="utf-8") as fp:
            lines = fp.readlines()
        uv_lines = [line for line in lines if line.startswith("** uV ")]
        self.assertEqual(len(uv_lines), 1)
        with open(add_extension(basename, ".mediawiki"), "w", encoding="utf-8") as fp:
            fp.writelines(line for line in lines if line not in uv_lines)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = convert_and_update([add_extension(basename, ".mediawiki")], set_ids=False)
        self.assertEqual(result, 0)
        self.assertIn(
            "Removed retired row 'uV' (HED_0011644) from Unit: removed in 8.5.0; replacement V", output.getvalue()
        )

        schema_reloaded = load_schema(add_extension(basename, ".xml"))
        self.assertNotIn("uV", schema_reloaded.units)
        self.assertIn("V", schema_reloaded.units)
        tsv_reloaded = load_schema(add_extension(basename, ".tsv"))
        self.assertNotIn("uV", tsv_reloaded.units)
        self.assertEqual(schema_reloaded, tsv_reloaded)

    def test_library_prerelease_forms(self):
        # hed-schemas keeps a library's mediawiki, TSV and JSON unmerged and only the XML merged.
        basename = os.path.join(self.base_path, "HED_score_2.1.0")
        load_schema_version("score_2.1.0").save_as_mediawiki(basename + ".mediawiki")  # unmerged by default
        with contextlib.redirect_stdout(io.StringIO()):
            result = convert_and_update([basename + ".mediawiki"], set_ids=False)
        self.assertEqual(result, 0)

        with open(basename + ".json", encoding="utf-8") as fp:
            as_json = json.load(fp)
        self.assertEqual(as_json.get("unmerged"), "True", "the prerelease JSON is unmerged")
        self.assertNotIn("Event", as_json.get("tags", {}), "an unmerged library JSON carries no standard tags")
        with open(basename + ".xml", encoding="utf-8") as fp:
            xml_text = fp.read()
        self.assertIn("<name>Event</name>", xml_text, "the prerelease XML is merged")
        self.assertNotIn('unmerged="True"', xml_text.split("\n", 2)[1])
        with open(basename + ".mediawiki", encoding="utf-8") as fp:
            self.assertIn('unmerged="True"', fp.readline())
        self.assertEqual(load_schema(basename + ".json"), load_schema(basename + ".xml"))

    def test_format_removed_row(self):
        full = {"section": "Unit", "label": "uV", "hedId": "HED_0011644", "removed_in": "8.5.0", "replacement": "V"}
        self.assertEqual(
            format_removed_row(full),
            "Removed retired row 'uV' (HED_0011644) from Unit: removed in 8.5.0; replacement V",
        )
        bare = {"section": "Tag", "label": "Old-tag", "hedId": "HED_0012345", "removed_in": "", "replacement": ""}
        self.assertEqual(format_removed_row(bare), "Removed retired row 'Old-tag' (HED_0012345) from Tag")

    @classmethod
    def tearDownClass(cls):
        # Clean up the directory created for testing
        shutil.rmtree(cls.base_path)
