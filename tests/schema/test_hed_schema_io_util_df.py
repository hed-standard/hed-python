import unittest
import pandas as pd
from hed.schema.schema_io.df_util import _merge_dataframes, merge_dataframe_dicts
from hed import HedFileError


class TestMergeDataFrames(unittest.TestCase):
    def setUp(self):
        # Sample DataFrames for testing
        self.df1 = pd.DataFrame({
            'label': [1, 2, 3],
            'A_col1': ['A1', 'A2', 'A3'],
            'A_col2': [10, 20, 30]
        })

        self.df2 = pd.DataFrame({
            'label': [2, 3, 4],
            'B_col1': ['B2', 'B3', 'B4'],
            'A_col2': [200, 300, 400]
        })

        self.df3 = pd.DataFrame({
            'A_col1': ['A1', 'A2', 'A3'],
            'label': [2, 3, 4],
            'B_col1': ['B2', 'B3', 'B4'],
            'A_col2': [200, 300, 400],
            'B_col2': [3, 4, 5]
        })

    def test_merge_all_columns_present(self):
        # Test that all columns from both DataFrames are present in the result
        result = _merge_dataframes(self.df1, self.df2, 'label')
        expected_columns = ['label', 'A_col1', 'A_col2', 'B_col1']
        self.assertListEqual(list(result.columns), expected_columns)


    def test_merge_all_columns_present_different_order(self):
        # Test that all columns from both DataFrames are present in the result
        result = _merge_dataframes(self.df1, self.df3, 'label')
        expected_columns = ['label', 'A_col1', 'A_col2', 'B_col1', 'B_col2']
        self.assertListEqual(list(result.columns), expected_columns)

    def test_merge_rows_from_df1(self):
        # Test that only rows from df1 are present in the result
        result = _merge_dataframes(self.df1, self.df2, 'label')
        expected_labels = [1, 2, 3]  # Only labels present in df1
        self.assertListEqual(list(result['label']), expected_labels)

    def test_merge_add_columns_from_df2(self):
        # Test that columns from df2 are added to df1
        result = _merge_dataframes(self.df1, self.df2, 'label')
        self.assertIn('B_col1', result.columns)
        self.assertEqual(result.loc[result['label'] == 2, 'B_col1'].values[0], 'B2')
        self.assertEqual(result.loc[result['label'] == 3, 'B_col1'].values[0], 'B3')

    def test_fill_missing_values(self):
        # Test that missing values are filled with ''
        result = _merge_dataframes(self.df1, self.df2, 'label')
        self.assertEqual(result.loc[result['label'] == 1, 'B_col1'].values[0], '')

    def test_reset_index(self):
        # Test that the index is reset correctly
        result = _merge_dataframes(self.df1, self.df2, 'label')
        expected_index = [0, 1, 2]
        self.assertListEqual(list(result.index), expected_index)

    def test_missing_label_column_raises_error(self):
        # Test that if one of the DataFrames does not have 'label' column, a HedFileError is raised
        df_no_label = pd.DataFrame({
            'A_col1': ['A1', 'A2', 'A3'],
            'A_col2': [10, 20, 30]
        })
        with self.assertRaises(HedFileError):
            _merge_dataframes(self.df1, df_no_label, 'label')
        with self.assertRaises(HedFileError):
            _merge_dataframes(df_no_label, self.df2, 'label')

    def test_merge_source_empty(self):
        # Test that throws an exception if one frame is empty
        with self.assertRaises(HedFileError):
            _merge_dataframes(pd.DataFrame(), self.df1, 'label')
        with self.assertRaises(HedFileError):
            _merge_dataframes(self.df1, pd.DataFrame(), 'label')


class TestMergeDataFrameDicts(unittest.TestCase):
    def setUp(self):
        # Sample DataFrames for testing
        self.df1 = pd.DataFrame({
            'label': [1, 2, 3],
            'A_col1': ['A1', 'A2', 'A3'],
            'A_col2': [10, 20, 30]
        })

        self.df2 = pd.DataFrame({
            'label': [2, 3, 4],
            'B_col1': ['B2', 'B3', 'B4'],
            'A_col2': [200, 300, 400]
        })

        self.dict1 = {'df1': self.df1}
        self.dict2 = {'df1': self.df2, 'df2': self.df2}

    def test_merge_common_keys(self):
        # Test that common keys are merged using _merge_dataframes
        result = merge_dataframe_dicts(self.dict1, self.dict2, 'label')
        expected_columns = ['label', 'A_col1', 'A_col2', 'B_col1']
        self.assertIn('df1', result)
        self.assertListEqual(list(result['df1'].columns), expected_columns)

    def test_merge_unique_keys(self):
        # Test that unique keys are preserved in the result dictionary
        result = merge_dataframe_dicts(self.dict1, self.dict2, 'label')
        self.assertIn('df2', result)
        self.assertTrue(result['df2'].equals(self.df2))

    def test_merge_no_common_keys(self):
        # Test merging dictionaries with no common keys
        dict1 = {'df1': self.df1}
        dict2 = {'df2': self.df2}
        result = merge_dataframe_dicts(dict1, dict2, 'label')
        self.assertIn('df1', result)
        self.assertIn('df2', result)
        self.assertTrue(result['df1'].equals(self.df1))
        self.assertTrue(result['df2'].equals(self.df2))


if __name__ == '__main__':
    unittest.main()
