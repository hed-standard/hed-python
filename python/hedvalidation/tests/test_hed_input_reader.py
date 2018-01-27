import random;
import unittest;

from hedvalidation.hed_string_delimiter import HedStringDelimiter;
from hedvalidation.hed_input_reader import HedInputReader;


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generic_hed_input_reader = HedInputReader('Attribute/Onset');
        cls.text_file_with_extension = 'file_with_extension.txt';
        cls.integer_key_dictionary = {1: 'one', 2: 'two', 3: 'three'};
        cls.float_value = 1.1;
        cls.one_based_tag_columns = [1, 2, 3];
        cls.zero_based_tag_columns = [0, 1, 2, 3, 4];
        cls.zero_based_row_column_count = 3;
        cls.zero_based_tag_columns_less_than_row_column_count = [0, 1, 2];
        cls.comma_separated_string_with_double_quotes = 'a,b,c,"d,e,f"';
        cls.comma_delimited_list_with_double_quotes = ['a', 'b', 'c', "d,e,f"];
        cls.comma_delimiter = ',';
        cls.category_key = 'Category';
        cls.hed_string_with_multiple_unique_tags = 'event/label/this is a label,event/label/this is another label';
        cls.hed_string_with_invalid_tags = 'this/is/not/a/valid/tag1,this/is/not/a/valid/tag2';
        cls.hed_string_with_too_many_tildes = '(this/is/not/a/valid/tag1~this/is/not/a/valid/tag2' \
                                                 '~this/is/not/a/valid/tag3~this/is/not/a/valid/tag4)';
        cls.attribute_onset_tag = 'Attribute/Onset';
        cls.category_partipant_and_stimulus_tags = 'Event/Category/Participant response,Event/Category/Stimulus';
        cls.category_tags = 'Participant response, Stimulus';
        cls.validation_issues = '';
        cls.semantic_version_one = '1.2.3';
        cls.semantic_version_two = '1.2.4';
        cls.semantic_version_three = '1.2.5';
        cls.semantic_version_list = ['1.2.3', '1.2.4', '1.2.5'];


    def test__convert_tag_columns_to_processing_format(self):
        processing_tag_columns = self.generic_hed_input_reader._convert_tag_columns_to_processing_format(
            self.one_based_tag_columns);
        self.assertIsInstance(processing_tag_columns, list);
        self.assertEqual(processing_tag_columns, self.zero_based_tag_columns_less_than_row_column_count);

    def test__validate_hed_input(self):
        validation_issues = self.generic_hed_input_reader._validate_hed_input();
        self.assertIsInstance(validation_issues, basestring);

    def test_validate_hed_string(self):
        validation_issues = self.generic_hed_input_reader._validate_hed_string(self.hed_string_with_invalid_tags);
        self.assertIsInstance(validation_issues, basestring);
        self.assertTrue(validation_issues);

    def test__validate_individual_tags_in_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.hed_string_with_invalid_tags);
        validation_issues = self.generic_hed_input_reader._validate_individual_tags_in_hed_string(hed_string_delimiter);
        self.assertIsInstance(validation_issues, basestring);
        self.assertTrue(validation_issues);

    def test__validate_top_levels_in_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.hed_string_with_invalid_tags);
        validation_issues = self.generic_hed_input_reader._validate_top_levels_in_hed_string(hed_string_delimiter);
        self.assertIsInstance(validation_issues, basestring);
        self.assertTrue(validation_issues);

    def test__validate_tag_levels_in_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.hed_string_with_multiple_unique_tags);
        validation_issues = self.generic_hed_input_reader._validate_tag_levels_in_hed_string(hed_string_delimiter);
        self.assertIsInstance(validation_issues, basestring);
        self.assertTrue(validation_issues);

    def test__validate_groups_in_hed_string(self):
        hed_string_delimiter = HedStringDelimiter(self.hed_string_with_too_many_tildes);
        validation_issues = self.generic_hed_input_reader._validate_groups_in_hed_string(hed_string_delimiter);
        self.assertIsInstance(validation_issues, basestring);
        self.assertTrue(validation_issues);

    def test__append_validation_issues_if_found(self):
        row_number = random.randint(0,100);
        self.assertFalse(self.validation_issues);
        validation_issues = \
            self.generic_hed_input_reader._append_validation_issues_if_found(self.validation_issues,
                                                                             row_number,
                                                                             self.hed_string_with_invalid_tags);
        self.assertIsInstance(validation_issues, basestring);
        self.assertTrue(validation_issues);

    def test_get_validation_issues(self):
        validation_issues = self.generic_hed_input_reader.get_validation_issues();
        self.assertIsInstance(validation_issues, basestring);

    def test_get_delimiter_from_text_file_extension(self):
        text_file_extension = HedInputReader.get_file_extension(self.text_file_with_extension)
        text_file_delimiter = HedInputReader.get_delimiter_from_text_file_extension(text_file_extension);
        self.assertIsInstance(text_file_delimiter, basestring);
        self.assertEqual(text_file_delimiter, HedInputReader.TAB_DELIMITER);

    def test_get_file_extension(self):
        file_extension = HedInputReader.get_file_extension(self.text_file_with_extension);
        self.assertIsInstance(file_extension, basestring);
        self.assertTrue(file_extension);

    def test_file_path_has_extension(self):
        file_extension = HedInputReader.file_path_has_extension(self.text_file_with_extension);
        self.assertIsInstance(file_extension, bool);
        self.assertTrue(file_extension);

    def test_subtract_1_from_dictionary_keys(self):
        one_subtracted_key_dictionary = HedInputReader.subtract_1_from_dictionary_keys(self.integer_key_dictionary);
        self.assertIsInstance(one_subtracted_key_dictionary, dict);
        self.assertTrue(one_subtracted_key_dictionary);
        original_dictionary_key_sum = sum(self.integer_key_dictionary.keys());
        new_dictionary_key_sum = sum(one_subtracted_key_dictionary.keys());
        original_dictionary_key_length = len(self.integer_key_dictionary.keys());
        self.assertEqual(original_dictionary_key_sum - new_dictionary_key_sum, original_dictionary_key_length);

    def test_subtract_1_from_list_elements(self):
        one_subtracted_list = HedInputReader.subtract_1_from_list_elements(self.one_based_tag_columns);
        self.assertIsInstance(one_subtracted_list, list);
        self.assertTrue(one_subtracted_list);
        original_list_sum = sum(self.one_based_tag_columns);
        new_list_sum = sum(one_subtracted_list);
        original_list_length = len(self.one_based_tag_columns);
        self.assertEqual(original_list_sum - new_list_sum, original_list_length);

    def test_split_delimiter_separated_string_with_quotes(self):
        split_string = HedInputReader.split_delimiter_separated_string_with_quotes(
            self.comma_separated_string_with_double_quotes,
            self.comma_delimiter);
        self.assertIsInstance(split_string, list);
        self.assertEqual(split_string, self.comma_delimited_list_with_double_quotes);

    def test_prepend_prefix_to_required_tag_column_if_needed(self):
        prepended_hed_string = HedInputReader.prepend_prefix_to_required_tag_column_if_needed(self.category_tags,
                                                                                              self.category_key);
        self.assertIsInstance(prepended_hed_string, basestring);
        self.assertEqual(prepended_hed_string, self.category_partipant_and_stimulus_tags);

    def test_remove_tag_columns_greater_than_row_column_count(self):
        rows_less_than_row_column_count = HedInputReader.remove_tag_columns_greater_than_row_column_count(
        self.zero_based_row_column_count, self.zero_based_tag_columns);
        self.assertIsInstance(rows_less_than_row_column_count, list);
        self.assertEqual(rows_less_than_row_column_count, self.zero_based_tag_columns_less_than_row_column_count);

    def test_convert_column_to_unicode_if_not(self):
        unicode_value = HedInputReader.convert_column_to_unicode_if_not(self.float_value);
        self.assertIsInstance(unicode_value, unicode)

    def test_get_latest_hed_version_path(self):
        latest_hed_version_path = HedInputReader.get_latest_hed_version_path();
        self. assertIsInstance(latest_hed_version_path, basestring);

    def test_get_all_hed_versions(self):
        hed_versions = HedInputReader.get_all_hed_versions();
        self. assertIsInstance(hed_versions, list);

    def test_get_latest_semantic_version_in_list(self):
        latest_version = HedInputReader.get_latest_semantic_version_in_list(self.semantic_version_list);
        self. assertIsInstance(latest_version, basestring);
        self.assertEqual(latest_version, self.semantic_version_three);

    def test_compare_semantic_versions(self):
        latest_version = HedInputReader.compare_semantic_versions(self.semantic_version_one, self.semantic_version_two);
        self. assertIsInstance(latest_version, basestring);
        self.assertEqual(latest_version, self.semantic_version_two);


if __name__ == '__main__':
    unittest.main();
