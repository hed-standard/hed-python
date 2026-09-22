"""The four stages of SpreadsheetValidator, their stops, and the DataFrame-free path."""

import io
import json
import unittest

import pandas as pd

from hed import Sidecar, SpreadsheetInput, TabularInput, load_schema_version
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ErrorContext, SidecarErrors, ValidationErrors
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

    def test_value_errors_stop_before_assembly(self):
        """A stage-2 error hides what the assembly stage would report: unordered onsets and a lone Offset."""
        rows = [
            ["onset", "duration", "response_time", "event_code", "HED"],
            ["5.0", "0", "abc", "face", "(Offset, Def/Acc/3.5)"],
            ["4.5", "0", "3.4", "face", "Red"],
        ]
        events = _tabular(rows, _sidecar(self.sidecar_dict))
        issues = events.validate(self.schema, extra_def_dicts=self.definitions)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.VALUE_INVALID])

        rows[1][2] = "3.4"
        issues = _tabular(rows, _sidecar(self.sidecar_dict)).validate(self.schema, extra_def_dicts=self.definitions)
        codes = {issue["code"] for issue in issues}
        self.assertIn(ValidationErrors.ONSETS_UNORDERED, codes)
        self.assertIn(ValidationErrors.TEMPORAL_TAG_ERROR, codes)

    def test_sidecar_warning_does_not_stop(self):
        """A sidecar with only a warning goes on to the later stages, and the warning is reported once."""
        sidecar = _sidecar({"event_code": {"HED": {"face": "Item/Extended-thing", "ball": "Red"}}})
        rows = [["onset", "duration", "event_code", "HED"], ["1.0", "0", "face", "InvalidTagXYZ"]]
        issues = _tabular(rows, sidecar).validate(self.schema, error_handler=ErrorHandler(check_for_warnings=True))
        self.assertEqual(
            sorted(issue["code"] for issue in issues), [ValidationErrors.TAG_EXTENDED, ValidationErrors.TAG_INVALID]
        )

    def test_hed_column_warning_is_reported_once_and_not_repeated_by_assembly(self):
        rows = [
            ["onset", "duration", "HED"],
            ["1.0", "0", "Item/Extended-thing"],
            ["2.0", "0", "Item/Extended-thing"],
            ["3.0", "0", "Red, Red"],
        ]
        issues = _tabular(rows).validate(self.schema, error_handler=ErrorHandler(check_for_warnings=True))
        self.assertEqual(
            [(issue["code"], issue[ErrorContext.ROW]) for issue in issues],
            [(ValidationErrors.TAG_EXTENDED, 2), (ValidationErrors.TAG_EXPRESSION_REPEATED, 4)],
        )
        self.assertEqual(issues[0][ROW_COUNT_KEY], 2)
        self.assertNotIn(ROW_COUNT_KEY, issues[1])

    def test_validate_sidecar_false_trusts_the_caller(self):
        """With validate_sidecar=False a sidecar error nobody caught is not found by the later stages."""
        rows = [["onset", "duration", "rt", "code"], ["1.0", "0", "3", "a"]]
        sidecar = _sidecar({"rt": {"HED": "Bogus/#"}, "code": {"HED": {"a": "BogusTag"}}})
        self.assertTrue(_tabular(rows, sidecar).validate(self.schema))
        self.assertEqual(_tabular(rows, sidecar).validate(self.schema, validate_sidecar=False), [])

    def test_sidecar_issues_keep_the_sidecar_name_when_the_table_has_none(self):
        sidecar = _sidecar({"code": {"HED": {"a": "InvalidTagXYZ"}}}, name="events.json")
        rows = [["onset", "duration", "code"], ["1.0", "0", "a"]]
        issues = _tabular(rows, sidecar).validate(self.schema)  # the table has no name
        self.assertEqual([issue["ec_filename"] for issue in issues], ["events.json"])

        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.TABLE_NAME, "trials")
        issues = _tabular(rows, sidecar).validate(self.schema, name="", error_handler=error_handler)
        self.assertEqual(
            [("ec_filename" in issue, issue.get("ec_table_name")) for issue in issues], [(False, "trials")]
        )
        self.assertEqual(error_handler.error_context, [(ErrorContext.TABLE_NAME, "trials")])

    def test_column_source_with_a_base_input_reaches_assembly(self):
        """A non-BaseInput source that hands over a BaseInput gets the assembly stage (ndx-hed assemble=True)."""
        columns = {
            "onset": [1.0, 2.0],
            "duration": [0, 0],
            "HED": ["(Onset, Def/Acc/3.5)", "(Offset, Def/Acc/3.5), (Offset, Def/Acc/3.5)"],
        }
        frame = TabularInput(pd.DataFrame({name: [str(v) for v in values] for name, values in columns.items()}))
        source = ListColumnSource(columns, base_input=frame)
        issues = self.validator.validate(source, extra_def_dicts=self.definitions)
        codes = {issue["code"] for issue in issues}
        self.assertIn(ValidationErrors.TAG_EXPRESSION_REPEATED, codes)
        self.assertIn(ValidationErrors.TEMPORAL_TAG_ERROR, codes)
        self.assertTrue(all(issue[ErrorContext.ROW] == 1 for issue in issues))  # row_offset 0 for a plain source

        source = ListColumnSource(columns)
        self.assertEqual(self.validator.validate(source, extra_def_dicts=self.definitions), [])

    def test_plain_source_gets_a_warning_for_a_column_the_sidecar_does_not_describe(self):
        source = ListColumnSource({"id": [1, 2], "onset": [1.0, 2.0], "HED": ["Red", "Blue"]})
        issues = self.validator.validate(
            source, sidecar=_sidecar({}), error_handler=ErrorHandler(check_for_warnings=True)
        )
        self.assertEqual(
            [(issue["code"], "id" in issue["message"]) for issue in issues],
            [(ValidationErrors.HED_UNKNOWN_COLUMN, True)],
        )

    def test_headerless_spreadsheet_columns_by_number(self):
        text = "Red\t12\nInvalidTagXYZ\tabc\nRed\t34\nInvalidTagXYZ\t56\n"
        spreadsheet = SpreadsheetInput(
            io.StringIO(text),
            file_type=".tsv",
            has_column_names=False,
            tag_columns=[0],
            column_prefix_dictionary={1: "Age/"},
        )
        issues = spreadsheet.validate(self.schema)
        # Stage 2 finds the bad age (row 1, column 1, 1-based rows with no header) and stops before stage 3.
        self.assertEqual(
            [
                (issue["code"], issue[ErrorContext.ROW], issue[ErrorContext.COLUMN], issue[ROW_COUNT_KEY])
                for issue in issues
            ],
            [(ValidationErrors.VALUE_INVALID, 2, 1, 1)],
        )
        spreadsheet = SpreadsheetInput(
            io.StringIO(text.replace("abc", "7")),
            file_type=".tsv",
            has_column_names=False,
            tag_columns=[0],
            column_prefix_dictionary={1: "Age/"},
        )
        issues = spreadsheet.validate(self.schema)
        self.assertEqual(
            [
                (issue["code"], issue[ErrorContext.ROW], issue[ErrorContext.COLUMN], issue[ROW_COUNT_KEY])
                for issue in issues
            ],
            [(ValidationErrors.TAG_INVALID, 2, 0, 2)],
        )

    def test_row_offset_applies_to_the_assembly_stage(self):
        rows = [["onset", "duration", "HED"], ["1.0", "0", "Red"], ["2.0", "0", "(Offset, Def/Acc/3.5)"]]
        issues = _tabular(rows).validate(self.schema, extra_def_dicts=self.definitions, row_offset=0)
        self.assertEqual(
            [(issue["code"], issue[ErrorContext.ROW]) for issue in issues], [(ValidationErrors.TEMPORAL_TAG_ERROR, 1)]
        )
        issues = _tabular(rows).validate(self.schema, extra_def_dicts=self.definitions)
        self.assertEqual(
            [(issue["code"], issue[ErrorContext.ROW]) for issue in issues], [(ValidationErrors.TEMPORAL_TAG_ERROR, 3)]
        )

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

    def test_value_cells_that_break_hed_syntax_are_rejected(self):
        """A value that passes its value class may still break the string it is spliced into.

        Before the staged validator every assembled cell was parsed, which caught these; the column stage
        parses the substituted tag for the same reason. The comma and brace cases are reported by the
        value-class check first, with their own codes.
        """
        sidecar = _sidecar({"note": {"HED": "Parameter-value/#"}})
        expected = {
            "(a": ValidationErrors.PARENTHESES_MISMATCH,
            "a)": ValidationErrors.PARENTHESES_MISMATCH,
            "a~b": ValidationErrors.TILDES_UNSUPPORTED,
            "a#b": ValidationErrors.PLACEHOLDER_INVALID,
            "7,3": ValidationErrors.CHARACTER_INVALID,
            "{x}": SidecarErrors.SIDECAR_BRACES_INVALID,
        }
        for value, code in expected.items():
            with self.subTest(value=value):
                rows = [["onset", "duration", "note"], ["1.0", "0", value]]
                issues = _tabular(rows, sidecar).validate(self.schema)
                self.assertIn(code, [issue["code"] for issue in issues])
                self.assertTrue(all(issue[ErrorContext.COLUMN] == "note" for issue in issues))
        rows = [["onset", "duration", "note"], ["1.0", "0", "A plain note."], ["2.0", "0", "a/b"]]
        self.assertEqual(_tabular(rows, sidecar).validate(self.schema), [])

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
