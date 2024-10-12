import unittest
import os
import io

from hed.errors import HedFileError
from hed.models import TabularInput, SpreadsheetInput,  Sidecar
import shutil
from hed import schema
import pandas as pd


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        cls.base_data_dir = base
        hed_xml_file = os.path.join(base, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        default = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "../data/spreadsheet_validator_tests/ExcelMultipleSheets.xlsx")
        cls.default_test_file_name = default
        cls.generic_file_input = SpreadsheetInput(default)
        base_output = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        cls.base_output_folder = base_output
        os.makedirs(base_output, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_all(self):
        hed_input = self.default_test_file_name
        has_column_names = True
        column_prefix_dictionary = {1: 'Label/', 2: 'Description'}
        tag_columns = [4]
        worksheet_name = 'LKT Events'

        file_input = SpreadsheetInput(hed_input, has_column_names=has_column_names, worksheet_name=worksheet_name,
                                      tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary)

        self.assertTrue(isinstance(file_input.dataframe_a, pd.DataFrame))
        self.assertTrue(isinstance(file_input.series_a, pd.Series))
        self.assertTrue(file_input.dataframe_a.size)
        self.assertEqual(len(file_input._mapper.get_column_mapping_issues()), 0)

    def test_all2(self):
        # This should work, but raise an issue as Short label and column 1 overlap.
        hed_input = self.default_test_file_name
        has_column_names = True
        column_prefix_dictionary = {1: 'Label/', "Short label": 'Description'}
        tag_columns = [4]
        worksheet_name = 'LKT Events'

        file_input = SpreadsheetInput(hed_input, has_column_names=has_column_names, worksheet_name=worksheet_name,
                                      tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary)

        self.assertTrue(isinstance(file_input.dataframe_a, pd.DataFrame))
        self.assertTrue(isinstance(file_input.series_a, pd.Series))
        self.assertTrue(file_input.dataframe_a.size)
        self.assertEqual(len(file_input._mapper.get_column_mapping_issues()), 1)

    def test_file_as_string(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_no_index.tsv')

        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        sidecar = Sidecar(json_path)
        self.assertEqual(len(sidecar.validate(self.hed_schema)), 0)
        #input_file = TabularInput(events_path, sidecar=sidecar)

        with open(events_path) as file:
            events_file_as_string = io.StringIO(file.read())
        input_file_from_string = TabularInput(file=events_file_as_string, sidecar=sidecar)

        #self.assertTrue(input_file._dataframe.equals(input_file_from_string._dataframe))

    def test_bad_file_inputs(self):
        self.assertRaises(HedFileError, TabularInput, None)

    def test_loading_binary(self):
        with open(self.default_test_file_name, "rb") as f:
            self.assertRaises(HedFileError, SpreadsheetInput, f)

        with open(self.default_test_file_name, "rb") as f:
            opened_binary_file = SpreadsheetInput(f, file_type=".xlsx")
            self.assertIsInstance(opened_binary_file, SpreadsheetInput, "SpreadsheetInput creates a correct object.")
            self.assertTrue(True)

    def test_to_excel(self):
        test_input_file = self.generic_file_input
        test_output_name = self.base_output_folder + "ExcelMultipleSheets_resave.xlsx"
        test_input_file.to_excel(test_output_name)

        test_input_file = self.generic_file_input
        test_output_name = self.base_output_folder + "ExcelMultipleSheets_resave_formatting.xlsx"
        test_input_file.to_excel(test_output_name)

        # Test to a file stream
        test_input_file = self.generic_file_input
        test_output_name = self.base_output_folder + "ExcelMultipleSheets_fileio.xlsx"
        with open(test_output_name, "wb") as f:
            test_input_file.to_excel(f)

    def test_to_excel_should_work(self):
        spreadsheet = SpreadsheetInput(file=self.default_test_file_name, file_type='.xlsx',
                                       tag_columns=[3], has_column_names=True,
                                       column_prefix_dictionary={1: 'Label/', 2: 'Description/'},
                                       name='ExcelOneSheet.xlsx')
        buffer = io.BytesIO()
        spreadsheet.to_excel(buffer)
        buffer.seek(0)
        v = buffer.getvalue()
        self.assertGreater(len(v), 0, "It should have a length greater than 0")

    def test_to_csv(self):
        test_input_file = self.generic_file_input
        test_output_name = self.base_output_folder + "ExcelMultipleSheets_resave.csv"
        test_input_file.to_csv(test_output_name)

        test_input_file = self.generic_file_input
        file_as_csv = test_input_file.to_csv(None)
        self.assertIsInstance(file_as_csv, str)

    def test_loading_and_reloading(self):
        test_input_file = self.generic_file_input
        test_output_name = self.base_output_folder + "ExcelMultipleSheets_test_save.xlsx"

        test_input_file.to_excel(test_output_name)

        reloaded_input = SpreadsheetInput(test_output_name)

        self.assertTrue(test_input_file._dataframe.equals(reloaded_input._dataframe))

    def test_loading_and_reset_mapper(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_no_index.tsv')
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        sidecar = Sidecar(json_path)
        self.assertEqual(len(sidecar.validate(self.hed_schema)), 0)
        input_file_1 = TabularInput(events_path, sidecar=sidecar)
        input_file_2 = TabularInput(events_path, sidecar=sidecar)

        input_file_2.reset_column_mapper()

        self.assertTrue(input_file_1.dataframe.equals(input_file_2.dataframe))

    def test_no_column_header_and_convert(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[0, 1])
        hed_input.convert_to_long(self.hed_schema)

        events_path_long = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../data/model_tests/no_column_header_long.tsv')
        hed_input_long = SpreadsheetInput(events_path_long, has_column_names=False, tag_columns=[0, 1])
        self.assertTrue(hed_input._dataframe.equals(hed_input_long._dataframe))

    def test_convert_short_long_with_definitions(self):
        # Verify behavior works as expected even if definitions are present
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header_definition.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[0, 1])
        hed_input.convert_to_long(self.hed_schema)

        events_path_long = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../data/model_tests/no_column_header_definition_long.tsv')
        hed_input_long = SpreadsheetInput(events_path_long, has_column_names=False, tag_columns=[0, 1])
        self.assertTrue(hed_input._dataframe.equals(hed_input_long._dataframe))

    def test_loading_dataframe_directly(self):
        ds_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../data/model_tests/no_column_header_definition.tsv')
        ds = pd.read_csv(ds_path, delimiter="\t", header=None)
        hed_input = SpreadsheetInput(ds, has_column_names=False, tag_columns=[0, 1])

        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header_definition.tsv')
        hed_input2 = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[0, 1])
        self.assertTrue(hed_input._dataframe.equals(hed_input2._dataframe))

    def test_ignoring_na_column(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/na_tag_column.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[0, 1])
        self.assertTrue(hed_input.dataframe_a.loc[1, 1] == 'n/a')

    def test_ignoring_na_value_column(self):
        from hed import TabularInput
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/na_value_column.tsv')
        sidecar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    '../data/model_tests/na_value_column.json')
        hed_input = TabularInput(events_path, sidecar=sidecar_path)
        self.assertTrue(hed_input.dataframe_a.loc[1, 'Value'] == 'n/a')

    def test_to_excel_workbook(self):
        excel_book = SpreadsheetInput(self.default_test_file_name, worksheet_name="LKT 8HED3",
                                      tag_columns=["HED tags"])
        test_output_name = self.base_output_folder + "ExcelMultipleSheets_resave_assembled.xlsx"
        excel_book.convert_to_long(self.hed_schema)
        excel_book.to_excel(test_output_name)
        reloaded_df = SpreadsheetInput(test_output_name, worksheet_name="LKT 8HED3")

        self.assertTrue(excel_book.dataframe.equals(reloaded_df.dataframe))

    def test_to_excel_workbook_no_col_names(self):
        excel_book = SpreadsheetInput(self.default_test_file_name, worksheet_name="LKT 8HED3",
                                      tag_columns=[4], has_column_names=False)
        test_output_name = self.base_output_folder + "ExcelMultipleSheets_resave_assembled_no_col_names.xlsx"
        excel_book.convert_to_long(self.hed_schema)
        excel_book.to_excel(test_output_name)
        reloaded_df = SpreadsheetInput(test_output_name, worksheet_name="LKT 8HED3", tag_columns=[4],
                                       has_column_names=False)
        self.assertTrue(excel_book.dataframe.equals(reloaded_df.dataframe))


if __name__ == '__main__':
    unittest.main()
