import unittest
import os

from hed.models import ColumnMapper, ColumnType, HedString
from hed.models.sidecar import Sidecar


class Test(unittest.TestCase):
    schema_file = '../data/schema_tests/HED8.0.0t.xml'

    @classmethod
    def setUpClass(cls):
        cls.integer_key_dictionary = {0: 'one', 1: 'two', 2: 'three'}
        cls.zero_based_tag_columns = [0, 1, 2]
        cls.zero_based_row_column_count = 3
        cls.column_prefix_dictionary = {2: 'Event/Description/', 3: 'Event/Label/', 4: 'Event/Category/'}
        cls.category_key = 'Event/Category/'
        cls.category_participant_and_stimulus_tags = \
            HedString('Event/Category/Participant response, Event/Category/Stimulus')

        cls.row_with_hed_tags = ['event1', 'tag1', 'tag2']

        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        cls.basic_events_json = os.path.join(cls.base_data_dir, "sidecar_tests/both_types_events.json")
        cls.basic_event_name = "trial_type"
        cls.basic_event_type = ColumnType.Categorical
        cls.basic_hed_tags_column = "onset"
        cls.basic_column_map = ["onset", "duration", "trial_type", "response_time", " stim_file"]
        cls.basic_event_row = ["1.2", "0.6", "go", "1.435", "images/red_square.jpg"]
        cls.basic_event_row_invalid = ["1.2", "0.6", "invalid_category_key", "1.435", "images/red_square.jpg"]

        cls.add_column_name = "TestColumn"
        cls.add_column_number = 0
        cls.hed_string = "Event/Label/#"
        cls.test_column_map = ["TestColumn"]
        cls.required_prefix = "TestRequiredPrefix/"
        cls.complex_hed_tag_required_prefix = \
            "TestRequiredPrefix/ThisIsAHedTag, (TestRequiredPrefix/NewTag, TestRequiredPrefix/NewTag3)"
        cls.complex_hed_tag_no_prefix = "ThisIsAHedTag,(NewTag,NewTag3)"

        cls.short_tag_key = 'Item/Language-item/Character/'
        cls.short_tag_with_missing_prefix = "D"
        cls.short_tag_partial_prefix = 'Language-item/Character/'
        cls.short_tag_partial_prefix2 = 'Character/'

    def test_set_tag_columns(self):
        mapper = ColumnMapper()
        mapper.set_tag_columns(self.zero_based_tag_columns, finalize_mapping=True)
        self.assertTrue(len(mapper._final_column_map) >= 2)

    def test_optional_column(self):
        mapper = ColumnMapper()
        mapper.set_tag_columns(tag_columns=["HED"])
        mapper.set_column_map({1: "HED"})
        self.assertTrue(len(mapper._final_column_map) == 1)

        mapper = ColumnMapper()
        mapper.set_requested_columns(requested_columns=["HED"])
        mapper.set_column_map({1: "HED"})
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper._finalize_mapping_issues) == 0)

        mapper = ColumnMapper()
        mapper.set_tag_columns(optional_tag_columns=["HED"])
        mapper.set_column_map({1: "HED"})
        self.assertTrue(len(mapper._final_column_map) == 1)

        mapper = ColumnMapper()
        mapper.set_tag_columns(tag_columns=["HED"])
        self.assertTrue(len(mapper._final_column_map) == 0)
        self.assertTrue(len(mapper._finalize_mapping_issues) == 1)

        mapper = ColumnMapper()
        mapper.set_requested_columns(requested_columns=["HED"])
        self.assertTrue(len(mapper._final_column_map) == 0)
        self.assertTrue(len(mapper._finalize_mapping_issues) == 1)

        mapper = ColumnMapper()
        mapper.set_tag_columns(optional_tag_columns=["HED"])
        self.assertTrue(len(mapper._final_column_map) == 0)
        self.assertTrue(len(mapper._finalize_mapping_issues) == 0)

    def test_add_json_file_events(self):
        mapper = ColumnMapper()
        mapper._set_sidecar(Sidecar(self.basic_events_json))
        self.assertTrue(len(mapper.column_data) >= 2)

    def test__detect_event_type(self):
        mapper = ColumnMapper()
        mapper._set_sidecar(Sidecar(self.basic_events_json))
        self.assertTrue(mapper.column_data[self.basic_event_name].column_type == self.basic_event_type)

    def test_add_hed_tags_columns(self):
        mapper = ColumnMapper()
        mapper.add_columns([self.add_column_name], ColumnType.HEDTags)
        self.assertTrue(len(mapper.column_data) >= 1)

    def test__add_single_event_type(self):
        mapper = ColumnMapper()
        mapper.add_columns([self.add_column_name], ColumnType.Value)
        self.assertTrue(len(mapper.column_data) >= 1)

    def test_set_column_map(self):
        mapper = ColumnMapper()
        mapper.add_columns([self.add_column_name], ColumnType.Value)
        mapper.set_column_map(self.test_column_map)
        self.assertTrue(len(mapper._final_column_map) >= 1)

    def test__finalize_mapping(self):
        mapper = ColumnMapper()
        mapper.add_columns([self.add_column_number], ColumnType.Value)
        mapper._finalize_mapping()
        self.assertTrue(len(mapper._final_column_map) >= 1)



if __name__ == '__main__':
    unittest.main()
