import os
import io
import json
import unittest
import numpy as np
from pandas import DataFrame, Series
from hed import schema as hedschema
from hed.errors.exceptions import HedFileError
from hed.models.sidecar import Sidecar
from hed.models.hed_string import HedString
from hed.models.tabular_input import TabularInput

from hed.tools.analysis import annotation_util
from hed.tools.analysis.tabular_summary import TabularSummary
from hed.tools.util import io_util


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        curation_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/remodel_tests')
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids_tests/eeg_ds003645s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../data/schema_tests/HED8.2.0.xml'))
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        cls.events_path = os.path.realpath(os.path.join(bids_root_path, 'sub-002', 'eeg',
                                                        'sub-002_task-FacePerception_run-1_events.tsv'))
        cls.json_path = json_path
        json_sm_path = os.path.realpath(os.path.join(curation_base_dir, 'task-FacePerceptionSmall_events.json'))
        cls.sidecar1a = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": "Purple"}}
        cls.sidecar1b = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": "Purple", "Description": "Its a color."}}
        cls.sidecar1c = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": "Purple, Description/New purple", "Description": "Its a color."}}
        cls.sidecar2a = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": {"b2": "Purple", "b3": "Red"}}}
        cls.sidecar2b = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": {"b2": "Purple", "b3": "Red"}}}
        cls.sidecar2c = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": {"b2": "Purple,Description/Bad purple", "b3": "Red"},
                               "Levels": {"b2": "Its purple.", "b3": "Its red."}}}
        cls.sidecar3 = {"a": {"HED": {"b2": "Purple,Description/Bad purple", "b3": "Red"},
                              "Levels": {"b2": "Its purple.", "b3": "Its red."}},
                        "b": {"HED": {"b4": "Purple", "b5": "Red"},
                              "Levels": {"b4": "Its purple.", "b5": "Its red."}},
                        "c": {"HED": {"b6": "Purple", "b7": "Red"},
                              "Levels": {"b6": "Its purple.", "b7": "Its red."}}
                        }

        cls.hed_schema = hedschema.load_schema(schema_path)
        with open(json_path) as fp:
            cls.sidecar_face = json.load(fp)
        with open(json_sm_path) as fp:
            cls.sidecar_facesm = json.load(fp)

    def test_check_df_columns(self):
        df1 = annotation_util.hed_to_df(self.sidecar1a)
        missing1 = annotation_util.check_df_columns(df1)
        self.assertFalse(missing1)
        df2 = df1.drop('column_value', axis=1)
        missing2 = annotation_util.check_df_columns(df2, ('column_name', 'column_value'))
        self.assertTrue(missing2, "check_df_column has non-empty return if items missing")
        self.assertEqual(len(missing2), 1, "check_df_column finds correct number of missing items")

    def test_extract_tags_no_tag(self):
        remainder0, extracted0 = annotation_util.extract_tags("", 'Description/')
        self.assertFalse(remainder0, "extract_tags should have empty remainder if empty string")
        self.assertFalse(extracted0, "extract_tags should have empty extracted if empty string")

        str1 = "Bear, Description, Junk"
        remainder1, extracted1 = annotation_util.extract_tags(str1, 'Description/')
        self.assertEqual(remainder1, str1, "extract_tags should return same string if no extracted tag")
        self.assertIsInstance(extracted1, list, "extract_tags should return an empty list list")
        self.assertFalse(extracted1, "extract_tags return an empty extracted list if no tag in string ")

    def test_extract_tags_with_remainder(self):
        str2 = "Bear, Description/Pluck this leaf., Junk"
        remainder2, extracted2 = annotation_util.extract_tags(str2, 'Description/')
        self.assertEqual(remainder2, "Bear, Junk", "extract_tags should return the right string")
        self.assertIsInstance(extracted2, list, "extract_tags should return a list")
        self.assertEqual(len(extracted2), 1, "extract_tags should return a list of the right length")
        self.assertEqual(extracted2[0], "Description/Pluck this leaf.", "extract_tag return right item ")

        str3 = "Description/Pluck this leaf., Junk, Bells"
        remainder3, extracted3 = annotation_util.extract_tags(str3, 'Description/')
        self.assertEqual(remainder3, "Junk, Bells", "extract_tags should return the right remainder when at beginning")
        self.assertIsInstance(extracted3, list, "extract_tags should return a list when at beginning")
        self.assertEqual(len(extracted3), 1, "extract_tags should return a list of the right length when at beginning")
        self.assertEqual(extracted3[0], "Description/Pluck this leaf.",
                         "extract_tags return right item when at beginning")

        str4 = "Junk, Bells, Description/Pluck this leaf."
        remainder4, extracted4 = annotation_util.extract_tags(str4, 'Description/')
        self.assertEqual(remainder4, "Junk, Bells", "extract_tags should return the right remainder when at end")
        self.assertIsInstance(extracted4, list, "extract_tags should return a list when at beginning")
        self.assertEqual(len(extracted4), 1, "extract_tags should return a list of the right length when at end")
        self.assertEqual(extracted4[0], "Description/Pluck this leaf.",
                         "extract_tags return right item when at beginning")

    def extract_tag_multiple_matches(self):
        str5 = "Bear, Description/Pluck this leaf., Junk, Description/Another description."
        remainder5, extracted5 = annotation_util.extract_tags(str5, 'Description/')
        self.assertEqual(remainder5, "Bear, Junk", "extract_tags should return the right string")
        self.assertIsInstance(extracted5, list, "extract_tags should return a list")
        self.assertEqual(len(extracted5), 2, "extract_tags should return a list of the right length")
        self.assertEqual(extracted5[0], "Description/Pluck this leaf.", "extract_tags return right item ")
        self.assertEqual(extracted5[1], "Description/Another description.", "extract_tags return right item ")

        str6 = "Bear, ((Description/Pluck this leaf., Junk), Description/Another description.)"
        remainder6, extracted6 = annotation_util.extract_tags(str6, 'Description/')
        self.assertEqual(remainder6, "Bear, ((Junk))", "extract_tags should return the right string when parens")
        self.assertIsInstance(extracted6, list, "extract_tags should return a list when parens")
        self.assertEqual(len(extracted6), 2, "extract_tags should return a list of the right length when parens")
        self.assertEqual(extracted6[0], "Description/Pluck this leaf.", "extract_tags return right item when parens")
        self.assertEqual(extracted6[1], "Description/Another description.",
                         "extract_tags return right item when parens")

    def test_extract_tag_with_parens(self):
        str7 = "Bear, ((Informational-property/Description/Pluck this leaf., Junk), Description/Another description.)"
        remainder7, extracted7 = annotation_util.extract_tags(str7, 'Description/')
        self.assertEqual(remainder7, "Bear, ((Junk))", "extract_tags should return the right string when parens")
        self.assertIsInstance(extracted7, list, "extract_tags should return a list when parens")
        self.assertEqual(len(extracted7), 2, "extract_tags should return a list of the right length when parens")
        self.assertEqual(extracted7[0], "Informational-property/Description/Pluck this leaf.",
                         "extract_tags return right item when parens")
        self.assertEqual(extracted7[1], "Description/Another description.",
                         "extract_tags return right item when parens")

    def test_df_to_hed(self):
        df1 = annotation_util.hed_to_df(self.sidecar1a, col_names=None)
        hed1 = annotation_util.df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed1), 1, "df_to_hed ")
        df2 = annotation_util.hed_to_df(self.sidecar2b, col_names=None)
        hed2 = annotation_util.df_to_hed(df2)
        self.assertIsInstance(hed2, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed2), 1, "df_to_hed ")

    def test_df_to_hed_wrong_format(self):
        data = [['event_code', 'baloney', 'this is baloney', 'junk1'],
                ['event_code', 'sausage', 'this is sausage', 'junk2']]
        df = DataFrame(data, columns=['column_name', 'column_value', 'description', 'blech'])
        with self.assertRaises(HedFileError) as context:
            annotation_util.df_to_hed(df)
        self.assertEqual(context.exception.args[0], 'RequiredColumnsMissing')

    def test_df_to_hed_nas(self):
        data = [['event_code', 'baloney', 'n/a', 'n/a'],
                ['event_code', 'sausage', 'this is sausage', 'n/a']]
        df = DataFrame(data, columns=['column_name', 'column_value', 'description', 'HED'])
        hed1 = annotation_util.df_to_hed(df)
        self.assertIsInstance(hed1, dict)
        self.assertIsInstance(hed1['event_code'], dict)
        self.assertEqual(len(hed1['event_code']), 2)

    def test_df_to_hed_columns_missing(self):
        df1 = annotation_util.hed_to_df(self.sidecar3, col_names=["a", "b"])
        hed1 = annotation_util.df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should return a dictionary two columns")
        self.assertEqual(len(hed1), 2, "df_to_hed should have two keys when two columns")

        df2 = annotation_util.hed_to_df(self.sidecar3, col_names=["a"])
        hed2 = annotation_util.df_to_hed(df2)
        self.assertIsInstance(hed2, dict, "df_to_hed should return a dictionary one columns")
        self.assertEqual(len(hed2), 1, "df_to_hed should have one keys when one columns")

        df3 = annotation_util.hed_to_df(self.sidecar3, col_names=[])
        hed3 = annotation_util.df_to_hed(df3)
        self.assertIsInstance(hed3, dict, "df_to_hed should return a dictionary three columns")
        self.assertEqual(len(hed3), 3, "df_to_hed should have three keys when three columns")

    def test_df_to_hed_extra_col_names(self):
        df1 = annotation_util.hed_to_df(self.sidecar3, col_names=["a", "b", "c", "d"])
        hed1 = annotation_util.df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should return a dictionary three columns")
        self.assertEqual(len(hed1), 3, "df_to_hed should have three keys when three columns match")

    def test_generate_sidecar_entry(self):
        entry1 = annotation_util.generate_sidecar_entry('event_type', column_values=['apple', 'banana', 'n/a'])
        self.assertIsInstance(entry1, dict, "generate_sidecar_entry should be a dictionary when column values")
        self.assertEqual(len(entry1), 3, "generate_sidecar_entry should have 3 entries when column values")
        self.assertIn('Description', entry1, "generate_sidecar_entry should have Description when column values")
        self.assertIn('HED', entry1,  "generate_sidecar_entry should have HED when column values")
        self.assertEqual(len(entry1['HED']), 2, "generate_sidecar_entry should not include n/a in HED")
        self.assertIn('Levels', entry1, "generate_sidecar_entry should have Levels when column values")
        self.assertEqual(len(entry1['Levels']), 2, "generate_sidecar_entry should not include n/a in Levels")
        entry2 = annotation_util.generate_sidecar_entry('event_type')
        self.assertIsInstance(entry2, dict, "generate_sidecar_entry should be a dictionary when no column values")
        self.assertEqual(len(entry2), 2, "generate_sidecar_entry should have 2 entries when no column values")
        self.assertIn('Description', entry2, "generate_sidecar_entry should have a Description when no column values")
        self.assertIn('HED', entry2, "generate_sidecar_entry should have a Description when no column values")
        self.assertIsInstance(entry2['HED'], str,
                              "generate_sidecar_entry HED entry should be str when no column values")

    def test_generate_sidecar_entry_non_letters(self):
        entry1 = annotation_util.generate_sidecar_entry('my !#$-123_10',
                                                        column_values=['apple 1', '@banana', 'grape%cherry&'])
        self.assertIsInstance(entry1, dict,
                              "generate_sidecar_entry is a dictionary when column values and special chars.")
        self.assertIn('HED', entry1,
                      "generate_sidecar_entry has a HED key when column values and special chars")
        hed_entry1 = entry1['HED']
        self.assertEqual(hed_entry1['apple 1'], '(Label/my_-123_10, ID/apple_1)',
                         "generate_sidecar_entry HED entry should convert labels correctly when column values")
        entry2 = annotation_util.generate_sidecar_entry('my !#$-123_10')
        self.assertIsInstance(entry2, dict,
                              "generate_sidecar_entry is a dictionary when no column values and special chars.")
        self.assertEqual(entry2['HED'], '(Label/my_-123_10, ID/#)',
                         "generate_sidecar_entry HED entry has correct label when no column values and special chars.")

    def test_hed_to_df(self):
        df1a = annotation_util.hed_to_df(self.sidecar1a, col_names=None)
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 1)
        df1a = annotation_util.hed_to_df(self.sidecar1a, col_names=["a"])
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 0)
        df2a = annotation_util.hed_to_df(self.sidecar2a)
        self.assertIsInstance(df2a, DataFrame)
        self.assertEqual(len(df2a), 2)

    def test_hed_to_df_with_definitions(self):
        df1 = annotation_util.hed_to_df(self.sidecar_facesm)
        self.assertIsInstance(df1, DataFrame)
        self.assertEqual(len(df1), 12)
        remainder = "(Definition/Scrambled-face-cond, (Condition-variable/Face-type, (Image, (Face, Disordered))))"
        description = "A scrambled face image generated by taking face 2D FFT."
        self.assertEqual(remainder, df1.loc[11, 'HED'], "hed_to_df should have right remainder when in parentheses")
        self.assertEqual(description, df1.loc[11, 'description'],
                         "hed_to_df should have right description when in parentheses")

    def test_hed_to_df_to_hed(self):
        # validator = HedValidator(self.hed_schema)
        side1 = Sidecar(files=self.json_path, name="sidecar_face.json")
        issues1 = side1.validate(self.hed_schema)
        self.assertFalse(issues1, "hed_to_df_to_hed is starting with a valid JSON sidecar")
        df1 = annotation_util.hed_to_df(self.sidecar_face)
        self.assertIsInstance(df1, DataFrame, "hed_to_df_to_hed starting sidecar can be converted to df")
        hed2 = annotation_util.df_to_hed(df1, description_tag=True)
        side2 = Sidecar(files=io.StringIO(json.dumps(hed2)), name='JSON_Sidecar2')
        issues2 = side2.validate(self.hed_schema)
        self.assertFalse(issues2, "hed_to_df_to_hed is valid after conversion back and forth with description True")
        hed3 = annotation_util.df_to_hed(df1, description_tag=False)
        side3 = Sidecar(files=io.StringIO(json.dumps(hed3)), name='JSON_Sidecar2')
        issues3 = side3.validate(self.hed_schema)
        self.assertFalse(issues3, "hed_to_df_to_hed is valid after conversion back and forth with description False")

    def test_merge_hed_dict_cat_col(self):
        df2a = annotation_util.hed_to_df(self.sidecar2a, col_names=None)
        df2b = annotation_util.hed_to_df(self.sidecar2b, col_names=None)
        df2c = annotation_util.hed_to_df(self.sidecar2c, col_names=None)
        hed2a = annotation_util.df_to_hed(df2a)
        self.assertIsInstance(hed2a, dict)
        hed2b = annotation_util.df_to_hed(df2b)
        self.assertIsInstance(hed2b, dict)
        hed2c = annotation_util.df_to_hed(df2c)
        self.assertIsInstance(hed2c, dict)
        # TODO: test of categorical columns not yet written

    def test_merge_hed_dict_value_col(self):
        df1a = annotation_util.hed_to_df(self.sidecar1a, col_names=None)
        df1b = annotation_util.hed_to_df(self.sidecar1b, col_names=None)
        hed1a = annotation_util.df_to_hed(df1a)
        hed1b = annotation_util.df_to_hed(df1b)
        self.assertEqual(len(df1a), 1, "merge_hed_dict should have the right length before merge")
        self.assertEqual(len(self.sidecar1a), 2, "merge_hed_dict should have the right length before merge")
        annotation_util.merge_hed_dict(self.sidecar1a, hed1a)
        self.assertEqual(len(self.sidecar1a), 2, "merge_hed_dict should have the right length after merge")
        self.assertIsInstance(self.sidecar1a['b']['HED'], str, "merge_hed_dict preserve a value key")
        self.assertNotIn('Description', self.sidecar1a['b'], "merge_hed_dict should not have description when n/a")
        annotation_util.merge_hed_dict(self.sidecar1b, hed1a)
        self.assertIsInstance(self.sidecar1b['b']['HED'], str, "merge_hed_dict preserve a value key")
        self.assertIn('Description', self.sidecar1b['b'], "merge_hed_dict should not have description when n/a")
        annotation_util.merge_hed_dict(self.sidecar1b, hed1b)
        self.assertIn('Description', self.sidecar1b['b'], "merge_hed_dict should not have description when n/a")

    def test_merge_hed_dict_full(self):
        exclude_dirs = ['stimuli']
        skip_columns = ["onset", "duration", "sample", "trial", "response_time"]
        value_columns = ["rep_lag", "stim_file", "value"]
        event_files = io_util.get_file_list(self.bids_root_path, extensions=[".tsv"], name_suffix="_events",
                                            exclude_dirs=exclude_dirs)
        value_sum = TabularSummary(value_cols=value_columns, skip_cols=skip_columns)
        value_sum.update(event_files)
        sidecar_template = value_sum.extract_sidecar_template()
        example_spreadsheet = annotation_util.hed_to_df(sidecar_template)
        spreadsheet_sidecar = annotation_util.df_to_hed(example_spreadsheet, description_tag=False)
        example_sidecar = {}
        self.assertEqual(0, len(example_sidecar), 'merge_hed_dict input is empty for this test')
        annotation_util.merge_hed_dict(example_sidecar, spreadsheet_sidecar)
        self.assertEqual(6, len(example_sidecar), 'merge_hed_dict merges with the correct length')

    def test_series_to_factor(self):
        series1 = Series([1.0, 2.0, 3.0, 4.0])
        factor1 = annotation_util.series_to_factor(series1)
        self.assertEqual(len(series1), len(factor1))
        self.assertEqual(sum(factor1), len(factor1))
        series2 = Series(['a', '', None, np.nan, 'n/a'])
        factor2 = annotation_util.series_to_factor(series2)
        self.assertEqual(len(series2), len(factor2))
        self.assertEqual(sum(factor2), 1)

    def test_strs_to_hed_objs(self):
        self.assertIsNone(annotation_util.strs_to_hed_objs('', self.hed_schema))
        self.assertIsNone(annotation_util.strs_to_hed_objs(None, self.hed_schema))
        self.assertIsNone(annotation_util.strs_to_hed_objs([], self.hed_schema))
        hed_objs1 = annotation_util.strs_to_hed_objs(['Sensory-event', 'Red'], self.hed_schema)
        self.assertIsInstance(hed_objs1, list)
        self.assertEqual(len(hed_objs1), 2)
        self.assertEqual('Red', str(hed_objs1[1]))
        hed_objs2 = annotation_util.strs_to_hed_objs(['Sensory-event', 'Blech'], self.hed_schema)
        self.assertEqual(len(hed_objs2), 2)

    def test_strs_to_sidecar(self):
        with open(self.json_path, 'r') as fp:
            sidecar_dict = json.load(fp)
        self.assertIsInstance(sidecar_dict, dict)
        sidecar_str = json.dumps(sidecar_dict)
        self.assertIsInstance(sidecar_str, str)
        sidecar_obj = annotation_util.strs_to_sidecar(sidecar_str)
        self.assertIsInstance(sidecar_obj, Sidecar)

    def test_strs_to_tabular(self):
        with open(self.events_path, 'r') as file:
            events_contents = file.read()
        tab_in = annotation_util.str_to_tabular(events_contents, sidecar=self.json_path)
        self.assertIsInstance(tab_in, TabularInput)

    def test_to_strlist(self):
        # schema
        # list1 = [HedString('Red, Sensory-event', schema)]
        list1 = ['abc', '', None, 3.24]
        str_list1 = annotation_util.to_strlist(list1)
        self.assertEqual(len(str_list1), len(list1))
        self.assertFalse(str_list1[2])
        self.assertEqual(str_list1[3], '3.24')
        self.assertFalse(str_list1[1])
        list2 = [HedString('Red, Sensory-event', self.hed_schema), None, HedString('', self.hed_schema)]
        str_list2 = annotation_util.to_strlist(list2)
        self.assertEqual(len(str_list2), len(list2))
        self.assertFalse(str_list2[1])
        self.assertEqual(str_list2[0], 'Red,Sensory-event')
        self.assertEqual(str_list2[2], '')

    def test_flatten_cat_col(self):
        col1 = self.sidecar2c["a"]
        col2 = self.sidecar2c["b"]
        try:
            annotation_util._flatten_cat_col("a", col1)
        except KeyError:
            pass
        except Exception:
            self.fail("_flatten_cat_col threw the wrong exception when no HED key")
        else:
            self.fail("_flatten_cat_col should have thrown a KeyError exception when no HED key")

        keys2, values2, descriptions2, tags2 = annotation_util._flatten_cat_col("b", col2)
        self.assertEqual(len(keys2), 2, "_flatten_cat_col should have right number of keys if HED")
        self.assertEqual(len(values2), 2, "_flatten_cat_col should have right number of values if HED")
        self.assertEqual(len(descriptions2), 2, "_flatten_cat_col should have right number of descriptions if HED")
        self.assertEqual(len(tags2), 2, "_flatten_cat_col should have right number of tags if HED")
        self.assertEqual(descriptions2[0], 'Bad purple',
                         "_flatten_cat_col should use the Description tag if available")

    def test_flatten_cat_col_only_description(self):
        keys, values, descriptions, tags = \
            annotation_util._flatten_cat_col("event_type", {"HED": {"code1": "Description/Code 1 here."}})
        self.assertIsInstance(tags, list)
        self.assertEqual(tags[0], 'n/a')

    def test_flatten_val_col_only_description(self):
        keys, values, descriptions, tags = annotation_util._flatten_val_col("response",
                                                                            {"HED": "Description/Code 1 here."})
        self.assertEqual(descriptions[0], 'Code 1 here.')
        self.assertFalse(tags[0])

    def test_flatten_value_col(self):
        col1 = self.sidecar1a["a"]
        col2 = self.sidecar1b["b"]
        with self.assertRaises(KeyError) as context:
            annotation_util._flatten_val_col("a", col1)
        self.assertEqual(context.exception.args[0], 'HED')

        keys2, values2, descriptions2, tags2 = annotation_util._flatten_val_col("b", col2)
        self.assertEqual(len(keys2), 1, "_flatten_val_col should have right number of keys if HED")
        self.assertEqual(len(values2), 1, "_flatten_val_col should have right number of values if HED")
        self.assertEqual(len(descriptions2), 1, "_flatten_val_col should have right number of descriptions if HED")
        self.assertEqual(len(tags2), 1, "_flatten_cat_col should have right number of tags if HED")
        self.assertEqual(descriptions2[0], 'Its a color.',
                         "_flatten_cat_col should use the Description tag if available")
        self.assertEqual(values2[0], 'n/a', "_flatten_cat_col should a n/a value column")

    def test_get_row_tags(self):
        col1 = self.sidecar2c["a"]
        col2 = self.sidecar2c["b"]
        self.assertTrue(col1)
        self.assertTrue(col2)

    def test_get_value_entry(self):
        dict1 = annotation_util._get_value_entry('n/a', 'n/a')
        self.assertFalse(dict1, "_get_value_entry should return empty dict if everything n/a")
        dict2 = annotation_util._get_value_entry('', '')
        self.assertFalse(dict2, "_get_value_entry should return empty dict if everything empty")
        dict3 = annotation_util._get_value_entry('Red,Blue', '')
        self.assertIn('HED', dict3, "_get_value_entry should have a HED entry when tags but no description")
        self.assertNotIn('Description', dict3,
                         "_get_value_entry should not have a Description entry when tags but no description")
        dict4 = annotation_util._get_value_entry('Red,Blue,Description/Too bad', '')
        self.assertIn('HED', dict4, "_get_value_entry should have a HED entry when Description tag")
        self.assertNotIn('Description', dict4,
                         "_get_value_entry should not have a Description entry when Description tag")
        dict5 = annotation_util._get_value_entry('', 'This is a test')
        self.assertIn('HED', dict5, "_get_value_entry should have a HED entry when Description used")
        self.assertIn('Description', dict5,
                      "_get_value_entry should have a Description entry when Description used")
        dict6 = annotation_util._get_value_entry('Red,Blue', 'This is a test')
        self.assertIn('HED', dict6, "_get_value_entry should have a HED entry when Description used")
        self.assertEqual(dict6['HED'], 'Red,Blue, Description/This is a test',
                         "_get_value_entry should correct value when Description used for HED tags")
        self.assertIn('Description', dict6,
                      "_get_value_entry should have a Description entry when Description used")
        dict7 = annotation_util._get_value_entry('Red,Blue', 'This is a test')
        self.assertIn('HED', dict7, "_get_value_entry should have a HED entry when Description used")
        self.assertIn('Description', dict7, "_get_value_entry should have a HED entry when Description used")
        dict8 = annotation_util._get_value_entry('', 'This is a test', description_tag=False)
        self.assertNotIn('HED', dict8, "_get_value_entry should not have a HED entry when Description not used")
        self.assertIn('Description', dict8, "_get_value_entry should have Description entry when Description not used")

    def test_tag_list_to_str(self):
        ext1 = ["apple", "banana"]
        str1 = annotation_util._tag_list_to_str(ext1)
        self.assertEqual("apple banana", str1, "tag_list_to_str should return the correct amount when no extra tag")
        ext2 = ["apple", "Description/banana", "Informational-property/Description/Pear is it."]
        str2 = annotation_util._tag_list_to_str(ext2, "Description/")
        self.assertEqual("apple banana Pear is it.", str2,
                         "tag_list_to_str should return the correct amount when extra tag")

    def test_to_factor(self):
        series1 = Series([1.0, 2.0, 3.0, 4.0])
        factor1 = annotation_util.to_factor(series1)
        self.assertEqual(len(series1), len(factor1))
        self.assertEqual(sum(factor1), len(factor1))
        series2 = Series(['a', '', None, np.nan, 'n/a'])
        factor2 = annotation_util.to_factor(series2)
        self.assertEqual(len(series2), len(factor2))
        self.assertEqual(sum(factor2), 1)
        data = {
            'Name': ['Alice', '', 'n/a', 1.0],  # Contains a space
            'Age': [25, np.nan, 35, 0]
        }
        df = DataFrame(data)
        factor3 = annotation_util.to_factor(df, column='Name')
        self.assertEqual(sum(factor3), 2)
        factor4 = annotation_util.to_factor(df)
        self.assertEqual(sum(factor4), 2)
        with self.assertRaises(HedFileError):
            annotation_util.to_factor(data)

    def test_update_cat_dict(self):
        # TODO: Improve tests
        cat_dict = self.sidecar_face['event_type']
        self.assertNotEqual(cat_dict['HED']['show_face'], 'Blue,Red')
        annotation_util._update_cat_dict(cat_dict, 'show_face', 'Blue,Red', 'n/a', description_tag=True)
        self.assertEqual(cat_dict['HED']['show_face'], 'Blue,Red')


if __name__ == '__main__':
    unittest.main()
