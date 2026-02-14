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

    def test_empty_tag_dataframe_has_headers(self):
        """Test that when a schema has no tags, the tag DataFrame still has proper column headers."""
        from hed.schema.schema_io.schema2df import Schema2DF
        from tests.schema.util_create_schemas import _get_test_schema

        # Create a minimal schema with no tags (only required sections)
        schema = _get_test_schema([])

        # Test the schema converter
        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        tag_df = output_dfs[df_constants.TAG_KEY]

        # The DataFrame should be empty but have proper column headers
        self.assertTrue(tag_df.empty, "Tag DataFrame should be empty")
        self.assertGreater(len(tag_df.columns), 0, "Tag DataFrame should have column headers")
        self.assertEqual(
            list(tag_df.columns),
            df_constants.tag_columns,
            f"Expected columns {df_constants.tag_columns}, got {list(tag_df.columns)}",
        )

    def test_all_empty_dataframes_have_headers(self):
        """Test that all empty DataFrames have proper column headers."""
        from hed.schema.schema_io.schema2df import Schema2DF
        from tests.schema.util_create_schemas import _get_test_schema

        # Create a minimal schema with no tags
        schema = _get_test_schema([])

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        # Check all DataFrames have proper headers even when empty
        for key, df in output_dfs.items():
            if key in df_constants.attribute_key_names:
                expected_columns = df_constants.attribute_key_names[key]
                if df.empty:
                    self.assertGreater(len(df.columns), 0, f"{key} DataFrame should have column headers when empty")
                    self.assertEqual(list(df.columns), expected_columns, f"{key} DataFrame has incorrect columns")

    def test_no_equivalent_to_column_in_tags(self):
        """Test that equivalent_to column is never generated in tag DataFrames."""
        from hed.schema.schema_io.schema2df import Schema2DF
        from tests.schema.util_create_schemas import load_schema1

        # Load a schema with tags
        schema = load_schema1()

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        tag_df = output_dfs[df_constants.TAG_KEY]

        # Verify no equivalent_to column exists
        self.assertNotIn("omn:EquivalentTo", tag_df.columns, "Tag DataFrame should not have equivalent_to column")
        self.assertNotIn(
            df_constants.hed_id + ":EquivalentTo", tag_df.columns, "Tag DataFrame should not have any equivalent_to variant"
        )

    def test_no_equivalent_to_column_in_units(self):
        """Test that equivalent_to column is never generated in unit-related DataFrames."""
        from hed.schema.schema_io.schema2df import Schema2DF

        # Use the standard schema which has units
        schema = self.schema

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        # Check units, unit classes, and unit modifiers
        for key in [df_constants.UNIT_KEY, df_constants.UNIT_CLASS_KEY, df_constants.UNIT_MODIFIER_KEY]:
            if key in output_dfs and not output_dfs[key].empty:
                df = output_dfs[key]
                self.assertNotIn("omn:EquivalentTo", df.columns, f"{key} DataFrame should not have equivalent_to column")

    def test_no_equivalent_to_column_in_value_classes(self):
        """Test that equivalent_to column is never generated in value class DataFrames."""
        from hed.schema.schema_io.schema2df import Schema2DF

        schema = self.schema

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        if df_constants.VALUE_CLASS_KEY in output_dfs:
            vc_df = output_dfs[df_constants.VALUE_CLASS_KEY]
            if not vc_df.empty:
                self.assertNotIn(
                    "omn:EquivalentTo", vc_df.columns, "Value class DataFrame should not have equivalent_to column"
                )

    def test_tag_columns_correct_with_data(self):
        """Test that tag DataFrames with data have exactly the expected columns."""
        from hed.schema.schema_io.schema2df import Schema2DF
        from tests.schema.util_create_schemas import load_schema1

        schema = load_schema1()

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        tag_df = output_dfs[df_constants.TAG_KEY]

        # Should have data
        self.assertFalse(tag_df.empty, "Tag DataFrame should have data")

        # Should have exactly the expected columns (no more, no less)
        self.assertEqual(
            set(tag_df.columns), set(df_constants.tag_columns), "Tag DataFrame should have exactly the expected columns"
        )

    def test_save_and_load_empty_schema(self):
        """Test that an empty schema can be saved and loaded with proper headers."""
        from tests.schema.util_create_schemas import _get_test_schema
        import tempfile

        schema = _get_test_schema([])

        # Save to a temporary location
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "empty_schema.tsv")
            schema.save_as_dataframes(output_path)

            # Check that the tag TSV file exists and has headers
            tag_file = output_path.replace(".tsv", "_Tag.tsv")
            self.assertTrue(os.path.exists(tag_file), "Tag TSV file should exist")

            # Read the file and verify it has headers
            with open(tag_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                self.assertTrue(len(first_line) > 0, "Tag TSV should have header line")
                # Should have tab-separated column names
                headers = first_line.split("\t")
                self.assertGreater(len(headers), 0, "Should have column headers")

            # Verify we can reload the schema
            reloaded_schema = load_schema(output_path)
            self.assertIsNotNone(reloaded_schema, "Should be able to reload empty schema")

    def test_schema2df_constructor_no_params(self):
        """Test that Schema2DF constructor works without parameters."""
        from hed.schema.schema_io.schema2df import Schema2DF

        # Should work without any parameters
        converter = Schema2DF()
        self.assertIsNotNone(converter, "Schema2DF should construct without parameters")

        # Should be able to process a schema
        from tests.schema.util_create_schemas import load_schema1

        schema = load_schema1()
        output_dfs = converter.process_schema(schema)
        self.assertIsNotNone(output_dfs, "Should be able to process schema")
        self.assertIn(df_constants.TAG_KEY, output_dfs, "Should produce tag DataFrame")

    def test_unit_columns_with_has_unit_class(self):
        """Test that unit DataFrames have hasUnitClass column populated correctly."""
        from hed.schema.schema_io.schema2df import Schema2DF

        schema = self.schema

        converter = Schema2DF()
        output_dfs = converter.process_schema(schema)

        if df_constants.UNIT_KEY in output_dfs and not output_dfs[df_constants.UNIT_KEY].empty:
            unit_df = output_dfs[df_constants.UNIT_KEY]

            # Should have hasUnitClass column
            self.assertIn(df_constants.has_unit_class, unit_df.columns, "Unit DataFrame should have hasUnitClass column")

            # Values should be unit class names (strings), not IDs
            has_unit_class_values = unit_df[df_constants.has_unit_class].dropna()
            if len(has_unit_class_values) > 0:
                # Check that values don't look like IDs (e.g., "hed:HED_0012345")
                for value in has_unit_class_values:
                    self.assertFalse(value.startswith("hed:HED_"), f"hasUnitClass should contain names, not IDs: {value}")


if __name__ == "__main__":
    unittest.main()
