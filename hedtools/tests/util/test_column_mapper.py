import unittest
import os

from hed.util.column_mapper import ColumnMapper, ColumnType, ColumnDef

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.event_mapper = ColumnMapper()
        cls.integer_key_dictionary = {1: 'one', 2: 'two', 3: 'three'}
        cls.one_based_tag_columns = [1, 2, 3]
        cls.zero_based_row_column_count = 3
        cls.column_prefix_dictionary = {3: 'Event/Description/', 4: 'Event/Label/', 5: 'Event/Category/'}
        cls.category_key = 'Event/Category/'
        cls.category_partipant_and_stimulus_tags = 'Event/Category/Participant response, Event/Category/Stimulus'
        cls.category_tags = 'Participant response, Stimulus'
        cls.row_with_hed_tags = ['event1', 'tag1', 'tag2']

        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        cls.basic_events_json = os.path.join(cls.base_data_dir, "both_types_events.json")
        cls.basic_event_name = "trial_type"
        cls.basic_event_type = ColumnType.Categorical
        cls.basic_attribute_column = "onset"
        cls.basic_column_map = ["onset", "duration", "trial_type", "response_time", " stim_file"]
        cls.basic_event_row = ["1.2", "0.6", "go", "1.435", "images/red_square.jpg"]

        cls.add_column_name = "TestColumn"
        cls.add_column_number = 0
        cls.hed_string = "Event/Label/#"
        cls.test_column_map = ["TestColumn"]
        cls.required_prefix = "TestRequiredPrefix/"
        cls.complex_hed_tag_required_prefix = "TestRequiredPrefix/ThisIsAHedTag, (TestRequiredPrefix/NewTag, TestRequiredPrefix/NewTag3)"
        cls.complex_hed_tag_no_prefix = "ThisIsAHedTag, (NewTag, NewTag3)"

    def test_set_column_prefix_dict(self):
        mapper = ColumnMapper()
        mapper.set_column_prefix_dict(self.column_prefix_dictionary, True)
        self.assertTrue(len(mapper._final_column_map) == 3)

    def test_set_tag_columns(self):
        mapper = ColumnMapper()
        mapper.set_tag_columns(self.one_based_tag_columns, True)
        self.assertTrue(len(mapper._final_column_map) >= 2)

    def test_add_json_file_events(self):
        mapper = ColumnMapper()
        mapper.add_json_file_defs(self.basic_events_json)
        self.assertTrue(len(mapper.column_defs) >= 2)

    def test__detect_event_type(self):
        mapper = ColumnMapper()
        mapper.add_json_file_defs(self.basic_events_json)
        self.assertTrue(mapper.column_defs[self.basic_event_name].column_type == self.basic_event_type)

    # def test_add_value_column(self):
    #     mapper = ColumnMapper()
    #     mapper.add_value_column(self.add_column_name, self.hed_string)
    #     self.assertTrue(len(mapper.column_defs) >= 1)

    def test_add_attribute_columns(self):
        mapper = ColumnMapper()
        mapper.add_columns([self.add_column_name], ColumnType.Attribute)
        self.assertTrue(len(mapper.column_defs) >= 1)

    # def test_add_hedtag_columns(self):
    #     mapper = ColumnMapper()
    #     mapper.add_hedtag_columns(self.add_column_name)
    #     self.assertTrue(len(mapper.column_defs) >= 1)
    #
    # def test_add_ignore_columns(self):
    #     mapper = ColumnMapper()
    #     mapper.add_ignore_columns(self.add_column_name)
    #     self.assertTrue(len(mapper.column_defs) >= 1)

    def test__add_single_event_type(self):
        mapper = ColumnMapper()
        mapper.add_columns([self.add_column_name], ColumnType.Value)
        self.assertTrue(len(mapper.column_defs) >= 1)

    def test_set_column_map(self):
        mapper = ColumnMapper()
        mapper.add_columns([self.add_column_name], ColumnType.Value)
        mapper.set_column_map(self.test_column_map)
        self.assertTrue(len(mapper._final_column_map) >= 1)

    def test__set_column_prefix(self):
        mapper = ColumnMapper()
        mapper._set_column_prefix(self.add_column_number, self.required_prefix)
        self.assertTrue(len(mapper._final_column_map) >= 1)

        mapper = ColumnMapper()
        with self.assertRaises(TypeError):
            mapper._set_column_prefix(self.add_column_name, self.required_prefix)

    def test__finalize_mapping(self):
        mapper = ColumnMapper()
        mapper.add_columns([self.add_column_number], ColumnType.Value)
        mapper._finalize_mapping()
        self.assertTrue(len(mapper._final_column_map) >= 1)

    def test_expand_column(self):
        mapper = ColumnMapper()
        mapper.add_json_file_defs(self.basic_events_json)
        mapper.set_column_map(self.basic_column_map)
        expanded_column = mapper._expand_column(2, "go")
        self.assertTrue(isinstance(expanded_column[0], str))

    def test_expand_row_tags(self):
        mapper = ColumnMapper()
        mapper.add_json_file_defs(self.basic_events_json)
        mapper.add_columns(self.basic_attribute_column)
        mapper.set_column_map(self.basic_column_map)
        expanded_row = mapper.expand_row_tags(self.basic_event_row)
        self.assertTrue(isinstance(expanded_row, dict))
        self.assertTrue(self.basic_attribute_column in expanded_row)


    def test_remove_prefix_if_needed(self):
        mapper = ColumnMapper()
        mapper.set_column_prefix_dict({self.add_column_number: self.required_prefix})
        no_prefix_string = mapper.remove_prefix_if_needed(self.add_column_number, self.complex_hed_tag_required_prefix)
        self.assertEqual(no_prefix_string, self.complex_hed_tag_no_prefix)

    def test_subtract_1_from_dictionary_keys(self):
        one_subtracted_key_dictionary = self.event_mapper._subtract_1_from_dictionary_keys(self.integer_key_dictionary)
        self.assertIsInstance(one_subtracted_key_dictionary, dict)
        self.assertTrue(one_subtracted_key_dictionary)
        original_dictionary_key_sum = sum(self.integer_key_dictionary.keys())
        new_dictionary_key_sum = sum(one_subtracted_key_dictionary.keys())
        original_dictionary_key_length = len(self.integer_key_dictionary.keys())
        self.assertEqual(original_dictionary_key_sum - new_dictionary_key_sum, original_dictionary_key_length)

    def test_subtract_1_from_list_elements(self):
        one_subtracted_list = self.event_mapper._subtract_1_from_list_elements(self.one_based_tag_columns)
        self.assertIsInstance(one_subtracted_list, list)
        self.assertTrue(one_subtracted_list)
        original_list_sum = sum(self.one_based_tag_columns)
        new_list_sum = sum(one_subtracted_list)
        original_list_length = len(self.one_based_tag_columns)
        self.assertEqual(original_list_sum - new_list_sum, original_list_length)

    def test__prepend_prefix_to_required_tag_column_if_needed(self):
        prepended_hed_string = ColumnDef._prepend_prefix_to_required_tag_column_if_needed(
            self.category_tags, self.category_key)
        self.assertIsInstance(prepended_hed_string, str)
        self.assertEqual(prepended_hed_string, self.category_partipant_and_stimulus_tags)


if __name__ == '__main__':
    unittest.main()
