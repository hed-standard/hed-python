import pandas as pd
from hed import BaseInput
from hed.errors import ErrorHandler, ValidationErrors, ErrorContext
from hed.errors.error_types import ColumnErrors
from hed.models import ColumnType
from hed import HedString
from hed.models.hed_string_group import HedStringGroup
from hed.errors.error_reporter import sort_issues, check_for_any_errors

PANDAS_COLUMN_PREFIX_TO_IGNORE = "Unnamed: "


class SpreadsheetValidator:
    def __init__(self, hed_schema):
        """
        Constructor for the HedValidator class.

        Parameters:
            hed_schema (HedSchema): HED schema object to use for validation.
        """
        self._schema = hed_schema
        self._hed_validator = None

    def validate(self, data, def_dicts=None, name=None, error_handler=None):
        """
        Validate the input data using the schema

        Parameters:
            data (BaseInput or pd.DataFrame): Input data to be validated.
                If a dataframe, it is assumed to be assembled already.
            def_dicts(list of DefDict or DefDict): all definitions to use for validation
            name(str): The name to report errors from this file as
            error_handler (ErrorHandler): Error context to use.  Creates a new one if None
        Returns:
            issues (list of dict): A list of issues for hed string
        """
        from hed.validator import HedValidator
        issues = []
        if error_handler is None:
            error_handler = ErrorHandler()

        error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        self._hed_validator = HedValidator(self._schema, def_dicts=def_dicts)
        # Check the structure of the input data, if it's a BaseInput
        if isinstance(data, BaseInput):
            issues += self._validate_column_structure(data, error_handler)
            data = data.dataframe_a

        # Check the rows of the input data
        issues += self._run_checks(data, error_handler)
        error_handler.pop_error_context()

        issues = sort_issues(issues)
        return issues

    def _run_checks(self, data, error_handler):
        issues = []
        columns = list(data.columns)
        for row_number, text_file_row in enumerate(data.itertuples(index=False)):
            error_handler.push_error_context(ErrorContext.ROW, row_number)
            row_strings = []
            new_column_issues = []
            for column_number, cell in enumerate(text_file_row):
                if not cell or cell == "n/a":
                    continue

                error_handler.push_error_context(ErrorContext.COLUMN, columns[column_number])

                column_hed_string = HedString(cell)
                row_strings.append(column_hed_string)
                error_handler.push_error_context(ErrorContext.HED_STRING, column_hed_string)
                new_column_issues = self._hed_validator.run_basic_checks(column_hed_string, allow_placeholders=False)

                error_handler.add_context_and_filter(new_column_issues)
                error_handler.pop_error_context()
                error_handler.pop_error_context()

                issues += new_column_issues
            if check_for_any_errors(new_column_issues):
                continue
            else:
                row_string = HedStringGroup(row_strings)
                error_handler.push_error_context(ErrorContext.HED_STRING, row_string)
                new_column_issues = self._hed_validator.run_full_string_checks(row_string)

                error_handler.add_context_and_filter(new_column_issues)
                error_handler.pop_error_context()
                issues += new_column_issues
            error_handler.pop_error_context()
        return issues

    def _validate_column_structure(self, base_input, error_handler):
        """
        Validate that each column in the input data has valid values.

        Parameters:
            base_input (BaseInput): The input data to be validated.
            error_handler (ErrorHandler): Holds context
        Returns:
            List of issues associated with each invalid value. Each issue is a dictionary.
        """
        issues = []
        col_issues = base_input._mapper.check_for_mapping_issues(base_input)
        error_handler.add_context_and_filter(col_issues)
        issues += col_issues
        for column in base_input.column_metadata().values():
            if column.column_type == ColumnType.Categorical:
                error_handler.push_error_context(ErrorContext.COLUMN, column.column_name)
                valid_keys = column.hed_dict.keys()
                for row_number, value in enumerate(base_input.dataframe[column.column_name]):
                    if value != "n/a" and value not in valid_keys:
                        error_handler.push_error_context(ErrorContext.ROW, row_number)
                        issues += error_handler.format_error_with_context(ValidationErrors.SIDECAR_KEY_MISSING,
                                                                          invalid_key=value,
                                                                          category_keys=list(valid_keys))
                        error_handler.pop_error_context()
                error_handler.pop_error_context()

        column_refs = base_input.get_column_refs()
        columns = base_input.columns
        for ref in column_refs:
            if ref not in columns:
                issues += error_handler.format_error_with_context(ColumnErrors.INVALID_COLUMN_REF,
                                                                  bad_ref=ref)

        return issues
