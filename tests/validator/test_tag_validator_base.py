import unittest
import os
from hed.models.hed_string import HedString
from hed.validator.hed_validator import HedValidator
from hed.errors import error_reporter
from hed.errors import ErrorHandler, ErrorContext
from hed import schema


# todo: update these tests(TagValidator no longer exists)
class TestHedBase(unittest.TestCase):
    schema_file = None
    hed_schema = None

    @classmethod
    def setUpClass(cls):
        if cls.schema_file and not cls.hed_schema:
            hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.schema_file)
            cls.hed_schema = schema.load_schema(hed_xml)
        elif not cls.hed_schema:
            raise ValueError("No schema set for test case")
        cls.error_handler = error_reporter.ErrorHandler()

    def format_error(self, error_type, *args, **kwargs):
        """
            The parameters vary based on what type of error this is.

            Note: If you want to pass a tag as a number to this function, you will need to pass tag as a keyword.

        Parameters:
            error_type (str): The type of error for this.  Registered with @hed_error or @hed_tag_error.
            args (args): The rest of the unnamed args.
            kwargs:  The other parameters to pass down to the error handling func.

        Returns:
            list:  A list consisting of a single dictionary representing an error.

        """
        _ = ErrorHandler.format_error(error_type, *args, **kwargs)
        # Save off params
        params = [error_type, args, kwargs]
        # return params
        return [params]

    def filter_issues(self, issue_list):
        if not issue_list:
            return []
        return [{key: d[key] for key in ('code', 'message', 'severity') if key in d} for d in issue_list]

    def format_errors_fully(self, error_handler, hed_string, params):
        formatted_errors = []
        for code, args, kwargs in params:
            if 'tag' in kwargs and isinstance(kwargs['tag'], int):
                tag_index = kwargs['tag']
                if tag_index >= 1000:
                    tag_index = tag_index - 1000
                    source_list = hed_string.get_all_groups()
                else:
                    source_list = hed_string.get_all_tags()
                if tag_index >= len(source_list):
                    raise ValueError("Bad group or tax index in expected errors for unit tests")
                kwargs['tag'] = source_list[tag_index]
            formatted_errors += error_handler.format_error_with_context(code, *args, **kwargs)

        return formatted_errors


class TestValidatorBase(TestHedBase):
    compute_forms = True
    hed_schema = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.error_handler = error_reporter.ErrorHandler()
        cls.semantic_hed_input_reader = HedValidator(hed_schema=cls.hed_schema)

    def validator_base(self, test_strings, expected_results, expected_issues, test_function,
                       hed_schema, check_for_warnings=False):
        for test_key in test_strings:
            hed_string_obj = HedString(test_strings[test_key], self.hed_schema)
            error_handler = ErrorHandler(check_for_warnings=check_for_warnings)
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj)
            test_issues = []
            if self.compute_forms:
                test_issues += hed_string_obj._calculate_to_canonical_forms(hed_schema)
            if not test_issues:
                test_issues += test_function(hed_string_obj)
            expected_params = expected_issues[test_key]
            expected_result = expected_results[test_key]
            expected_issue = self.format_errors_fully(error_handler, hed_string=hed_string_obj,
                                                      params=expected_params)
            error_handler.add_context_and_filter(test_issues)
            test_result = not test_issues
            self.assertEqual(test_result, expected_result, test_strings[test_key])
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])

    def validator_base_new(self, test_strings, expected_results, expected_issues, test_function,
                           hed_schema, check_for_warnings=False):
        # This does direct comparison of the issue before formatting or context.
        for test_key in test_strings:
            hed_string_obj = HedString(test_strings[test_key], self.hed_schema)
            test_issues = []
            if self.compute_forms:
                test_issues += hed_string_obj._calculate_to_canonical_forms(hed_schema)
            if not test_issues:
                test_issues += test_function(hed_string_obj)
            filtered_issues = self.filter_issues(test_issues)
            these_issues = expected_issues[test_key]
            self.assertEqual(len(filtered_issues), len(these_issues),
                             f"{test_strings[test_key]} should have the same number of issues.")
            self.assertCountEqual(filtered_issues, these_issues, test_strings[test_key])

    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        validator = self.semantic_hed_input_reader
        self.validator_base(test_strings, expected_results, expected_issues,
                            self.string_obj_func(validator), check_for_warnings=check_for_warnings,
                            hed_schema=validator._hed_schema)

    def validator_semantic_new(self, test_strings, expected_results, expected_issues, check_for_warnings):
        validator = self.semantic_hed_input_reader
        self.validator_base_new(test_strings, expected_results, expected_issues,
                                self.string_obj_func(validator), check_for_warnings=check_for_warnings,
                                hed_schema=validator._hed_schema)
