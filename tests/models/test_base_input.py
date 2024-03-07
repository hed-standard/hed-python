import io
import unittest
import os
import shutil
from hed import Sidecar, load_schema_version
from hed import BaseInput, TabularInput
from hed.models.column_mapper import ColumnMapper
from hed.models import DefinitionDict
from hed import schema
from hed import HedFileError
from hed.errors import ErrorContext, ValidationErrors


import pandas as pd
import numpy as np



class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # todo: clean up these unit tests/add more
        base_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../data/'))
        cls.base_data_dir = base_data_dir
        json_def_filename = os.path.join(base_data_dir, "sidecar_tests/both_types_events_with_defs.json")
        # cls.json_def_filename = json_def_filename
        json_def_sidecar = Sidecar(json_def_filename)
        events_path = os.path.join(base_data_dir, '../data/validator_tests/bids_events_no_index.tsv')
        cls.tabular_file = TabularInput(events_path, sidecar=json_def_sidecar)

        base_output = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        cls.base_output_folder = base_output
        os.makedirs(base_output, exist_ok=True)

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                       '../data/bids_tests/eeg_ds003645s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../data/schema_tests/HED8.2.0.xml'))
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))

        cls.hed_schema = schema.load_schema(schema_path)
        sidecar1 = Sidecar(json_path, name='face_sub1_json')
        mapper1 = ColumnMapper(sidecar=sidecar1, optional_tag_columns=['HED'], warn_on_missing_column=False)
        cls.input_data1 = BaseInput(events_path, file_type='.tsv', has_column_names=True,
                                    name="face_sub1_events", mapper=mapper1, allow_blank_names=False)
        cls.input_data2 = BaseInput(events_path, file_type='.tsv', has_column_names=True, name="face_sub2_events")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_gathered_defs(self):
        # todo: probably remove this test?
        # todo: add unit tests for definitions in tsv file
        defs = DefinitionDict.get_as_strings(self.tabular_file._sidecar.extract_definitions(hed_schema=self.hed_schema))
        expected_defs = {
            'jsonfiledef': '(Acceleration/#,Item/JsonDef1)',
            'jsonfiledef2': '(Age/#,Item/JsonDef2)',
            'jsonfiledef3': '(Age/#)',
            'takesvaluedef': '(Age/#)',
            'valueclassdef': '(Acceleration/#)'
        }
        self.assertEqual(defs, expected_defs)

    def test_file_not_found(self):
        with self.assertRaises(HedFileError):
            BaseInput('nonexistent_file.tsv')

    def test_invalid_input_type_int(self):
        with self.assertRaises(HedFileError):
            BaseInput(123)

    def test_invalid_input_type_dict(self):
        with self.assertRaises(HedFileError):
            BaseInput({'key': 'value'})

class TestSortingByOnset(unittest.TestCase):
    @staticmethod
    def generate_test_dataframe():
        data = {
            'onset': [0.5, 1.0, 1.5, 2.0, 2.5],
            'HED': [
                'Age/1',
                'Age/2',
                'Age/3',
                'NotATag',
                'Age/5'
            ]
        }

        df = pd.DataFrame(data)

        return df

    def test_needs_sort(self):
        df = self.generate_test_dataframe()
        opened_file = TabularInput(df)
        self.assertFalse(opened_file.needs_sorting)

        issues = opened_file.validate(load_schema_version("8.2.0"))
        self.assertEqual(issues[1][ErrorContext.ROW], 5)
        df.at[3, "onset"] = 1.5
        opened_file = TabularInput(df)
        self.assertFalse(opened_file.needs_sorting)

        df.at[3, "onset"] = 1.0
        opened_file = TabularInput(df)
        self.assertTrue(opened_file.needs_sorting)
        issues = opened_file.validate(load_schema_version("8.2.0"))
        # Should still report the same issue row despite needing sorting for validation
        self.assertEqual(issues[1]['code'], ValidationErrors.ONSETS_OUT_OF_ORDER)
        self.assertEqual(issues[2][ErrorContext.ROW], 5)

    def test_sort(self):
        from hed.models.df_util import sort_dataframe_by_onsets
        df = self.generate_test_dataframe()
        df2 = sort_dataframe_by_onsets(df)
        self.assertTrue(df.equals(df2))

        df.at[3, "onset"] = 1.5
        df2 = sort_dataframe_by_onsets(df)
        self.assertTrue(df.equals(df2))

        df.at[3, "onset"] = 1.0
        df2 = sort_dataframe_by_onsets(df)
        self.assertFalse(df.equals(df2))


class TestCombineDataframe(unittest.TestCase):
    def test_combine_dataframe_with_strings(self):
        data = {
            'A': ['apple', 'banana', 'cherry'],
            'B': ['dog', 'elephant', 'fox'],
            'C': ['guitar', 'harmonica', 'piano']
        }
        df = pd.DataFrame(data)
        result = BaseInput.combine_dataframe(df)
        expected = pd.Series(['apple, dog, guitar', 'banana, elephant, harmonica', 'cherry, fox, piano'])
        self.assertTrue(result.equals(expected))

    def test_combine_dataframe_with_nan_values(self):
        data = {
            'A': ['apple', np.nan, 'cherry'],
            'B': [np.nan, 'elephant', 'fox'],
            'C': ['guitar', 'harmonica', np.nan]
        }
        df = pd.DataFrame(data)
        # this is called on load normally
        df = df.fillna("n/a")
        result = BaseInput.combine_dataframe(df)
        expected = pd.Series(['apple, guitar', 'elephant, harmonica', 'cherry, fox'])
        self.assertTrue(result.equals(expected))

    def test_combine_dataframe_with_empty_values(self):
        data = {
            'A': ['apple', '', 'cherry'],
            'B': ['', 'elephant', 'fox'],
            'C': ['guitar', 'harmonica', '']
        }
        df = pd.DataFrame(data)

        result = BaseInput.combine_dataframe(df)
        expected = pd.Series(['apple, guitar', 'elephant, harmonica', 'cherry, fox'])
        self.assertTrue(result.equals(expected))

    def test_combine_dataframe_with_mixed_values(self):
        data = {
            'A': ['apple', np.nan, 'cherry', 'n/a', ''],
            'B': [np.nan, 'elephant', 'fox', 'n/a', ''],
            'C': ['guitar', 'harmonica', np.nan, 'n/a', '']
        }
        df = pd.DataFrame(data)
        # this is called on load normally
        df = df.fillna("n/a")
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, header=False, index=False)
        csv_buffer.seek(0)

        # Use the same loading function we normally use to verify n/a translates right.
        loaded_df = pd.read_csv(csv_buffer, header=None)
        loaded_df = loaded_df.fillna("n/a")
        result = BaseInput.combine_dataframe(loaded_df)
        expected = pd.Series(['apple, guitar', 'elephant, harmonica', 'cherry, fox', '', ''])
        self.assertTrue(result.equals(expected))


class TestOnsetDict(unittest.TestCase):
    def test_empty_and_single_onset(self):
        self.assertEqual(BaseInput._indexed_dict_from_onsets([]), {})
        self.assertEqual(BaseInput._indexed_dict_from_onsets([3.5]), {3.5: [0]})

    def test_identical_and_approx_equal_onsets(self):
        self.assertEqual(BaseInput._indexed_dict_from_onsets([3.5, 3.5]), {3.5: [0, 1]})
        self.assertEqual(BaseInput._indexed_dict_from_onsets([3.5, 3.500000001]), {3.5: [0], 3.500000001: [1]})
        self.assertEqual(BaseInput._indexed_dict_from_onsets([3.5, 3.5000000000001]), {3.5: [0, 1]})

    def test_distinct_and_mixed_onsets(self):
        self.assertEqual(BaseInput._indexed_dict_from_onsets([3.5, 4.0, 4.4]), {3.5: [0], 4.0: [1], 4.4: [2]})
        self.assertEqual(BaseInput._indexed_dict_from_onsets([3.5, 3.5, 4.0, 4.4]), {3.5: [0, 1], 4.0: [2], 4.4: [3]})
        self.assertEqual(BaseInput._indexed_dict_from_onsets([4.0, 3.5, 4.4, 4.4]), {4.0: [0], 3.5: [1], 4.4: [2, 3]})

    def test_complex_onsets(self):
        # Negative, zero, and positive onsets
        self.assertEqual(BaseInput._indexed_dict_from_onsets([-1.0, 0.0, 1.0]), {-1.0: [0], 0.0: [1], 1.0: [2]})

        # Very close but distinct onsets
        self.assertEqual(BaseInput._indexed_dict_from_onsets([1.0, 1.0 + 1e-8, 1.0 + 2e-8]),
                         {1.0: [0], 1.0 + 1e-8: [1], 1.0 + 2e-8: [2]})
        # Very close
        self.assertEqual(BaseInput._indexed_dict_from_onsets([1.0, 1.0 + 1e-10, 1.0 + 2e-10]),
                         {1.0: [0, 1, 2]})

        # Mixed scenario
        self.assertEqual(BaseInput._indexed_dict_from_onsets([3.5, 3.5, 4.0, 4.4, 4.4, -1.0]),
                         {3.5: [0, 1], 4.0: [2], 4.4: [3, 4], -1.0: [5]})

    def test_empty_and_single_item_series(self):
        self.assertTrue(BaseInput._filter_by_index_list(pd.Series([], dtype=str), {}).equals(pd.Series([], dtype=str)))
        self.assertTrue(BaseInput._filter_by_index_list(pd.Series(["apple"]), {0: [0]}).equals(pd.Series(["apple"])))

    def test_two_item_series_with_same_onset(self):
        input_series = pd.Series(["apple", "orange"])
        expected_series = pd.Series(["apple,orange", ""])
        self.assertTrue(BaseInput._filter_by_index_list(input_series, {0: [0, 1]}).equals(expected_series))

    def test_multiple_item_series(self):
        input_series = pd.Series(["apple", "orange", "banana", "mango"])
        indexed_dict = {0: [0, 1], 1: [2], 2: [3]}
        expected_series = pd.Series(["apple,orange", "", "banana", "mango"])
        self.assertTrue(BaseInput._filter_by_index_list(input_series, indexed_dict).equals(expected_series))

    def test_complex_scenarios(self):
        # Test with negative, zero and positive onsets
        original = pd.Series(["negative", "zero", "positive"])
        indexed_dict = {-1: [0], 0: [1], 1: [2]}
        expected_series1 = pd.Series(["negative", "zero", "positive"])
        self.assertTrue(BaseInput._filter_by_index_list(original, indexed_dict).equals(expected_series1))

        # Test with more complex indexed_dict
        original2 = ["apple", "orange", "banana", "mango", "grape"]
        indexed_dict2= {0: [0, 1], 1: [2], 2: [3, 4]}
        expected_series2 = pd.Series(["apple,orange", "", "banana", "mango,grape", ""])
        self.assertTrue(BaseInput._filter_by_index_list(original2, indexed_dict2).equals(expected_series2))

