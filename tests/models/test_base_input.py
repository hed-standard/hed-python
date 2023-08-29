import io
import unittest
import os
import shutil
from hed import Sidecar
from hed import BaseInput, TabularInput
from hed.models.column_mapper import ColumnMapper
from hed.models import DefinitionDict
from hed import schema
from hed import HedFileError

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
                                                    '../data/schema_tests/HED8.0.0.xml'))
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
        # todo: add unit tests for type_defs in tsv file
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


class TestInsertColumns(unittest.TestCase):

    def test_insert_columns_simple(self):
        df = pd.DataFrame({
            "column1": ["{column2}, Event, Action"],
            "column2": ["Item"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Item, Event, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_multiple_rows(self):
        df = pd.DataFrame({
            "column1": ["{column2}, Event, Action", "Event, Action"],
            "column2": ["Item", "Subject"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Item, Event, Action", "Event, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_multiple_columns(self):
        df = pd.DataFrame({
            "column1": ["{column2}, Event, {column3}, Action"],
            "column2": ["Item"],
            "column3": ["Subject"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Item, Event, Subject, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2", "column3"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_four_columns(self):
        df = pd.DataFrame({
            "column1": ["{column2}, Event, {column3}, Action"],
            "column2": ["Item"],
            "column3": ["Subject"],
            "column4": ["Data"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Item, Event, Subject, Action"],
            "column4": ["Data"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2", "column3"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["Item"],
            "column3": ["Subject"],
            "column4": ["Data"]
        })
        expected_df = pd.DataFrame({
            "column1": ["(Item, (Subject, Data)), Event, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses_na_values(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["Data"],
            "column3": ["n/a"],
            "column4": ["n/a"]
        })
        expected_df = pd.DataFrame({
            "column1": ["(Data), Event, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses_na_values2(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["n/a"],
            "column3": ["n/a"],
            "column4": ["Data"]
        })
        expected_df = pd.DataFrame({
            "column1": ["((Data)), Event, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses_mixed_na_values(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["n/a"],
            "column3": ["Subject"],
            "column4": ["n/a"]
        })
        expected_df = pd.DataFrame({
            "column1": ["((Subject)), Event, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses_all_na_values(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["n/a"],
            "column3": ["n/a"],
            "column4": ["n/a"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Event, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_parentheses(self):
        df = pd.DataFrame({
            "column1": ["({column2}), Event, Action"],
            "column2": ["Item"]
        })
        expected_df = pd.DataFrame({
            "column1": ["(Item), Event, Action"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_parentheses_na_values(self):
        df = pd.DataFrame({
            "column1": ["({column2}), Event, Action"],
            "column2": ["n/a"],
            "column3": ["n/a"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Event, Action"],
            "column3": ["n/a"]
        })
        result = BaseInput._handle_curly_braces_refs(df, refs=["column2"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)


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
