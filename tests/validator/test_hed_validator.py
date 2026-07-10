import unittest
import os

# from hed import
from hed.errors import ErrorContext, ErrorSeverity
from hed import schema
from hed.models import HedString, SpreadsheetInput, TabularInput, Sidecar
from hed.validator import HedValidator


# todo: redo all this so we
class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_hed_input = "Event"
        cls.hed_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/")
        schema_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED8.1.0.xml")
        )
        # hed_schema = schema.load_schema(schema_filename)
        hed_schema = schema.load_schema(schema_path)
        cls.hed_schema = hed_schema
        cls.hed_validator = HedValidator(hed_schema=hed_schema)
        cls.validation_issues = []
        cls.hed_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/validator_tests/")
        cls.hed_filepath_with_errors = os.path.join(cls.hed_base_dir, "ExcelMultipleSheets.xlsx")
        cls.hed_file_with_errors = SpreadsheetInput(cls.hed_filepath_with_errors, tag_columns=[1])

        cls.hed_filepath_major_errors = os.path.join(cls.hed_base_dir, "bids_events_invalid.tsv")
        cls.hed_file_with_major_errors = SpreadsheetInput(cls.hed_filepath_major_errors, tag_columns=[1])

        cls.hed_filepath_major_errors_multi_column = os.path.join(cls.hed_base_dir, "bids_events_invalid_columns.tsv")
        cls.hed_file_with_major_errors_multi_column = SpreadsheetInput(
            cls.hed_filepath_major_errors_multi_column, tag_columns=[1, 2]
        )

    def test__validate_input(self):
        test_string_obj = HedString(self.base_hed_input, self.hed_schema)
        validation_issues = test_string_obj.validate(self.hed_schema)
        self.assertIsInstance(validation_issues, list)

        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_errors.validate(self.hed_schema, name=name)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_input_major_errors(self):
        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_major_errors.validate(self.hed_schema, name=name)

        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_input_major_errors_columns(self):
        name = "DummyDisplayFilename.txt"
        validation_issues = self.hed_file_with_major_errors.validate(self.hed_schema, name=name)
        self.assertIsInstance(validation_issues, list)
        self.assertTrue(name in validation_issues[0][ErrorContext.FILE_NAME])

    def test__validate_input_major_errors_multi_column(self):
        validation_issues = self.hed_file_with_major_errors_multi_column.validate(self.hed_schema)
        self.assertIsInstance(validation_issues, list)
        self.assertEqual(len(validation_issues), 2)

    def test_complex_file_validation_no_index(self):
        events_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events_no_index.tsv")
        )
        json_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events.json")
        )
        sidecar = Sidecar(json_path)
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate(self.hed_schema)
        self.assertEqual(len(validation_issues), 0)

    def test_complex_file_validation_with_index(self):
        events_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events_no_index.tsv")
        )

        # hed_schema = schema.load_schema(schema_path)
        json_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events.json")
        )
        sidecar = Sidecar(json_path)
        issues = sidecar.validate(hed_schema=self.hed_schema)
        self.assertEqual(len(issues), 0)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate(hed_schema=self.hed_schema)
        self.assertEqual(len(validation_issues), 0)

    def test_complex_file_validation_invalid(self):
        # todo: Update or remove
        schema_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_schema.mediawiki")
        )
        events_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events_no_index.tsv")
        )

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events_bad_defs.json")
        )
        sidecar = Sidecar(json_path)
        issues = sidecar.validate(hed_schema)
        filtered_issues = [issue for issue in issues if issue["severity"] < ErrorSeverity.WARNING]
        self.assertEqual(len(filtered_issues), 10)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate(hed_schema)
        self.assertEqual(len(validation_issues), 105)

    def test_complex_file_validation_invalid_definitions_removed(self):
        # todo: update this/remove
        # This verifies definitions are being removed from sidecar strings before being added, or it will produce
        # extra errors.
        schema_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_schema.mediawiki")
        )
        events_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/validator_tests/bids_events_no_index.tsv"
        )

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events_bad_defs2.json")
        )
        sidecar = Sidecar(json_path)
        issues = sidecar.validate(hed_schema)
        self.assertEqual(len(issues), 8)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate(hed_schema)
        self.assertEqual(len(validation_issues), 42)

    def test_file_bad_defs_in_spreadsheet(self):
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED8.0.0t.xml")
        events_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/validator_tests/hed3_tags_single_sheet_bad_defs.xlsx"
        )
        hed_schema = schema.load_schema(schema_path)

        prefixed_needed_tag_columns = {
            1: "Property/Informational-property/Label/",
            2: "Property/Informational-property/Description/",
        }
        loaded_file = SpreadsheetInput(
            events_path,
            tag_columns=[3],
            column_prefix_dictionary=prefixed_needed_tag_columns,
            worksheet_name="LKT Events",
        )

        validation_issues = loaded_file.validate(hed_schema=hed_schema)
        self.assertEqual(len(validation_issues), 5)

    def test_tabular_input_with_HED_col_in_json(self):
        schema_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_schema.mediawiki")
        )
        events_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events_HED.tsv")
        )

        hed_schema = schema.load_schema(schema_path)
        json_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/validator_tests/bids_events_HED.json")
        )
        sidecar = Sidecar(json_path)
        issues = sidecar.validate(hed_schema)
        self.assertEqual(len(issues), 1)
        input_file = TabularInput(events_path, sidecar=sidecar)

        validation_issues = input_file.validate(hed_schema)
        self.assertEqual(len(validation_issues), 1)

    def test_error_spans_from_file_and_missing_required_column(self):
        events_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/validator_tests/tag_error_span_test.tsv"
        )

        input_file = SpreadsheetInput(events_path, tag_columns=[0, 1, "error"])
        validation_issues = input_file.validate(hed_schema=self.hed_schema)
        self.assertEqual(validation_issues[1]["char_index"], 6)
        self.assertEqual(validation_issues[2]["char_index"], 6)
        self.assertEqual(len(validation_issues), 3)

    # todo: move this test somewhere more appropriate
    def test_org_tag_missing(self):
        test_string_obj = HedString("Event, Item/NotItem", self.hed_schema)
        removed_tag = test_string_obj.tags()[0]
        test_string_obj.remove([removed_tag])
        from hed import HedTag

        source_span = test_string_obj._get_org_span(removed_tag)
        self.assertEqual(source_span, (0, 5))

        source_span = test_string_obj._get_org_span(HedTag("Event", self.hed_schema))
        self.assertEqual(source_span, (None, None))

    def test_duplicate_group_in_definition(self):
        schema_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED8.2.0.mediawiki"
        )
        hed_schema = schema.load_schema(schema_path)
        string_with_def = "(Definition/TestDef,(Item,Item))"
        test_string = HedString(string_with_def, hed_schema)
        issues = test_string.validate(hed_schema)
        self.assertEqual(len(issues), 1)

    def test_severity_enum_not_string_github_hedit_161(self):
        """Regression test for critical bug: severity should be ErrorSeverity enum, not string.

        GitHub issue: Annotation-Garden/HEDit#161
        Bug: Downstream code comparing issue["severity"] == "error" always fails because
        hedtools returns ErrorSeverity.ERROR (enum=1), not the string "error".

        This test verifies:
        1. Invalid HED strings return errors with ErrorSeverity.ERROR (enum), not string
        2. Valid HED strings don't return errors
        3. Severity values can be compared to ErrorSeverity enum
        """
        from hed.errors.error_reporter import check_for_any_errors

        # Test 1: Invalid HED string (bare non-schema tag without extension)
        # "Sky" is invalid because it's not in schema and has no extension
        invalid_string = "Sensory-event, Sky"
        test_string_obj = HedString(invalid_string, self.hed_schema)
        issues = test_string_obj.validate(self.hed_schema)

        # Should have at least one error
        self.assertGreater(len(issues), 0, "Invalid HED string should produce validation errors")

        # Verify severity is enum, not string
        for issue in issues:
            severity = issue.get("severity")
            # Severity should be the ErrorSeverity enum itself, not a plain int or a string.
            # (assertIsInstance(severity, int) would also pass for a bare int, since
            # ErrorSeverity is an IntEnum - that wouldn't actually lock in the enum contract.)
            self.assertIsInstance(severity, ErrorSeverity, f"Severity should be ErrorSeverity enum, not {type(severity)}")
            # Should be comparable to ErrorSeverity enum
            self.assertTrue(
                severity == ErrorSeverity.ERROR or severity == ErrorSeverity.WARNING,
                f"Severity {severity} should equal ErrorSeverity.ERROR (1) or ErrorSeverity.WARNING (10)",
            )

        # check_for_any_errors should return True (indicating errors exist)
        self.assertTrue(check_for_any_errors(issues), "check_for_any_errors should return True for invalid HED string")

        # Test 2: Valid HED string
        valid_string = "Event"
        test_string_obj = HedString(valid_string, self.hed_schema)
        issues = test_string_obj.validate(self.hed_schema)

        # Should have no errors
        error_issues = [issue for issue in issues if issue.get("severity", ErrorSeverity.ERROR) <= ErrorSeverity.ERROR]
        self.assertEqual(len(error_issues), 0, "Valid HED string 'Event' should not produce errors")

        # check_for_any_errors should return False (no errors)
        self.assertFalse(check_for_any_errors(issues), "check_for_any_errors should return False for valid HED string")

        # Test 3: Verify downstream consumers can correctly filter errors by severity enum
        invalid_string_obj = HedString("Sensory-event, Sky", self.hed_schema)
        invalid_issues = invalid_string_obj.validate(self.hed_schema)

        # Simulate what downstream code should do (compare to enum, not string)
        error_count = sum(
            1 for issue in invalid_issues if issue.get("severity", ErrorSeverity.ERROR) == ErrorSeverity.ERROR
        )
        self.assertGreater(
            error_count, 0, "Should detect at least one error when comparing to ErrorSeverity.ERROR enum"
        )

        # Show that comparing to string "error" would fail (the bug)
        error_count_string = sum(1 for issue in invalid_issues if issue.get("severity") == "error")
        self.assertEqual(error_count_string, 0, "Comparing to string 'error' incorrectly returns 0 errors (the bug)")


if __name__ == "__main__":
    unittest.main()
