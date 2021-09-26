import unittest
import os
import pandas as pd
from hed.errors.exceptions import HedFileError
from hedweb.remap_events import RemapEvents
from hedweb.remap_utils import extract_dataframe, reorder_columns, separate_columns


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
        t_map = RemapEvents(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        t_map.update_map(stern_df)
        t_col = t_map.col_map
        stern_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        for index, row in stern_test1.iterrows():
            key, key_value = t_map._lookup_cols(row)
            self.assertEqual(t_col.iloc[key_value]['type'], row['type'], "The key should be looked up correctly")

    def test_make_template(self):
        event_map = RemapEvents(self.key_cols, self.target_cols)
        df = event_map.make_template(self.stern_map_path)
        self.assertEqual(len(df.columns), len(self.key_cols) + len(self.target_cols),
                         "The template should have keys and targets")
        self.assertEqual(len(df), 85, "Sternberg template should have 85 keys")
        self.assertEqual(len(df), 85, "Sternberg template should have 85 keys")
        self.assertEqual(df.iloc[0]["event_type"], "n/a", "Sternberg template first key is right click")

    def test_make_template_with_targets(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        event_map = RemapEvents(self.key_cols, self.target_cols)
        df = event_map.make_template(events_path, use_targets=True)
        self.assertEqual(len(df.columns), len(self.key_cols) + len(self.target_cols),
                         "The template should have keys and targets")
        self.assertEqual(len(df), 85, "Sternberg template should have 85 keys")
        self.assertEqual(df.iloc[0]["event_type"], "right_click", "Sternberg template first key is right click")

    def test_make_template_with_keys_unique_true(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        df = extract_dataframe(events_path)
        df.iloc[0] = df.iloc[1].copy()
        event_map = RemapEvents(self.key_cols, self.target_cols)
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
        df = extract_dataframe(events_path)
        df.iloc[0] = df.iloc[1].copy()
        event_map = RemapEvents(self.key_cols, self.target_cols)

        df_new = event_map.make_template(df)
        self.assertEqual(len(df_new.columns), len(self.key_cols) + len(self.target_cols),
                         "The template should have keys and targets")
        self.assertEqual(len(df_new), 84, "Sternberg template with a duplicate should have 84 keys")

    def test_make_template_multiple_columns(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        target_cols = ['type']
        key_cols = ['event_type', 'purpose', 'letter']
        event_map = RemapEvents(key_cols, target_cols)
        df = event_map.make_template(events_path)
        self.assertEqual(85, len(df), "The unique mapped keys should have same number of keys")

    def test_remap_events_constructor(self):
        t_map = RemapEvents(self.key_cols, self.target_cols)
        self.assertIsInstance(t_map, RemapEvents)
        df = t_map.col_map
        self.assertIsInstance(df, pd.DataFrame)
        try:
            RemapEvents([], ['a'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'RemapEvents threw the wrong exception {ex} when no key columns')
        else:
            self.fail('RemapEvents should have thrown a HedFileError exception when no key columns')

        try:
            RemapEvents(['a', 'b', 'c'], ['b', 'c', 'd'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'RemapEvents threw the wrong exception {ex} when no key and target columns overlap')
        else:
            self.fail('RemapEvents should have thrown a HedFileError exception when no key and target columns overlap')

        try:
            RemapEvents(['a'], [])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'RemapEvents threw the wrong exception {ex} when no target columns')
        else:
            self.fail('RemapEvents should have thrown a HedFileError exception when no target columns')

    def test_remap_events_no_reorder(self):
        t_map = RemapEvents(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        t_map.update_map(stern_df)
        stern_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        df_new, missing = t_map.remap_events(stern_test1)
        self.assertFalse(missing, "remap_events should return empty missing when all events accounted for")
        self.assertEqual(len(stern_test1), len(df_new), "remap_events should not change number rows in events file")
        self.assertEqual(df_new.iloc[3]["event_type"], 'show_letter',
                         "remap_events should not change number rows in events file")

    def test_update_map(self):
        t_map = RemapEvents(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        t_map.update_map(stern_df)
        df_map = t_map.col_map
        df_dict = t_map.map_dict
        self.assertEqual(len(df_map), len(stern_df), "update_map map should contain all the entries")
        self.assertEqual(len(df_dict.keys()), len(stern_df),
                         "update_map dictionary should contain all the entries")

    def test_update_map_missing_key(self):
        keys = self.key_cols + ['another']
        t_map = RemapEvents(keys, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        try:
            t_map.update_map(stern_df)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'update_map threw the wrong exception {ex} when key column missing')
        else:
            self.fail('update_map should have thrown a HedFileError exception when key column was missing')
