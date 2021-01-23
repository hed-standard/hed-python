import unittest
from hed.util import error_reporter
from hed.util import error_types

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.error_handler = error_reporter.ErrorHandler()
        pass

    def test_push_error_context(self):
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.push_error_context(error_types.ErrorContext.FILE_NAME, "DummyFileName.txt")
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 2)
        self.error_handler.push_error_context(error_types.ErrorContext.SIDECAR_COLUMN_NAME, "DummyColumnName")
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 2)
        self.error_handler.reset_error_context()
        self.error_handler.push_error_context(error_types.ErrorContext.FILE_NAME, "DummyFileName.txt")
        self.error_handler.push_error_context(error_types.ErrorContext.SIDECAR_COLUMN_NAME, "DummyColumnName")
        self.error_handler.push_error_context(error_types.ErrorContext.COLUMN, 1, column_context=3)
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 4)
        self.error_handler.reset_error_context()

    def test_pop_error_context(self):
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.push_error_context(error_types.ErrorContext.FILE_NAME, "DummyFileName.txt")
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 2)
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.push_error_context(error_types.ErrorContext.SIDECAR_COLUMN_NAME, "DummyColumnName")
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 2)
        self.error_handler.push_error_context(error_types.ErrorContext.FILE_NAME, "DummyFileName.txt")
        self.error_handler.push_error_context(error_types.ErrorContext.SIDECAR_COLUMN_NAME, "DummyColumnName")
        self.error_handler.push_error_context(error_types.ErrorContext.COLUMN, 1, column_context=3)
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 4)
        self.error_handler.pop_error_context()
        self.error_handler.pop_error_context()
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_schema_error(error_types.SchemaErrors.EMPTY_TAG_FOUND, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.reset_error_context()
