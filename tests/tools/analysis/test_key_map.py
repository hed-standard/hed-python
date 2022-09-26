import unittest
import os
import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools.analysis.key_map import KeyMap
from hed.tools.util.data_util import get_new_dataframe
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        curation_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/remodeling')
        cls.curation_base_dir = curation_base_dir
        cls.stern_map_path = os.path.join(curation_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(curation_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(curation_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(curation_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path2 = os.path.join(curation_base_dir,
                                                 "sub-001_task-AuditoryVisualShift_run-01_events.tsv")
        cls.attn_map_path = os.path.join(curation_base_dir, "attention_shift_remap_event_template_filled.tsv")
        cls.key_cols1 = ['type']
        cls.target_cols1 = ['event_type', 'task_role', 'letter']
        cls.count_col1 = ['counts']
        cls.key_cols2 = ["event_code", "cond_code", "focus_modality"]
        cls.target_cols2 = ["event_type", "attention_status", "task_role"]

    # def test_lookup_cols(self):
    #     t_map = KeyMap(self.key_cols1, self.target_cols1)
    #     stern_df = get_new_dataframe(self.stern_map_path)
    #     t_map.update(stern_df)
    #     t_col = t_map.col_map
    #     for index, row in stern_df.iterrows():
    #         key = get_row_hash(row, self.key_cols1)
    #         key_value = t_map.map_dict[key]
    #         self.assertEqual(t_col.iloc[key_value]['type'], row['type'], "The key should be looked up for same map")
    #
    #     stern_test1 = get_new_dataframe(self.stern_test1_path)
    #     for index, row in stern_test1.iterrows():
    #         key = get_row_hash(row, self.key_cols1)
    #         key_value = t_map.map_dict[key]
    #         self.assertEqual(t_col.iloc[key_value]['type'], row['type'], "The key should be looked up for other file")

    def test_constructor(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        self.assertIsInstance(t_map, KeyMap)
        df = t_map.col_map
        self.assertIsInstance(df, pd.DataFrame)
        try:
            KeyMap(None, ['a'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'KeyMap threw the wrong exception {ex} when no key columns')
        else:
            self.fail('KeyMap should have thrown a HedFileError exception when no key columns')

        try:
            KeyMap(['a', 'b', 'c'], ['b', 'c', 'd'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'KeyMap threw the wrong exception {ex} when key and target columns overlap')
        else:
            self.fail('KeyMap should have thrown a HedFileError exception when key and target columns overlap')

        emap1 = KeyMap(['a'], [])
        self.assertIsInstance(emap1, KeyMap, "KeyMap: target columns can be empty")
        self.assertEqual(len(emap1.col_map.columns), 1,
                         "The column map should have only key columns when no target")

    def test_make_template(self):
        t_map = KeyMap(self.key_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map.update(stern_df)
        df1 = t_map.make_template()
        self.assertIsInstance(df1, pd.DataFrame, "make_template should return a DataFrame")
        self.assertEqual(len(df1.columns), 1, "make_template should return 1 column single key, no additional columns")
        t_map2 = KeyMap(['event_type', 'type'])
        t_map2.update(self.stern_map_path)
        df2 = t_map2.make_template()
        self.assertIsInstance(df2, pd.DataFrame, "make_template should return a DataFrame")
        self.assertEqual(len(df2.columns), 2, "make_template should return 2 columns w 2 keys, no additional columns")
        df3 = t_map2.make_template(['bananas', 'pears', 'apples'])
        self.assertIsInstance(df3, pd.DataFrame, "make_template should return a DataFrame")
        self.assertEqual(len(df3.columns), 5, "make_template should return 5 columns w 2 keys, 3 additional columns")

    def test_make_template_key_overlap(self):
        t_map = KeyMap(['event_type', 'type'])
        t_map.update(self.stern_map_path)
        try:
            t_map.make_template(['Bananas', 'type', 'Pears'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'make_template threw the wrong exception {ex} when additional columns overlapped keys')
        else:
            self.fail('KeyTemplate should have thrown a HedFileError exception when key overlap but threw none')

    def test_remap(self):
        t_map_stern = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map_stern.update(stern_df)
        stern_test1 = get_new_dataframe(self.stern_test1_path)
        df1, missing1 = t_map_stern.remap(stern_test1)
        self.assertFalse(missing1, "remap should return empty missing when all keys are accounted for")
        self.assertEqual(len(stern_test1), len(df1), "remap should not change number rows in file")
        self.assertEqual(df1.iloc[3]["event_type"], 'show_letter',
                         "remap should have right value when single column key")

    def test_remap_multiple_keys(self):
        t_map_attn = KeyMap(self.key_cols2, self.target_cols2)
        attn_df_map = get_new_dataframe(self.attn_map_path)
        t_map_attn.update(attn_df_map)
        attn_test = get_new_dataframe(self.attention_shift_path2)
        df1, missing1 = t_map_attn.remap(attn_test)
        self.assertFalse(missing1, "remap should return empty missing when all keys are accounted for")
        self.assertEqual(len(attn_test), len(df1), "remap should not change number rows in file")
        self.assertEqual(df1.iloc[3]["event_type"], 'button_press',
                         "remap should have correct value when multiple keys")

    def test_remap_missing(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map.update(stern_df)
        stern_test1 = get_new_dataframe(self.stern_test1_path)
        stern_test1.at[3, 'type'] = 'baloney'
        stern_test1.at[10, 'type'] = 'special'
        df_new, missing = t_map.remap(stern_test1)
        self.assertTrue(missing, "remap should return return nonempty missing when when keys missing")
        self.assertEqual(len(stern_test1), len(df_new), "remap should not change number rows in file")
        self.assertEqual(df_new.iloc[3]["event_type"], 'n/a',
                         "remap should have n/a in the targets when key is missing")

    def test_remap_files(self):
        key_cols = ['type']
        target_cols = ['event_type', 'task_role', 'letter']
        key_map = KeyMap(key_cols, target_cols, 'my_name')
        key_map.update(self.stern_map_path)
        event_file_list = get_file_list(self.curation_base_dir, name_prefix='sternberg',
                                        name_suffix="_events", extensions=[".tsv"])
        for file in event_file_list:
            df_new, missing = key_map.remap(file)
            self.assertFalse(missing)

    def test_update_map(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        duplicates = t_map.update(stern_df)
        df_map = t_map.col_map
        df_dict = t_map.map_dict
        self.assertEqual(len(df_map), len(stern_df), "update map should contain all the entries")
        self.assertEqual(len(df_dict.keys()), len(stern_df),
                         "update dictionary should contain all the entries")
        self.assertFalse(duplicates, "update should not have any duplicates for stern map")

    def test_update_map_missing(self):
        keys = self.key_cols1 + ['another']
        t_map = KeyMap(keys, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        try:
            t_map.update(stern_df, allow_missing=False)
        except HedFileError or KeyError:
            pass
        except Exception as ex:
            self.fail(f'update threw the wrong exception {ex} when key column missing')
        else:
            self.fail('update should have thrown a HedFileError exception when key column was missing')

    def test_update_map_missing_allowed(self):
        keys = self.key_cols1 + ['another']
        t_map = KeyMap(keys, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map.update(stern_df, allow_missing=True)

    def test_update_map_duplicate_keys(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_test2_path)
        duplicates = t_map.update(stern_df, keep_counts=False)
        self.assertTrue(duplicates, "update should return a list of duplicates if repeated keys")

    def test_update_map_not_unique(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_test2_path)
        duplicates = t_map.update(stern_df, keep_counts=False)
        self.assertEqual(len(t_map.col_map.columns), 4, "update should produce correct number of columns")
        self.assertEqual(len(t_map.col_map), len(stern_df) - len(duplicates),
                         "update should produce the correct number of rows")
        self.assertTrue(duplicates, "update using event file has duplicates")


if __name__ == '__main__':
    unittest.main()
