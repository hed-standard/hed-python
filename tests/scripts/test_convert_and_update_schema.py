import unittest
import os
import shutil
import copy
from hed import load_schema, load_schema_version
from hed.schema import HedSectionKey, HedKey
from hed.scripts.script_util import add_extension
from hed.scripts.convert_and_update_schema import convert_and_update


class TestConvertAndUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary directory for schema files
        cls.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schemas_update', 'prerelease')
        if not os.path.exists(cls.base_path):
            os.makedirs(cls.base_path)

    def test_schema_conversion_and_update(self):
        # Load a known schema, modify it if necessary, and save it
        schema = load_schema_version("8.3.0")
        original_name = os.path.join(self.base_path, "test_schema.mediawiki")
        schema.save_as_mediawiki(original_name)

        # Assume filenames updated includes just the original schema file for simplicity
        filenames = [original_name]
        result = convert_and_update(filenames, set_ids=False)

        # Verify no error from convert_and_update and the correct schema version was saved
        self.assertEqual(result, 0)

        tsv_filename = add_extension(os.path.join(self.base_path, "test_schema"), ".tsv")
        schema_reload1 = load_schema(tsv_filename)
        schema_reload2 = load_schema(os.path.join(self.base_path, "test_schema.xml"))

        self.assertEqual(schema, schema_reload1)
        self.assertEqual(schema, schema_reload2)

        # Now verify after doing this again with a new schema, they're still the same.
        schema = load_schema_version("8.2.0")
        schema.save_as_dataframes(tsv_filename)

        filenames = [os.path.join(tsv_filename, "test_schema_Tag.tsv")]
        result = convert_and_update(filenames, set_ids=False)

        # Verify no error from convert_and_update and the correct schema version was saved
        self.assertEqual(result, 0)

        schema_reload1 = load_schema(os.path.join(self.base_path, "test_schema.mediawiki"))
        schema_reload2 = load_schema(os.path.join(self.base_path, "test_schema.xml"))

        self.assertEqual(schema, schema_reload1)
        self.assertEqual(schema, schema_reload2)

    def test_schema_adding_tag(self):
        schema = load_schema_version("8.3.0")
        basename = os.path.join(self.base_path, "test_schema_edited")
        schema.save_as_mediawiki(add_extension(basename, ".mediawiki"))
        schema.save_as_xml(add_extension(basename, ".xml"))
        schema.save_as_dataframes(add_extension(basename, ".tsv"))

        schema_edited = copy.deepcopy(schema)
        test_tag_name = "NewTagWithoutID"
        new_entry = schema_edited._create_tag_entry(test_tag_name, HedSectionKey.Tags)
        schema_edited._add_tag_to_dict(test_tag_name, new_entry, HedSectionKey.Tags)

        schema_edited.save_as_mediawiki(add_extension(basename, ".mediawiki"))

        # Assume filenames updated includes just the original schema file for simplicity
        filenames = [add_extension(basename, ".mediawiki")]
        result = convert_and_update(filenames, set_ids=False)
        self.assertEqual(result, 0)

        schema_reloaded = load_schema(add_extension(basename, ".xml"))

        self.assertEqual(schema_reloaded, schema_edited)

        result = convert_and_update(filenames, set_ids=True)
        self.assertEqual(result, 0)

        schema_reloaded = load_schema(add_extension(basename, ".xml"))

        reloaded_entry = schema_reloaded.tags[test_tag_name]
        self.assertTrue(reloaded_entry.has_attribute(HedKey.HedID))


    @classmethod
    def tearDownClass(cls):
        # Clean up the directory created for testing
        shutil.rmtree(cls.base_path)
