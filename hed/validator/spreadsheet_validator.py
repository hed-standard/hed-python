import pandas as pd
from hed import BaseInput
from hed.errors import ErrorHandler, ValidationErrors, ErrorContext
from hed.errors.error_types import ColumnErrors
from hed.models import ColumnType
from hed import HedString
from hed.errors.error_reporter import sort_issues, check_for_any_errors
from hed.validator.onset_validator import OnsetValidator
from hed.validator.hed_validator import HedValidator

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
        self._onset_validator = None

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

        issues = []
        if error_handler is None:
            error_handler = ErrorHandler()

        error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        self._hed_validator = HedValidator(self._schema, def_dicts=def_dicts)
        self._onset_validator = OnsetValidator()
        onset_filtered = None
        # Adjust to account for 1 based
        row_adj = 1
        if isinstance(data, BaseInput):
            # Adjust to account for column names
            if data.has_column_names:
                row_adj += 1
            issues += self._validate_column_structure(data, error_handler, row_adj)
            onset_filtered = data.series_filtered
            data = data.dataframe_a

        # Check the rows of the input data
        issues += self._run_checks(data, onset_filtered, error_handler=error_handler, row_adj=row_adj)
        error_handler.pop_error_context()

        issues = sort_issues(issues)
        return issues

    def _run_checks(self, hed_df, onset_filtered, error_handler, row_adj):
        issues = []
        columns = list(hed_df.columns)
        for row_number, text_file_row in enumerate(hed_df.itertuples(index=False)):
            error_handler.push_error_context(ErrorContext.ROW, row_number + row_adj)
            row_strings = []
            new_column_issues = []
            for column_number, cell in enumerate(text_file_row):
                if not cell or cell == "n/a":
                    continue

                error_handler.push_error_context(ErrorContext.COLUMN, columns[column_number])

                column_hed_string = HedString(cell, self._schema)
                row_strings.append(column_hed_string)
                error_handler.push_error_context(ErrorContext.HED_STRING, column_hed_string)
                new_column_issues = self._hed_validator.run_basic_checks(column_hed_string, allow_placeholders=False)

                error_handler.add_context_and_filter(new_column_issues)
                error_handler.pop_error_context()
                error_handler.pop_error_context()

                issues += new_column_issues
            if check_for_any_errors(new_column_issues):
                error_handler.pop_error_context()
                continue

            row_string = None
            if onset_filtered is not None:
                row_string = HedString(onset_filtered[row_number], self._schema, self._hed_validator._def_validator)
            elif row_strings:
                row_string = HedString.from_hed_strings(row_strings)

            if row_string:
                error_handler.push_error_context(ErrorContext.HED_STRING, row_string)
                new_column_issues = self._hed_validator.run_full_string_checks(row_string)
                new_column_issues += self._onset_validator.validate_temporal_relations(row_string)
                error_handler.add_context_and_filter(new_column_issues)
                error_handler.pop_error_context()
                issues += new_column_issues
            error_handler.pop_error_context()
        return issues

    def _validate_column_structure(self, base_input, error_handler, row_adj):
        """
        Validate that each column in the input data has valid values.

        Parameters:
            base_input (BaseInput): The input data to be validated.
            error_handler (ErrorHandler): Holds context
            row_adj(int): Number to adjust row by for reporting errors
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
                        error_handler.push_error_context(ErrorContext.ROW, row_number + row_adj)
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
