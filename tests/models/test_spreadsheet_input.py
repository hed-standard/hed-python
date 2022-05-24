import unittest
import os
import io

from hed.errors import HedFileError
from hed.models import TabularInput, SpreadsheetInput, model_constants, Sidecar
import shutil
from hed import schema


# TODO: Add tests about correct handling of 'n/a'


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "schema_test_data/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.default_test_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  "../data/validator_tests/ExcelMultipleSheets.xlsx")
        cls.generic_file_input = SpreadsheetInput(cls.default_test_file_name)
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

        cls.base_output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        os.makedirs(cls.base_output_folder, exist_ok=True)

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

        for column_to_hed_tags in file_input:
            break_here = 3

        # Just make sure this didn't crash for now
        self.assertTrue(True)

    def test_get_row_hed_tags(self):
        row_dict = self.generic_file_input._mapper.expand_row_tags(self.row_with_hed_tags)
        column_to_hed_tags_dictionary = row_dict[model_constants.COLUMN_TO_HED_TAGS]
        # self.assertIsInstance(hed_string, HedString)
        # self.assertTrue(hed_string)
        self.assertIsInstance(column_to_hed_tags_dictionary, dict)
        self.assertTrue(column_to_hed_tags_dictionary)

    def test_file_as_string(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_with_index.tsv')

        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        sidecar = Sidecar(json_path)
        self.assertEqual(len(sidecar.validate_entries(expand_defs=True)), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        with open(events_path) as file:
            events_file_as_string = io.StringIO(file.read())
        input_file_from_string = TabularInput(file=events_file_as_string, sidecar=sidecar)

        for  column_dict, column_dict in zip(input_file, input_file_from_string):
            self.assertEqual(column_dict, column_dict)

    def test_bad_file_inputs(self):
        self.assertRaises(HedFileError, TabularInput, None)

    def test_loading_binary(self):
        with open(self.default_test_file_name, "rb") as f:
            self.assertRaises(HedFileError, SpreadsheetInput, f)

        with open(self.default_test_file_name, "rb") as f:
            opened_binary_file = SpreadsheetInput(f, file_type=".xlsx")
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
                                   '../data/validator_tests/bids_events_with_index.tsv')
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        sidecar = Sidecar(json_path)
        self.assertEqual(len(sidecar.validate_entries()), 0)
        input_file_1 = TabularInput(events_path, sidecar=sidecar)
        input_file_2 = TabularInput(events_path, sidecar=sidecar)

        input_file_2.reset_column_mapper()

        for (row_number, row_dict), (row_number2, row_dict2) in zip(enumerate(input_file_1.iter_dataframe(return_string_only=False)),
                                                                          enumerate(input_file_2.iter_dataframe(return_string_only=False))):
            self.assertEqual(row_number, row_number2,
                             f"TabularInput should have row {row_number} equal to {row_number2} after reset")
            column_dict = row_dict["column_to_hed_tags"]
            self.assertTrue(len(column_dict) == 5,
                            f"The column dictionary for row {row_number} should have the right length")
            column_dict2 = row_dict2["column_to_hed_tags"]
            self.assertTrue(len(column_dict2) == 11,
                            f"The reset column dictionary for row {row_number2} should have the right length")

    def test_no_column_header_and_convert(self):
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])
        hed_input.convert_to_long(self.hed_schema)

        events_path_long = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../data/model_tests/no_column_header_long.tsv')
        hed_input_long = SpreadsheetInput(events_path_long, has_column_names=False, tag_columns=[1, 2])
        for column1, column2 in zip(hed_input, hed_input_long):
            self.assertEqual(column1, column2)

        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])
        events_path_long = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../data/model_tests/no_column_header_long.tsv')
        hed_input_long = SpreadsheetInput(events_path_long, has_column_names=False, tag_columns=[1, 2])
        hed_input_long.convert_to_short(self.hed_schema)
        for column1, column2 in zip(hed_input, hed_input_long):
            self.assertEqual(column1, column2)

    def test_convert_short_long_with_definitions(self):
        # Verify behavior works as expected even if definitions are present
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/model_tests/no_column_header_definition.tsv')
        hed_input = SpreadsheetInput(events_path, has_column_names=False, tag_columns=[1, 2])
        hed_input.convert_to_long(self.hed_schema)

        events_path_long = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../data/model_tests/no_column_header_definition_long.tsv')
        hed_input_long = SpreadsheetInput(events_path_long, has_column_names=False, tag_columns=[1, 2])
        for column1, column2 in zip(hed_input, hed_input_long):
            self.assertEqual(column1, column2)



if __name__ == '__main__':
    unittest.main()
