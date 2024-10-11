import io
import unittest
import os
import shutil
from hed.models.sidecar import Sidecar
from hed.schema.hed_schema_io import load_schema_version
from hed.models.base_input import BaseInput
from hed.models.tabular_input import TabularInput
from hed.models.column_mapper import ColumnMapper
from hed.models.definition_dict import DefinitionDict
from hed import schema
from hed.errors.exceptions import HedFileError
from hed.errors.error_types import ErrorContext, ValidationErrors
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

        issues = opened_file.validate(load_schema_version("8.3.0"))
        self.assertEqual(issues[0][ErrorContext.ROW], 5)
        df.at[3, "onset"] = 1.5
        opened_file = TabularInput(df)
        self.assertFalse(opened_file.needs_sorting)

        df.at[3, "onset"] = 1.0
        opened_file = TabularInput(df)
        self.assertTrue(opened_file.needs_sorting)
        issues = opened_file.validate(load_schema_version("8.3.0"))
        # Should still report the same issue row despite needing sorting for validation
        self.assertEqual(issues[0]['code'], ValidationErrors.ONSETS_UNORDERED)
        self.assertEqual(issues[1][ErrorContext.ROW], 5)

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
