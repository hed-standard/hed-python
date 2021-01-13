import unittest
import os

from hed.util.hed_file_input import HedFileInput


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_test_file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "../data/ExcelMultipleSheets.xlsx")
        cls.generic_file_input = HedFileInput(cls.default_test_file_name)
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

        file_input = HedFileInput(hed_input, has_column_names=has_column_names, worksheet_name=worksheet_name,
                                  tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary)

        for row_number, row, dict in file_input:
            breakHere = 3
        breakHere = 3
        # Just make sure this didn't crash for now
        self.assertTrue(True)


    def test_get_row_hed_tags(self):
        row_dict = self.generic_file_input._get_dict_from_row_hed_tags(self.row_with_hed_tags, self.generic_file_input._mapper)
        hed_string, column_to_hed_tags_dictionary = self.generic_file_input._get_row_hed_tags_from_dict(row_dict)
        self.assertIsInstance(hed_string, str)
        self.assertTrue(hed_string)
        self.assertIsInstance(column_to_hed_tags_dictionary, dict)
        self.assertTrue(column_to_hed_tags_dictionary)

    # Add more tests here


if __name__ == '__main__':
    unittest.main()
