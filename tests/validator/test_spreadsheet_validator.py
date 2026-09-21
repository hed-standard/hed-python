import io
import json
import os
import shutil
import unittest

import pandas as pd

from hed import Sidecar, SpreadsheetInput, TabularInput, load_schema, load_schema_version
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ErrorContext, ValidationErrors
from hed.validator import SpreadsheetValidator


class TestSpreadsheetValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.4.0")
        cls.validator = SpreadsheetValidator(cls.schema)
        base = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")
        cls.base_data_dir = base
        hed_xml_file = os.path.join(base, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = load_schema(hed_xml_file)
        default = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/spreadsheet_validator_tests/ExcelMultipleSheets.xlsx"
        )
        cls.default_test_file_name = default
        cls.generic_file_input = SpreadsheetInput(default)
        base_output = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        cls.base_output_folder = base_output
        os.makedirs(base_output, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_basic_validate(self):
        hed_input = self.default_test_file_name
        has_column_names = True
        column_prefix_dictionary = {1: "Label/", 3: "Description"}
        tag_columns = [4]
        worksheet_name = "LKT 8HED3"

        file_input = SpreadsheetInput(
            hed_input,
            has_column_names=has_column_names,
            worksheet_name=worksheet_name,
            tag_columns=tag_columns,
            column_prefix_dictionary=column_prefix_dictionary,
        )

        self.assertTrue(isinstance(file_input.dataframe_a, pd.DataFrame))
        self.assertTrue(isinstance(file_input.series_a, pd.Series))
        self.assertTrue(file_input.dataframe_a.size)

        issues = file_input.validate(self.schema)
        self.assertTrue(len(issues), 1)

    def test_invalid_onset_invalid_column(self):
        def_dict = "(Definition/DefaultOnset, (Event))"
        base_df = pd.DataFrame({"HED": ["Event, (Age/5, Label/Example)", "Age/1, Label/Example", "Age/3, (Event)"]})

        self.df_with_onset = base_df.copy()
        self.df_with_onset["onset"] = [1, 2, 3]
        self.df_without_onset = base_df.copy()

        # No tags in either of these
        issues = self.validator.validate(TabularInput(self.df_without_onset), extra_def_dicts=def_dict)
        self.assertEqual(len(issues), 0)

        issues = self.validator.validate(TabularInput(self.df_with_onset), extra_def_dicts=def_dict)
        self.assertEqual(len(issues), 0)

        base_has_tags_df = pd.DataFrame(
            {
                "HED": [
                    "(Onset, Def/DefaultOnset)",
                    "(Inset, Def/DefaultOnset), (Event, Age/2)",
                    "(Offset, Def/DefaultOnset), (Age/4)",
                ]
            }
        )

        self.df_with_onset_has_tags = base_has_tags_df.copy()
        self.df_with_onset_has_tags["onset"] = [1, 2, 3]
        self.df_without_onset_has_tags = base_has_tags_df.copy()

        issues = self.validator.validate(TabularInput(self.df_without_onset_has_tags), extra_def_dicts=def_dict)
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[0]["code"], ValidationErrors.TEMPORAL_TAG_ERROR)
        issues = self.validator.validate(TabularInput(self.df_with_onset_has_tags), extra_def_dicts=def_dict)
        self.assertEqual(len(issues), 0)

        base_has_tags_unordered_df = pd.DataFrame(
            {
                "HED": [
                    "(Onset, Def/DefaultOnset)",
                    "(Offset, Def/DefaultOnset), (Age/4)",
                    "(Inset, Def/DefaultOnset), (Event, Age/2)",
                ]
            }
        )
        self.df_with_onset_has_tags_unordered = base_has_tags_unordered_df.copy()
        self.df_with_onset_has_tags_unordered["onset"] = [1, 2, 3]
        self.df_without_onset_has_tags_unordered = base_has_tags_unordered_df.copy()

        issues = self.validator.validate(
            TabularInput(self.df_without_onset_has_tags_unordered), extra_def_dicts=def_dict
        )
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[0]["code"], ValidationErrors.TEMPORAL_TAG_ERROR)
        issues = self.validator.validate(TabularInput(self.df_with_onset_has_tags_unordered), extra_def_dicts=def_dict)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], ValidationErrors.TEMPORAL_TAG_ERROR)

    def test_empty(self):
        spreadsheet = SpreadsheetInput(
            file=io.StringIO("BadFile"),
            worksheet_name=None,
            file_type=".tsv",
            tag_columns=[3],
            has_column_names=True,
            column_prefix_dictionary=None,
            name="spreadsheets.tsv",
        )
        error_handler = ErrorHandler(check_for_warnings=True)
        issues = self.validator.validate(spreadsheet, error_handler=error_handler)
        self.assertEqual(len(issues), 0)

    def test_tabular_with_hed(self):
        sidecar_hed_json = """
           {
               "event_code": {
                   "HED": {
                        "face": "{HED}",
                        "ball": "Red"
                   }
               }
           }
           """
        sidecar = Sidecar(io.StringIO(sidecar_hed_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 0)
        data = [["onset", "duration", "event_code", "HED"], [4.5, 0, "face", "Black"], [5.0, 0, "n/a", ""]]
        df = pd.DataFrame(data[1:], columns=data[0])
        my_tab = TabularInput(df, sidecar=sidecar, name="test_no_hed")
        error_handler = ErrorHandler(check_for_warnings=False)
        issues = self.validator.validate(my_tab, error_handler=error_handler)
        self.assertEqual(len(issues), 0)

    def test_tabular_no_hed(self):
        sidecar_hed_json = """
        {
            "event_code": {
                "HED": {
                     "face": "{HED}",
                     "ball": "Red"
                }
            }
        }
        """
        sidecar = Sidecar(io.StringIO(sidecar_hed_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 0)
        data = [["onset", "duration", "event_code"], [4.5, 0, "face"], [5.0, 0, "ball"]]
        df = pd.DataFrame(data[1:], columns=data[0])
        my_tab = TabularInput(df, sidecar=sidecar, name="test_no_hed")
        error_handler = ErrorHandler(check_for_warnings=False)
        issues = self.validator.validate(my_tab, error_handler=error_handler)
        self.assertEqual(len(issues), 0)

    def test_onset_na(self):
        # Test with no sidecar
        def_dict = "(Definition/Def1, (Event))"
        tsv = {
            "onset": [0.0, 1.2, 1.2, 3.0, "n/a", 3.5, "n/a", 6],
            "duration": [0.5, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"],
            "event_code": ["show", "respond", "show", "respond", "whatever", "show", "whatelse", "respond"],
            "HED": [
                "Age/100",
                "(Def/Def1, Onset)",
                "Red",
                "n/a",
                "Green",
                "(Def/Def1, Offset)",
                "Female,(Def/Def1,Onset)",
                "n/a",
            ],
        }
        df_with_nans = pd.DataFrame(tsv)
        issues = self.validator.validate(TabularInput(df_with_nans), extra_def_dicts=def_dict)
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[2]["code"], ValidationErrors.TEMPORAL_TAG_ERROR)

        # Test with sidecar
        sidecar_dict = {
            "event_code": {
                "HED": {
                    "show": "Sensory-event,Visual-presentation",
                    "respond": "Press",
                    "whatever": "Black",
                    "whatelse": "Purple",
                }
            }
        }

        sidecar1 = Sidecar(io.StringIO(json.dumps(sidecar_dict)))
        issues1 = self.validator.validate(TabularInput(df_with_nans, sidecar=sidecar1), extra_def_dicts=def_dict)
        self.assertEqual(len(issues1), 2)
        self.assertEqual(issues1[1]["code"], ValidationErrors.TEMPORAL_TAG_ERROR)

        # The whatelse does not use the bad HED columns and HED column appears in {} so only when assembled is used.
        sidecar_dict["event_code"]["HED"]["whatever"] = "Black, {HED}"
        sidecar2 = Sidecar(io.StringIO(json.dumps(sidecar_dict)))
        issues2 = self.validator.validate(TabularInput(df_with_nans, sidecar=sidecar2), extra_def_dicts=def_dict)
        self.assertEqual(len(issues2), 1)
        self.assertEqual(issues1[0]["code"], ValidationErrors.ONSETS_UNORDERED)

    def test_delay_without_conversion_factor(self):
        # 'Delay/3 month' is valid HED but month has no conversionFactor, so the delayed onset cannot be
        # computed. Validation must report this as a TEMPORAL_TAG_ERROR on that row, not raise, and the
        # onset checks must still run for the rest of the file.
        def_dict = "(Definition/Def1, (Event))"
        tsv = {
            "onset": [0.0, 1.0, 2.0, 3.0],
            "duration": ["n/a", "n/a", "n/a", "n/a"],
            "HED": [
                "(Def/Def1, Onset)",
                "(Delay/3 month, (Red))",
                "(Delay/3 s, (Green))",
                "(Def/Def1, Offset)",
            ],
        }
        issues = self.validator.validate(TabularInput(pd.DataFrame(tsv)), extra_def_dicts=def_dict)
        self.assertEqual(len(issues), 1, issues)
        self.assertEqual(issues[0]["code"], ValidationErrors.TEMPORAL_TAG_ERROR)
        self.assertEqual(issues[0][ErrorContext.ROW], 3)  # 1-based, plus the header row
        self.assertIn("Delay/3 month", issues[0]["message"])

        # An unmatched Offset later in the file is still reported, so the onset checks did run.
        tsv["HED"][3] = "(Def/Def1, Offset), (Def/Def1, Offset)"
        issues = self.validator.validate(TabularInput(pd.DataFrame(tsv)), extra_def_dicts=def_dict)
        codes = [issue["code"] for issue in issues]
        self.assertGreaterEqual(codes.count(ValidationErrors.TEMPORAL_TAG_ERROR), 2, codes)

    def test_duration_without_conversion_factor_in_timeline_file(self):
        # In a timeline file a Duration gives the end time of its group, so 'Duration/3 year' (year has no
        # conversionFactor) is a TEMPORAL_TAG_ERROR, as is a non-convertible Duration paired with a
        # convertible Delay. Convertible durations pass. The Duration group is reported, not dropped, so the
        # onset checks still see every row.
        def_dict = "(Definition/Def1, (Event))"
        tsv = {
            "onset": [0.0, 1.0, 2.0, 3.0, 4.0],
            "duration": ["n/a", "n/a", "n/a", "n/a", "n/a"],
            "HED": [
                "(Def/Def1, Onset)",
                "(Duration/3 year, (Red))",
                "(Delay/2 s, Duration/1 month, (Green))",
                "(Duration/3 day, (Blue)), (Delay/2 s, Duration/4 hours, (Green))",
                "(Def/Def1, Offset)",
            ],
        }
        issues = self.validator.validate(TabularInput(pd.DataFrame(tsv)), extra_def_dicts=def_dict)
        self.assertEqual(len(issues), 2, issues)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TEMPORAL_TAG_ERROR] * 2)
        self.assertEqual([issue[ErrorContext.ROW] for issue in issues], [3, 4])  # 1-based, plus the header row
        self.assertIn("Duration/3 year", issues[0]["message"])
        self.assertIn("Duration/1 month", issues[1]["message"])

        # Both halves of a group with a non-convertible Delay and a non-convertible Duration are reported.
        tsv["HED"][2] = "(Delay/2 month, Duration/1 year, (Green))"
        issues = self.validator.validate(TabularInput(pd.DataFrame(tsv)), extra_def_dicts=def_dict)
        messages = " ".join(issue["message"] for issue in issues)
        self.assertEqual(len(issues), 3, issues)
        self.assertIn("Delay/2 month", messages)
        self.assertIn("Duration/1 year", messages)

    def test_duration_any_unit_in_non_timeline_file(self):
        # Without an onset column nothing is placed on a timeline, so Duration may use any valid time unit
        # (participants.tsv style). Delay stays banned there, reported by the existing no-onset check.
        df = pd.DataFrame(
            {"participant_id": ["sub-01", "sub-02"], "HED": ["(Duration/3 year, (Red))", "(Duration/6 month, (Blue))"]}
        )
        issues = self.validator.validate(TabularInput(df))
        self.assertEqual(
            [issue["code"] for issue in issues if issue["code"] != ValidationErrors.HED_UNKNOWN_COLUMN], []
        )

        df = pd.DataFrame({"participant_id": ["sub-01"], "HED": ["(Delay/3 year, (Red))"]})
        issues = self.validator.validate(TabularInput(df))
        codes = [issue["code"] for issue in issues]
        self.assertIn(ValidationErrors.TEMPORAL_TAG_ERROR, codes)

    def _small_events(self):
        return TabularInput(pd.DataFrame({"onset": [1.0, 2.0], "duration": [0, 0], "HED": ["Red", "InvalidTagXYZ"]}))

    def test_validate_without_name_adds_no_filename_context(self):
        """With no name, the validator adds no FILE_NAME context and leaves the caller's context intact."""
        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.TABLE_NAME, "trials")

        issues = self.validator.validate(self._small_events(), error_handler=error_handler)

        self.assertGreater(len(issues), 0)
        for issue in issues:
            self.assertNotIn("ec_filename", issue)
            self.assertEqual(issue.get("ec_table_name"), "trials")
        self.assertEqual(error_handler.error_context, [(ErrorContext.TABLE_NAME, "trials")])

    def test_validate_with_name_keeps_filename_context(self):
        """With a name, every issue carries it as ec_filename, as before."""
        error_handler = ErrorHandler()

        issues = self.validator.validate(self._small_events(), name="events.tsv", error_handler=error_handler)

        self.assertGreater(len(issues), 0)
        self.assertTrue(all(issue.get("ec_filename") == "events.tsv" for issue in issues))
        self.assertEqual(error_handler.error_context, [])

    def test_tabular_input_validate_empty_name_suppresses_filename_context(self):
        """TabularInput.validate with name="" adds no FILE_NAME context even though the input has a name."""
        named = TabularInput(
            pd.DataFrame({"onset": [1.0], "duration": [0], "HED": ["InvalidTagXYZ"]}), name="events.tsv"
        )

        issues = named.validate(self.schema)
        self.assertGreater(len(issues), 0)
        self.assertTrue(all(issue.get("ec_filename") == "events.tsv" for issue in issues))

        issues = named.validate(self.schema, name="")
        self.assertGreater(len(issues), 0)
        self.assertTrue(all("ec_filename" not in issue for issue in issues))

    def test_validate_pops_context_on_onset_na_early_return(self):
        """The early return on onset n/a issues must not leave the FILE_NAME context on the stack."""
        # A temporal tag on a row whose onset is n/a is reported as TEMPORAL_TAG_ERROR by the assembly
        # stage, which then returns early. The first row's group is fine on its own, so the earlier
        # stages pass and the assembly stage is reached.
        def_dict = "(Definition/MyDef, (Event))"
        tsv = "onset\tduration\tHED\n1.0\t0\t(Red, Blue)\nn/a\t0\t(Onset, Def/MyDef)\n"
        error_handler = ErrorHandler()

        issues = self.validator.validate(
            TabularInput(io.StringIO(tsv)), extra_def_dicts=def_dict, name="events.tsv", error_handler=error_handler
        )

        codes = {issue["code"] for issue in issues}
        # The n/a onset also makes the onsets non-monotonic, which is reported alongside.
        self.assertEqual(codes, {ValidationErrors.TEMPORAL_TAG_ERROR, ValidationErrors.ONSETS_UNORDERED})
        self.assertTrue(all(issue.get("ec_filename") == "events.tsv" for issue in issues))
        self.assertEqual(error_handler.error_context, [])

    def test_hed_column_errors_stop_before_assembly(self):
        """An invalid tag in the HED column stops the run before the assembly stage's onset checks."""
        tsv = "onset\tduration\tHED\n1.0\t0\tInvalidTagXYZ\nn/a\t0\t(Onset, Def/MyDef)\n"
        error_handler = ErrorHandler()

        issues = self.validator.validate(TabularInput(io.StringIO(tsv)), name="events.tsv", error_handler=error_handler)

        codes = {issue["code"] for issue in issues}
        self.assertIn(ValidationErrors.TAG_INVALID, codes)
        self.assertNotIn(ValidationErrors.TEMPORAL_TAG_ERROR, codes)
        self.assertEqual(error_handler.error_context, [])
