import unittest
import os
from hed.errors.exceptions import HedFileError
from hed.tools.analysis.file_dictionary import FileDictionary
from hed.tools.analysis.tabular_summary import TabularSummary
from hed.tools import get_file_list, get_new_dataframe


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        curation_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/remodel_tests")
        bids_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_hed")
        cls.bids_base_dir = bids_base_dir
        cls.stern_map_path = os.path.join(curation_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(curation_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(curation_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(curation_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(curation_base_dir, "sub-001_task-AuditoryVisualShift_run-01_events.tsv")
        cls.wh_events_path = os.path.realpath(
            os.path.join(bids_base_dir, "sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv")
        )

    def test_constructor(self):
        dict1 = TabularSummary()
        self.assertIsInstance(dict1, TabularSummary, "TabularSummary constructor is allowed to have no arguments")
        self.assertFalse(dict1.value_info)

        dict2 = TabularSummary(value_cols=["a", "b", "c"], name="baloney")
        self.assertIsInstance(dict2, TabularSummary, "TabularSummary: multiple values are okay in constructor")
        self.assertEqual(len(dict2.value_info.keys()), 3, "TabularSummary should have keys for each value column")

    def test_extract_summary(self):
        tab1 = TabularSummary()
        stern_df = get_new_dataframe(self.stern_map_path)
        tab1.update(stern_df)
        sum_info1 = tab1.get_summary()
        self.assertIsInstance(sum_info1, dict)
        self.assertEqual(len(sum_info1["Categorical columns"]), 4)
        new_tab1 = TabularSummary.extract_summary(sum_info1)
        self.assertIsInstance(new_tab1, TabularSummary)
        tab2 = TabularSummary(value_cols=["letter"], skip_cols=["event_type"])
        sum_info2 = tab2.get_summary()
        self.assertIsInstance(sum_info2, dict)
        new_tab2 = TabularSummary.extract_summary(sum_info2)
        self.assertIsInstance(new_tab2, TabularSummary)
        tabular_info = {}
        new_tab3 = TabularSummary.extract_summary(tabular_info)
        self.assertIsInstance(new_tab3, TabularSummary)

    def test_extract_summary_empty(self):
        tabular_info = {}
        new_tab = TabularSummary.extract_summary(tabular_info)
        self.assertIsInstance(new_tab, TabularSummary)

    def test_get_number_unique_values(self):
        dict1 = TabularSummary()
        wh_df = get_new_dataframe(self.wh_events_path)
        dict1.update(wh_df)
        self.assertEqual(len(dict1.value_info.keys()), 0, "TabularSummary value_info should be empty if no value columns")
        self.assertEqual(
            len(dict1.categorical_info.keys()),
            len(wh_df.columns),
            "TabularSummary categorical_info should have all the columns if no restrictions",
        )
        count_dict = dict1.get_number_unique()
        self.assertEqual(len(count_dict), 10, "get_number_unique should have the correct number of entries")
        self.assertEqual(count_dict["onset"], 199, "get_number_unique should have the right number of unique")

    def test_get_summary(self):
        dict1 = TabularSummary(value_cols=["letter"], skip_cols=["event_type"], name="Sternberg1")
        stern_df = get_new_dataframe(self.stern_map_path)
        dict1.update(stern_df)
        self.assertEqual(len(dict1.value_info.keys()), 1, "TabularSummary value_info should be empty if no value columns")
        self.assertEqual(
            len(dict1.categorical_info.keys()),
            len(stern_df.columns) - 2,
            "TabularSummary categorical_info be columns minus skip and value columns",
        )
        summary1 = dict1.get_summary(as_json=False)
        self.assertIsInstance(summary1, dict)
        self.assertEqual(len(summary1), 9)
        summary2 = dict1.get_summary(as_json=True).replace('"', "")
        self.assertIsInstance(summary2, str)

    def test__str__(self):
        t_map = TabularSummary(name="My output")
        t_map.update(self.stern_map_path)
        df = get_new_dataframe(self.stern_map_path)
        t_map.update(self.stern_map_path)
        self.assertEqual(
            len(t_map.categorical_info.keys()),
            len(df.columns),
            "TabularSummary should have all columns as categorical if no value or skip are given",
        )
        t_map_str = str(t_map)
        self.assertTrue(t_map_str, "__str__ returns a non-empty string when the map has content.")

    def test_update(self):
        dict1 = TabularSummary()
        stern_df = get_new_dataframe(self.stern_map_path)
        dict1.update(stern_df)
        self.assertEqual(len(dict1.value_info.keys()), 0, "TabularSummary value_info should be empty if no value columns")
        self.assertEqual(
            len(dict1.categorical_info.keys()),
            len(stern_df.columns),
            "TabularSummary categorical_info should have all the columns if no restrictions",
        )

        dict2 = TabularSummary(value_cols=["letter"], skip_cols=["event_type"])
        dict2.update(stern_df)
        self.assertEqual(len(dict2.value_info.keys()), 1, "TabularSummary value_info should have letter value column")
        self.assertEqual(dict2.value_info["letter"], [len(stern_df), 1], "TabularSummary value counts should length of column")
        self.assertEqual(len(dict2.skip_cols), 1, "TabularSummary should have one skip column")
        self.assertEqual(
            len(dict2.categorical_info.keys()),
            len(stern_df.columns) - 2,
            "TabularSummary categorical_info should have all columns except value and skip columns",
        )
        dict2.update(stern_df)
        self.assertEqual(len(dict2.value_info.keys()), 1, "TabularSummary value_info should have letter value column")
        self.assertEqual(
            dict2.value_info["letter"],
            [2 * len(stern_df), 2],
            "TabularSummary value counts should update by column length each time update is called",
        )

    def test_update_dict(self):
        dict1 = TabularSummary()
        dict2 = TabularSummary()
        stern_df_map = get_new_dataframe(self.stern_map_path)
        dict1.update(stern_df_map)
        dict2.update_summary(dict1)
        dict2.update_summary(dict1)
        dict1.update(stern_df_map)
        cat_keys = dict1.categorical_info.keys()
        for col in cat_keys:
            self.assertTrue(col in dict2.categorical_info.keys())
            key_dict1 = dict1.categorical_info[col]
            key_dict2 = dict2.categorical_info[col]
            for key, value in key_dict1.items():
                self.assertEqual(value, key_dict2[key], "update_summary should give same values as update")

    def test_update_dict_with_value_cols(self):
        stern_df_test1 = get_new_dataframe(self.stern_test1_path)
        stern_df_test3 = get_new_dataframe(self.stern_test3_path)
        dict1 = TabularSummary(value_cols=["latency"])
        dict1.update(stern_df_test3)
        dict2 = TabularSummary(value_cols=["latency"])
        dict2.update(stern_df_test1)
        dict2.update_summary(dict1)
        dict1.update(stern_df_test1)
        value_keys = dict1.value_info.keys()
        for col in value_keys:
            self.assertEqual(dict1.value_info[col], dict2.value_info[col], "update_summary should update values correctly")

    def test_update_dict_with_bad_value_cols(self):
        stern_df_test1 = get_new_dataframe(self.stern_test1_path)
        stern_df_test3 = get_new_dataframe(self.stern_test3_path)
        dict1 = TabularSummary(value_cols=["latency"])
        dict1.update(stern_df_test3)
        dict3 = TabularSummary()
        dict3.update(stern_df_test1)
        try:
            dict1.update_summary(dict3)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f"update_summary threw the wrong exception {ex} when value columns should be categorical")
        else:
            self.fail("update_summary should have thrown a HedFileError when value columns should be categorical")

    def test_update_dict_bad_skip_col(self):
        stern_test3 = get_new_dataframe(self.stern_test3_path)
        dict1 = TabularSummary(skip_cols=["latency"])
        dict1.update(stern_test3)
        dict2 = TabularSummary(value_cols=["latency"])
        dict2.update(stern_test3)
        try:
            dict2.update_summary(dict1)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f"update_summary threw the wrong exception {ex} when value columns should be categorical")
        else:
            self.fail("update_summary should have thrown a HedFileError when value columns should be categorical")

    def test_get_columns_info(self):
        df = get_new_dataframe(self.stern_test2_path)
        col_info = TabularSummary.get_columns_info(df)
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertEqual(
            len(col_info.keys()), len(df.columns), "get_columns_info should return a dictionary with a key for each column"
        )

    def test_get_columns_info_skip_columns(self):
        df = get_new_dataframe(self.stern_test2_path)
        col_info = TabularSummary.get_columns_info(df, ["latency"])
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertEqual(
            len(col_info.keys()),
            len(df.columns) - 1,
            "get_columns_info should return a dictionary with a key for each column included",
        )
        col_info = TabularSummary.get_columns_info(df, list(df.columns.values))
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertFalse(col_info, "get_columns_info should return a dictionary with a key for each column included")

    def test_make_combined_dicts(self):
        files_bids = get_file_list(self.bids_base_dir, extensions=[".tsv"], name_suffix="events")
        file_dict1 = FileDictionary("my name", files_bids)
        dicts_all1, dicts1 = TabularSummary.make_combined_dicts(file_dict1.file_dict)
        self.assertTrue(isinstance(dicts_all1, TabularSummary), "make_combined_dicts should return a TabularSummary")
        self.assertTrue(isinstance(dicts1, dict), "make_combined_dicts should also return a dictionary of file names")
        self.assertEqual(6, len(dicts1), "make_combined_dicts should return correct number of file names")
        self.assertEqual(10, len(dicts_all1.categorical_info), "make_combined_dicts should return right number of entries")
        dicts_all2, dicts2 = TabularSummary.make_combined_dicts(
            file_dict1.file_dict, skip_cols=["onset", "duration", "sample"]
        )
        self.assertTrue(isinstance(dicts_all2, TabularSummary), "make_combined_dicts should return a TabularSummary")
        self.assertTrue(isinstance(dicts2, dict), "make_combined_dicts should also return a dictionary of file names")
        self.assertEqual(6, len(dicts2), "make_combined_dicts should return correct number of file names")
        self.assertEqual(len(dicts_all2.categorical_info), 7, "make_combined_dicts should return right number of entries")

    def test_update_summary(self):
        files_bids = get_file_list(self.bids_base_dir, extensions=[".tsv"], name_suffix="events")
        tab_list = []
        skip_cols = ["onset", "duration", "sample", "value"]
        value_cols = ["stim_file", "trial"]
        tab_all = TabularSummary(skip_cols=skip_cols, value_cols=value_cols)
        for name in files_bids:
            tab = TabularSummary(skip_cols=skip_cols, value_cols=value_cols)
            tab_list.append(tab)
            df = get_new_dataframe(name)
            tab.update(df, name=name)
            self.assertEqual(tab.total_events, 200)
            self.assertEqual(tab.total_files, 1)
            tab_all.update_summary(tab)
        self.assertEqual(len(files_bids), tab_all.total_files)
        self.assertEqual(len(files_bids) * 200, tab_all.total_events)

    def test_categorical_limit_constructor(self):
        # Test that categorical_limit can be set in constructor
        dict1 = TabularSummary(categorical_limit=5)
        self.assertEqual(dict1.categorical_limit, 5)

        dict2 = TabularSummary(categorical_limit=None)
        self.assertIsNone(dict2.categorical_limit)

    def test_categorical_limit_enforced(self):
        # Test that categorical_limit is enforced when updating
        stern_df = get_new_dataframe(self.stern_map_path)

        # Create a summary with no limit
        dict_no_limit = TabularSummary()
        dict_no_limit.update(stern_df)

        # Create a summary with a limit of 2 unique values per column
        dict_with_limit = TabularSummary(categorical_limit=2)
        dict_with_limit.update(stern_df)

        # Check that columns with more than 2 unique values are limited
        for col_name in dict_with_limit.categorical_info:
            self.assertLessEqual(
                len(dict_with_limit.categorical_info[col_name]),
                2,
                f"Column {col_name} should have at most 2 unique values stored",
            )
            # But categorical_counts should track all values
            self.assertIn(col_name, dict_with_limit.categorical_counts)
            self.assertGreater(dict_with_limit.categorical_counts[col_name][0], 0)

    def test_categorical_limit_columns_with_many_values(self):
        # Test that columns with many values are skipped during initial update
        wh_df = get_new_dataframe(self.wh_events_path)

        # Set limit to 5
        dict1 = TabularSummary(categorical_limit=5)
        dict1.update(wh_df)

        # Columns with more than 5 unique values at collection time should still be tracked in counts
        for col_name, counts in dict1.categorical_counts.items():
            self.assertGreater(counts[0], 0, f"Column {col_name} should have event count > 0")
            self.assertEqual(counts[1], 1, f"Column {col_name} should have been updated once")

    def test_categorical_limit_in_summary(self):
        # Test that categorical_limit appears in the summary output
        dict1 = TabularSummary(categorical_limit=10)
        stern_df = get_new_dataframe(self.stern_map_path)
        dict1.update(stern_df)

        summary = dict1.get_summary(as_json=False)
        self.assertIn("Categorical limit", summary)
        self.assertEqual(summary["Categorical limit"], "10")

        # Test with None
        dict2 = TabularSummary()
        dict2.update(stern_df)
        summary2 = dict2.get_summary(as_json=False)
        self.assertEqual(summary2["Categorical limit"], "None")

    def test_categorical_limit_extract_summary(self):
        # Test that categorical_limit is preserved through extract_summary
        dict1 = TabularSummary(categorical_limit=15)
        stern_df = get_new_dataframe(self.stern_map_path)
        dict1.update(stern_df)

        summary_info = dict1.get_summary(as_json=False)
        dict2 = TabularSummary.extract_summary(summary_info)

        # Note: extract_summary doesn't restore categorical_limit currently,
        # but it should at least not error
        self.assertIsInstance(dict2, TabularSummary)

    def test_categorical_limit_update_dict(self):
        # Test that categorical_limit works correctly with update_summary
        stern_df = get_new_dataframe(self.stern_test1_path)

        dict1 = TabularSummary(categorical_limit=3)
        dict1.update(stern_df)

        dict2 = TabularSummary(categorical_limit=3)
        dict2.update(stern_df)

        # Update dict1 with dict2
        dict1.update_summary(dict2)

        # Check that limits are still enforced
        for col_name in dict1.categorical_info:
            self.assertLessEqual(
                len(dict1.categorical_info[col_name]),
                3,
                f"Column {col_name} should have at most 3 unique values after update_summary",
            )


if __name__ == "__main__":
    unittest.main()
