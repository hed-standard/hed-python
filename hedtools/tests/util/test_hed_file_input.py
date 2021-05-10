import unittest
import os

from hed.util.hed_file_input import HedFileInput
from hed.util.hed_string import HedString
from hed.schema import load_schema
from hed.util.column_def_group import ColumnDefGroup
from hed.util.event_file_input import EventFileInput


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

        for row_number, column_to_hed_tags in file_input:
            breakHere = 3
        breakHere = 3
        # Just make sure this didn't crash for now
        self.assertTrue(True)


    def test_get_row_hed_tags(self):
        row_dict = self.generic_file_input._get_dict_from_row_hed_tags(self.row_with_hed_tags, self.generic_file_input._mapper)
        hed_string, column_to_hed_tags_dictionary = self.generic_file_input._get_row_hed_tags_from_dict(row_dict)
        self.assertIsInstance(hed_string, HedString)
        self.assertTrue(hed_string)
        self.assertIsInstance(column_to_hed_tags_dictionary, dict)
        self.assertTrue(column_to_hed_tags_dictionary)

    def test_file_as_string(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.2.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        hed_schema = load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/bids_events.json")
        column_group = ColumnDefGroup(json_path)
        def_dict, def_issues = column_group.extract_defs(hed_schema)
        self.assertEqual(len(def_issues), 0)
        input_file = EventFileInput(events_path, json_def_files=column_group,
                                    hed_schema=hed_schema, def_dicts=def_dict)

        events_file_as_string = "".join([line for line in open(events_path)])
        input_file_from_string = EventFileInput(events_path, json_def_files=column_group,
                                                hed_schema=hed_schema, def_dicts=def_dict,
                                                data_as_csv_string=events_file_as_string)

        for (row_number, column_dict), (row_number2, column_dict) in zip(input_file, input_file_from_string):
            self.assertEqual(row_number, row_number2)
            self.assertEqual(column_dict, column_dict)

    # Add more tests here


if __name__ == '__main__':
    unittest.main()
