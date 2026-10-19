import io
import os
import shutil
import socket
import unittest

import numpy as np
import pandas as pd

from hed import schema
from hed.errors.error_types import ErrorContext, ValidationErrors
from hed.errors.exceptions import HedFileError
from hed.models.base_input import BaseInput
from hed.models.column_mapper import ColumnMapper
from hed.models.definition_dict import DefinitionDict
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # todo: clean up these unit tests/add more
        base_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/"))
        cls.base_data_dir = base_data_dir
        json_def_filename = os.path.join(base_data_dir, "sidecar_tests/both_types_events_with_defs.json")
        # cls.json_def_filename = json_def_filename
        json_def_sidecar = Sidecar(json_def_filename)
        events_path = os.path.join(base_data_dir, "../data/validator_tests/bids_events_no_index.tsv")
        cls.tabular_file = TabularInput(events_path, sidecar=json_def_sidecar)

        base_output = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/tests_output/")
        cls.base_output_folder = base_output
        os.makedirs(base_output, exist_ok=True)

        bids_root_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/bids_tests/eeg_ds003645s_hed")
        )
        schema_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED8.2.0.xml")
        )
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, "task-FacePerception_events.json"))
        events_path = os.path.realpath(
            os.path.join(bids_root_path, "sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv")
        )

        cls.hed_schema = schema.load_schema(schema_path)
        sidecar1 = Sidecar(json_path, name="face_sub1_json")
        mapper1 = ColumnMapper(sidecar=sidecar1, optional_tag_columns=["HED"], warn_on_missing_column=False)
        cls.input_data1 = BaseInput(
            events_path,
            file_type=".tsv",
            has_column_names=True,
            name="face_sub1_events",
            mapper=mapper1,
            allow_blank_names=False,
        )
        cls.input_data2 = BaseInput(events_path, file_type=".tsv", has_column_names=True, name="face_sub2_events")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base_output_folder)

    def test_gathered_defs(self):
        # todo: probably remove this test?
        # todo: add unit tests for definitions in tsv file
        defs = DefinitionDict.get_as_strings(
            self.tabular_file._sidecar._extract_definitions(hed_schema=self.hed_schema)
        )
        expected_defs = {
            "jsonfiledef": "(Acceleration/#,Item/JsonDef1)",
            "jsonfiledef2": "(Age/#,Item/JsonDef2)",
            "jsonfiledef3": "(Age/#)",
            "takesvaluedef": "(Age/#)",
            "valueclassdef": "(Acceleration/#)",
        }
        self.assertEqual(defs, expected_defs)

    def test_file_not_found(self):
        with self.assertRaises(HedFileError):
            BaseInput("nonexistent_file.tsv")

    def test_invalid_input_type_int(self):
        with self.assertRaises(HedFileError):
            BaseInput(123)

    def test_invalid_input_type_dict(self):
        with self.assertRaises(HedFileError):
            BaseInput({"key": "value"})


class TestSortingByOnset(unittest.TestCase):
    @staticmethod
    def generate_test_dataframe():
        data = {"onset": [0.5, 1.0, 1.5, 2.0, 2.5], "HED": ["Age/1", "Age/2", "Age/3", "NotATag", "Age/5"]}

        df = pd.DataFrame(data)

        return df

    def test_needs_sort(self):
        schema = load_schema_version("8.4.0")
        df = self.generate_test_dataframe()
        opened_file = TabularInput(df)
        self.assertFalse(opened_file.needs_sorting)

        issues = opened_file.validate(schema)
        self.assertEqual(issues[0][ErrorContext.ROW], 5)
        df.at[3, "onset"] = 1.5
        opened_file = TabularInput(df)
        self.assertFalse(opened_file.needs_sorting)

        df.at[3, "onset"] = 1.0
        opened_file = TabularInput(df)
        self.assertTrue(opened_file.needs_sorting)
        issues = opened_file.validate(schema)
        # The HED column stage reports the invalid tag at its file row whether or not the file needs sorting,
        # and stops there: the unordered onsets belong to the assembly stage, which does not run.
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TAG_INVALID])
        self.assertEqual(issues[0][ErrorContext.ROW], 5)

        # With the tag fixed, the assembly stage runs and reports the unordered onsets.
        df.at[3, "HED"] = "Age/4"
        opened_file = TabularInput(df)
        issues = opened_file.validate(schema)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.ONSETS_UNORDERED])

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
            "A": ["apple", "banana", "cherry"],
            "B": ["dog", "elephant", "fox"],
            "C": ["guitar", "harmonica", "piano"],
        }
        df = pd.DataFrame(data)
        result = BaseInput.combine_dataframe(df)
        expected = pd.Series(["apple, dog, guitar", "banana, elephant, harmonica", "cherry, fox, piano"])
        self.assertTrue(result.equals(expected))

    def test_combine_dataframe_with_nan_values(self):
        data = {
            "A": ["apple", np.nan, "cherry"],
            "B": [np.nan, "elephant", "fox"],
            "C": ["guitar", "harmonica", np.nan],
        }
        df = pd.DataFrame(data)
        # this is called on load normally
        df = df.fillna("n/a")
        result = BaseInput.combine_dataframe(df)
        expected = pd.Series(["apple, guitar", "elephant, harmonica", "cherry, fox"])
        self.assertTrue(result.equals(expected))

    def test_combine_dataframe_with_empty_values(self):
        data = {"A": ["apple", "", "cherry"], "B": ["", "elephant", "fox"], "C": ["guitar", "harmonica", ""]}
        df = pd.DataFrame(data)

        result = BaseInput.combine_dataframe(df)
        expected = pd.Series(["apple, guitar", "elephant, harmonica", "cherry, fox"])
        self.assertTrue(result.equals(expected))

    def test_combine_dataframe_with_mixed_values(self):
        data = {
            "A": ["apple", np.nan, "cherry", "n/a", ""],
            "B": [np.nan, "elephant", "fox", "n/a", ""],
            "C": ["guitar", "harmonica", np.nan, "n/a", ""],
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
        expected = pd.Series(["apple, guitar", "elephant, harmonica", "cherry, fox", "", ""])
        self.assertTrue(result.equals(expected))


class TestDuplicateColumns(unittest.TestCase):
    """duplicate_columns: the names a header repeats, read before pandas suffixes them (TABULAR_INVALID)."""

    @staticmethod
    def _text(header, rows=("1\t2\t3\t4",)):
        return "\n".join([header, *rows]) + "\n"

    def test_from_path(self):
        path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../data/spreadsheet_validator_tests/duplicate_columns.tsv")
        )
        input_file = BaseInput(path)
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        # The dataframe is still loaded; pandas' suffix names the second column internally.
        self.assertEqual(input_file.columns, ["onset", "duration", "trial", "trial.1"])
        self.assertEqual(list(input_file.dataframe["trial.1"]), ["stop", "go"])

    def test_from_bytes_and_string_io(self):
        text = self._text("onset\tduration\ttrial\ttrial")
        for file in (io.BytesIO(text.encode("utf-8")), io.StringIO(text)):
            input_file = BaseInput(file, file_type=".tsv")
            self.assertEqual(input_file.duplicate_columns, ["trial"])
            self.assertEqual(input_file.columns, ["onset", "duration", "trial", "trial.1"])
            self.assertEqual(len(input_file.dataframe), 1)

    def test_file_like_read_from_its_position(self):
        text = self._text("onset\tduration\ttrial\ttrial")
        file = io.StringIO("skipped\n" + text)
        file.readline()
        input_file = BaseInput(file, file_type=".tsv")
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        self.assertEqual(len(input_file.dataframe), 1)

    def test_from_non_seekable_stream(self):
        # A socket file cannot seek on any platform (a pipe can, inside its buffer, on Windows).
        sender, receiver = socket.socketpair()
        with sender, receiver:
            sender.sendall(self._text("trial\tHED\ttrial\tHED").encode("utf-8"))
            sender.shutdown(socket.SHUT_WR)
            with receiver.makefile("rb") as reader:
                self.assertFalse(reader.seekable())
                input_file = BaseInput(reader, file_type=".tsv")
        self.assertEqual(input_file.duplicate_columns, ["trial", "HED"])
        self.assertEqual(input_file.columns, ["trial", "HED", "trial.1", "HED.1"])
        self.assertEqual(len(input_file.dataframe), 1)

    def test_bom_blank_line_and_crlf(self):
        text = "\ufeff\r\nonset\tduration\ttrial\ttrial\r\n1\t2\t3\t4\r\n"
        input_file = BaseInput(io.BytesIO(text.encode("utf-8")), file_type=".tsv")
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        self.assertEqual(input_file.columns, ["onset", "duration", "trial", "trial.1"])

    def test_names_are_trimmed(self):
        input_file = BaseInput(io.StringIO(self._text("onset \t duration\ttrial \ttrial")), file_type=".tsv")
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        self.assertEqual(input_file.columns, ["onset", "duration", "trial", "trial.1"])
        unique = BaseInput(io.StringIO(self._text("onset \tduration\ttrial \tHED")), file_type=".tsv")
        self.assertEqual(unique.duplicate_columns, [])
        self.assertEqual(unique.columns, ["onset", "duration", "trial", "HED"])

    def test_order_and_count(self):
        input_file = BaseInput(io.StringIO(self._text("b\ta\ta\tb\tb")), file_type=".tsv")
        # Each name once, in order of its second appearance.
        self.assertEqual(input_file.duplicate_columns, ["a", "b"])
        self.assertEqual(input_file.columns, ["b", "a", "a.1", "b.1", "b.2"])

    def test_no_repeats(self):
        input_file = BaseInput(io.StringIO(self._text("trial\ttrial_type\tHED", ("1\t2\t3",))), file_type=".tsv")
        self.assertEqual(input_file.duplicate_columns, [])
        self.assertEqual(self._blank_repeats().duplicate_columns, [])

    def _blank_repeats(self):
        # Blank names have their own rule (allow_blank_names) and are not counted as repeats.
        return BaseInput(io.StringIO(self._text("onset\t\t\tHED")), file_type=".tsv")

    def test_no_column_names(self):
        input_file = BaseInput(
            io.StringIO(self._text("trial\ttrial\ttrial\ttrial")), file_type=".tsv", has_column_names=False
        )
        self.assertEqual(input_file.duplicate_columns, [])
        self.assertEqual(len(input_file.dataframe), 2)

    def test_from_dataframe(self):
        frame = pd.DataFrame([["1", "go", "stop"]], columns=["onset", "trial ", "trial"])
        input_file = BaseInput(frame)
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        self.assertEqual(input_file.columns, ["onset", "trial", "trial.1"])
        # The caller's frame keeps its own labels.
        self.assertEqual(list(frame.columns), ["onset", "trial ", "trial"])

    def test_from_excel(self):
        import openpyxl

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.append(["onset", "trial", "HED ", "trial", "HED"])
        worksheet.append(["1", "go", "Red", "stop", "Blue"])
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        input_file = BaseInput(buffer, file_type=".xlsx")
        self.assertEqual(input_file.duplicate_columns, ["trial", "HED"])
        self.assertEqual(input_file.columns, ["onset", "trial", "HED", "trial.1", "HED.1"])
