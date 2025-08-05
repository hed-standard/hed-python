""" Validates spreadsheet tabular data. """
from __future__ import annotations
import copy
import pandas as pd
import math
import re
from hed.models.base_input import BaseInput
from hed.errors.error_types import  ErrorContext, ValidationErrors, TemporalErrors
from hed.errors.error_reporter import ErrorHandler
from hed.models.column_mapper import ColumnType
from hed.models.hed_string import HedString
from hed.errors.error_reporter import sort_issues, check_for_any_errors
from hed.validator.onset_validator import OnsetValidator
from hed.validator.hed_validator import HedValidator
from hed.models import df_util
from hed.models.model_constants import DefTagNames


PANDAS_COLUMN_PREFIX_TO_IGNORE = "Unnamed: "


class SpreadsheetValidator:
    ONSET_TOLERANCE = 10-7
    TEMPORAL_ANCHORS = re.compile(r"|".join(map(re.escape, ["onset", "inset", "offset", "delay"])))

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

    def validate(self, data, def_dicts=None, name=None, error_handler=None) -> list[dict]:
        """
        Validate the input data using the schema

        Parameters:
            data (BaseInput): Input data to be validated.
            def_dicts (list of DefDict or DefDict): all definitions to use for validation
            name (str): The name to report errors from this file as
            error_handler (ErrorHandler): Error context to use.  Creates a new one if None.

        Returns:
            list[dict]: A list of issues for HED string
        """

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

        issues = self._validate_column_structure(data, error_handler)

        if data.needs_sorting:
            data_new = copy.deepcopy(data)
            data_new._dataframe = df_util.sort_dataframe_by_onsets(data.dataframe)
            issues += error_handler.format_error_with_context(ValidationErrors.ONSETS_UNORDERED)
            data = data_new

        # If there are n/a errors in the onset column, further validation cannot proceed
        onsets = data.onsets
        if onsets is not None:
            onsets = onsets.astype(str).str.strip()
            onsets = pd.to_numeric(onsets, errors='coerce')
            assembled = data.series_a
            na_issues = self._check_onset_nans(onsets, assembled, self._schema, error_handler, row_adj)
            issues += na_issues
            if len(na_issues) > 0:
                return issues
            onsets = df_util.split_delay_tags(assembled, self._schema, onsets)
        else:
            onsets = None

        df = data.dataframe_a

        self._hed_validator = HedValidator(self._schema, def_dicts=def_dicts)
        if onsets is not None:
            self._onset_validator = OnsetValidator()
            onset_mask = ~pd.isna(pd.to_numeric(onsets['onset'], errors='coerce'))
        else:
            self._onset_validator = None
            onset_mask = None

        # Check the rows of the input data
        issues += self._run_checks(df, error_handler=error_handler, row_adj=row_adj, onset_mask=onset_mask)
        if self._onset_validator:
            issues += self._run_onset_checks(onsets, error_handler=error_handler, row_adj=row_adj)
            issues += self._recheck_duplicates(onsets, error_handler=error_handler, row_adj=row_adj)
        error_handler.pop_error_context()

        issues = sort_issues(issues)
        return issues

    def _run_checks(self, hed_df, error_handler, row_adj, onset_mask=None):
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

            if not row_strings or (onset_mask is not None and onset_mask.iloc[row_number]):
                error_handler.pop_error_context()  # Row
                continue

            # Continue on if not a timeline file
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

    def _recheck_duplicates(self, onset_filtered, error_handler, row_adj):
        issues = []
        for i in range(len(onset_filtered) - 1):
            current_row = onset_filtered.iloc[i]
            next_row = onset_filtered.iloc[i + 1]

            # Skip if the HED column is empty or there was already an error
            if not current_row["HED"] or \
                (current_row["original_index"] in self.invalid_original_rows) or \
                    (not self._is_within_tolerance(next_row["onset"], current_row["onset"])):
                continue

            # At least two rows have been merged with their onsets recognized as the same.
            error_handler.push_error_context(ErrorContext.ROW, current_row.original_index + row_adj)
            row_string = HedString(current_row.HED, self._schema, self._hed_validator._def_validator)
            error_handler.push_error_context(ErrorContext.HED_STRING, row_string)
            new_column_issues = self._hed_validator.run_full_string_checks(row_string)
            error_handler.add_context_and_filter(new_column_issues)
            error_handler.pop_error_context()  # HedString
            issues += new_column_issues
            error_handler.pop_error_context()  # Row

        return issues

    def _is_within_tolerance(self, onset1, onset2):
        """
        Checks if two onset strings are within the specified tolerance.

        Parameters:
            onset1 (str): The first onset value as a string.
            onset2 (str): The second onset value as a string.

        Returns:
            bool: True if the values are within tolerance and valid, False otherwise.
        """
        try:
            # Convert to floats
            onset1 = float(onset1)
            onset2 = float(onset2)

            # Check if both values are finite
            if not (math.isfinite(onset1) and math.isfinite(onset2)):
                return False

            # Check if the difference is within tolerance
            return abs(onset1 - onset2) <= self.ONSET_TOLERANCE
        except ValueError:
            # Return False if either value is not convertible to a float
            return False

    def _validate_column_structure(self, base_input, error_handler):
        """
        Validate that each column in the input data has valid values.

        Parameters:
            base_input (BaseInput): The input data to be validated.
            error_handler (ErrorHandler): Holds context.

        Returns:
            List[dict]: Issues associated with each invalid value. Each issue is a dictionary.
        """
        issues = []
        col_issues = base_input._mapper.check_for_mapping_issues()
        error_handler.add_context_and_filter(col_issues)
        issues += col_issues
        for column in base_input.column_metadata().values():
            if column.column_type == ColumnType.Categorical:
                valid_keys = set(column.hed_dict.keys())
                column_values = base_input.dataframe[column.column_name]

                # Find non n/a values that are not in the valid keys
                invalid_values = set(column_values[(column_values != "n/a") & (~column_values.isin(valid_keys))])

                # If there are invalid values, log a single error
                if invalid_values:
                    error_handler.push_error_context(ErrorContext.COLUMN, column.column_name)
                    issues += error_handler.format_error_with_context(ValidationErrors.SIDECAR_KEY_MISSING,
                        invalid_keys=str(list(invalid_values)),  category_keys=list(valid_keys),
                        column_name=column.column_name)
                    error_handler.pop_error_context()

        column_refs = set(base_input.get_column_refs())  # Convert to set for O(1) lookup
        columns = set(base_input.columns)  # Convert to set for efficient comparison

        # Find missing column references
        missing_refs = column_refs - columns  # Set difference: elements in column_refs but not in columns

        # If there are missing references, log a single error
        if missing_refs:
            issues += error_handler.format_error_with_context(
                ValidationErrors.TSV_COLUMN_MISSING,
                invalid_keys=list(missing_refs)  # Include all missing column references
            )

        return issues

    def _check_onset_nans(self, onsets, assembled, hed_schema, error_handler, row_adj):
        onset_mask = pd.isna(onsets)
        if not onset_mask.any():
            return []
        filtered = assembled[onset_mask]
        issues = []
        for index, value in filtered.items():
            if not bool(self.TEMPORAL_ANCHORS.search(value.casefold())):
                continue
            hed_obj = HedString(value, hed_schema)
            error_handler.push_error_context(ErrorContext.ROW, index + row_adj)
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_obj)
            for tag in hed_obj.find_top_level_tags(anchor_tags=DefTagNames.TIMELINE_KEYS, include_groups=0):
                issues += error_handler.format_error_with_context(TemporalErrors.TEMPORAL_TAG_NO_TIME, tag=tag)
            error_handler.pop_error_context()
            error_handler.pop_error_context()
        return issues
        #filtered = assembled.loc[onset_mask.index[onset_mask]]
        # for row_number, text_file_row in filtered.iteritems():
        #     error_handler.push_error_context(ErrorContext.ROW, row_number + row_adj)
        #     error_handler.push_error_context(ErrorContext.COLUMN, text_file_row.name)
        #     error_handler.push_error_context(ErrorContext.HED_STRING, text_file_row)
        #     issues = error_handler.format_error_with_context(ValidationErrors.ONSETS_NAN)
        #     error_handler.pop_error_context()

