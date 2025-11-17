import unittest
import shutil
import os
import pandas as pd
from hed.errors import HedExceptions, HedFileError
from hed.schema.hed_schema_io import load_schema, load_schema_version, from_dataframes
from hed.schema.schema_io import df_constants as df_constants
from hed.schema.schema_io.df_util import convert_filenames_to_dict, create_empty_dataframes


class TestHedSchemaDF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output_folder = "test_output/"
        os.makedirs(cls.output_folder, exist_ok=True)
        cls.schema = load_schema_version("8.4.0")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.output_folder)

    def test_saving_default_schemas(self):
        # schema = load_schema_version("8.3.0")
        # schema.save_as_dataframes(self.output_folder + "test_8.tsv")
        #
        # reloaded_schema = load_schema(self.output_folder + "test_8.tsv")
        # self.assertEqual(schema, reloaded_schema)
        #
        schema = load_schema_version("score_1.1.0")

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
        filename = self.output_folder + "test_8_string.tsv"
        self.schema.save_as_dataframes(self.output_folder + "test_8_string.tsv")

        filenames = convert_filenames_to_dict(filename)
        new_file_strings = {}
        for key, value in filenames.items():
            try:
                with open(value, "r") as f:
                    all_lines = f.readlines()
                    new_file_strings[key] = "".join(all_lines)
            except FileNotFoundError:
                pass

        reloaded_schema = from_dataframes(new_file_strings)
        self.assertEqual(self.schema, reloaded_schema)

        dfs = self.schema.get_as_dataframes()
        reloaded_schema = from_dataframes(dfs)
        self.assertEqual(self.schema, reloaded_schema)

    def test_save_load_location(self):
        schema_name = "test_output"
        output_location = self.output_folder + schema_name
        self.schema.save_as_dataframes(output_location)
        expected_location = os.path.join(output_location, f"{schema_name}_Tag.tsv")
        self.assertTrue(os.path.exists(expected_location))

        reloaded_schema = load_schema(output_location)

        self.assertEqual(self.schema, reloaded_schema)

    def test_save_load_location2(self):
        schema_name = "test_output"
        output_location = self.output_folder + schema_name + ".tsv"
        self.schema.save_as_dataframes(output_location)
        expected_location = self.output_folder + schema_name + "_Tag.tsv"
        self.assertTrue(os.path.exists(expected_location))

        reloaded_schema = load_schema(output_location)

        self.assertEqual(self.schema, reloaded_schema)

    def _create_structure_df(self):
        data = {
            "hedId": ["HED_0060010"],
            "rdfs:label": ["LangHeader"],
            "Attributes": ['version="1.0.0", library="lang", withStandard="8.3.0", unmerged="True"'],
            "omn:SubClassOf": ["HedHeader"],
            "dc:description": [""],
            "omn:EquivalentTo": [
                'HedHeader and (inHedSchema some LangSchema) and (version value "1.0.0")'
                + 'and (library value "lang") and (withStandard value "8.3.0")'
                + 'and (unmerged value "True")'
            ],
        }

        df = pd.DataFrame(data)
        return df

    def _add_tag_row(self, tag_df, name, parent):
        new_row = dict.fromkeys(tag_df.columns, "")
        new_row[df_constants.name] = name
        new_row[df_constants.subclass_of] = parent
        return pd.concat([tag_df, pd.DataFrame([new_row])], ignore_index=True)

    def test_loading_out_of_order(self):
        # Verify loading a .tsv file that defines a child before it's parent works
        dataframes = create_empty_dataframes()
        struct_df = self._create_structure_df()
        tag_df = pd.DataFrame([], columns=df_constants.tag_columns, dtype=str)

        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameParent", "HedTag")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameChild", "MadeUpLongTagNameParent")

        dataframes[df_constants.STRUCT_KEY] = struct_df
        dataframes[df_constants.TAG_KEY] = tag_df

        loaded_schema = from_dataframes(dataframes)
        issues = loaded_schema.check_compliance(check_for_warnings=False)
        self.assertEqual(len(issues), 0)

        self.assertEqual(loaded_schema.tags["MadeUpLongTagNameChild"].name, "MadeUpLongTagNameParent/MadeUpLongTagNameChild")
        self.assertEqual(loaded_schema.tags["MadeUpLongTagNameParent"].name, "MadeUpLongTagNameParent")

        tag_df = pd.DataFrame([], columns=df_constants.tag_columns, dtype=str)

        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameChild", "MadeUpLongTagNameParent")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameParent", "HedTag")

        dataframes[df_constants.TAG_KEY] = tag_df

        loaded_out_of_order = from_dataframes(dataframes)
        issues = loaded_schema.check_compliance(check_for_warnings=False)
        self.assertEqual(len(issues), 0)
        self.assertEqual(loaded_schema.tags["MadeUpLongTagNameChild"].name, "MadeUpLongTagNameParent/MadeUpLongTagNameChild")
        self.assertEqual(loaded_schema.tags["MadeUpLongTagNameParent"].name, "MadeUpLongTagNameParent")
        self.assertEqual(loaded_schema, loaded_out_of_order)

    def test_loading_circular(self):
        # Verify a circular reference properly reports an error
        dataframes = create_empty_dataframes()
        struct_df = self._create_structure_df()
        tag_df = pd.DataFrame([], columns=df_constants.tag_columns, dtype=str)

        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameParent", "MadeUpLongTagNameChild")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagNameChild", "MadeUpLongTagNameParent")

        dataframes[df_constants.STRUCT_KEY] = struct_df
        dataframes[df_constants.TAG_KEY] = tag_df

        with self.assertRaises(HedFileError) as error:
            _ = from_dataframes(dataframes)
        self.assertEqual(error.exception.args[0], HedExceptions.SCHEMA_TAG_TSV_BAD_PARENT)

        dataframes = create_empty_dataframes()
        struct_df = self._create_structure_df()
        tag_df = pd.DataFrame([], columns=df_constants.tag_columns, dtype=str)

        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagName1", "MadeUpLongTagName2")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagName2", "MadeUpLongTagName3")
        tag_df = self._add_tag_row(tag_df, "MadeUpLongTagName3", "MadeUpLongTagName1")

        dataframes[df_constants.STRUCT_KEY] = struct_df
        dataframes[df_constants.TAG_KEY] = tag_df

        with self.assertRaises(HedFileError) as error:
            _ = from_dataframes(dataframes)
        self.assertEqual(error.exception.args[0], HedExceptions.SCHEMA_TAG_TSV_BAD_PARENT)


if __name__ == "__main__":
    unittest.main()
