import unittest

from hed.validator.hed_file_input import HedFileInput


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generic_file_input = HedFileInput("tests/data/ExcelMultipleSheets.xlsx")
        cls.integer_key_dictionary = {1: 'one', 2: 'two', 3: 'three'}
        cls.one_based_tag_columns = [1, 2, 3]
        cls.zero_based_tag_columns = [0, 1, 2, 3, 4]
        cls.zero_based_row_column_count = 3
        cls.zero_based_tag_columns_less_than_row_column_count = [0, 1, 2]
        cls.required_tag_columns = {3: 'Event/Description/', 4: 'Event/Label/', 5: 'Event/Category/'}
        cls.category_key = 'Event/Category/'
        cls.category_partipant_and_stimulus_tags = 'Event/Category/Participant response,Event/Category/Stimulus'
        cls.category_tags = 'Participant response, Stimulus'
        cls.row_with_hed_tags = ['event1', 'tag1', 'tag2']

    def test_all(self):
        hed_input = 'tests/data/ExcelMultipleSheets.xlsx'
        has_column_names = True
        required_tag_columns = {2: 'Label', 3: 'Description'}
        tag_columns = [4]
        worksheet_name = 'LKT Events'

        file_input = HedFileInput(hed_input, has_column_names=has_column_names, worksheet_name=worksheet_name,
                                  tag_columns=tag_columns, required_tag_columns=required_tag_columns)

        for row_number, row, dict in file_input:
            breakHere = 3
        breakHere = 3
        # Just make sure this didn't crash for now
        self.assertTrue(True)

    def test_subtract_1_from_dictionary_keys(self):
        one_subtracted_key_dictionary = self.generic_file_input._subtract_1_from_dictionary_keys(self.integer_key_dictionary)
        self.assertIsInstance(one_subtracted_key_dictionary, dict)
        self.assertTrue(one_subtracted_key_dictionary)
        original_dictionary_key_sum = sum(self.integer_key_dictionary.keys())
        new_dictionary_key_sum = sum(one_subtracted_key_dictionary.keys())
        original_dictionary_key_length = len(self.integer_key_dictionary.keys())
        self.assertEqual(original_dictionary_key_sum - new_dictionary_key_sum, original_dictionary_key_length)

    def test_subtract_1_from_list_elements(self):
        one_subtracted_list = self.generic_file_input._subtract_1_from_list_elements(self.one_based_tag_columns)
        self.assertIsInstance(one_subtracted_list, list)
        self.assertTrue(one_subtracted_list)
        original_list_sum = sum(self.one_based_tag_columns)
        new_list_sum = sum(one_subtracted_list)
        original_list_length = len(self.one_based_tag_columns)
        self.assertEqual(original_list_sum - new_list_sum, original_list_length)

    def test__prepend_prefix_to_required_tag_column_if_needed(self):
        prepended_hed_string = self.generic_file_input._prepend_prefix_to_required_tag_column_if_needed(
            self.category_tags, self.category_key)
        self.assertIsInstance(prepended_hed_string, str)
        self.assertEqual(prepended_hed_string, self.category_partipant_and_stimulus_tags)

    def test_remove_tag_columns_greater_than_row_column_count(self):
        rows_less_than_row_column_count = HedFileInput._remove_tag_columns_greater_than_row_column_count(
            self.zero_based_row_column_count, self.zero_based_tag_columns)
        self.assertIsInstance(rows_less_than_row_column_count, list)
        self.assertEqual(rows_less_than_row_column_count, self.zero_based_tag_columns_less_than_row_column_count)

    def test_get_row_hed_tags(self):
        hed_string, column_to_hed_tags_dictionary = self.generic_file_input.get_row_hed_tags(
            self.row_with_hed_tags, is_worksheet=False)
        self.assertIsInstance(hed_string, str)
        self.assertTrue(hed_string)
        self.assertIsInstance(column_to_hed_tags_dictionary, dict)
        self.assertTrue(column_to_hed_tags_dictionary)

    def test__convert_tag_columns_to_processing_format(self):
        processing_tag_columns = self.generic_file_input._convert_tag_columns_to_processing_format(
            self.one_based_tag_columns, required_tag_columns={})
        self.assertIsInstance(processing_tag_columns, list)
        self.assertEqual(processing_tag_columns, self.zero_based_tag_columns_less_than_row_column_count)


if __name__ == '__main__':
    unittest.main()
