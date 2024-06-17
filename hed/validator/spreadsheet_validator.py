""" Validates spreadsheet tabular data. """
import copy

from hed.models.base_input import BaseInput
from hed.errors.error_types import ColumnErrors, ErrorContext, ValidationErrors
from hed.errors.error_reporter import ErrorHandler
from hed.models.column_mapper import ColumnType
from hed.models.hed_string import HedString
from hed.errors.error_reporter import sort_issues, check_for_any_errors
from hed.validator.onset_validator import OnsetValidator
from hed.validator.hed_validator import HedValidator
from hed.models import df_util


PANDAS_COLUMN_PREFIX_TO_IGNORE = "Unnamed: "


class SpreadsheetValidator:
    def __init__(self, hed_schema):
        """
        Constructor for the SpreadsheetValidator class.

        Parameters:
            hed_schema (HedSchema): HED schema object to use for validation.
        """
        self._schema = hed_schema
        self._hed_validator = None
        self._onset_validator = None
        self.invalid_original_rows = set()

    def validate(self, data, def_dicts=None, name=None, error_handler=None):
        """
        Validate the input data using the schema

        Parameters:
            data (BaseInput): Input data to be validated.
            def_dicts(list of DefDict or DefDict): all definitions to use for validation
            name(str): The name to report errors from this file as
            error_handler (ErrorHandler): Error context to use.  Creates a new one if None
        Returns:
            issues (list of dict): A list of issues for hed string
        """

        issues = []
        if error_handler is None:
            error_handler = ErrorHandler()

        if not isinstance(data, BaseInput):
            raise TypeError("Invalid type passed to spreadsheet validator.  Can only validate BaseInput objects.")

        self.invalid_original_rows = set()

        error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        # Adjust to account for 1 based
        row_adj = 1
        # Adjust to account for column names
        if data.has_column_names:
            row_adj += 1
        issues += self._validate_column_structure(data, error_handler, row_adj)

        if data.needs_sorting:
            data_new = copy.deepcopy(data)
            data_new._dataframe = df_util.sort_dataframe_by_onsets(data.dataframe)
            issues += error_handler.format_error_with_context(ValidationErrors.ONSETS_OUT_OF_ORDER)
            data = data_new

        onsets = df_util.split_delay_tags(data.series_a, self._schema, data.onsets)
        df = data.dataframe_a

        self._hed_validator = HedValidator(self._schema, def_dicts=def_dicts)
        if data.onsets is not None:
            self._onset_validator = OnsetValidator()
        else:
            self._onset_validator = None

        # Check the rows of the input data
        issues += self._run_checks(df, error_handler=error_handler, row_adj=row_adj,
                                   has_onsets=bool(self._onset_validator))
        if self._onset_validator:
            issues += self._run_onset_checks(onsets, error_handler=error_handler, row_adj=row_adj)
        error_handler.pop_error_context()

        issues = sort_issues(issues)
        return issues

    def _run_checks(self, hed_df, error_handler, row_adj, has_onsets):
        issues = []
        columns = list(hed_df.columns)
        self.invalid_original_rows = set()
        for row_number, text_file_row in hed_df.iterrows():
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
                error_handler.pop_error_context()  # HedString
                error_handler.pop_error_context()  # column

                issues += new_column_issues
            # We want to do full onset checks on the combined and filtered rows
            if check_for_any_errors(new_column_issues):
                self.invalid_original_rows.add(row_number)
                error_handler.pop_error_context()  # Row
                continue

            if has_onsets or not row_strings:
                error_handler.pop_error_context()  # Row
                continue

            row_string = HedString.from_hed_strings(row_strings)

            if row_string:
                error_handler.push_error_context(ErrorContext.HED_STRING, row_string)
                new_column_issues = self._hed_validator.run_full_string_checks(row_string)
                new_column_issues += OnsetValidator.check_for_banned_tags(row_string)
                error_handler.add_context_and_filter(new_column_issues)
                error_handler.pop_error_context()  # HedString
                issues += new_column_issues
            error_handler.pop_error_context()  # Row
        return issues

    def _run_onset_checks(self, onset_filtered, error_handler, row_adj):
        issues = []
        for row in onset_filtered[["HED", "original_index"]].itertuples(index=True):
            # Skip rows that had issues.
            if row.original_index in self.invalid_original_rows:
                continue
            error_handler.push_error_context(ErrorContext.ROW, row.original_index + row_adj)
            row_string = HedString(row.HED, self._schema, self._hed_validator._def_validator)

            if row_string:
                error_handler.push_error_context(ErrorContext.HED_STRING, row_string)
                new_column_issues = self._hed_validator.run_full_string_checks(row_string)
                new_column_issues += self._onset_validator.validate_temporal_relations(row_string)
                error_handler.add_context_and_filter(new_column_issues)
                error_handler.pop_error_context()  # HedString
                issues += new_column_issues
            error_handler.pop_error_context()  # Row
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
