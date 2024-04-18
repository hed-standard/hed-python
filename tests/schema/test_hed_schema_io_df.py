import unittest
import shutil

from hed.schema import load_schema, load_schema_version, from_string
from hed.schema.hed_schema_df_constants import *

import os


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

    def test_saving_default(self):
        schema = load_schema_version("8.3.0")
        schema.save_as_dataframes(self.output_folder + "test_8_string.tsv")

        filenames = {STRUCT_KEY: self.output_folder + "test_8_string_Structure.tsv",
                     TAG_KEY: self.output_folder + "test_8_string_Tag.tsv"}

        new_file_strings = {}
        for key, value in filenames.items():
            with open(value, "r") as f:
                all_lines = f.readlines()
                new_file_strings[key] = "".join(all_lines)

        reloaded_schema = from_string(new_file_strings, ".tsv")
        self.assertEqual(schema, reloaded_schema)