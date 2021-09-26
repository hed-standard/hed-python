import os
import unittest
import pandas as pd
from tests.test_web_base import TestWebBase
from hed.errors.exceptions import HedFileError
from hedweb.remap_utils import extract_dataframe, reorder_columns, separate_columns


class Test(TestWebBase):

    def test_extract_dataframe(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        df_new = extract_dataframe(events_path)
        self.assertIsInstance(df_new, pd.DataFrame)
        self.assertEqual(len(df_new), 85, f"extract_dataframe should return correct number of rows")
        self.assertEqual(len(df_new.columns), 4, f"extract_dataframe should return correct number of rows")
        df_new1 = extract_dataframe(events_path)
        self.assertIsInstance(df_new1, pd.DataFrame)
        self.assertEqual(len(df_new1), 85, f"extract_dataframe should return correct number of rows")
        self.assertEqual(len(df_new1.columns), 4, f"extract_dataframe should return correct number of rows")
        df_new.iloc[0]['type'] = 'Pear'
        self.assertNotEqual(df_new.iloc[0]['type'], df_new1.iloc[0]['type'],
                            "extract_dataframe returns a new dataframe")

    def test_get_columns_info(self):
        from hedweb.remap_utils import get_columns_info, extract_dataframe
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_events.tsv')
        df = extract_dataframe(events_path)
        col_info = get_columns_info(df)
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertEqual(len(col_info.keys()), len(df.columns),
                         "get_columns_info should return a dictionary with a key for each column")

    def test_get_columns_info_skip_columns(self):
        from hedweb.remap_utils import get_columns_info, extract_dataframe
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_events.tsv')
        df = extract_dataframe(events_path)
        col_info = get_columns_info(df, ['latency'])
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertEqual(len(col_info.keys()), len(df.columns) - 1,
                         "get_columns_info should return a dictionary with a key for each column included")
        col_info = get_columns_info(df, list(df.columns.values))
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertFalse(col_info, "get_columns_info should return a dictionary with a key for each column included")

    def test_get_event_files(self):
        from hedweb.remap_utils import get_file_list
        dir_css = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../hedweb/static/css')
        dir_web = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../hedweb')
        test_len = len([name for name in os.listdir(dir_css) if os.path.isfile(os.path.join(dir_css, name))])
        file_list1 = get_file_list(dir_css)
        self.assertEqual(test_len, len(file_list1), "get_event_files should have right number of files when same dir")
        file_list2 = get_file_list(dir_web, types=[".css"])
        self.assertEqual(test_len, len(file_list2), "get_event_files should have right number of files")
        file_list3 = get_file_list(dir_web, types=[".html", ".js"])
        for item in file_list3:
            if item.endswith(".html") or item.endswith(".js"):
                continue
            raise HedFileError("BadFileType", "get_event_files expected only .html or .js files", "")

    def test_reorder_columns(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        df = extract_dataframe(events_path)
        df_new = reorder_columns(df, ['event_type', 'type'])
        self.assertEqual(len(df_new), 85, f"reorder_columns should return correct number of rows")
        self.assertEqual(len(df_new.columns), 2, f"reorder_columns should return correct number of rows")
        self.assertEqual(len(df), 85, f"reorder_columns should return correct number of rows")
        self.assertEqual(len(df.columns), 4, f"reorder_columns should return correct number of rows")
        df_new1 = reorder_columns(df, ['event_type', 'type', 'baloney'])
        self.assertEqual(len(df_new1), 85, f"reorder_columns should return correct number of rows")
        self.assertEqual(len(df_new1.columns), 2, f"reorder_columns should return correct number of rows")

    def test_reorder_columns_no_skip(self):
        events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sternberg_map.tsv')
        try:
            reorder_columns(events_path, ['event_type', 'type', 'baloney'], skip_missing=False)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'reorder_columns threw the wrong exception {str(ex)} when missing column')
        else:
            self.fail('reorder_columns should have thrown a HedFileError exception when missing')

    def test_separate_columns(self):
        base_cols = ['a', 'b', 'c', 'd']
        present, missing = separate_columns(base_cols, [])
        self.assertFalse(present, "separate_columns should have empty present when no target columns")
        self.assertFalse(missing, "separate_columns should have empty missing when no target columns")
        present, missing = separate_columns(base_cols, ['b', 'd'])
        self.assertEqual(len(present), len(['b', 'd']),
                         "separate_columns should have target columns present when target columns subset of base")
        self.assertFalse(missing, "separate_columns should no missing columns when target columns subset of base")
        present, missing = separate_columns(base_cols, base_cols)
        self.assertEqual(len(present), len(base_cols),
                         "separate_columns should have target columns present when target columns equals base")
        self.assertFalse(missing, "separate_columns should no missing columns when target columns equals base")
        present, missing = separate_columns(base_cols, ['g', 'h'])
        self.assertFalse(present, "separate_columns should have empty present when target columns do not overlap base")
        self.assertEqual(len(missing), 2, "separate_columns should have all target columns missing")

if __name__ == '__main__':
    unittest.main()
