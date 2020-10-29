import random
import unittest

from hed.util.hed_string_delimiter import HedStringDelimiter
from hed.validator.hed_validator import HedValidator


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generic_hed_input_reader = HedValidator('Attribute/Temporal/Onset')
        cls.text_file_with_extension = 'file_with_extension.txt'
        cls.integer_key_dictionary = {1: 'one', 2: 'two', 3: 'three'}
        cls.float_value = 1.1
        cls.one_based_tag_columns = [1, 2, 3]
        cls.zero_based_tag_columns = [0, 1, 2, 3, 4]
        cls.zero_based_row_column_count = 3
        cls.zero_based_tag_columns_less_than_row_column_count = [0, 1, 2]
        cls.comma_separated_string_with_double_quotes = 'a,b,c,"d,e,f"'
        cls.comma_delimited_list_with_double_quotes = ['a', 'b', 'c', "d,e,f"]
        cls.comma_delimiter = ','
        cls.category_key = 'Category'
        cls.hed_string_with_multiple_unique_tags = 'event/label/this is a label,event/label/this is another label'
        cls.hed_string_with_invalid_tags = 'this/is/not/a/valid/tag1,this/is/not/a/valid/tag2'
        cls.hed_string_with_no_required_tags = 'no/required/tags1,no/required/tags2'
        cls.hed_string_with_too_many_tildes = '(this/is/not/a/valid/tag1~this/is/not/a/valid/tag2' \
                                              '~this/is/not/a/valid/tag3~this/is/not/a/valid/tag4)'
        cls.attribute_onset_tag = 'Attribute/Onset'
        cls.category_partipant_and_stimulus_tags = 'Event/Category/Participant response,Event/Category/Stimulus'
        cls.category_tags = 'Participant response, Stimulus'
        cls.validation_issues = []
        cls.column_to_hed_tags_dictionary = {}
        cls.row_with_hed_tags = ['event1', 'tag1', 'tag2']
        cls.row_hed_tag_columns = [1, 2]
        cls.original_and_formatted_tag = [('Event/Label/Test', 'event/label/test'),
                                          ('Event/Description/Test', 'event/description/test')]

    def test__validate_hed_input(self):
        validation_issues = self.generic_hed_input_reader._validate_hed_input()
        self.assertIsInstance(validation_issues, list)

    def test__validate_individual_tags_in_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.hed_string_with_invalid_tags)
        validation_issues = self.generic_hed_input_reader._validate_individual_tags_in_hed_string(hed_string_delimiter)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(validation_issues)

    def test__validate_top_levels_in_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.hed_string_with_no_required_tags)
        validation_issues = self.generic_hed_input_reader._validate_top_level_in_hed_string(hed_string_delimiter)
        self.assertIsInstance(validation_issues, list)
        self.assertFalse(validation_issues)

    def test__validate_tag_levels_in_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.hed_string_with_multiple_unique_tags)
        validation_issues = self.generic_hed_input_reader._validate_tag_levels_in_hed_string(hed_string_delimiter)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(validation_issues)

    def test__validate_groups_in_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.hed_string_with_too_many_tildes)
        validation_issues = self.generic_hed_input_reader._validate_groups_in_hed_string(hed_string_delimiter)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(validation_issues)

    def test__append_validation_issues_if_found(self):
        row_number = random.randint(0, 100)
        self.assertFalse(self.validation_issues)
        validation_issues = \
            self.generic_hed_input_reader._append_validation_issues_if_found(self.validation_issues,
                                                                             row_number,
                                                                             self.hed_string_with_invalid_tags,
                                                                             self.column_to_hed_tags_dictionary)
        self.assertIsInstance(validation_issues, list)
        self.assertFalse(validation_issues)

    def test__append_row_validation_issues_if_found(self):
        row_number = random.randint(0, 100)
        self.assertFalse(self.validation_issues)
        validation_issues = \
            self.generic_hed_input_reader._append_row_validation_issues_if_found(self.validation_issues,
                                                                                 row_number,
                                                                                 self.hed_string_with_invalid_tags)
        self.assertIsInstance(validation_issues, list)
        self.assertFalse(validation_issues)

    def test__append_column_validation_issues_if_found(self):
        row_number = random.randint(0, 100)
        self.assertFalse(self.validation_issues)
        validation_issues = \
            self.generic_hed_input_reader._append_column_validation_issues_if_found(self.validation_issues,
                                                                                    row_number,
                                                                                    self.column_to_hed_tags_dictionary)
        self.assertIsInstance(validation_issues, list)
        self.assertFalse(validation_issues)

    def test_validate_column_hed_string(self):
        self.assertFalse(self.validation_issues)
        validation_issues = self.generic_hed_input_reader.validate_column_hed_string(self.hed_string_with_invalid_tags)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(validation_issues)

    def test_get_validation_issues(self):
        validation_issues = self.generic_hed_input_reader.get_validation_issues()
        self.assertIsInstance(validation_issues, list)


    def test_get_previous_original_and_formatted_tag(self):
        loop_index = 1
        previous_original_tag, previous_formatted_tag = HedValidator.get_previous_original_and_formatted_tag(
            self.original_and_formatted_tag, loop_index)
        self.assertEqual(previous_original_tag, self.original_and_formatted_tag[0][0])
        self.assertEqual(previous_formatted_tag, self.original_and_formatted_tag[0][1])


if __name__ == '__main__':
    unittest.main()
