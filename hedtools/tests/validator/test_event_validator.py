import random
import unittest
import os

from hed.models.hed_string import HedString
from hed.models.hed_input import HedInput
from hed.errors.error_types import ErrorContext
from hed.models.events_input import EventsInput
from hed.validator.hed_validator import HedValidator
from hed.models.sidecar import Sidecar
from hed.models import model_constants
from hed import schema
from hed.models.def_mapper import DefinitionMapper


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_hed_input = 'Attribute/Temporal/Onset'
        cls.hed_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../schema_cache_test/')
        schema.set_cache_directory(new_cache_dir=cls.hed_cache_dir)
        schema.cache_all_hed_xml_versions()
        hed_schema = schema.load_schema_version(xml_version_number='7.1.1')
        cls.generic_hed_input_reader = HedValidator(hed_schema=hed_schema)
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
        cls.hed_string_with_multiple_unique_tags = HedString('event/label/this is a label,event/label/this is another label')
        cls.hed_string_with_invalid_tags = HedString('this/is/not/a/valid/tag1,this/is/not/a/valid/tag2')
        cls.hed_string_with_no_required_tags = HedString('no/required/tags1,no/required/tags')
        cls.attribute_onset_tag = 'Attribute/Onset'
        cls.category_partipant_and_stimulus_tags = 'Event/Category/Participant response,Event/Category/Stimulus'
        cls.category_tags = 'Participant response, Stimulus'
        cls.validation_issues = []
        cls.column_to_hed_tags_dictionary = {}
        cls.row_with_hed_tags = ['event1', 'tag1', 'tag2']
        cls.row_hed_tag_columns = [1, 2]
        cls.original_and_formatted_tag = [('Event/Label/Test', 'event/label/test'),
                                          ('Event/Description/Test', 'event/description/test')]
        cls.hed_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data')
        cls.hed_filepath_with_errors = os.path.join(cls.hed_base_dir, "ExcelMultipleSheets.xlsx")
        cls.hed_file_with_errors = HedInput(cls.hed_filepath_with_errors)

        cls.hed_filepath_major_errors = os.path.join(cls.hed_base_dir, "bids_events_invalid.tsv")
        cls.hed_file_with_major_errors = HedInput(cls.hed_filepath_major_errors, tag_columns=[3])

        hed_schema2 = schema.load_schema(os.path.join(cls.hed_base_dir, "HED8.0.0-alpha.3_add_currency.xml"))
        cls.generic_hed_input_reader2 = HedValidator(hed_schema=hed_schema2)
        cls.hed_filepath_major_errors_multi_column = os.path.join(cls.hed_base_dir, "bids_events_invalid_columns.tsv")
        cls.hed_file_with_major_errors_multi_column = HedInput(cls.hed_filepath_major_errors_multi_column, tag_columns=[3, 4])

    def test__validate_input(self):
        test_string_obj = HedString(self.base_hed_input)
        validation_issues = test_string_obj.validate(self.generic_hed_input_reader)
        self.assertIsInstance(validation_issues, list)

        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_errors.validate_file(self.generic_hed_input_reader, name=name)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_input_major_errors(self):
        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_major_errors.validate_file(self.generic_hed_input_reader, name=name)

        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_input_major_errors_columns(self):
        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_major_errors.validate_file(self.generic_hed_input_reader2, name=name)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_individual_tags_in_hed_string(self):
        validation_issues = self.generic_hed_input_reader._validate_individual_tags_in_hed_string(self.hed_string_with_invalid_tags)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(validation_issues)

    def test__validate_top_levels_in_hed_string(self):
        validation_issues = self.generic_hed_input_reader._validate_tags_in_hed_string(self.hed_string_with_no_required_tags)
        self.assertIsInstance(validation_issues, list)
        self.assertFalse(validation_issues)

    def test__validate_tag_levels_in_hed_string(self):
        validation_issues = self.generic_hed_input_reader._validate_tags_in_hed_string(self.hed_string_with_multiple_unique_tags)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(validation_issues)

    # def test__append_validation_issues_if_found(self):
    #     row_number = random.randint(0, 100)
    #     self.assertFalse(self.validation_issues)
    #     row_dict = {
    #         model_constants.ROW_HED_STRING: self.hed_string_with_invalid_tags,
    #         model_constants.COLUMN_TO_HED_TAGS: self.column_to_hed_tags_dictionary
    #     }
    #     validation_issues = \
    #         self.generic_hed_input_reader._append_validation_issues_if_found(self.validation_issues,
    #                                                                          row_number,
    #                                                                          row_dict)
    #     self.assertIsInstance(validation_issues, list)
    #     self.assertFalse(validation_issues)
    #
    # def test__append_row_validation_issues_if_found(self):
    #     row_number = random.randint(0, 100)
    #     self.assertFalse(self.validation_issues)
    #     validation_issues = \
    #         self.generic_hed_input_reader._append_row_validation_issues_if_found(self.validation_issues,
    #                                                                              self.column_to_hed_tags_dictionary,
    #                                                                              HedString(""),
    #                                                                              {})
    #     self.assertIsInstance(validation_issues, list)
    #     self.assertFalse(validation_issues)

    def test_complex_file_validation(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.2.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/bids_events.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(validator)
        self.assertEqual(len(issues), 0)
        input_file = EventsInput(events_path, sidecars=sidecar)


        validation_issues = input_file.validate_file_sidecars(validator)
        self.assertEqual(len(validation_issues), 0)
        validation_issues = input_file.validate_file(validator)
        self.assertEqual(len(validation_issues), 0)

    def test_complex_file_validation_invalid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.2.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/bids_events_bad_defs.json")
        sidecar = Sidecar(json_path)
        validator = HedValidator(hed_schema=hed_schema, check_for_warnings=True)
        issues = sidecar.validate_entries(validators=validator)
        self.assertEqual(len(issues), 4)
        input_file = EventsInput(events_path, sidecars=sidecar)

        validation_issues = input_file.validate_file_sidecars(validator)
        self.assertEqual(len(validation_issues), 4)

        validation_issues = input_file.validate_file(validator)
        self.assertEqual(len(validation_issues), 42)

    def test_complex_file_validation_invalid_definitions_removed(self):
        # This verifies definitions are being remvoed from sidecar strings before being added, or it will produce
        # extra errors.
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.2.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/bids_events_bad_defs2.json")
        sidecar = Sidecar(json_path)
        input_file = EventsInput(events_path, sidecars=sidecar)
        validator = HedValidator(hed_schema=hed_schema)

        validation_issues1 = input_file.validate_file_sidecars(validator)
        self.assertEqual(len(validation_issues1), 4)

        validation_issues = input_file.validate_file(validator)
        self.assertEqual(len(validation_issues), 42)

    def test_file_bad_defs_in_spreadsheet(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '../data/HED8.0.0-alpha.3_add_currency.xml')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/hed3_tags_single_sheet_bad_defs.xlsx')
        hed_schema = schema.load_schema(schema_path)

        prefixed_needed_tag_columns = {2: 'Attribute/Informational/Label/', 3: 'Attribute/Informational/Description/'}
        loaded_file = HedInput(events_path, tag_columns=[4],
                               column_prefix_dictionary=prefixed_needed_tag_columns,
                               worksheet_name='LKT Events')

        validator = HedValidator(hed_schema=hed_schema)
        validation_issues = loaded_file.validate_file(validator)
        self.assertEqual(len(validation_issues), 3)

    def test_error_spans_from_file(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.2.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/tag_error_span_test.tsv')

        hed_schema = schema.load_schema(schema_path)

        input_file = HedInput(events_path, tag_columns=[2, 3, "error"])
        validator = HedValidator(hed_schema=hed_schema)
        validation_issues = input_file.validate_file(validator)
        self.assertEqual(validation_issues[1]['char_index'], 6)
        self.assertEqual(validation_issues[2]['char_index'], 6)
        self.assertEqual(len(validation_issues), 3)

    def test_def_mapping_single_line(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.2.mediawiki')
        hed_schema = schema.load_schema(schema_path)
        validator = HedValidator(hed_schema=hed_schema)
        def_mapper = DefinitionMapper()
        string_with_def = '(Definition/TestDefPlaceholder/#,(Item/TestDef1/#,Item/TestDef2)), def/TestDefPlaceholder/2471'
        test_string = HedString(string_with_def)
        issues = test_string.validate([validator, def_mapper], check_for_definitions=True)
        self.assertEqual(len(issues), 0)

        # hed_string_list = [string_with_def, string_with_def]
        # issues = validator.validate_strings(hed_string_list)
        # combined_issues_list = sum(issues, [])
        # self.assertEqual(len(combined_issues_list), 0)
        #
        # # This produces an extra error as the definition isn't known on the second line
        # string_with_def2 = 'def/TestDefPlaceholder/2471'
        # hed_string_list = [string_with_def, string_with_def2]
        # issues = validator.validate_strings(hed_string_list)
        # combined_issues_list = sum(issues, [])
        # self.assertEqual(len(combined_issues_list), 1)

if __name__ == '__main__':
    unittest.main()
