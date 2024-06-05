import unittest
import shutil

from hed.schema.hed_schema_io import load_schema, load_schema_version, from_dataframes

import os
from hed.schema.schema_io.df2schema import SchemaLoaderDF


class TestHedSchemaDF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output_folder = "test_output/"
        os.makedirs(cls.output_folder, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.output_folder)

    def test_saving_default_schemas(self):
        schema = load_schema_version("8.3.0")
        schema.save_as_dataframes(self.output_folder + "test_8.tsv")

        reloaded_schema = load_schema(self.output_folder + "test_8.tsv")
        self.assertEqual(schema, reloaded_schema)

        schema = load_schema_version("score_1.1.1")
        schema.save_as_dataframes(self.output_folder + "test_score.tsv", save_merged=True)

        reloaded_schema = load_schema(self.output_folder + "test_score.tsv")
        self.assertEqual(schema, reloaded_schema)

        schema = load_schema_version("testlib_3.0.0")
        schema.save_as_dataframes(self.output_folder + "test_testlib.tsv", save_merged=True)

        reloaded_schema = load_schema(self.output_folder + "test_testlib.tsv")
        self.assertEqual(schema, reloaded_schema)

        schema = load_schema_version("testlib_3.0.0")
        schema.save_as_dataframes(self.output_folder + "test_testlib2.tsv", save_merged=False)

        reloaded_schema = load_schema(self.output_folder + "test_testlib2.tsv")
        self.assertEqual(schema, reloaded_schema)

    def test_from_dataframes(self):
        schema = load_schema_version("8.3.0")
        filename = self.output_folder + "test_8_string.tsv"
        schema.save_as_dataframes(self.output_folder + "test_8_string.tsv")

        filenames = SchemaLoaderDF.convert_filenames_to_dict(filename)
        new_file_strings = {}
        for key, value in filenames.items():
            with open(value, "r") as f:
                all_lines = f.readlines()
                new_file_strings[key] = "".join(all_lines)

        reloaded_schema = from_dataframes(new_file_strings)
        self.assertEqual(schema, reloaded_schema)

        schema = load_schema_version("8.3.0")
        dfs = schema.get_as_dataframes()
        reloaded_schema = from_dataframes(dfs)
        self.assertEqual(schema, reloaded_schema)

    def test_save_load_location(self):
        schema = load_schema_version("8.3.0")
        schema_name = "test_output"
        output_location = self.output_folder + schema_name
        schema.save_as_dataframes(output_location)
        expected_location = os.path.join(output_location, f"{schema_name}_Tag.tsv")
        self.assertTrue(os.path.exists(expected_location))

        reloaded_schema = load_schema(output_location)

        self.assertEqual(schema, reloaded_schema)

    def test_save_load_location2(self):
        schema = load_schema_version("8.3.0")
        schema_name = "test_output"
        output_location = self.output_folder + schema_name + ".tsv"
        schema.save_as_dataframes(output_location)
        expected_location = self.output_folder + schema_name + "_Tag.tsv"
        self.assertTrue(os.path.exists(expected_location))

        reloaded_schema = load_schema(output_location)

        self.assertEqual(schema, reloaded_schema)
