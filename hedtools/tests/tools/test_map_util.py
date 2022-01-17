import os
import unittest
from hed.tools.col_dict import ColumnDict
from hed.tools.io_util import get_file_list, make_file_dict
from hed.tools.map_util import get_columns_info, get_key_counts, make_combined_dicts, update_dict_counts
from hed.tools.data_util import get_new_dataframe


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bids_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids')
        stern_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "auditory_visual_shift_events.tsv")

    def test_get_columns_info(self):
        df = get_new_dataframe(self.stern_test2_path)
        col_info = get_columns_info(df)
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertEqual(len(col_info.keys()), len(df.columns),
                         "get_columns_info should return a dictionary with a key for each column")

    def test_get_columns_info_skip_columns(self):
        df = get_new_dataframe(self.stern_test2_path)
        col_info = get_columns_info(df, ['latency'])
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertEqual(len(col_info.keys()), len(df.columns) - 1,
                         "get_columns_info should return a dictionary with a key for each column included")
        col_info = get_columns_info(df, list(df.columns.values))
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertFalse(col_info, "get_columns_info should return a dictionary with a key for each column included")

    def test_get_key_counts(self):
        key_counts1 = get_key_counts(self.bids_dir)
        self.assertIsInstance(key_counts1, dict, "get_columns_info should return a dictionary")
        self.assertEqual(len(key_counts1), 10, "get_key_counts should have key for each column if non skipped")
        self.assertTrue('event_type' in key_counts1, "The dictionary has an event_type key")
        self.assertEqual(len(key_counts1['event_type']), 8, "get_key_counts has right number of entries for event_type")
        self.assertTrue('onset' in key_counts1, "get_key_counts dictionary has onset if not skipped")

        key_counts2 = get_key_counts(self.bids_dir, skip_cols=["onset", "duration", "sample"])
        self.assertIsInstance(key_counts2, dict, "get_columns_info should return a dictionary")
        self.assertEqual(len(key_counts2), 7, "get_key_counts should have key for each column if non skipped")
        self.assertTrue('event_type' in key_counts2, "The dictionary has an event_type key")
        self.assertEqual(len(key_counts2['event_type']), 8, "get_key_counts has right number of entries for event_type")
        self.assertTrue('onset' not in key_counts2, "get_key_counts dictionary does not have onset if skipped")

    def test_make_combined_dicts(self):
        files_bids = get_file_list(self.bids_dir, extensions=[".tsv"], name_suffix="_events")
        file_dict = make_file_dict(files_bids)
        dicts_all1, dicts1 = make_combined_dicts(file_dict)
        self.assertTrue(isinstance(dicts_all1, ColumnDict), "make_combined_dicts should return a ColumnDict")
        self.assertTrue(isinstance(dicts1, dict), "make_combined_dicts should also return a dictionary of file names")
        self.assertEqual(len(dicts1), 2, "make_combined_dicts should return correct number of file names")
        self.assertEqual(len(dicts_all1.categorical_info), 10,
                         "make_combined_dicts should return right number of entries")
        dicts_all2, dicts2 = make_combined_dicts(file_dict, skip_cols=["onset", "duration", "sample"])
        self.assertTrue(isinstance(dicts_all2, ColumnDict), "make_combined_dicts should return a ColumnDict")
        self.assertTrue(isinstance(dicts2, dict), "make_combined_dicts should also return a dictionary of file names")
        self.assertEqual(len(dicts2), 2, "make_combined_dicts should return correct number of file names")
        self.assertEqual(len(dicts_all2.categorical_info), 7,
                         "make_combined_dicts should return right number of entries")

    def test_update_dict_counts(self):
        files_bids = get_file_list(self.bids_dir, extensions=[".tsv"], name_suffix="_events")
        dataframe = get_new_dataframe(files_bids[0])
        count_dicts = {}
        update_dict_counts(count_dicts, "onset", dataframe["onset"])
        self.assertTrue("onset" in count_dicts, "update_dict_counts updates a column counts")
        self.assertEqual(len(count_dicts["onset"]), 551, "update_dict_counts has the right number of counts")
        update_dict_counts(count_dicts, "onset", dataframe["onset"])
        self.assertEqual(len(count_dicts["onset"]), 551, "update_dict_counts has the right number of counts")


if __name__ == '__main__':
    unittest.main()
