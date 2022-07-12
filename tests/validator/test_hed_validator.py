import unittest
import os

# from hed import
from hed.errors import ErrorContext
from hed import schema
from hed.models import DefMapper, HedString, SpreadsheetInput, TabularInput, Sidecar
from hed.validator import HedValidator


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_hed_input = 'Event'
        cls.hed_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/schema_test_data/')
        schema_filename = os.path.join(cls.hed_base_dir, "HED8.0.0t.xml")
        hed_schema = schema.load_schema(schema_filename)
        cls.hed_schema = hed_schema
        cls.hed_validator = HedValidator(hed_schema=hed_schema)
        cls.validation_issues = []
        cls.hed_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/validator_tests/')
        cls.hed_filepath_with_errors = os.path.join(cls.hed_base_dir, "ExcelMultipleSheets.xlsx")
        cls.hed_file_with_errors = SpreadsheetInput(cls.hed_filepath_with_errors)

        cls.hed_filepath_major_errors = os.path.join(cls.hed_base_dir, "bids_events_invalid.tsv")
        cls.hed_file_with_major_errors = SpreadsheetInput(cls.hed_filepath_major_errors, tag_columns=[1])

        cls.hed_filepath_major_errors_multi_column = os.path.join(cls.hed_base_dir, "bids_events_invalid_columns.tsv")
        cls.hed_file_with_major_errors_multi_column = \
            SpreadsheetInput(cls.hed_filepath_major_errors_multi_column, tag_columns=[1, 2])

    def test__validate_input(self):
        test_string_obj = HedString(self.base_hed_input)
        validation_issues = test_string_obj.validate(self.hed_validator)
        self.assertIsInstance(validation_issues, list)

        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_errors.validate_file(self.hed_validator, name=name)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_input_major_errors(self):
        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_major_errors.validate_file(self.hed_validator, name=name)

        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_input_major_errors_columns(self):
        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_major_errors.validate_file(self.hed_validator,
                                                                          check_for_warnings=True, name=name)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_input_major_errors_multi_column(self):
        validation_issues = self.hed_file_with_major_errors_multi_column.validate_file(self.hed_validator,
                                                                                       check_for_warnings=True)
        self.assertIsInstance(validation_issues, list)
        self.assertEqual(len(validation_issues), 2)

    def test_complex_file_validation_no_index(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_no_index.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(validator)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate_sidecar(validator)
        self.assertEqual(len(validation_issues), 0)
        validation_issues = input_file.validate_file(validator)
        self.assertEqual(len(validation_issues), 0)

    def test_complex_file_validation_with_index(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_no_index.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(validator)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate_sidecar(validator)
        self.assertEqual(len(validation_issues), 0)
        validation_issues = input_file.validate_file(validator)
        self.assertEqual(len(validation_issues), 0)

    def test_complex_file_validation_invalid(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_no_index.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events_bad_defs.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(hed_ops=validator, check_for_warnings=True)
        self.assertEqual(len(issues), 4)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate_sidecar(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 4)

        validation_issues = input_file.validate_file(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 42)

    def test_complex_file_validation_invalid_definitions_removed(self):
        # This verifies definitions are being removed from sidecar strings before being added, or it will produce
        # extra errors.
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_no_index.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events_bad_defs2.json")
        sidecar = Sidecar(json_path)
        input_file = TabularInput(events_path, sidecar=sidecar)
        validator = HedValidator(hed_schema=hed_schema)

        validation_issues1 = input_file.validate_sidecar(validator)
        self.assertEqual(len(validation_issues1), 4)

        validation_issues = input_file.validate_file(validator)
        self.assertEqual(len(validation_issues), 21)

    def test_file_bad_defs_in_spreadsheet(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/schema_test_data/HED8.0.0t.xml')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/hed3_tags_single_sheet_bad_defs.xlsx')
        hed_schema = schema.load_schema(schema_path)

        prefixed_needed_tag_columns = {1: 'Property/Informational-property/Label/',
                                       2: 'Property/Informational-property/Description/'}
        loaded_file = SpreadsheetInput(events_path, tag_columns=[3],
                                       column_prefix_dictionary=prefixed_needed_tag_columns,
                                       worksheet_name='LKT Events')

        validator = HedValidator(hed_schema=hed_schema)
        validation_issues = loaded_file.validate_file(validator, check_for_warnings=True)
        self.assertEqual(len(validation_issues), 4)

    def test_tabular_input_with_HED_col_in_json(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_schema.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/bids_events_HED.tsv')

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../data/validator_tests/bids_events_HED.json")
        validator = HedValidator(hed_schema=hed_schema)
        sidecar = Sidecar(json_path)
        issues = sidecar.validate_entries(validator)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate_sidecar(validator)
        self.assertEqual(len(validation_issues), 0)
        validation_issues = input_file.validate_file(validator)
        self.assertEqual(len(validation_issues), 1)

    def test_error_spans_from_file_and_missing_required_column(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/schema_test_data/HED8.0.0.mediawiki')
        events_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/validator_tests/tag_error_span_test.tsv')

        hed_schema = schema.load_schema(schema_path)

        input_file = SpreadsheetInput(events_path, tag_columns=[0, 1, "error"])
        validator = HedValidator(hed_schema=hed_schema)
        validation_issues = input_file.validate_file(validator)
        self.assertEqual(validation_issues[1]['char_index'], 6)
        self.assertEqual(validation_issues[2]['char_index'], 6)
        self.assertEqual(len(validation_issues), 3)

    # todo: move this test somewhere more appropriate
    def test_org_tag_missing(self):
        test_string_obj = HedString("Event, Item/NotItem")
        removed_tag = test_string_obj.tags()[0]
        test_string_obj.remove([removed_tag])
        from hed import HedTag
        source_span = test_string_obj._get_org_span(removed_tag)
        self.assertEqual(source_span, (0, 5))

        source_span = test_string_obj._get_org_span(HedTag("Event"))
        self.assertEqual(source_span, (None, None))

    def test_def_mapping_single_line(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/schema_test_data/HED8.0.0.mediawiki')
        hed_schema = schema.load_schema(schema_path)
        validator = HedValidator(hed_schema=hed_schema)
        def_mapper = DefMapper()
        string_with_def = \
            '(Definition/TestDefPlaceholder/#,(Item/TestDef1/#,Item/TestDef2)), def/TestDefPlaceholder/2471'
        test_string = HedString(string_with_def)
        issues = test_string.validate([validator, def_mapper], check_for_definitions=True)
        self.assertEqual(len(issues), 0)

    def test_duplicate_group_in_definition(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/schema_test_data/HED8.0.0.mediawiki')
        hed_schema = schema.load_schema(schema_path)
        validator = HedValidator(hed_schema=hed_schema)
        def_mapper = DefMapper()
        string_with_def = \
            '(Definition/TestDef,(Item/TestDef1,Item/TestDef1))'
        test_string = HedString(string_with_def)
        issues = test_string.validate([validator, def_mapper], check_for_definitions=False)
        self.assertEqual(len(issues), 1)


if __name__ == '__main__':
    unittest.main()
