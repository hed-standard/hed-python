import pandas as pd
import os
import shutil
import json
import io

import unittest
from hed import load_schema_version, load_schema
from hed.validator import SpreadsheetValidator
from hed import TabularInput, SpreadsheetInput, Sidecar
from hed.errors.error_types import ValidationErrors


class TestSpreadsheetValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.3.0")
        cls.validator = SpreadsheetValidator(cls.schema)
        base = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        cls.base_data_dir = base
        hed_xml_file = os.path.join(base, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = load_schema(hed_xml_file)
        default = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               "../data/spreadsheet_validator_tests/ExcelMultipleSheets.xlsx")
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
        column_prefix_dictionary = {1: 'Label/', 3: 'Description'}
        tag_columns = [4]
        worksheet_name = 'LKT 8HED3'

        file_input = SpreadsheetInput(hed_input, has_column_names=has_column_names, worksheet_name=worksheet_name,
                                      tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary)

        self.assertTrue(isinstance(file_input.dataframe_a, pd.DataFrame))
        self.assertTrue(isinstance(file_input.series_a, pd.Series))
        self.assertTrue(file_input.dataframe_a.size)

        issues = file_input.validate(self.schema)
        self.assertTrue(len(issues), 1)

    def test_invalid_onset_invalid_column(self):
        def_dict = "(Definition/DefaultOnset, (Event))"
        base_df = pd.DataFrame({
            'HED': ["Event, (Age/5, Label/Example)", "Age/1, Label/Example", "Age/3, (Event)"]
        })

        self.df_with_onset = base_df.copy()
        self.df_with_onset['onset'] = [1, 2, 3]
        self.df_without_onset = base_df.copy()

        # No tags in either of these
        issues = self.validator.validate(TabularInput(self.df_without_onset), def_dicts=def_dict)
        self.assertEqual(len(issues), 0)

        issues = self.validator.validate(TabularInput(self.df_with_onset), def_dicts=def_dict)
        self.assertEqual(len(issues), 0)

        base_has_tags_df = pd.DataFrame({
            'HED': ["(Onset, Def/DefaultOnset)", "(Inset, Def/DefaultOnset), (Event, Age/2)",
                    "(Offset, Def/DefaultOnset), (Age/4)"]
        })

        self.df_with_onset_has_tags = base_has_tags_df.copy()
        self.df_with_onset_has_tags['onset'] = [1, 2, 3]
        self.df_without_onset_has_tags = base_has_tags_df.copy()

        issues = self.validator.validate(TabularInput(self.df_without_onset_has_tags), def_dicts=def_dict)
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[0]['code'], ValidationErrors.TEMPORAL_TAG_ERROR)
        issues = self.validator.validate(TabularInput(self.df_with_onset_has_tags), def_dicts=def_dict)
        self.assertEqual(len(issues), 0)

        base_has_tags_unordered_df = pd.DataFrame({
            'HED': ["(Onset, Def/DefaultOnset)", "(Offset, Def/DefaultOnset), (Age/4)",
                    "(Inset, Def/DefaultOnset), (Event, Age/2)"]
        })
        self.df_with_onset_has_tags_unordered = base_has_tags_unordered_df.copy()
        self.df_with_onset_has_tags_unordered['onset'] = [1, 2, 3]
        self.df_without_onset_has_tags_unordered = base_has_tags_unordered_df.copy()

        issues = self.validator.validate(TabularInput(self.df_without_onset_has_tags_unordered), def_dicts=def_dict)
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[0]['code'], ValidationErrors.TEMPORAL_TAG_ERROR)
        issues = self.validator.validate(TabularInput(self.df_with_onset_has_tags_unordered), def_dicts=def_dict)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['code'], ValidationErrors.TEMPORAL_TAG_ERROR)

    def test_onset_na(self):
        # Test with no sidecar
        def_dict = "(Definition/Def1, (Event))"
        tsv = {
            "onset": [0.0, 1.2, 1.2, 3.0, "n/a", 3.5, "n/a", 6],
            "duration": [0.5, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"],
            "event_code": ["show", "respond", "show", "respond", "whatever", "show", "whatelse", "respond"],
            "HED": ["Age/100", "(Def/Def1, Onset)", "Red", "n/a", "Green", "(Def/Def1, Offset)",
                    "Female,(Def/Def1,Onset)", "n/a"],
        }
        df_with_nans = pd.DataFrame(tsv)
        issues = self.validator.validate(TabularInput(df_with_nans), def_dicts=def_dict)
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[2]['code'], ValidationErrors.TEMPORAL_TAG_ERROR)

        # Test with sidecar
        sidecar_dict = {
            "event_code": {
                "HED": {
                    "show": "Sensory-event,Visual-presentation",
                    "respond": "Press",
                    "whatever": "Black",
                    "whatelse": "Purple"
                }
            }
        }

        sidecar1 = Sidecar(io.StringIO(json.dumps(sidecar_dict)))
        issues1 = self.validator.validate(TabularInput(df_with_nans, sidecar=sidecar1), def_dicts=def_dict)
        self.assertEqual(len(issues1), 2)
        self.assertEqual(issues1[1]['code'], ValidationErrors.TEMPORAL_TAG_ERROR)

        # The whatelse does not use the bad HED columns and HED column appears in {} so only when assembled is used.
        sidecar_dict["event_code"]["HED"]["whatever"] = "Black, {HED}"
        sidecar2 = Sidecar(io.StringIO(json.dumps(sidecar_dict)))
        issues2 = self.validator.validate(TabularInput(df_with_nans, sidecar=sidecar2), def_dicts=def_dict)
        self.assertEqual(len(issues2), 1)
        self.assertEqual(issues1[0]['code'], ValidationErrors.ONSETS_UNORDERED)
