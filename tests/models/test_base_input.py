import csv
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
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, "task-FacePerception_events.json"))
        events_path = os.path.realpath(
            os.path.join(bids_root_path, "sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv")
        )

        cls.hed_schema = schema.load_schema_version("8.2.0")
        sidecar1 = Sidecar(json_path, name="face_sub1_json")
        mapper1 = ColumnMapper(sidecar=sidecar1, optional_tag_columns=["HED"], warn_on_missing_column=False)
        cls.input_data1 = BaseInput(
            events_path,
            file_type=".tsv",
            has_column_names=True,
            name="face_sub1_events",
            mapper=mapper1,
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


def _excel_input(*rows):
    """Return a BaseInput read from an in-memory workbook holding the given rows."""
    import openpyxl

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return BaseInput(buffer, file_type=".xlsx")


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

    def test_text_stream_advanced_with_next(self):
        # TextIOWrapper.tell() fails after next(); the rest of the stream is still read from where it is.
        text = "preamble\n" + self._text("trial\ttrial\tHED", ("a\tb\tRed",))
        stream = io.TextIOWrapper(io.BytesIO(text.encode("utf-8")), encoding="utf-8")
        next(stream)
        input_file = BaseInput(stream, file_type=".tsv")
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        self.assertEqual(input_file.columns, ["trial", "trial.1", "HED"])
        self.assertEqual(len(input_file.dataframe), 1)

    def test_bom_blank_line_and_crlf(self):
        text = "\ufeff\r\nonset\tduration\ttrial\ttrial\r\n1\t2\t3\t4\r\n"
        input_file = BaseInput(io.BytesIO(text.encode("utf-8")), file_type=".tsv")
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        self.assertEqual(input_file.columns, ["onset", "duration", "trial", "trial.1"])

    def test_names_are_kept_as_read(self):
        # Names are compared exactly: "trial " beside "trial" is one padded name, not a repeat.
        input_file = BaseInput(io.StringIO(self._text("onset \t duration\ttrial \ttrial")), file_type=".tsv")
        self.assertEqual(input_file.duplicate_columns, [])
        self.assertEqual(input_file.padded_columns, ["onset ", " duration", "trial "])
        self.assertEqual(input_file.columns, ["onset ", " duration", "trial ", "trial"])

    def test_quoted_header_cells(self):
        # A double quote is an ordinary character (as in hed-javascript and the BIDS validator).
        mixed = BaseInput(io.StringIO(self._text('trial\t"trial"\tHED', ("a\tb\tRed",))), file_type=".tsv")
        self.assertEqual(mixed.duplicate_columns, [])
        self.assertEqual(mixed.columns, ["trial", '"trial"', "HED"])
        quoted = BaseInput(io.StringIO(self._text('"trial"\t"trial"\tHED', ("a\tb\tRed",))), file_type=".tsv")
        self.assertEqual(quoted.duplicate_columns, ['"trial"'])
        padded = BaseInput(io.StringIO(self._text('"trial "\tHED', ("a\tRed",))), file_type=".tsv")
        self.assertEqual(padded.padded_columns, [])
        self.assertEqual(padded.columns, ['"trial "', "HED"])

    def test_quotes_do_not_join_lines(self):
        # A quote does not open a cell that spans lines: the header is the first line, split on tabs.
        text = self._text('"trial\nnote"\ttrial\ttrial', ("a\tb\tc",))
        with self.assertWarns(pd.errors.ParserWarning):  # the later lines have more cells than the header
            input_file = BaseInput(io.BytesIO(text.encode("utf-8")), file_type=".tsv")
        self.assertEqual(input_file.columns, ['"trial'])
        self.assertEqual(input_file.duplicate_columns, [])

    def test_quoted_data_cells(self):
        text = 'onset\tnote\tHED\n1\t"a, b"\t"Red"\n2\t"open\tBlue\n'
        input_file = BaseInput(io.StringIO(text), file_type=".tsv")
        self.assertEqual(list(input_file.dataframe["note"]), ['"a, b"', '"open'])
        self.assertEqual(list(input_file.dataframe["HED"]), ['"Red"', "Blue"])
        # A quote is an invalid HED character, so a quoted HED cell is reported rather than unquoted.
        tabular = TabularInput(io.StringIO('onset\tHED\n1\t"Red"\n'))
        issues = tabular.validate(load_schema_version("8.4.0"))
        self.assertEqual([issue["code"] for issue in issues], ["CHARACTER_INVALID", "CHARACTER_INVALID"])

    def test_quotes_survive_save_and_reload(self):
        text = 'onset\tsay "x"\tHED\n1\tsay "go"\tRed\n2\t"quoted"\tBlue\n'
        original = BaseInput(io.StringIO(text), file_type=".tsv")
        saved = original.to_csv()
        self.assertEqual(saved, text)
        reloaded = BaseInput(io.StringIO(saved), file_type=".tsv")
        self.assertEqual(reloaded.columns, ["onset", 'say "x"', "HED"])
        self.assertTrue(reloaded.dataframe.equals(original.dataframe))

    def test_save_refuses_a_tab_in_a_cell(self):
        # A TSV file cannot hold a tab inside a cell when quotes are ordinary characters.
        input_file = BaseInput(pd.DataFrame([["1", "a\tb"]], columns=["onset", "note"]))
        with self.assertRaises(csv.Error):
            input_file.to_csv()

    def test_quoted_tab_splits_the_cell(self):
        # The extra cell of the row is dropped, as hed-javascript drops it; the BIDS validator reports the row.
        text = 'onset\tnote\tHED\n1\t"a\tb"\tRed\n'
        with self.assertWarns(pd.errors.ParserWarning):
            input_file = BaseInput(io.StringIO(text), file_type=".tsv")
        self.assertEqual(input_file.dataframe.iloc[0].tolist(), ["1", '"a', 'b"'])

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
        # Blank names have their own rule (blank_columns) and are not counted as repeats.
        return BaseInput(io.StringIO(self._text("onset\t\t\tHED")), file_type=".tsv")

    def test_no_column_names(self):
        input_file = BaseInput(
            io.StringIO(self._text("trial\ttrial\ttrial\ttrial")), file_type=".tsv", has_column_names=False
        )
        self.assertEqual(input_file.duplicate_columns, [])
        self.assertEqual(len(input_file.dataframe), 2)

    def test_from_dataframe(self):
        frame = pd.DataFrame([["1", "go", "stop", "x"]], columns=["onset", "trial ", "trial", "trial"])
        input_file = BaseInput(frame)
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        self.assertEqual(input_file.padded_columns, ["trial "])
        self.assertEqual(input_file.columns, ["onset", "trial ", "trial", "trial.1"])
        # The caller's frame keeps its own labels.
        self.assertEqual(list(frame.columns), ["onset", "trial ", "trial", "trial"])

    def test_from_excel(self):
        input_file = _excel_input(["onset", "trial", "HED ", "trial", "HED"], ["1", "go", "Red", "stop", "Blue"])
        self.assertEqual(input_file.duplicate_columns, ["trial"])
        self.assertEqual(input_file.padded_columns, ["HED "])
        self.assertEqual(input_file.columns, ["onset", "trial", "HED ", "trial.1", "HED"])


class TestPaddedAndBlankColumns(unittest.TestCase):
    """padded_columns and blank_columns: TABULAR_INVALID (b) and (c), read from the header as written."""

    @staticmethod
    def _text_input(header, rows=("1\t2\t3",)):
        return BaseInput(io.StringIO("\n".join([header, *rows]) + "\n"), file_type=".tsv")

    def test_padded_names(self):
        input_file = self._text_input("onset\tduration\t HED")
        self.assertEqual(input_file.padded_columns, [" HED"])
        self.assertEqual(input_file.blank_columns, [])
        # In a text file a tab always separates cells, so only a label from a DataFrame or Excel holds one.
        tab = BaseInput(pd.DataFrame([["a", "b", "Red"]], columns=["trial\t", "x\r", "HED"]))
        self.assertEqual(tab.padded_columns, ["trial\t", "x\r"])

    def test_padded_and_repeated_is_padded_once(self):
        input_file = self._text_input("trial \ttrial \tHED")
        self.assertEqual(input_file.padded_columns, ["trial "])
        self.assertEqual(input_file.duplicate_columns, [])

    def test_whitespace_only_name_is_padded_not_blank(self):
        input_file = self._text_input("onset\t \tHED")
        self.assertEqual(input_file.padded_columns, [" "])
        self.assertEqual(input_file.blank_columns, [])

    def test_non_breaking_space_is_not_padding(self):
        input_file = self._text_input("onset\ttrial\u00a0\tHED")
        self.assertEqual(input_file.padded_columns, [])
        self.assertEqual(input_file.columns, ["onset", "trial\u00a0", "HED"])

    def test_inner_blank_is_not_padding(self):
        input_file = self._text_input("onset\ttrial type\tHED")
        self.assertEqual(input_file.padded_columns, [])

    def test_blank_last_name_from_trailing_tab(self):
        input_file = self._text_input("onset\tduration\tHED\t", ("1\t2\tRed\t",))
        self.assertEqual(input_file.blank_columns, [3])
        self.assertEqual(input_file.columns, ["onset", "duration", "HED", ""])

    def test_blank_middle_and_two_blanks(self):
        middle = self._text_input("onset\t\tHED")
        self.assertEqual(middle.blank_columns, [1])
        two = self._text_input("onset\t\t\tHED", ("1\t2\t3\t4",))
        self.assertEqual(two.blank_columns, [1, 2])
        self.assertEqual(two.duplicate_columns, [])

    def test_blank_from_excel(self):
        input_file = _excel_input(["onset", None, "HED"], ["1", "x", "Red"])
        self.assertEqual(input_file.blank_columns, [1])

    def test_dataframe_labels_are_literal(self):
        # A label pandas would give an empty header cell is an ordinary name; "", None and NaN are blank.
        frame = pd.DataFrame([["1", "a", "b", "c", "d"]], columns=["onset", "Unnamed: 1", "", None, np.nan])
        input_file = BaseInput(frame)
        self.assertEqual(input_file.blank_columns, [2, 3, 4])
        self.assertEqual(input_file.padded_columns, [])
        self.assertEqual(input_file.duplicate_columns, [])
        suffixed = BaseInput(pd.DataFrame([["1", "a", "b"]], columns=["onset", "trial", "trial.1"]))
        self.assertEqual(suffixed.duplicate_columns, [])

    def test_names_converted_to_text(self):
        # Excel: a whole number is written without a decimal point, so 1 and "1" are a repeated name.
        excel = _excel_input([1, "1", 1.5, None, "HED"], ["a", "b", "c", "d", "Red"])
        self.assertEqual(excel.columns, ["1", "1.1", "1.5", "", "HED"])
        self.assertEqual(excel.duplicate_columns, ["1"])
        self.assertEqual(excel.blank_columns, [3])
        repeated = _excel_input([1, 1, "HED"], ["a", "b", "Red"])
        self.assertEqual(repeated.duplicate_columns, ["1"])
        # DataFrame: 1.0 and "1" are the same name; None and NaN are blank.
        frame = pd.DataFrame([["a", "b", "c", "d", "Red"]], columns=[1.0, "1", None, np.nan, "HED"])
        input_file = BaseInput(frame)
        self.assertEqual(input_file.columns, ["1", "1.1", "", "", "HED"])
        self.assertEqual(input_file.duplicate_columns, ["1"])
        self.assertEqual(input_file.blank_columns, [2, 3])
        # The caller's frame keeps its own labels.
        self.assertEqual(list(frame.columns)[:2], [1.0, "1"])

    def test_numeric_name_matches_sidecar_key(self):
        sidecar = Sidecar(io.StringIO('{"1": {"HED": {"go": "Red"}}}'))
        frame = pd.DataFrame([["1.0", "go", "Blue"]], columns=["onset", 1, "HED"])
        tabular = TabularInput(frame, sidecar=sidecar)
        self.assertEqual(tabular.columns, ["onset", "1", "HED"])
        self.assertEqual(sorted(tabular.series_a[0].split(", ")), ["Blue", "Red"])

    def test_assembly_refused_for_bad_names(self):
        cases = {
            "padded": ("onset\tHED \n1\tRed\n", "padded ['HED ']"),
            "blank": ("onset\t\tHED\n1\tx\tRed\n", "blank at columns [2]"),
            "repeated": ("onset\tHED\tHED\n1\tRed\tBlue\n", "repeated ['HED']"),
        }
        for label, (text, expected) in cases.items():
            input_file = TabularInput(io.StringIO(text), name="events.tsv")
            for attribute in ("dataframe_a", "series_a", "series_filtered"):
                with self.subTest(label=label, attribute=attribute), self.assertRaises(HedFileError) as context:
                    getattr(input_file, attribute)
                self.assertEqual(context.exception.code, "BAD_COLUMN_NAMES")
            with self.subTest(label=label, attribute="assemble"), self.assertRaises(HedFileError) as context:
                input_file.assemble()
            self.assertEqual(context.exception.code, "BAD_COLUMN_NAMES")
            self.assertIn(expected, context.exception.message)
            self.assertEqual(context.exception.filename, "events.tsv")

    def test_assembly_of_good_names(self):
        input_file = TabularInput(io.StringIO("onset\ttrial type\tHED\n1\tgo\tRed\n"))
        self.assertEqual(list(input_file.series_a), ["Red"])

    def test_deprecated_allow_blank_names_is_ignored(self):
        # The argument is accepted for compatibility, warns, and no longer makes a blank name raise.
        for value in (False, True):
            with self.assertWarns(DeprecationWarning):
                input_file = BaseInput(
                    io.StringIO("onset\t\tHED\n1\t2\t3\n"), file_type=".tsv", allow_blank_names=value
                )
            self.assertEqual(input_file.blank_columns, [1])

    def test_no_column_names(self):
        input_file = BaseInput(io.StringIO(" a\t\tb \n1\t2\t3\n"), file_type=".tsv", has_column_names=False)
        self.assertEqual(input_file.padded_columns, [])
        self.assertEqual(input_file.blank_columns, [])
