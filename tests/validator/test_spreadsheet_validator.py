import pandas as pd
import unittest
from hed import BaseInput, load_schema_version
from hed.validator import SpreadsheetValidator
from hed.errors import ErrorHandler, sort_issues
from hed.errors.error_types import ColumnErrors



class TestInsertColumns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.1.0")
        cls.validator = SpreadsheetValidator(cls.schema)

    def test_insert_columns_no_nested_or_circular_reference(self):
        df = pd.DataFrame({
            "column1": ["[column2], Event, Action"],
            "column2": ["[column1], Item"]
        })
        issues = self.validator._validate_square_brackets(df, error_handler=ErrorHandler(True))
        self.assertEqual(issues[0]['code'], ColumnErrors.NESTED_COLUMN_REF)

    def test_insert_columns_invalid_column_name(self):
        df = pd.DataFrame({
            "column1": ["[invalid_column], Event, Action"],
            "column2": ["Item"]
        })
        issues = self.validator._validate_square_brackets(df, error_handler=ErrorHandler(True))
        self.assertEqual(issues[0]['code'], ColumnErrors.INVALID_COLUMN_REF)

    def test_insert_columns_invalid_syntax(self):
        df = pd.DataFrame({
            "column1": ["column2], Event, Action"],
            "column2": ["Item"]
        })
        issues = self.validator._validate_square_brackets(df, error_handler=ErrorHandler(True))
        self.assertEqual(issues[0]['code'], ColumnErrors.MALFORMED_COLUMN_REF)

    def test_insert_columns_invalid_syntax2(self):
        df = pd.DataFrame({
            "column1": ["column2], Event, Action", "[column, Event, Action"],
            "column2": ["Item", "Action"],
            "column3": ["This is a [malformed [input string]] with extra [opening brackets", "[Event[Action]]"],
        })
        issues = self.validator._validate_square_brackets(df, error_handler=ErrorHandler(True))
        issues = sort_issues(issues)
        self.assertEqual(issues[0]['code'], ColumnErrors.MALFORMED_COLUMN_REF)
        self.assertEqual(len(issues), 6)

    def test_insert_columns_no_self_reference(self):
        df = pd.DataFrame({
            "column1": ["[column1], Event, Action"],
            "column2": ["Item"]
        })
        issues = self.validator._validate_square_brackets(df, error_handler=ErrorHandler(True))
        self.assertEqual(issues[0]['code'], ColumnErrors.SELF_COLUMN_REF)
