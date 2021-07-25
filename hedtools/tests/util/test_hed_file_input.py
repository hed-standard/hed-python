import unittest
import os
import io

from hed.models.hed_input import HedInput
from hed.models.hed_string import HedString
from hed.models.column_def_group import ColumnDefGroup
from hed.models.events_input import EventsInput
from hed.errors.exceptions import HedFileError


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_test_file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "../data/ExcelMultipleSheets.xlsx")
        cls.generic_file_input = HedInput(cls.default_test_file_name)
        cls.integer_key_dictionary = {1: 'one', 2: 'two', 3: 'three'}
        cls.one_based_tag_columns = [1, 2, 3]
        cls.zero_based_tag_columns = [0, 1, 2, 3, 4]
        cls.zero_based_row_column_count = 3
        cls.zero_based_tag_columns_less_than_row_column_count = [0, 1, 2]
        cls.column_prefix_dictionary = {3: 'Event/Description/', 4: 'Event/Label/', 5: 'Event/Category/'}
        cls.category_key = 'Event/Category/'
        cls.category_partipant_and_stimulus_tags = 'Event/Category/Participant response,Event/Category/Stimulus'
        cls.category_tags = 'Participant response, Stimulus'
        cls.row_with_hed_tags = ['event1', 'tag1', 'tag2']

    def test_all(self):
        hed_input = self.default_test_file_name
        has_column_names = True
        column_prefix_dictionary = {2: 'Label', 3: 'Description'}
        tag_columns = [4]
        worksheet_name = 'LKT Events'

        file_input = HedInput(hed_input, has_column_names=has_column_names, worksheet_name=worksheet_name,
                              tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary)

        for row_number, column_to_hed_tags in file_input:
            breakHere = 3

        # Just make sure this didn't crash for now
        self.assertTrue(True)

    def test_get_row_hed_tags(self):
        row_dict = self.generic_file_input._mapper.expand_row_tags(self.row_with_hed_tags)
        hed_string, column_to_hed_tags_dictionary = self.generic_file_input._get_row_hed_tags_from_dict(row_dict)
        self.assertIsInstance(hed_string, HedString)
        self.assertTrue(hed_string)
        self.assertIsInstance(column_to_hed_tags_dictionary, dict)
        self.assertTrue(column_to_hed_tags_dictionary)

    def test_file_as_string(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/bids_events.json")
        column_group = ColumnDefGroup(json_path)
        self.assertEqual(len(column_group.validate_entries()), 0)
        input_file = EventsInput(events_path, json_def_files=column_group)

        with open(events_path) as file:
            events_file_as_string = io.StringIO(file.read())
        input_file_from_string = EventsInput(filename=events_file_as_string, json_def_files=column_group)

        for (row_number, column_dict), (row_number2, column_dict) in zip(input_file, input_file_from_string):
            self.assertEqual(row_number, row_number2)
            self.assertEqual(column_dict, column_dict)

    def test_bad_file_inputs(self):
        self.assertRaises(HedFileError, EventsInput, None)

    def test_loading_binary(self):
        with open(self.default_test_file_name, "rb") as f:
            self.assertRaises(HedFileError, HedInput, f)

        with open(self.default_test_file_name, "rb") as f:
            opened_binary_file = HedInput(f, file_type=".xlsx")
            self.assertTrue(True)

    def test_to_excel(self):
        test_input_file = self.generic_file_input
        test_output_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/ExcelMultipleSheets_resave.xlsx")
        test_input_file.to_excel(test_output_name)

        test_input_file = self.generic_file_input
        test_output_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "../data/ExcelMultipleSheets_resave_formatting.xlsx")
        test_input_file.to_excel(test_output_name)

        #Test to a file stream
        test_input_file = self.generic_file_input
        test_output_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "../data/ExcelMultipleSheets_fileio.xlsx")
        with open(test_output_name, "wb") as f:
            test_input_file.to_excel(f)

    def test_to_csv(self):
        test_input_file = self.generic_file_input
        test_output_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "../data/ExcelMultipleSheets_resave.csv")
        test_input_file.to_csv(test_output_name)

        test_input_file = self.generic_file_input
        file_as_csv = test_input_file.to_csv(None)
        self.assertIsInstance(file_as_csv, str)

    def test_loading_and_reloading(self):
        test_input_file = self.generic_file_input
        test_output_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "../data/ExcelMultipleSheets_test_save.xlsx")

        test_input_file.to_excel(test_output_name)

        reloaded_input = HedInput(test_output_name)

        self.assertTrue(test_input_file._dataframe.equals(reloaded_input._dataframe))

    def test_loading_and_reset_mapper(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/bids_events.json")
        column_group = ColumnDefGroup(json_path)
        self.assertEqual(len(column_group.validate_entries()), 0)
        input_file_1 = EventsInput(events_path, json_def_files=column_group)
        input_file_2 = EventsInput(events_path, json_def_files=column_group)

        input_file_2.reset_column_defs()

        for (row_number, column_dict), (row_number2, column_dict2) in zip(input_file_1.iter_dataframe(expand_defs=True), input_file_2.iter_dataframe(expand_defs=True)):
            self.assertEqual(row_number, row_number2)
            self.assertTrue(len(column_dict) == 4)
            self.assertTrue(len(column_dict2) == 11)


if __name__ == '__main__':
    unittest.main()
