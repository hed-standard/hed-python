import unittest
from hed.util import error_reporter
from hed.util import error_types

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_push_error_context(self):
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        error_reporter.push_error_context(error_types.ErrorContext.FILE_NAME, "DummyFileName.txt")
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 2)
        error_reporter.push_error_context(error_types.ErrorContext.SIDECAR_COLUMN_NAME, "DummyColumnName")
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 2)
        error_reporter.reset_error_context()
        error_reporter.push_error_context(error_types.ErrorContext.FILE_NAME, "DummyFileName.txt")
        error_reporter.push_error_context(error_types.ErrorContext.SIDECAR_COLUMN_NAME, "DummyColumnName")
        error_reporter.push_error_context(error_types.ErrorContext.COLUMN, 1, column_context=3)
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 4)
        error_reporter.reset_error_context()

    def test_pop_error_context(self):
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        error_reporter.push_error_context(error_types.ErrorContext.FILE_NAME, "DummyFileName.txt")
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 2)
        error_reporter.pop_error_context()
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        error_reporter.push_error_context(error_types.ErrorContext.SIDECAR_COLUMN_NAME, "DummyColumnName")
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 2)
        error_reporter.push_error_context(error_types.ErrorContext.FILE_NAME, "DummyFileName.txt")
        error_reporter.push_error_context(error_types.ErrorContext.SIDECAR_COLUMN_NAME, "DummyColumnName")
        error_reporter.push_error_context(error_types.ErrorContext.COLUMN, 1, column_context=3)
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 4)
        error_reporter.pop_error_context()
        error_reporter.pop_error_context()
        error_reporter.pop_error_context()
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        error_reporter.pop_error_context()
        error_list = error_reporter.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        error_reporter.reset_error_context()
