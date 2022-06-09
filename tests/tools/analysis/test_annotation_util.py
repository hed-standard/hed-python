import os
import io
import json
import unittest
from pandas import DataFrame
from hed import schema as hedschema
from hed.models import Sidecar
from hed.tools import BidsTabularSummary, check_df_columns, df_to_hed, extract_tags, hed_to_df, merge_hed_dict
from hed.tools.analysis.annotation_util import _find_last_pos, _find_first_pos, \
    _flatten_cat_col, _flatten_val_col, _get_value_entry, trim_back, trim_front, _tag_list_to_str, _update_cat_dict, \
    generate_sidecar_entry
from hed.util import get_file_list
from hed.validator import HedValidator


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        curation_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/curation')
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                       '../../data/schema_test_data/HED8.0.0.xml'))
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
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
        df1 = hed_to_df(self.sidecar1a)
        missing1 = check_df_columns(df1)
        self.assertFalse(missing1)
        df2 = df1.drop('column_value', axis=1)
        missing2 = check_df_columns(df2, ('column_name', 'column_value'))
        self.assertTrue(missing2, "check_df_column has non-empty return if items missing")
        self.assertEqual(len(missing2), 1, "check_df_column finds correct number of missing items")

    def test_extract_tags(self):
        remainder0, extracted0 = extract_tags("", 'Description/')
        self.assertFalse(remainder0, "extract_tags should have empty remainder if empty string")
        self.assertFalse(extracted0, "extract_tags should have empty extracted if empty string")

        str1 = "Bear, Description, Junk"
        remainder1, extracted1 = extract_tags(str1, 'Description/')
        self.assertEqual(remainder1, str1, "extract_tags should return same string if no extracted tag")
        self.assertIsInstance(extracted1, list, "extract_tags should return an empty list list")
        self.assertFalse(extracted1, "extract_tags return an empty extracted list if no tag in string ")

        str2 = "Bear, Description/Pluck this leaf., Junk"
        remainder2, extracted2 = extract_tags(str2, 'Description/')
        self.assertEqual(remainder2, "Bear, Junk", "extract_tags should return the right string")
        self.assertIsInstance(extracted2, list, "extract_tags should return a list")
        self.assertEqual(len(extracted2), 1, "extract_tags should return a list of the right length")
        self.assertEqual(extracted2[0], "Description/Pluck this leaf.", "extract_tag return right item ")

        str3 = "Description/Pluck this leaf., Junk, Bells"
        remainder3, extracted3 = extract_tags(str3, 'Description/')
        self.assertEqual(remainder3, "Junk, Bells", "extract_tags should return the right remainder when at beginning")
        self.assertIsInstance(extracted3, list, "extract_tags should return a list when at beginning")
        self.assertEqual(len(extracted3), 1, "extract_tags should return a list of the right length when at beginning")
        self.assertEqual(extracted3[0], "Description/Pluck this leaf.",
                         "extract_tags return right item when at beginning")

        str4 = "Junk, Bells, Description/Pluck this leaf."
        remainder4, extracted4 = extract_tags(str4, 'Description/')
        self.assertEqual(remainder4, "Junk, Bells", "extract_tags should return the right remainder when at end")
        self.assertIsInstance(extracted4, list, "extract_tags should return a list when at beginning")
        self.assertEqual(len(extracted4), 1, "extract_tags should return a list of the right length when at end")
        self.assertEqual(extracted4[0], "Description/Pluck this leaf.",
                         "extract_tags return right item when at beginning")

        str5 = "Bear, Description/Pluck this leaf., Junk, Description/Another description."
        remainder5, extracted5 = extract_tags(str5, 'Description/')
        self.assertEqual(remainder5, "Bear, Junk", "extract_tags should return the right string")
        self.assertIsInstance(extracted5, list, "extract_tags should return a list")
        self.assertEqual(len(extracted5), 2, "extract_tags should return a list of the right length")
        self.assertEqual(extracted5[0], "Description/Pluck this leaf.", "extract_tags return right item ")
        self.assertEqual(extracted5[1], "Description/Another description.", "extract_tags return right item ")

        str6 = "Bear, ((Description/Pluck this leaf., Junk), Description/Another description.)"
        remainder6, extracted6 = extract_tags(str6, 'Description/')
        self.assertEqual(remainder6, "Bear, ((Junk))", "extract_tags should return the right string when parens")
        self.assertIsInstance(extracted6, list, "extract_tags should return a list when parens")
        self.assertEqual(len(extracted6), 2, "extract_tags should return a list of the right length when parens")
        self.assertEqual(extracted6[0], "Description/Pluck this leaf.", "extract_tags return right item when parens")
        self.assertEqual(extracted6[1], "Description/Another description.",
                         "extract_tags return right item when parens")

        str7 = "Bear, ((Informational-property/Description/Pluck this leaf., Junk), Description/Another description.)"
        remainder7, extracted7 = extract_tags(str7, 'Description/')
        self.assertEqual(remainder7, "Bear, ((Junk))", "extract_tags should return the right string when parens")
        self.assertIsInstance(extracted7, list, "extract_tags should return a list when parens")
        self.assertEqual(len(extracted7), 2, "extract_tags should return a list of the right length when parens")
        self.assertEqual(extracted7[0], "Informational-property/Description/Pluck this leaf.",
                         "extract_tags return right item when parens")
        self.assertEqual(extracted7[1], "Description/Another description.",
                         "extract_tags return right item when parens")

    def test_df_to_hed(self):
        df1 = hed_to_df(self.sidecar1a, col_names=None)
        hed1 = df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed1), 1, "df_to_hed ")
        df2 = hed_to_df(self.sidecar2b, col_names=None)
        hed2 = df_to_hed(df2)
        self.assertIsInstance(hed2, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed2), 1, "df_to_hed ")

    def test_df_to_hed_columns_missing(self):
        df1 = hed_to_df(self.sidecar3, col_names=["a", "b"])
        hed1 = df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should return a dictionary two columns")
        self.assertEqual(len(hed1), 2, "df_to_hed should have two keys when two columns")

        df2 = hed_to_df(self.sidecar3, col_names=["a"])
        hed2 = df_to_hed(df2)
        self.assertIsInstance(hed2, dict, "df_to_hed should return a dictionary one columns")
        self.assertEqual(len(hed2), 1, "df_to_hed should have one keys when one columns")

        df3 = hed_to_df(self.sidecar3, col_names=[])
        hed3 = df_to_hed(df3)
        self.assertIsInstance(hed3, dict, "df_to_hed should return a dictionary three columns")
        self.assertEqual(len(hed3), 3, "df_to_hed should have three keys when three columns")

    def test_df_to_hed_extra_col_names(self):
        df1 = hed_to_df(self.sidecar3, col_names=["a", "b", "c", "d"])
        hed1 = df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should return a dictionary three columns")
        self.assertEqual(len(hed1), 3, "df_to_hed should have three keys when three columns match")

    def test_generate_sidecar_entry(self):
        entry1 = generate_sidecar_entry('event_type', column_values=['apple', 'banana', 'n/a'])
        self.assertIsInstance(entry1, dict, "generate_sidecar_entry should be a dictionary when column values")
        self.assertEqual(len(entry1), 3, "generate_sidecar_entry should have 3 entries when column values")
        self.assertIn('Description', entry1, "generate_sidecar_entry should have Description when column values")
        self.assertIn('HED', entry1,  "generate_sidecar_entry should have HED when column values")
        self.assertEqual(len(entry1['HED']), 2, "generate_sidecar_entry should not include n/a in HED")
        self.assertIn('Levels', entry1, "generate_sidecar_entry should have Levels when column values")
        self.assertEqual(len(entry1['Levels']), 2, "generate_sidecar_entry should not include n/a in Levels")
        entry2 = generate_sidecar_entry('event_type')
        self.assertIsInstance(entry2, dict, "generate_sidecar_entry should be a dictionary when no column values")
        self.assertEqual(len(entry2), 2, "generate_sidecar_entry should have 2 entries when no column values")
        self.assertIn('Description', entry2, "generate_sidecar_entry should have a Description when no column values")
        self.assertIn('HED', entry2, "generate_sidecar_entry should have a Description when no column values")
        self.assertIsInstance(entry2['HED'], str,
                              "generate_sidecar_entry HED entry should be str when no column values")

    def test_generate_sidecar_entry_non_letters(self):
        entry1 = generate_sidecar_entry('my !#$-123_10', column_values=['apple 1', '@banana', 'grape%cherry&'])
        self.assertIsInstance(entry1, dict,
                              "generate_sidecar_entry is a dictionary when column values and special chars.")
        self.assertIn('HED', entry1,
                      "generate_sidecar_entry has a HED key when column values and special chars")
        hed_entry1 = entry1['HED']
        self.assertEqual(hed_entry1['apple 1'], '(Label/my_-123_10, Label/apple_1)',
                         "generate_sidecar_entry HED entry should convert labels correctly when column values")
        entry2 = generate_sidecar_entry('my !#$-123_10')
        self.assertIsInstance(entry2, dict,
                              "generate_sidecar_entry is a dictionary when no column values and special chars.")
        self.assertEqual(entry2['HED'], '(Label/my_-123_10, Label/#)',
                         "generate_sidecar_entry HED entry has correct label when no column values and special chars.")

    def test_hed_to_df(self):
        df1a = hed_to_df(self.sidecar1a, col_names=None)
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 1)
        df1a = hed_to_df(self.sidecar1a, col_names=["a"])
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 0)
        df2a = hed_to_df(self.sidecar2a)
        self.assertIsInstance(df2a, DataFrame)
        self.assertEqual(len(df2a), 2)

    def test_hed_to_df_with_definitions(self):
        df1 = hed_to_df(self.sidecar_facesm)
        self.assertIsInstance(df1, DataFrame)
        self.assertEqual(len(df1), 12)
        remainder = "(Definition/Scrambled-face-cond, (Condition-variable/Face-type, (Image, (Face, Disordered))))"
        description = "A scrambled face image generated by taking face 2D FFT."
        self.assertEqual(remainder, df1.loc[11, 'HED'], "hed_to_df should have right remainder when in parentheses")
        self.assertEqual(description, df1.loc[11, 'description'],
                         "hed_to_df should have right description when in parentheses")

    def test_hed_to_df_to_hed(self):
        validator = HedValidator(self.hed_schema)
        side1 = Sidecar(files=self.json_path, name="sidecar_face.json")
        issues1 = side1.validate_entries(validator, check_for_warnings=True)
        self.assertFalse(issues1, "hed_to_df_to_hed is starting with a valid JSON sidecar")
        df1 = hed_to_df(self.sidecar_face)
        self.assertIsInstance(df1, DataFrame, "hed_to_df_to_hed starting sidecar can be converted to df")
        hed2 = df_to_hed(df1, description_tag=True)
        side2 = Sidecar(files=io.StringIO(json.dumps(hed2)), name='JSON_Sidecar2')
        issues2 = side2.validate_entries(validator, check_for_warnings=True)
        self.assertFalse(issues2, "hed_to_df_to_hed is valid after conversion back and forth with description True")
        hed3 = df_to_hed(df1, description_tag=False)
        side3 = Sidecar(files=io.StringIO(json.dumps(hed3)), name='JSON_Sidecar2')
        issues3 = side3.validate_entries(validator, check_for_warnings=True)
        self.assertFalse(issues3, "hed_to_df_to_hed is valid after conversion back and forth with description False")

    def test_merge_hed_dict_cat_col(self):
        df2a = hed_to_df(self.sidecar2a, col_names=None)
        df2b = hed_to_df(self.sidecar2b, col_names=None)
        df2c = hed_to_df(self.sidecar2c, col_names=None)
        hed2a = df_to_hed(df2a)
        self.assertIsInstance(hed2a, dict)
        # TODO: test of categorical columns not yet written

    def test_merge_hed_dict_value_col(self):
        df1a = hed_to_df(self.sidecar1a, col_names=None)
        df1b = hed_to_df(self.sidecar1b, col_names=None)
        hed1a = df_to_hed(df1a)
        hed1b = df_to_hed(df1b)
        self.assertEqual(len(df1a), 1, "merge_hed_dict should have the right length before merge")
        self.assertEqual(len(self.sidecar1a), 2, "merge_hed_dict should have the right length before merge")
        merge_hed_dict(self.sidecar1a, hed1a)
        self.assertEqual(len(self.sidecar1a), 2, "merge_hed_dict should have the right length after merge")
        self.assertIsInstance(self.sidecar1a['b']['HED'], str, "merge_hed_dict preserve a value key")
        self.assertNotIn('Description', self.sidecar1a['b'], "merge_hed_dict should not have description when n/a")
        merge_hed_dict(self.sidecar1b, hed1a)
        self.assertIsInstance(self.sidecar1b['b']['HED'], str, "merge_hed_dict preserve a value key")
        self.assertIn('Description', self.sidecar1b['b'], "merge_hed_dict should not have description when n/a")
        merge_hed_dict(self.sidecar1b, hed1b)
        self.assertIn('Description', self.sidecar1b['b'], "merge_hed_dict should not have description when n/a")

    def test_merge_hed_dict_full(self):
        exclude_dirs = ['stimuli']
        skip_columns = ["onset", "duration", "sample", "trial", "response_time"]
        value_columns = ["rep_lag", "stim_file", "value"]
        event_files = get_file_list(self.bids_root_path, extensions=[".tsv"], name_suffix="_events",
                                    exclude_dirs=exclude_dirs)
        value_sum = BidsTabularSummary(value_cols=value_columns, skip_cols=skip_columns)
        value_sum.update(event_files)
        sidecar_template = value_sum.extract_sidecar_template()
        example_spreadsheet = hed_to_df(sidecar_template)
        spreadsheet_sidecar = df_to_hed(example_spreadsheet, description_tag=False)
        example_sidecar = {}
        self.assertEqual(0, len(example_sidecar), 'merge_hed_dict input is empty for this test')
        merge_hed_dict(example_sidecar, spreadsheet_sidecar)
        self.assertEqual(6, len(example_sidecar), 'merge_hed_dict merges with the correct length')

    def test_trim_back(self):
        str1 = 'Blech, Cat, ('
        trim1 = trim_back(str1)
        self.assertEqual(trim1, str1, 'trim_back should trim the correct amount')
        str2 = ""
        trim2 = trim_back(str2)
        self.assertFalse(trim2, 'trim_back should trim an empty string to empty')
        str3 = '(Blech, Cat),   '
        trim3 = trim_back(str3)
        self.assertEqual('(Blech, Cat)', trim3, 'trim_back should trim extra blanks and comma')

    def test_trim_front(self):
        str1 = ',   (Blech, Cat)'
        trim1 = trim_front(str1)
        self.assertEqual(trim1, "(Blech, Cat)", 'trim_front should trim the correct amount')
        str2 = ""
        trim2 = trim_front(str2)
        self.assertFalse(trim2, 'trim_front should trim an empty string to empty')
        str3 = '(Blech, Cat)'
        trim3 = trim_front(str3)
        self.assertEqual(str3, trim3, 'trim_front should trim not trim if no extras')

    def test_find_last_pos(self):
        test1 = "Apple/1.0, ("
        pos1 = _find_last_pos(test1)
        self.assertEqual(pos1, len(test1))
        test2 = "Informational-property/"
        pos2 = _find_last_pos(test2)
        self.assertEqual(pos2, 0, "_find_last_pos should return the start if at the beginning")
        test3 = "(Blech), (Property/Informational-property"
        pos3 = _find_last_pos(test3)
        self.assertEqual(pos3, 10, "_find_last_pos should return the start if at the beginning")

    def test_find_first_pos(self):
        test1 = "My blech."
        pos1 = _find_first_pos(test1)
        self.assertEqual(pos1, len(test1),
                         "_find_first_position should return position at character after end of string")

        test2 = "My blech.))"
        pos2 = _find_first_pos(test2)
        self.assertEqual(pos2, 9, "_find_first_position should return position at closing parentheses")
        test3 = "My blech., Description/My apple."
        pos3 = _find_first_pos(test3)
        self.assertEqual(pos3, 9, "_find_first_position should return position at closing parentheses")

    def test_flatten_cat_col(self):
        col1 = self.sidecar2c["a"]
        col2 = self.sidecar2c["b"]
        try:
            _flatten_cat_col("a", col1)
        except KeyError:
            pass
        except Exception:
            self.fail("_flatten_cat_col threw the wrong exception when no HED key")
        else:
            self.fail("_flatten_cat_col should have thrown a KeyError exception when no HED key")

        keys2, values2, descriptions2, tags2 = _flatten_cat_col("b", col2)
        self.assertEqual(len(keys2), 2, "_flatten_cat_col should have right number of keys if HED")
        self.assertEqual(len(values2), 2, "_flatten_cat_col should have right number of values if HED")
        self.assertEqual(len(descriptions2), 2, "_flatten_cat_col should have right number of descriptions if HED")
        self.assertEqual(len(tags2), 2, "_flatten_cat_col should have right number of tags if HED")
        self.assertEqual(descriptions2[0], 'Bad purple',
                         "_flatten_cat_col should use the Description tag if available")

    def test_flatten_value_col(self):
        col1 = self.sidecar1a["a"]
        col2 = self.sidecar1b["b"]
        try:
            _flatten_val_col("a", col1)
        except KeyError:
            pass
        except Exception:
            self.fail("_flatten_value_col threw the wrong exception when no HED key")
        else:
            self.fail("_flatten_value_col should have thrown a KeyError exception when no HED key")

        keys2, values2, descriptions2, tags2 = _flatten_val_col("b", col2)
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

    def test_get_value_entry(self):
        dict1 = _get_value_entry('n/a', 'n/a')
        self.assertFalse(dict1, "_get_value_entry should return empty dict if everything n/a")
        dict2 = _get_value_entry('', '')
        self.assertFalse(dict2, "_get_value_entry should return empty dict if everything empty")
        dict3 = _get_value_entry('Red,Blue', '')
        self.assertIn('HED', dict3, "_get_value_entry should have a HED entry when tags but no description")
        self.assertNotIn('Description', dict3,
                         "_get_value_entry should not have a Description entry when tags but no description")
        dict4 = _get_value_entry('Red,Blue,Description/Too bad', '')
        self.assertIn('HED', dict4, "_get_value_entry should have a HED entry when Description tag")
        self.assertNotIn('Description', dict4,
                         "_get_value_entry should not have a Description entry when Description tag")
        dict5 = _get_value_entry('', 'This is a test')
        self.assertIn('HED', dict5, "_get_value_entry should have a HED entry when Description used")
        self.assertIn('Description', dict5,
                      "_get_value_entry should have a Description entry when Description used")
        dict6 = _get_value_entry('Red,Blue', 'This is a test')
        self.assertIn('HED', dict6, "_get_value_entry should have a HED entry when Description used")
        self.assertEqual(dict6['HED'], 'Red,Blue, Description/This is a test',
                         "_get_value_entry should correct value when Description used for HED tags")
        self.assertIn('Description', dict6,
                      "_get_value_entry should have a Description entry when Description used")
        dict7 = _get_value_entry('Red,Blue', 'This is a test')
        self.assertIn('HED', dict7, "_get_value_entry should have a HED entry when Description used")
        self.assertIn('Description', dict7, "_get_value_entry should have a HED entry when Description used")
        dict8 = _get_value_entry('', 'This is a test', description_tag=False)
        self.assertNotIn('HED', dict8, "_get_value_entry should not have a HED entry when Description not used")
        self.assertIn('Description', dict8, "_get_value_entry should have Description entry when Description not used")

    def test_tag_list_to_str(self):
        ext1 = ["apple", "banana"]
        str1 = _tag_list_to_str(ext1)
        self.assertEqual("apple banana", str1, "tag_list_to_str should return the correct amount when no extra tag")
        ext2 = ["apple", "Description/banana", "Informational-property/Description/Pear is it."]
        str2 = _tag_list_to_str(ext2, "Description/")
        self.assertEqual("apple banana Pear is it.", str2,
                         "tag_list_to_str should return the correct amount when extra tag")

    def test_update_cat_dict(self):
        # TODO: Improve tests
        cat_dict = self.sidecar_face['event_type']
        value1 = cat_dict['HED']['show_face']
        self.assertNotEqual(cat_dict['HED']['show_face'], 'Blue,Red')
        _update_cat_dict(cat_dict, 'show_face', 'Blue,Red', 'n/a', description_tag=True)
        self.assertEqual(cat_dict['HED']['show_face'], 'Blue,Red')


if __name__ == '__main__':
    unittest.main()
