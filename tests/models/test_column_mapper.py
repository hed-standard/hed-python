import unittest
import os

from hed.models import ColumnMapper, ColumnType, HedString
from hed.models.sidecar import Sidecar
from hed.errors import ValidationErrors
from hed import load_schema

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        schema_file = 'schema_tests/HED8.0.0t.xml'

        cls.hed_schema = load_schema(os.path.join(base_data_dir, schema_file))
        cls.integer_key_dictionary = {0: 'one', 1: 'two', 2: 'three'}
        cls.zero_based_row_column_count = 3
        cls.column_prefix_dictionary = {2: 'Event/Description/', 3: 'Event/Label/', 4: 'Event/Category/'}
        cls.category_key = 'Event/Category/'
        cls.category_participant_and_stimulus_tags = \
            HedString('Event/Category/Participant response, Event/Category/Stimulus', cls.hed_schema)

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
        zero_based_tag_columns = [0, 1, 2]
        mapper.set_tag_columns(zero_based_tag_columns, finalize_mapping=True)
        self.assertTrue(len(mapper._final_column_map) == 3)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 0)

    def test_set_tag_columns_named(self):
        mapper = ColumnMapper(warn_on_missing_column=True)
        named_columns = ["Col1", "Col2", "Col3"]
        mapper.set_tag_columns(named_columns)
        mapper.set_column_map(named_columns)
        self.assertTrue(len(mapper._final_column_map) == 3)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 0)

    def test_set_tag_columns_named_unknown(self):
        mapper = ColumnMapper(warn_on_missing_column=True)
        two_columns = ["Col1", "Col2"]
        named_columns = ["Col1", "Col2", "Col3"]
        mapper.set_tag_columns(two_columns)
        mapper.set_column_map(named_columns)
        self.assertTrue(len(mapper._final_column_map) == 2)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[0]['code'] == ValidationErrors.HED_UNKNOWN_COLUMN)

    def test_set_tag_columns_mixed(self):
        mapper = ColumnMapper()
        mixed_columns = ["Col1", "Col2", 2]
        column_map = ["Col1", "Col2", "Col3"]
        mapper.set_tag_columns(mixed_columns)
        mapper.set_column_map(column_map)
        self.assertTrue(len(mapper._final_column_map) == 3)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 0)

    def test_set_tag_column_missing(self):
        mapper = ColumnMapper()
        column_map = ["Col1", "Col2", "Col3"]
        mapper.set_tag_columns(["Col1", "Col4"])
        mapper.set_column_map(column_map)
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[0]['code'] == ValidationErrors.HED_MISSING_REQUIRED_COLUMN)

        column_map = ["Col1", "Col2", "Col3"]
        mapper.set_tag_columns(optional_tag_columns=["Col1", "Col4"])
        mapper.set_column_map(column_map)
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 0)


    def test_sidecar_and_columns(self):
        mapper = ColumnMapper(Sidecar(self.basic_events_json))
        mapper.set_tag_columns(["Invalid", "Invalid2"])
        mapper.set_column_map(["Invalid", "Invalid2"])
        self.assertTrue(len(mapper._final_column_map) == 2)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[0]['code'] == ValidationErrors.SIDECAR_AND_OTHER_COLUMNS)

    def test_duplicate_list(self):
        mapper = ColumnMapper()
        mapper.set_tag_columns(["Invalid", "Invalid"])
        self.assertTrue(len(mapper._final_column_map) == 0)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 3)
        self.assertTrue(mapper.check_for_mapping_issues()[-1]['code'] == ValidationErrors.DUPLICATE_COLUMN_IN_LIST)

        mapper.set_tag_columns([0, 0])
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[-1]['code'] == ValidationErrors.DUPLICATE_COLUMN_IN_LIST)

        mapper.set_tag_columns([0, "Column1"])
        mapper.set_column_map(["Column1"])
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[-1]['code'] == ValidationErrors.DUPLICATE_COLUMN_IN_LIST)

    def test_duplicate_prefix(self):
        mapper = ColumnMapper()
        prefix_dict = {
            0: "Label/",
            "Column1": "Description"
        }
        mapper.set_column_prefix_dictionary(prefix_dict)
        mapper.set_column_map(["Column1"])
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[-1]['code'] == ValidationErrors.DUPLICATE_COLUMN_IN_LIST)

    def test_duplicate_cross_lists(self):
        mapper = ColumnMapper()
        prefix_dict = {
            0: "Label/"
        }
        mapper.set_tag_columns([0])
        mapper.set_column_prefix_dictionary(prefix_dict)
        mapper.set_column_map(["Column1"])
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[-1]['code'] == ValidationErrors.DUPLICATE_COLUMN_BETWEEN_SOURCES)

        mapper = ColumnMapper()
        prefix_dict = {
            "Column1": "Label/"
        }
        mapper.set_tag_columns([0])
        mapper.set_column_prefix_dictionary(prefix_dict)
        mapper.set_column_map(["Column1"])
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[-1]['code'] == ValidationErrors.DUPLICATE_COLUMN_BETWEEN_SOURCES)


        mapper.set_tag_columns(["Column1"])
        self.assertTrue(len(mapper._final_column_map) == 1)
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 1)
        self.assertTrue(mapper.check_for_mapping_issues()[-1]['code'] == ValidationErrors.DUPLICATE_COLUMN_BETWEEN_SOURCES)

    def test_blank_column(self):
        mapper = ColumnMapper()
        mapper.set_column_map(["", None])
        self.assertTrue(len(mapper.check_for_mapping_issues()) == 2)
        self.assertTrue(mapper.check_for_mapping_issues(allow_blank_names=False)[1]['code'] == ValidationErrors.HED_BLANK_COLUMN)
        self.assertTrue(mapper.check_for_mapping_issues(allow_blank_names=False)[1]['code'] == ValidationErrors.HED_BLANK_COLUMN)

    def test_optional_column(self):
        mapper = ColumnMapper()
        mapper.set_tag_columns(tag_columns=["HED"])
        mapper.set_column_map({1: "HED"})
        self.assertTrue(len(mapper._final_column_map) == 1)

        mapper = ColumnMapper()
        mapper.set_tag_columns(optional_tag_columns=["HED"])
        mapper.set_column_map({1: "HED"})
        self.assertTrue(len(mapper._final_column_map) == 1)

        mapper = ColumnMapper()
        mapper.set_tag_columns(tag_columns=["HED"])
        self.assertTrue(len(mapper._final_column_map) == 0)
        self.assertTrue(len(mapper.get_column_mapping_issues()) == 1)

        mapper = ColumnMapper()
        mapper.set_tag_columns(optional_tag_columns=["HED"])
        self.assertTrue(len(mapper._final_column_map) == 0)
        self.assertTrue(len(mapper.get_column_mapping_issues()) == 0)

    def test_add_json_file_events(self):
        mapper = ColumnMapper()
        mapper._set_sidecar(Sidecar(self.basic_events_json))
        self.assertTrue(len(mapper.sidecar_column_data) >= 2)

    def test__detect_event_type(self):
        mapper = ColumnMapper()
        mapper._set_sidecar(Sidecar(self.basic_events_json))
        self.assertTrue(mapper.sidecar_column_data[self.basic_event_name].column_type == self.basic_event_type)

    def test_tag_mapping_complex(self):
        tag_columns = [0]
        column_prefix_dictionary = {1: "Label/"}
        optional_tag_columns = [2]
        mapper = ColumnMapper(tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary, optional_tag_columns=optional_tag_columns)
        self.assertEqual(list(mapper._final_column_map), [0, 1, 2])
        self.assertEqual(mapper._final_column_map[0].column_type, ColumnType.HEDTags)
        self.assertEqual(mapper._final_column_map[1].column_type, ColumnType.Value)
        self.assertEqual(mapper._final_column_map[1].hed_dict, "Label/#")
        self.assertEqual(mapper._final_column_map[2].column_type, ColumnType.HEDTags)



if __name__ == '__main__':
    unittest.main()
