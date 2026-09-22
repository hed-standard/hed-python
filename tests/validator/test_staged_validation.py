"""The four stages of SpreadsheetValidator, their stops, and the DataFrame-free path."""

import io
import json
import unittest

from hed import Sidecar, SpreadsheetInput, TabularInput, load_schema_version
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ErrorContext, ValidationErrors
from hed.models import DefinitionDict, ListColumnSource
from hed.validator import SpreadsheetValidator
from hed.validator.spreadsheet_validator import ROW_COUNT_KEY


def _sidecar(sidecar_dict, name=None):
    return Sidecar(io.BytesIO(json.dumps(sidecar_dict).encode("utf-8")), name=name)


def _tabular(rows, sidecar=None, name=None):
    text = "".join("\t".join(str(x) for x in row) + "\n" for row in rows)
    return TabularInput(io.BytesIO(text.encode("utf-8")), sidecar=sidecar, name=name)


class TestStagedValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.4.0")
        cls.validator = SpreadsheetValidator(cls.schema)
        cls.sidecar_dict = {
            "event_code": {"HED": {"face": "(Red, Blue), (Green, (Yellow))", "ball": "{response_time}, Def/Acc/3.5"}},
            "response_time": {"HED": "Distance/# m"},
        }
        cls.definitions = DefinitionDict(["(Definition/Acc/#, (Acceleration/# m-per-s^2, Red))"], cls.schema)

    def test_stages_run_without_a_dataframe(self):
        """A ListColumnSource with no BaseInput runs stages 1-3 and stops before assembly; rows are 0-based."""
        source = ListColumnSource(
            {
                "onset": [4.5, 5.0, 5.5, 6.0],
                "response_time": ["3.4", "abc", "abc", "n/a"],
                "event_code": ["face", "ball", "face", "face"],
                "HED": ["Sensory-event", "n/a", "Sensory-event", "InvalidTagXYZ"],
            }
        )
        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.TABLE_NAME, "trials")

        issues = self.validator.validate(
            source, sidecar=_sidecar(self.sidecar_dict), extra_def_dicts=self.definitions, error_handler=error_handler
        )

        # Stage 2 finds the bad value and stops, so the invalid tag in the HED column is not reported.
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.VALUE_INVALID])
        self.assertEqual(issues[0][ErrorContext.ROW], 1)
        self.assertEqual(issues[0][ErrorContext.COLUMN], "response_time")
        self.assertEqual(issues[0][ROW_COUNT_KEY], 2)
        self.assertEqual(issues[0].get("ec_table_name"), "trials")
        self.assertNotIn("ec_filename", issues[0])
        self.assertEqual(error_handler.error_context, [(ErrorContext.TABLE_NAME, "trials")])

        # With the value fixed, stage 3 reports the invalid tag, and with no BaseInput the run ends there.
        source = ListColumnSource(
            {
                "onset": [4.5, 5.0],
                "response_time": ["3.4", "n/a"],
                "event_code": ["face", "ball"],
                "HED": ["InvalidTagXYZ", "InvalidTagXYZ"],
            }
        )
        issues = self.validator.validate(source, sidecar=_sidecar(self.sidecar_dict), extra_def_dicts=self.definitions)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TAG_INVALID])
        self.assertEqual(issues[0][ErrorContext.ROW], 0)
        self.assertEqual(issues[0][ROW_COUNT_KEY], 2)

    def test_referenced_column_values_checked_in_every_row(self):
        """A value column that curly braces reference is checked in every row, once per distinct value.

        Row 3 (file line 4) selects the face template, which does not substitute {response_time}, so before
        the column stage the bad value in that row was silently dropped with the column.
        """
        rows = [
            ["onset", "duration", "response_time", "event_code"],
            ["4.5", "0", "3.4", "face"],
            ["5.0", "0", "abc", "ball"],
            ["5.5", "0", "abc", "face"],
            ["6.0", "0", "n/a", "face"],
        ]
        events = _tabular(rows, _sidecar(self.sidecar_dict))
        issues = events.validate(self.schema, extra_def_dicts=self.definitions)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.VALUE_INVALID])
        self.assertEqual(issues[0][ErrorContext.ROW], 3)
        self.assertEqual(issues[0][ErrorContext.COLUMN], "response_time")
        self.assertEqual(issues[0][ROW_COUNT_KEY], 2)
        # Assembly itself is unchanged: the unused value is still not part of the face rows.
        self.assertNotIn("Distance", events.series_a.iloc[2])
        self.assertIn("Distance/abc m", events.series_a.iloc[1])

    def test_sidecar_errors_stop_the_run(self):
        sidecar = _sidecar({"event_code": {"HED": {"face": "InvalidTagXYZ", "ball": "Red"}}}, name="events.json")
        rows = [["onset", "duration", "event_code", "HED"], ["4.5", "0", "face", "InvalidTagABC"]]
        error_handler = ErrorHandler()

        issues = _tabular(rows, sidecar, name="events.tsv").validate(self.schema, error_handler=error_handler)

        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TAG_INVALID])
        self.assertEqual(issues[0][ErrorContext.SIDECAR_COLUMN_NAME], "event_code")
        self.assertEqual(issues[0]["ec_filename"], "events.json")
        self.assertEqual(error_handler.error_context, [])

        # validate_sidecar=False trusts the caller's own sidecar check and goes on to the columns.
        issues = _tabular(rows, sidecar, name="events.tsv").validate(self.schema, validate_sidecar=False)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TAG_INVALID])
        self.assertEqual(issues[0][ErrorContext.COLUMN], "HED")
        self.assertEqual(issues[0]["ec_filename"], "events.tsv")

    def test_base_input_keeps_its_own_sidecar(self):
        """A BaseInput is validated with the sidecar it was built with; a different one is refused."""
        sidecar = _sidecar(self.sidecar_dict)
        rows = [["onset", "duration", "response_time", "event_code"], ["4.5", "0", "3.4", "face"]]
        events = _tabular(rows, sidecar)

        # The same object is fine, explicitly or by default.
        self.assertEqual(self.validator.validate(events, sidecar=sidecar, extra_def_dicts=self.definitions), [])
        self.assertEqual(self.validator.validate(events, extra_def_dicts=self.definitions), [])

        other = _sidecar({"event_code": {"HED": {"face": "Blue"}}})
        with self.assertRaises(ValueError):
            self.validator.validate(events, sidecar=other)
        with self.assertRaises(ValueError):
            self.validator.validate(_tabular(rows), sidecar=other)

    def test_value_errors_stop_before_the_hed_column(self):
        rows = [
            ["onset", "duration", "response_time", "event_code", "HED"],
            ["4.5", "0", "abc", "face", "InvalidTagXYZ"],
        ]
        issues = _tabular(rows, _sidecar(self.sidecar_dict)).validate(self.schema, extra_def_dicts=self.definitions)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.VALUE_INVALID])

    def test_hed_column_reports_each_distinct_string_once(self):
        rows = [
            ["onset", "duration", "HED"],
            ["1.0", "0", "Red"],
            ["2.0", "0", "InvalidTagXYZ"],
            ["3.0", "0", "Red"],
            ["4.0", "0", "InvalidTagXYZ"],
            ["5.0", "0", "Blue, InvalidTagXYZ"],
        ]
        issues = _tabular(rows).validate(self.schema)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TAG_INVALID] * 2)
        self.assertEqual([issue[ErrorContext.ROW] for issue in issues], [3, 6])
        self.assertEqual([issue[ROW_COUNT_KEY] for issue in issues], [2, 1])

    def test_value_column_with_a_definition_placeholder(self):
        sidecar = _sidecar({"acc": {"HED": "Def/Acc/#"}})
        rows = [["onset", "duration", "acc"], ["1.0", "0", "2.5"], ["2.0", "0", "fast"]]
        issues = _tabular(rows, sidecar).validate(self.schema, extra_def_dicts=self.definitions)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.VALUE_INVALID])
        self.assertEqual(issues[0][ErrorContext.ROW], 3)
        self.assertIn("Acceleration/fast m-per-s^2", issues[0]["message"])

    def test_value_column_units_and_value_classes(self):
        sidecar = _sidecar(
            {"dist": {"HED": "Distance/# m"}, "label": {"HED": "Label/#"}, "note": {"HED": "Description/#"}}
        )
        rows = [
            ["onset", "duration", "dist", "label", "note"],
            ["1.0", "0", "3.5", "trial-one", "A plain note."],
            ["2.0", "0", "4 cm", "trial two", "n/a"],
        ]
        issues = _tabular(rows, sidecar).validate(self.schema)
        codes = sorted((issue[ErrorContext.COLUMN], issue["code"]) for issue in issues)
        # "4 cm" substituted into "Distance/# m" gives "Distance/4 cm m", bad units. "trial two" has a
        # space, which nameClass forbids. The text-class note is fine.
        self.assertEqual(
            codes, [("dist", ValidationErrors.UNITS_INVALID), ("label", ValidationErrors.CHARACTER_INVALID)]
        )

    def test_categorical_unknown_value_is_a_warning_and_does_not_stop(self):
        sidecar = _sidecar({"event_code": {"HED": {"face": "Red", "ball": "Blue"}}})
        rows = [
            ["onset", "duration", "event_code", "HED"],
            ["1.0", "0", "face", "Green"],
            ["2.0", "0", "hand", "Green"],
        ]
        issues = _tabular(rows, sidecar).validate(self.schema, error_handler=ErrorHandler(check_for_warnings=True))
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.SIDECAR_KEY_MISSING])
        self.assertIn("hand", issues[0]["message"])

        rows[2][3] = "InvalidTagXYZ"
        issues = _tabular(rows, sidecar).validate(self.schema, error_handler=ErrorHandler(check_for_warnings=True))
        self.assertEqual(
            sorted(issue["code"] for issue in issues),
            [ValidationErrors.SIDECAR_KEY_MISSING, ValidationErrors.TAG_INVALID],
        )

    def test_row_offset_reports_table_rows(self):
        rows = [["onset", "duration", "HED"], ["1.0", "0", "Red"], ["2.0", "0", "InvalidTagXYZ"]]
        issues = _tabular(rows).validate(self.schema, row_offset=0)
        self.assertEqual(issues[0][ErrorContext.ROW], 1)
        issues = _tabular(rows).validate(self.schema)
        self.assertEqual(issues[0][ErrorContext.ROW], 3)

    def test_prefix_template_is_checked_when_there_is_no_sidecar(self):
        """A column_prefix_dictionary template has no sidecar to validate it, so the column stage does."""
        text = "HED\tcode\nRed\t12\nBlue\t34\n"
        spreadsheet = SpreadsheetInput(
            io.StringIO(text), file_type=".tsv", tag_columns=["HED"], column_prefix_dictionary={"code": "Bogus/"}
        )
        issues = spreadsheet.validate(self.schema)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TAG_INVALID])
        self.assertEqual(issues[0][ErrorContext.COLUMN], "code")
        self.assertNotIn(ROW_COUNT_KEY, issues[0])

        spreadsheet = SpreadsheetInput(
            io.StringIO(text), file_type=".tsv", tag_columns=["HED"], column_prefix_dictionary={"code": "Label/"}
        )
        self.assertEqual(spreadsheet.validate(self.schema), [])

    def test_stage_methods_on_their_own(self):
        """The column and HED stage methods take plain dictionaries and need no table at all."""
        validator = SpreadsheetValidator(self.schema, def_dicts=self.definitions)
        error_handler = ErrorHandler()

        issues = validator.validate_value_column("acc", "Def/Acc/#", {"2.5": [0, 4], "fast": [2]}, error_handler)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.VALUE_INVALID])
        self.assertEqual((issues[0][ErrorContext.ROW], issues[0][ROW_COUNT_KEY]), (2, 1))

        issues = validator.validate_categorical_column("code", ["a", "b"], {"a": [0], "c": [1, 2]}, error_handler)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.SIDECAR_KEY_MISSING])

        issues = validator.validate_hed_column("HED", {"Red": [0], "(Onset)": [1]}, error_handler, full_string=True)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(issues[0][ErrorContext.ROW], 1)
        self.assertEqual(error_handler.error_context, [])


if __name__ == "__main__":
    unittest.main()
