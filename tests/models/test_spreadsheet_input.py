import unittest
import os
import io

from hed.errors import HedFileError
from hed.models import TabularInput, SpreadsheetInput, model_constants, Sidecar
import shutil
from hed import schema
import pandas as pd


# TODO: Add tests about correct handling of 'n/a'


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        cls.base_data_dir = base
        hed_xml_file = os.path.join(base, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        default = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "../data/validator_tests/ExcelMultipleSheets.xlsx")
        cls.default_test_file_name = default
        cls.generic_file_input = SpreadsheetInput(default)
        cls.integer_key_dictionary = {1: 'one', 2: 'two', 3: 'three'}
        cls.one_based_tag_columns = [1, 2, 3]
        cls.zero_based_tag_columns = [0, 1, 2, 3, 4]
        cls.zero_based_row_column_count = 3
        cls.zero_based_tag_columns_less_than_row_column_count = [0, 1, 2]
        cls.column_prefix_dictionary = {3: 'Event/Description/', 4: 'Event/Label/', 5: 'Event/Category/'}
        cls.category_key = 'Event/Category/'
        cls.category_participant_and_stimulus_tags = 'Event/Category/Participant response,Event/Category/Stimulus'
        cls.category_tags = 'Participant response, Stimulus'
        cls.row_with_hed_tags = ['event1', 'tag1', 'tag2']
        base_output = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        cls.base_output_folder = base_output
        os.makedirs(base_output, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_all(self):
        hed_input = self.default_test_file_name
        has_column_names = True
        column_prefix_dictionary = {2: 'Label', 3: 'Description'}
        tag_columns = [4]
        worksheet_name = 'LKT Events'

        file_input = SpreadsheetInput(hed_input, has_column_names=has_column_names, worksheet_name=worksheet_name,
                                      tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary)

        self.assertTrue(isinstance(file_input.dataframe_a, pd.DataFrame))
        self.assertTrue(isinstance(file_input.series_a, pd.Series))
        self.assertTrue(file_input.dataframe_a.size)

        # Just make sure this didn't crash for now
        self.assertTrue(True)

    def test_file_as_string(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_no_index.tsv')

        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        sidecar = Sidecar(json_path)
        self.assertEqual(len(sidecar.validate(self.hed_schema)), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        with open(events_path) as file:
            events_file_as_string = io.StringIO(file.read())
        input_file_from_string = TabularInput(file=events_file_as_string, sidecar=sidecar)

        self.assertTrue(input_file._dataframe.equals(input_file_from_string._dataframe))

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
                                       tag_columns=[4], has_column_names=True,
                                       column_prefix_dictionary={1: 'Label/', 3: 'Description/'},
                                       name='ExcelOneSheet.xlsx')
        buffer = io.BytesIO()
        spreadsheet.to_excel(buffer, output_assembled=True)
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
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])
        hed_input.convert_to_long(self.hed_schema)

        events_path_long = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../data/model_tests/no_column_header_long.tsv')
        hed_input_long = SpreadsheetInput(events_path_long, has_column_names=False, tag_columns=[1, 2])
        self.assertTrue(hed_input._dataframe.equals(hed_input_long._dataframe))

    def test_convert_short_long_with_definitions(self):
        # Verify behavior works as expected even if definitions are present
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header_definition.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])
        hed_input.convert_to_long(self.hed_schema)

        events_path_long = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../data/model_tests/no_column_header_definition_long.tsv')
        hed_input_long = SpreadsheetInput(events_path_long, has_column_names=False, tag_columns=[1, 2])
        self.assertTrue(hed_input._dataframe.equals(hed_input_long._dataframe))

    def test_definitions_identified(self):
        # Todo ian: this test is no longer relevant
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header_definition.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header_definition.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])


    def test_loading_dataframe_directly(self):
        ds_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../data/model_tests/no_column_header_definition.tsv')
        ds = pd.read_csv(ds_path, delimiter="\t", header=None)
        hed_input = SpreadsheetInput(ds, has_column_names=False, tag_columns=[1, 2])

        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header_definition.tsv')
        hed_input2 = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])
        self.assertTrue(hed_input._dataframe.equals(hed_input2._dataframe))

    def test_ignoring_na_column(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/na_tag_column.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])
        self.assertTrue(hed_input.dataframe_a.loc[1, 1] == 'n/a')

    def test_ignoring_na_value_column(self):
        from hed import TabularInput
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/na_value_column.tsv')
        sidecar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/na_value_column.json')
        hed_input = TabularInput(events_path, sidecar=sidecar_path)
        self.assertTrue(hed_input.dataframe_a.loc[1, 'Value'] == 'n/a')

if __name__ == '__main__':
    unittest.main()
