import unittest
import os
import pandas as pd
from hed.errors.exceptions import HedFileError
from hedweb.event_remap import EventRemap


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/')
        cls.stern_map_path = os.path.join(base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(base_dir, "sternberg_events_test.tsv")
        cls.stern_test2_path = os.path.join(base_dir, "sternberg_events.tsv")
        cls.key_cols = ['type']
        cls.target_cols = ['event_type', 'purpose', 'letter']

    def test_lookup_cols(self):
        t_map = EventRemap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        t_map.update_map(stern_df)
        t_col = t_map.col_map
        stern_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        for index, row in stern_test1.iterrows():
            key, key_value = t_map.lookup_cols(row)
            self.assertEqual(t_col.iloc[key_value]['type'], row['type'], "The key should be looked up correctly")

    def test_make_template(self):
        event_map = EventRemap(self.key_cols, self.target_cols)
        df = event_map.make_template(self.stern_map_path)
        self.assertEqual(len(df.columns), len(self.key_cols) + len(self.target_cols),
                         "The template should have keys and targets")
        self.assertEqual(len(df), 85, "Sternberg template should have 85 keys")
        self.assertEqual(len(df), 85, "Sternberg template should have 85 keys")
        self.assertEqual(df.iloc[0]["event_type"], "n/a", "Sternberg template first key is right click")

    def test_make_template_with_targets(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        event_map = EventRemap(self.key_cols, self.target_cols)
        df = event_map.make_template(events_path, use_targets=True)
        self.assertEqual(len(df.columns), len(self.key_cols) + len(self.target_cols),
                         "The template should have keys and targets")
        self.assertEqual(len(df), 85, "Sternberg template should have 85 keys")
        self.assertEqual(df.iloc[0]["event_type"], "right_click", "Sternberg template first key is right click")

    def test_make_template_with_keys_unique_true(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        df = EventRemap.extract_dataframe(events_path)
        df.iloc[0] = df.iloc[1].copy()
        event_map = EventRemap(self.key_cols, self.target_cols)
        try:
            event_map.make_template(df, keys_unique=True)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'make_template threw the wrong exception {str(ex)} when non unique keys')
        else:
            self.fail('make_template should have thrown a HedFileError exception when non unique keys')

    def test_make_template_with_keys_unique_false(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        df = EventRemap.extract_dataframe(events_path)
        df.iloc[0] = df.iloc[1].copy()
        event_map = EventRemap(self.key_cols, self.target_cols)

        df_new = event_map.make_template(df)
        self.assertEqual(len(df_new.columns), len(self.key_cols) + len(self.target_cols),
                         "The template should have keys and targets")
        self.assertEqual(len(df_new), 84, "Sternberg template with a duplicate should have 84 keys")

    def test_make_template_multiple_columns(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        target_cols = ['type']
        key_cols = ['event_type', 'purpose', 'letter']
        event_map = EventRemap(key_cols, target_cols)
        df = event_map.make_template(events_path)
        self.assertEqual(85, len(df), "The unique mapped keys should have same number of keys")

    def test_remap_events_constructor(self):
        t_map = EventRemap(self.key_cols, self.target_cols)
        self.assertIsInstance(t_map, EventRemap)
        df = t_map.col_map
        self.assertIsInstance(df, pd.DataFrame)
        try:
            EventRemap([], ['a'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'EventRemap threw the wrong exception {ex} when no key columns')
        else:
            self.fail('EventRemap should have thrown a HedFileError exception when no key columns')

        try:
            EventRemap(['a', 'b', 'c'], ['b', 'c', 'd'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'EventRemap threw the wrong exception {ex} when no key and target columns overlap')
        else:
            self.fail('EventRemap should have thrown a HedFileError exception when no key and target columns overlap')

        try:
            EventRemap(['a'], [])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'EventRemap threw the wrong exception {ex} when no target columns')
        else:
            self.fail('EventRemap should have thrown a HedFileError exception when no target columns')

    def test_remap_events_no_reorder(self):
        t_map = EventRemap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        t_map.update_map(stern_df)
        stern_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        df_new, missing = t_map.remap_events(stern_test1)
        self.assertFalse(missing, "remap_events should return empty missing when all events accounted for")
        self.assertEqual(len(stern_test1), len(df_new), "remap_events should not change number rows in events file")
        self.assertEqual(df_new.iloc[3]["event_type"], 'show_letter',
                         "remap_events should not change number rows in events file")

    def test_update_map(self):
        t_map = EventRemap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        t_map.update_map(stern_df)
        df_map = t_map.col_map
        df_dict = t_map.map_dict
        self.assertEqual(len(df_map), len(stern_df), "update_map map should contain all the entries")
        self.assertEqual(len(df_dict.keys()), len(stern_df),
                         "update_map dictionary should contain all the entries")

    def test_update_map_missing_key(self):
        keys = self.key_cols + ['another']
        t_map = EventRemap(keys, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        try:
            t_map.update_map(stern_df)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'update_map threw the wrong exception {ex} when key column missing')
        else:
            self.fail('update_map should have thrown a HedFileError exception when key column was missing')

    def test_extract_dataframe(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        df_new = EventRemap.extract_dataframe(events_path)
        self.assertIsInstance(df_new, pd.DataFrame)
        self.assertEqual(len(df_new), 85, f"extract_dataframe should return correct number of rows")
        self.assertEqual(len(df_new.columns), 4, f"extract_dataframe should return correct number of rows")
        df_new1 = EventRemap.extract_dataframe(events_path)
        self.assertIsInstance(df_new1, pd.DataFrame)
        self.assertEqual(len(df_new1), 85, f"extract_dataframe should return correct number of rows")
        self.assertEqual(len(df_new1.columns), 4, f"extract_dataframe should return correct number of rows")
        df_new.iloc[0]['type'] = 'Pear'
        self.assertNotEqual(df_new.iloc[0]['type'], df_new1.iloc[0]['type'],
                            "extract_dataframe returns a new dataframe")

    def test_reorder_columns(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        df = EventRemap.extract_dataframe(events_path)
        df_new = EventRemap.reorder_columns(df, ['event_type', 'type'])
        self.assertEqual(len(df_new), 85, f"reorder_columns should return correct number of rows")
        self.assertEqual(len(df_new.columns), 2, f"reorder_columns should return correct number of rows")
        self.assertEqual(len(df), 85, f"reorder_columns should return correct number of rows")
        self.assertEqual(len(df.columns), 4, f"reorder_columns should return correct number of rows")
        df_new1 = EventRemap.reorder_columns(df, ['event_type', 'type', 'baloney'])
        self.assertEqual(len(df_new1), 85, f"reorder_columns should return correct number of rows")
        self.assertEqual(len(df_new1.columns), 2, f"reorder_columns should return correct number of rows")

    def test_reorder_columns_no_skip(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        try:
            EventRemap.reorder_columns(events_path, ['event_type', 'type', 'baloney'], skip_missing=False)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'reorder_columns threw the wrong exception {str(ex)} when missing column')
        else:
            self.fail('reorder_columns should have thrown a HedFileError exception when missing')

    def test_separate_columns(self):
        base_cols = ['a', 'b', 'c', 'd']
        present, missing = EventRemap.separate_columns(base_cols, [])
        self.assertFalse(present, "separate_columns should have empty present when no target columns")
        self.assertFalse(missing, "separate_columns should have empty missing when no target columns")
        present, missing = EventRemap.separate_columns(base_cols, ['b', 'd'])
        self.assertEqual(len(present), len(['b', 'd']),
                         "separate_columns should have target columns present when target columns subset of base")
        self.assertFalse(missing, "separate_columns should no missing columns when target columns subset of base")
        present, missing = EventRemap.separate_columns(base_cols, base_cols)
        self.assertEqual(len(present), len(base_cols),
                         "separate_columns should have target columns present when target columns equals base")
        self.assertFalse(missing, "separate_columns should no missing columns when target columns equals base")
        present, missing = EventRemap.separate_columns(base_cols, ['g', 'h'])
        self.assertFalse(present, "separate_columns should have empty present when target columns do not overlap base")
        self.assertEqual(len(missing), 2, "separate_columns should have all target columns missing")
