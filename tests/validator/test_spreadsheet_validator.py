import pandas as pd
import unittest
from hed import BaseInput, load_schema_version
from hed.validator import SpreadsheetValidator
from hed.errors import ErrorHandler, sort_issues
from hed.errors.error_types import ColumnErrors


class TestSpreadsheetValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.1.0")
        cls.validator = SpreadsheetValidator(cls.schema)

