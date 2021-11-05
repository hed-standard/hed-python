import unittest
import os
from io import StringIO
from hed.models.hed_string import HedString
from hed.validator.hed_validator import HedValidator
from hed.errors import error_reporter
from hed.errors import ErrorHandler, ErrorContext
from hed import schema


class TestHedBase(unittest.TestCase):
    schema_file = None

    @classmethod
    def setUpClass(cls):
        if cls.schema_file:
            hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
            cls.hed_schema = schema.load_schema(hed_xml)
        elif not cls.hed_schema:
            raise ValueError("No schema set for test case")
        cls.error_handler = error_reporter.ErrorHandler()

    def format_error_but_not_really(self, error_type, *args, **kwargs):
        """
            The parameters vary based on what type of error this is.

            Note: If you want to pass a tag as a number to this function, you will need to pass tag as a keyword.

        Parameters
        ----------
        error_type : str
            The type of error for this.  Registered with @hed_error or @hed_tag_error.
        args: args
            The rest of the unnamed args
        kwargs :
            The other parameters to pass down to the error handling func.
        Returns
        -------
        error: [{}]
            A single error
        """
        _ = ErrorHandler.format_error(error_type, *args, **kwargs)
        # Save off params
        params = [error_type, args, kwargs]
        # return params
        return [params]

    def really_format_errors(self, error_handler, hed_string, params):
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
        cls.syntactic_hed_input_reader = HedValidator(hed_schema=None,
                                                      run_semantic_validation=False)
        cls.syntactic_tag_validator = cls.syntactic_hed_input_reader._tag_validator
        cls.semantic_hed_input_reader = HedValidator(hed_schema=cls.hed_schema,
                                                     run_semantic_validation=True)
        cls.semantic_tag_validator = cls.semantic_hed_input_reader._tag_validator

    def validator_base(self, test_strings, expected_results, expected_issues, test_function,
                       hed_schema=None):
        for test_key in test_strings:
            hed_string_obj = HedString(test_strings[test_key])
            error_handler = ErrorHandler()
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj, increment_depth_after=False)
            test_issues = []
            if self.compute_forms:
                test_issues += hed_string_obj.convert_to_canonical_forms(hed_schema)
            if not test_issues:
                test_issues += test_function(hed_string_obj)
            test_result = not test_issues
            expected_params = expected_issues[test_key]
            expected_result = expected_results[test_key]
            expected_issue = self.really_format_errors(error_handler, hed_string=hed_string_obj,
                                                       params=expected_params)
            error_handler.add_context_to_issues(test_issues)

            # print(test_key)
            # print(str(expected_issue))
            # print(str(test_issues))
            error_handler.pop_error_context()
            self.assertEqual(test_result, expected_result, test_strings[test_key])
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])

    def validator_syntactic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        validator = self.syntactic_hed_input_reader
        self.validator_base(test_strings, expected_results, expected_issues,
                            self.string_obj_func(validator, check_for_warnings=check_for_warnings))

    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        validator = self.semantic_hed_input_reader
        self.validator_base(test_strings, expected_results, expected_issues,
                            self.string_obj_func(validator, check_for_warnings=check_for_warnings),
                            hed_schema=validator._hed_schema)
