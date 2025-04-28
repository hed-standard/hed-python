import unittest
from hed.errors import ErrorHandler, ErrorContext, ErrorSeverity, ValidationErrors, SchemaWarnings, \
    get_printable_issue_string, sort_issues, replace_tag_references
from hed.errors.error_reporter import hed_tag_error, get_printable_issue_string_html, iter_errors
from hed import HedString, HedTag
from hed import load_schema_version


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.error_handler = ErrorHandler()
        cls._schema = load_schema_version("8.3.0")
        pass

    def test_push_error_context(self):
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        name = "DummyFileName.txt"
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(name in error_list[0][ErrorContext.FILE_NAME])
        column_name = "DummyColumnName"
        self.error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(column_name in error_list[0][ErrorContext.SIDECAR_COLUMN_NAME])
        self.error_handler.reset_error_context()
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        self.error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
        self.error_handler.push_error_context(ErrorContext.COLUMN, column_name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(name in error_list[0][ErrorContext.FILE_NAME])
        self.assertTrue(column_name in error_list[0][ErrorContext.SIDECAR_COLUMN_NAME])
        self.assertTrue(column_name == error_list[0][ErrorContext.COLUMN])
        self.assertTrue(len(error_list) == 1)
        self.error_handler.reset_error_context()
        self.error_handler.push_error_context(ErrorContext.ROW, None)
        self.assertTrue(self.error_handler.error_context[0][1] == 0)
        self.error_handler.reset_error_context()

    def test_pop_error_context(self):
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        name = "DummyFileName.txt"
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.assertTrue(name in error_list[0][ErrorContext.FILE_NAME])
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        column_name = "DummyColumnName"
        self.error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        self.error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
        self.error_handler.push_error_context(ErrorContext.COLUMN, column_name)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.assertTrue(name in error_list[0][ErrorContext.FILE_NAME])
        self.assertTrue(column_name in error_list[0][ErrorContext.SIDECAR_COLUMN_NAME])
        self.assertTrue(column_name == error_list[0][ErrorContext.COLUMN])
        self.error_handler.pop_error_context()
        self.error_handler.pop_error_context()
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.assertTrue(ErrorContext.COLUMN not in error_list[0])
        self.error_handler.pop_error_context()
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        self.assertTrue(len(error_list) == 1)
        self.error_handler.reset_error_context()

    def test_filter_issues_by_severity(self):
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        error_list += self.error_handler.format_error_with_context(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION,
                                                                   "dummy", problem_char="#", char_index=0)
        self.assertTrue(len(error_list) == 2)
        filtered_list = self.error_handler.filter_issues_by_severity(issues_list=error_list,
                                                                     severity=ErrorSeverity.ERROR)
        self.assertTrue(len(filtered_list) == 1)

    def test_printable_issue_string(self):
        self.error_handler.push_error_context(ErrorContext.CUSTOM_TITLE, "Default Custom Title")
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        error_list += self.error_handler.format_error_with_context(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION,
                                                                   "dummy", problem_char="#", char_index=0)

        printable_issues = get_printable_issue_string(error_list)
        self.assertTrue(len(printable_issues) > 10)

        printable_issues2 = get_printable_issue_string(error_list, severity=ErrorSeverity.ERROR)
        self.assertTrue(len(printable_issues) > len(printable_issues2))

        printable_issues3 = get_printable_issue_string(error_list, severity=ErrorSeverity.ERROR,
                                                       title="Later added custom title that is longer")
        self.assertTrue(len(printable_issues3) > len(printable_issues2))

        self.error_handler.reset_error_context()

    def test_printable_issue_string_with_filenames(self):
        my_file = 'my_file.txt'
        self.error_handler.push_error_context(ErrorContext.CUSTOM_TITLE, "Default Custom Title")
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, my_file)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        error_list += self.error_handler.format_error_with_context(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION,
                                                                   "dummy", problem_char="#", char_index=0)

        printable_issues = get_printable_issue_string(error_list, skip_filename=False)
        self.assertTrue(len(printable_issues) > 10)
        self.assertEqual(printable_issues.count(my_file), 1)

        printable_issues2 = get_printable_issue_string(error_list, severity=ErrorSeverity.ERROR, skip_filename=False)
        self.assertTrue(len(printable_issues) > len(printable_issues2))
        self.assertEqual(printable_issues2.count(my_file), 1)
        printable_issues3 = get_printable_issue_string(error_list, severity=ErrorSeverity.ERROR, skip_filename=False,
                                                       title="Later added custom title that is longer")
        self.assertTrue(len(printable_issues3) > len(printable_issues2))
        self.assertEqual(printable_issues3.count(my_file), 1)

        printable_issues = get_printable_issue_string_html(error_list, skip_filename=False)
        self.assertTrue(len(printable_issues) > 10)
        self.assertEqual(printable_issues.count(my_file), 1)

        printable_issues2 = get_printable_issue_string_html(error_list, severity=ErrorSeverity.ERROR,
                                                            skip_filename=False)
        self.assertTrue(len(printable_issues) > len(printable_issues2))
        self.assertEqual(printable_issues2.count(my_file), 1)
        printable_issues3 = get_printable_issue_string_html(error_list, severity=ErrorSeverity.ERROR,
                                                            skip_filename=False,
                                                            title="Later added custom title that is longer")
        self.assertTrue(len(printable_issues3) > len(printable_issues2))
        self.assertEqual(printable_issues3.count(my_file), 1)

        self.error_handler.reset_error_context()

    def test_iter_errors_no_context(self):
        self.error_handler.push_error_context(ErrorContext.CUSTOM_TITLE, "Default Custom Title")
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        error_list += self.error_handler.format_error_with_context(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION,
                                                                   "dummy", problem_char="#", char_index=0)
        result = list(iter_errors(error_list))
        self.assertEqual(len(result), 2)

    def test_iter_errors_with_context(self):
        my_file = 'my_file.txt'
        self.error_handler.push_error_context(ErrorContext.CUSTOM_TITLE, "Blech")
        self.error_handler.push_error_context(ErrorContext.FILE_NAME, my_file)
        error_list = self.error_handler.format_error_with_context(ValidationErrors.TAG_NOT_UNIQUE, "")
        # error_list += self.error_handler.format_error(ValidationErrors.HED_RESERVED_TAG_REPEATED,
        #                                  tag=grouped[multiples[0]][1], group=group)
        incompatible_tag = HedTag('Green', self._schema)
        incompatible_group = HedString('Green, Red', self._schema)
        error_list += self.error_handler.format_error(ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=incompatible_tag,
                     group=incompatible_group)

        error_list += self.error_handler.format_error_with_context(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION,
                                                                   "dummy", problem_char="#", char_index=0)
        result = list(iter_errors(error_list))
        self.assertEqual(len(result), 3)

    def test_sort_issues(self):
        schema = load_schema_version("8.1.0")
        issues = [
            {ErrorContext.CUSTOM_TITLE: 'issue3', ErrorContext.FILE_NAME: 'File2', ErrorContext.ROW: 5,
             ErrorContext.HED_STRING: HedString('Test C', schema)},
            {ErrorContext.CUSTOM_TITLE: 'issue1', ErrorContext.FILE_NAME: 'File1', ErrorContext.ROW: 10,
             ErrorContext.HED_STRING: HedString('Test A', schema)},
            {ErrorContext.CUSTOM_TITLE: 'issue2', ErrorContext.FILE_NAME: 'File1', ErrorContext.ROW: 2},
            {ErrorContext.CUSTOM_TITLE: 'issue4', ErrorContext.FILE_NAME: 'File2', ErrorContext.ROW: 1,
             ErrorContext.HED_STRING: HedString('Test D', schema)},
            {ErrorContext.CUSTOM_TITLE: 'issue5', ErrorContext.FILE_NAME: 'File3', ErrorContext.ROW: 15}
        ]

        sorted_issues = sort_issues(issues)
        self.assertEqual(sorted_issues[0][ErrorContext.CUSTOM_TITLE], 'issue1')
        self.assertEqual(sorted_issues[1][ErrorContext.CUSTOM_TITLE], 'issue2')
        self.assertEqual(sorted_issues[2][ErrorContext.CUSTOM_TITLE], 'issue3')
        self.assertEqual(sorted_issues[3][ErrorContext.CUSTOM_TITLE], 'issue4')
        self.assertEqual(sorted_issues[4][ErrorContext.CUSTOM_TITLE], 'issue5')

        reversed_issues = sort_issues(issues, reverse=True)
        self.assertEqual(reversed_issues[0][ErrorContext.CUSTOM_TITLE], 'issue5')
        self.assertEqual(reversed_issues[1][ErrorContext.CUSTOM_TITLE], 'issue4')
        self.assertEqual(reversed_issues[2][ErrorContext.CUSTOM_TITLE], 'issue3')
        self.assertEqual(reversed_issues[3][ErrorContext.CUSTOM_TITLE], 'issue2')
        self.assertEqual(reversed_issues[4][ErrorContext.CUSTOM_TITLE], 'issue1')

    def test_replace_tag_references(self):
        # Test with mixed data types and HedString in a nested dict
        nested_dict = {'a': HedString('Hed1', self._schema), 
                       'b': {'c': 2, 'd': [3, {'e': HedString('Hed2', self._schema)}]}, 'f': [5, 6]}
        replace_tag_references(nested_dict)
        self.assertEqual(nested_dict, {'a': 'Hed1', 'b': {'c': 2, 'd': [3, {'e': 'Hed2'}]}, 'f': [5, 6]})

        # Test with mixed data types and HedString in a nested list
        nested_list = [HedString('Hed1', self._schema),
                       {'a': 2, 'b': [3, {'c': HedString('Hed2', self._schema)}]}]
        replace_tag_references(nested_list)
        self.assertEqual(nested_list, ['Hed1', {'a': 2, 'b': [3, {'c': 'Hed2'}]}])

        # Test with mixed data types and HedString in a list within a dict
        mixed = {'a': HedString('Hed1', self._schema),
                 'b': [2, 3, {'c': HedString('Hed2', self._schema)}, 4]}
        replace_tag_references(mixed)
        self.assertEqual(mixed, {'a': 'Hed1', 'b': [2, 3, {'c': 'Hed2'}, 4]})

    def test_register_error_twice(self):
        test_code = "test_error_code"

        @hed_tag_error(test_code)
        def test_error_code(tag):
            pass

        with self.assertRaises(KeyError):
            @hed_tag_error(test_code)
            def test_error_code(tag):
                pass

    def test_format_unknown_error(self):
        error_code = "Unknown error type"
        error_list = self.error_handler.format_error(error_code, "param1", param2=0)
        self.assertEqual(error_list[0]['code'], error_code)

        actual_code = "Actual unknown error type"
        error_list = self.error_handler.format_error_from_context(error_code, self.error_handler.error_context,
                                                                  "param1", param2=0,
                                                                  actual_error=actual_code)
        self.assertEqual(error_list[0]['code'], actual_code)
