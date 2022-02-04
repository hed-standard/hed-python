import unittest
from hed.errors import ErrorHandler, ErrorContext, ErrorSeverity, ValidationErrors, SchemaWarnings


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.error_handler = ErrorHandler()
        pass

    def test_push_error_context(self):
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        name = "DummyFileName.txt"
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(name in error_list[0][ErrorContext.FILE_NAME])
        column_name = "DummyColumnName"
        self.error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(column_name in error_list[0][ErrorContext.SIDECAR_COLUMN_NAME])
        self.error_handler.reset_error_context()
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        self.error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
        self.error_handler.push_error_context(ErrorContext.COLUMN, 1)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(name in error_list[0][ErrorContext.FILE_NAME])
        self.assertTrue(column_name in error_list[0][ErrorContext.SIDECAR_COLUMN_NAME])
        self.assertTrue(1 in error_list[0][ErrorContext.COLUMN])
        self.assertTrue(len(error_list) == 1)
        self.error_handler.reset_error_context()

    def test_pop_error_context(self):
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        name = "DummyFileName.txt"
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.assertTrue(name in error_list[0][ErrorContext.FILE_NAME])
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        column_name = "DummyColumnName"
        self.error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        self.error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
        self.error_handler.push_error_context(ErrorContext.COLUMN, 1)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.assertTrue(name in error_list[0][ErrorContext.FILE_NAME])
        self.assertTrue(column_name in error_list[0][ErrorContext.SIDECAR_COLUMN_NAME])
        self.assertTrue(1 in error_list[0][ErrorContext.COLUMN])
        self.error_handler.pop_error_context()
        self.error_handler.pop_error_context()
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.assertTrue(ErrorContext.COLUMN not in error_list[0])
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.reset_error_context()

    def test_filter_issues_by_severity(self):
        error_list = self.error_handler.format_error_with_context(ValidationErrors.HED_TAG_NOT_UNIQUE, "")
        error_list += self.error_handler.format_error_with_context(SchemaWarnings.INVALID_CAPITALIZATION,
                                                                   "dummy", problem_char="#", char_index=0)
        self.assertTrue(len(error_list) == 2)
        filtered_list = self.error_handler.filter_issues_by_severity(issues_list=error_list,
                                                                     severity=ErrorSeverity.ERROR)
        self.assertTrue(len(filtered_list) == 1)
