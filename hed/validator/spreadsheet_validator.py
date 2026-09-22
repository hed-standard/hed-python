"""Validates HED annotations in tabular data in four stopping stages."""

from __future__ import annotations

import copy
import math
import re
import warnings

import pandas as pd

from hed.errors.error_reporter import ErrorHandler, check_for_any_errors, sort_issues
from hed.errors.error_types import ErrorContext, TemporalErrors, ValidationErrors
from hed.models import df_util
from hed.models.base_input import BaseInput
from hed.models.column_mapper import ColumnMapper, ColumnType
from hed.models.column_source import ColumnSource
from hed.models.definition_dict import DefinitionDict
from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.model_constants import DefTagNames, TopTagReturnType
from hed.models.sidecar import Sidecar
from hed.validator.hed_validator import HedValidator
from hed.validator.onset_validator import OnsetValidator
from hed.validator.sidecar_validator import SidecarValidator
from hed.validator.util.placeholder_util import placeholder_tag

PANDAS_COLUMN_PREFIX_TO_IGNORE = "Unnamed: "

# Extra key on an issue found by a distinct-value stage: how many rows hold the value reported. It is not
# an "ec_" key, so the error handler does not treat it as context.
ROW_COUNT_KEY = "row_count"


class SpreadsheetValidator:
    """Validates HED annotations in tabular data against a HED schema, in four stages.

    The stages run in order and each stops the run when it finds an error (never on a warning alone):

    1. **Sidecar**: every template and categorical string of the sidecar (``SidecarValidator``).
    2. **Column values**: the column structure (mapper issues, sidecar references to columns the table
       lacks), then each value column's distinct values against the units or value class of its ``#``
       tag, and each categorical column's distinct values against its sidecar keys.
    3. **HED column**: each distinct string of every HED-tags column, the basic (single-string) checks.
    4. **Assembly**: the rows assembled from all columns, the group-level checks, and the onset and
       temporal checks of a timeline file.

    Stages 2 and 3 work from a :class:`~hed.models.column_source.ColumnSource`, which answers with column
    names and distinct values and never has to involve pandas; a source that returns None from
    ``as_base_input`` never reaches stage 4. :class:`~hed.models.base_input.BaseInput` is the source for
    BIDS files. Each stage is also a public method, so a caller can run one column at a time.

    Rows are reported as the 0-based row index plus ``row_offset``. For a :class:`~hed.models.base_input.BaseInput`
    the default offset counts the header line and reports 1-based file lines, as before. An issue found
    for a value or HED-column string is reported once, at the first row holding the value, with the number
    of rows holding it in ``row_count``. The categorical check keeps its column-level form: one
    SIDECAR_KEY_MISSING warning per column naming every unknown value, with no row, as before.
    """

    ONSET_TOLERANCE = 1e-7
    TEMPORAL_ANCHORS = re.compile(r"|".join(map(re.escape, ["onset", "inset", "offset", "delay"])))

    def __init__(self, hed_schema, def_dicts=None):
        """
        Constructor for the SpreadsheetValidator class.

        Parameters:
            hed_schema (HedSchema): HED schema object to use for validation.
            def_dicts (DefinitionDict, list, str, or None): Definitions for the stage methods when they are
                called on their own. ``validate`` replaces them with the sidecar's definitions plus its
                ``extra_def_dicts`` for the duration of the run.
        """
        self._schema = hed_schema
        self._onset_validator = None
        self._def_dict = None
        self._hed_validator = None
        self._set_definitions(DefinitionDict(def_dicts, hed_schema=hed_schema))

    def _set_definitions(self, def_dict):
        self._def_dict = def_dict
        self._hed_validator = HedValidator(self._schema, def_dicts=def_dict)

    def validate(
        self,
        source,
        sidecar=None,
        extra_def_dicts=None,
        name=None,
        error_handler=None,
        row_offset=None,
        validate_sidecar=True,
        def_dicts=None,
    ) -> list[dict]:
        """Run the four stages on a column source, stopping at the first stage that finds an error.

        Parameters:
            source (ColumnSource): The table to validate. A BaseInput (TabularInput, SpreadsheetInput) or any
                object with the ColumnSource methods.
            sidecar (Sidecar or None): The sidecar describing the columns. For a BaseInput this must be
                the sidecar it was constructed with (None takes it), since the input's mapper and
                assembly come from that sidecar; anything else raises ValueError.
            extra_def_dicts (list of DefinitionDict or DefinitionDict or None): Definitions in addition to
                the sidecar's.
            name (str or None): The name to report errors from this table as. If empty, no FILE_NAME
                context is added, so a caller that manages its own location context (for example a table
                inside a larger file) sees only the context it pushed.
            error_handler (ErrorHandler): Error context to use. Creates a new one if None.
            row_offset (int or None): Added to the 0-based row index in every reported row. None means
                1 plus 1 for the header line for a BaseInput (1-based file lines), and 0 otherwise.
            validate_sidecar (bool): If False, skip stage 1 because the caller has validated the sidecar
                already. The sidecar is still used for its definitions and column descriptions. A
                sidecar error that the caller did not catch is not found by the later stages: a template
                or categorical string with an invalid tag simply contributes nothing to check.
            def_dicts: Deprecated name for ``extra_def_dicts`` (removed in hedtools 2.0.0). Before the
                stages, this was the second positional parameter; a positional definition dictionary
                is now caught and reported as a TypeError rather than validated as a sidecar.

        Returns:
            list[dict]: The issues found, sorted by location.
        """
        if def_dicts is not None:
            warnings.warn(
                "The def_dicts= parameter of SpreadsheetValidator.validate is deprecated and will be removed "
                "in hedtools 2.0.0; pass the definitions as extra_def_dicts=.",
                DeprecationWarning,
                stacklevel=2,
            )
            extra_def_dicts = [extra_def_dicts, def_dicts] if extra_def_dicts is not None else def_dicts
        if sidecar is not None and not isinstance(sidecar, Sidecar):
            raise TypeError(
                "sidecar must be a Sidecar. Definitions go in extra_def_dicts=; the second positional "
                "parameter of SpreadsheetValidator.validate is the sidecar since the staged validator."
            )
        if error_handler is None:
            error_handler = ErrorHandler()
        if isinstance(source, BaseInput):
            if sidecar is None:
                sidecar = source.get_sidecar()
            elif sidecar is not source.get_sidecar():
                # The source's mapper and its assembly come from the sidecar it was built with, so a
                # different one here would validate one set of column descriptions and assemble another.
                raise ValueError(
                    "A BaseInput is validated with the sidecar it was constructed with; pass the sidecar to "
                    "TabularInput instead of to validate."
                )
            if row_offset is None:
                row_offset = 1 + int(source.has_column_names)
        elif not isinstance(source, ColumnSource):
            raise TypeError("Invalid type passed to spreadsheet validator. Can only validate ColumnSource objects.")
        if row_offset is None:
            row_offset = 0
        if extra_def_dicts is not None and not isinstance(extra_def_dicts, DefinitionDict):
            # Strings and lists of strings need the schema to become definitions.
            extra_def_dicts = DefinitionDict(extra_def_dicts, hed_schema=self._schema)

        issues = []
        # Stage 1 runs before this table's FILE_NAME context is pushed so that its issues carry the
        # sidecar's own name. With no name here, the caller manages the location context for both.
        if sidecar is not None and validate_sidecar:
            # An empty name means the caller manages the location context for both; None means only
            # that the table has no name, and the sidecar keeps its own.
            sidecar_name = "" if name == "" else sidecar.name
            issues += SidecarValidator(self._schema).validate(
                sidecar, extra_def_dicts, name=sidecar_name, error_handler=error_handler
            )
            if check_for_any_errors(issues):
                return sort_issues(issues)

        # The FILE_NAME context is popped in a finally block so that every return path, including the
        # early returns of each stage, leaves the caller's error handler as it found it.
        if name:
            error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        try:
            return self._validate_source(source, sidecar, extra_def_dicts, error_handler, row_offset, issues)
        finally:
            if name:
                error_handler.pop_error_context()

    def _validate_source(self, source, sidecar, extra_def_dicts, error_handler, row_offset, issues) -> list[dict]:
        """Stages 2 to 4, run with the FILE_NAME context (if any) already pushed."""
        if sidecar is not None:
            def_dict = sidecar.get_def_dict(self._schema, extra_def_dicts)
        else:
            def_dict = DefinitionDict(extra_def_dicts, hed_schema=self._schema)
        self._set_definitions(def_dict)

        column_names = source.column_names()
        mapper = source.column_mapper()
        if mapper is None:
            mapper = self._build_mapper(sidecar, column_names)
        columns = list(mapper._final_column_map.values())

        # Stage 2: the column structure, then every value and categorical column's own values. A value
        # column that curly braces reference is checked here like any other, whether or not a row's
        # template substitutes it, so a bad value never hides behind an unused reference. A template
        # is checked here only when no sidecar exists to have checked it (a column_prefix_dictionary).
        issues += self.validate_column_structure(column_names, mapper, sidecar, error_handler)
        for column in columns:
            if column.column_type == ColumnType.Value:
                issues += self.validate_value_column(
                    column.column_name,
                    column.hed_dict,
                    source.distinct_values(column.column_name),
                    error_handler,
                    row_offset=row_offset,
                    check_template=sidecar is None,
                )
            elif column.column_type == ColumnType.Categorical:
                issues += self.validate_categorical_column(
                    column.column_name,
                    list(column.hed_dict),
                    source.distinct_values(column.column_name),
                    error_handler,
                )
        if check_for_any_errors(issues):
            return sort_issues(issues)

        # Stage 3: every HED-tags column, one parse per distinct string.
        for column in columns:
            if column.column_type == ColumnType.HEDTags:
                issues += self.validate_hed_column(
                    column.column_name, source.distinct_values(column.column_name), error_handler, row_offset=row_offset
                )
        if check_for_any_errors(issues):
            return sort_issues(issues)

        # Stage 4: the assembled rows, only for a source that can provide them.
        base_input = source.as_base_input()
        if base_input is not None:
            issues += self.validate_assembled(base_input, error_handler, row_offset=row_offset)
        return sort_issues(issues)

    @staticmethod
    def _build_mapper(sidecar, column_names):
        """Build the mapper a TabularInput would use for these columns: an optional HED column and a
        warning for every column the sidecar does not describe."""
        mapper = ColumnMapper(sidecar=sidecar, optional_tag_columns=["HED"], warn_on_missing_column=True)
        mapper.set_column_map(column_names)
        return mapper

    # ------------------------------------------------------------------------------------------
    # Stage 2

    def validate_column_structure(self, column_names, mapper, sidecar, error_handler) -> list[dict]:
        """Report the column-level issues that need no data: mapper issues and sidecar references to
        columns the table does not have.

        Parameters:
            column_names (list): The table's column names.
            mapper (ColumnMapper): The mapper for these columns.
            sidecar (Sidecar or None): The sidecar whose column references are checked.
            error_handler (ErrorHandler): Holds context.

        Returns:
            list[dict]: The issues found.
        """
        issues = mapper.check_for_mapping_issues()
        error_handler.add_context_and_filter(issues)
        if sidecar is None:
            return issues
        missing_refs = sorted(set(sidecar.get_column_refs()) - set(column_names))
        if missing_refs:
            issues += error_handler.format_error_with_context(
                ValidationErrors.TSV_COLUMN_MISSING, invalid_keys=missing_refs
            )
        return issues

    def validate_value_column(
        self, column_name, template, distinct, error_handler, row_offset=0, check_template=False
    ) -> list[dict]:
        """Check each distinct value of a value column as the template's ``#`` tag with the value in place.

        Only that one tag is checked, with ``HedValidator.validate_units``: a unit class tag needs valid
        units and a numeric value, a value class tag needs a value of that class, and any other tag
        needs an extension made of allowed characters. A value that passes is then spliced into the tag
        and the result parsed with the basic single-string checks, so a value that would break the HED
        string it lands in (an unbalanced parenthesis, a tilde, a pound sign) is rejected too. The other
        tags of the template and its ``{column}`` references play no part; they are the sidecar
        validator's business. For a ``Def/Name/#`` template the placeholder tag inside the definition is
        the one checked.

        Parameters:
            column_name (str or int): The column, for the error context.
            template (str): The column's HED string with its ``#``.
            distinct (dict[str, list[int]]): Distinct cell text -> 0-based rows holding it.
            error_handler (ErrorHandler): Holds context.
            row_offset (int): Added to the first row of each reported value.
            check_template (bool): If True, run the basic checks on the template itself first (with
                placeholders allowed) and skip the values if it has an error. For a template that no
                sidecar validation has covered.

        Returns:
            list[dict]: The issues found, one per distinct bad value, each with ``row_count``.
        """
        issues = []
        error_handler.push_error_context(ErrorContext.COLUMN, column_name)
        try:
            if check_template:
                template_obj = HedString(template, self._schema, def_dict=self._def_dict)
                template_obj.remove_refs()
                error_handler.push_error_context(ErrorContext.HED_STRING, template_obj)
                template_issues = self._hed_validator.run_basic_checks(template_obj, allow_placeholders=True)
                error_handler.add_context_and_filter(template_issues)
                error_handler.pop_error_context()  # HedString
                issues += template_issues
                if check_for_any_errors(template_issues):
                    return issues
            placeholder = placeholder_tag(template, self._schema, self._def_dict)
            if placeholder is None:
                return issues
            tag_text = str(placeholder)
            for value, rows in distinct.items():
                substituted = tag_text.replace("#", value, 1)
                # Units and value class first, on the one tag, so a bad character in the value is reported
                # as such. A value that passes may still break the HED string it will be spliced into
                # ("(a", "a~b", "a#b"), so the substituted tag is then parsed and given the basic checks.
                tag = HedTag(substituted, self._schema)
                tag_issues = self._hed_validator.validate_units(tag, allow_placeholders=False)
                if not tag_issues:
                    tag_issues = self._hed_validator.run_basic_checks(
                        HedString(substituted, self._schema, def_dict=self._def_dict), allow_placeholders=False
                    )
                if not tag_issues:
                    continue
                error_handler.push_error_context(ErrorContext.ROW, rows[0] + row_offset)
                error_handler.add_context_and_filter(tag_issues)
                error_handler.pop_error_context()  # Row
                for issue in tag_issues:
                    issue[ROW_COUNT_KEY] = len(rows)
                issues += tag_issues
        finally:
            error_handler.pop_error_context()  # Column
        return issues

    @staticmethod
    def validate_categorical_column(column_name, keys, distinct, error_handler) -> list[dict]:
        """Report the distinct values of a categorical column that its sidecar does not annotate.

        Parameters:
            column_name (str or int): The column, for the error context.
            keys (iterable): The sidecar keys for this column.
            distinct (dict[str, list[int]]): Distinct cell text -> 0-based rows holding it.
            error_handler (ErrorHandler): Holds context.

        Returns:
            list[dict]: One SIDECAR_KEY_MISSING issue (a warning) naming every unknown value, or nothing.
        """
        keys = list(keys)
        known = set(keys)
        invalid = [value for value in distinct if value not in known]
        if not invalid:
            return []
        error_handler.push_error_context(ErrorContext.COLUMN, column_name)
        issues = error_handler.format_error_with_context(
            ValidationErrors.SIDECAR_KEY_MISSING, invalid_keys=str(invalid), category_keys=keys, column_name=column_name
        )
        error_handler.pop_error_context()
        return issues

    # ------------------------------------------------------------------------------------------
    # Stage 3

    def validate_hed_column(self, column_name, distinct, error_handler, row_offset=0, full_string=False) -> list[dict]:
        """Run the single-string checks on each distinct string of a HED-tags column, once per string.

        Parameters:
            column_name (str or int): The column, for the error context.
            distinct (dict[str, list[int]]): Distinct cell text -> 0-based rows holding it.
            error_handler (ErrorHandler): Holds context.
            row_offset (int): Added to the first row of each reported string.
            full_string (bool): If True, also run the full-string (group-level) checks on each string
                that passes the basic checks. For a caller that will never assemble rows; otherwise
                those checks belong to the assembly stage, where the row is whole.

        Returns:
            list[dict]: The issues found, each with ``row_count``.
        """
        issues = []
        for text, rows in distinct.items():
            hed_string = HedString(text, self._schema)
            string_issues = self._hed_validator.run_basic_checks(hed_string, allow_placeholders=False)
            if full_string and not check_for_any_errors(string_issues):
                string_issues += self._hed_validator.run_full_string_checks(hed_string)
            if not string_issues:
                continue
            error_handler.push_error_context(ErrorContext.ROW, rows[0] + row_offset)
            error_handler.push_error_context(ErrorContext.COLUMN, column_name)
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_string)
            error_handler.add_context_and_filter(string_issues)
            error_handler.pop_error_context()  # HedString
            error_handler.pop_error_context()  # Column
            error_handler.pop_error_context()  # Row
            for issue in string_issues:
                issue[ROW_COUNT_KEY] = len(rows)
            issues += string_issues
        return issues

    # ------------------------------------------------------------------------------------------
    # Stage 4

    def validate_assembled(self, data, error_handler, row_offset=None) -> list[dict]:
        """Validate the assembled rows of a BaseInput: the group-level checks on each whole row, and for a
        timeline file the onset ordering, time conversions, and temporal relations.

        The single-string checks are not repeated here; stages 2 and 3 have covered every column's values.

        Parameters:
            data (BaseInput): The table, with its sidecar attached.
            error_handler (ErrorHandler): Holds context.
            row_offset (int or None): Added to the 0-based row index. None means 1 plus 1 for the header.

        Returns:
            list[dict]: The issues found.
        """
        if row_offset is None:
            row_offset = 1 + int(data.has_column_names)
        issues = []

        if data.needs_sorting:
            data_new = copy.deepcopy(data)
            data_new._dataframe = df_util.sort_dataframe_by_onsets(data.dataframe)
            issues += error_handler.format_error_with_context(ValidationErrors.ONSETS_UNORDERED)
            data = data_new

        # If there are n/a errors in the onset column, further validation cannot proceed
        onsets = data.onsets
        if onsets is not None:
            onsets = onsets.astype(str).str.strip()
            onsets = pd.to_numeric(onsets, errors="coerce")
            assembled = data.series_a
            na_issues = self._check_onset_nans(onsets, assembled, self._schema, error_handler, row_offset)
            issues += na_issues
            if len(na_issues) > 0:
                return issues
            assembled, time_issues = self._check_time_conversions(assembled, error_handler, row_offset)
            issues += time_issues
            onsets = df_util.split_delay_tags(assembled, self._schema, onsets)
        else:
            onsets = None

        df = data.dataframe_a

        if onsets is not None:
            self._onset_validator = OnsetValidator()
            onset_mask = ~pd.isna(pd.to_numeric(onsets["onset"], errors="coerce"))
        else:
            self._onset_validator = None
            onset_mask = None

        issues += self._run_row_checks(df, error_handler=error_handler, row_offset=row_offset, onset_mask=onset_mask)
        if self._onset_validator:
            issues += self._run_onset_checks(onsets, error_handler=error_handler, row_offset=row_offset)
            issues += self._recheck_duplicates(onsets, error_handler=error_handler, row_offset=row_offset)
        return issues

    def _run_row_checks(self, hed_df, error_handler, row_offset, onset_mask=None):
        """Full-string checks on each assembled row of a non-timeline file (timeline rows are checked after
        the onset merge in _run_onset_checks)."""
        issues = []
        for row_number, text_file_row in hed_df.iterrows():
            row_strings = [HedString(cell, self._schema) for cell in text_file_row if cell and cell != "n/a"]
            if not row_strings or (onset_mask is not None and onset_mask.iloc[row_number]):
                continue
            row_string = HedString.from_hed_strings(row_strings)
            if not row_string:
                continue
            error_handler.push_error_context(ErrorContext.ROW, row_number + row_offset)
            error_handler.push_error_context(ErrorContext.HED_STRING, row_string)
            row_issues = self._hed_validator.run_full_string_checks(row_string)
            row_issues += OnsetValidator.check_for_banned_tags(row_string)
            error_handler.add_context_and_filter(row_issues)
            error_handler.pop_error_context()  # HedString
            error_handler.pop_error_context()  # Row
            issues += row_issues
        return issues

    def _run_onset_checks(self, onset_filtered, error_handler, row_offset):
        issues = []
        for row in onset_filtered[["HED", "original_index"]].itertuples(index=True):
            error_handler.push_error_context(ErrorContext.ROW, row.original_index + row_offset)
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

    def _recheck_duplicates(self, onset_filtered, error_handler, row_offset):
        issues = []
        for i in range(len(onset_filtered) - 1):
            current_row = onset_filtered.iloc[i]
            next_row = onset_filtered.iloc[i + 1]

            # Skip if the HED column is empty or the onsets differ
            if not current_row["HED"] or not self._is_within_tolerance(next_row["onset"], current_row["onset"]):
                continue

            # At least two rows have been merged with their onsets recognized as the same.
            error_handler.push_error_context(ErrorContext.ROW, current_row.original_index + row_offset)
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

    def _check_time_conversions(self, assembled, error_handler, row_offset):
        """Report Delay and Duration tags whose value cannot be converted to default units.

        In a timeline file (one with an onset column) a Delay is added to the row's onset and a Duration gives
        the end time of its group, so both must convert to the default unit of their unit class. A value that
        cannot be converted (non-numeric value, invalid unit, or a unit with no conversionFactor, such as
        'Delay/3 month' or 'Duration/3 year' in HED 8.4.0) is reported as TEMPORAL_TAG_ERROR (spec Appendix B
        cause n). Non-timeline files never reach this check: Duration may use any valid unit there, and Delay
        is banned by OnsetValidator.check_for_banned_tags.

        Unconvertible Delay groups are also removed from the copy of the assembled strings that feeds the onset
        checks, because df_util.split_delay_tags raises HedFileError on them and validation must return issues
        instead. Duration groups are left in place; nothing downstream computes with them. Any invalid unit or
        value in the tag itself was reported by the column stages.

        Parameters:
            assembled (pd.Series): The assembled HED strings, indexed by row.
            error_handler (ErrorHandler): The error handler to use for context.
            row_offset (int): Adjustment to add to the row index for reporting.

        Returns:
            tuple[pd.Series, list]: The assembled strings with unconvertible Delay groups removed (the input
                                    series itself when there were none), and the issues found.
        """
        issues = []
        copied = False
        time_keys = {key.casefold() for key in DefTagNames.DURATION_KEYS}
        for index, value in assembled.items():
            folded = value.casefold()
            if "delay/" not in folded and "duration/" not in folded:
                continue
            hed_obj = HedString(value, self._schema)
            bad_groups = []
            error_handler.push_error_context(ErrorContext.ROW, index + row_offset)
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_obj)
            for group in hed_obj.groups():
                for tag in group.tags():
                    if tag.short_base_tag.casefold() not in time_keys or tag.value_as_default_unit() is not None:
                        continue
                    issues += error_handler.format_error_with_context(
                        TemporalErrors.TEMPORAL_TAG_NO_CONVERSION, tag=tag
                    )
                    if tag.short_base_tag == DefTagNames.DELAY_KEY and group not in bad_groups:
                        bad_groups.append(group)
            error_handler.pop_error_context()
            error_handler.pop_error_context()
            if bad_groups:
                if not copied:
                    assembled = assembled.copy()
                    copied = True
                hed_obj.remove(bad_groups)
                assembled.at[index] = str(hed_obj)
        return assembled, issues

    def _check_onset_nans(self, onsets, assembled, hed_schema, error_handler, row_offset):
        onset_mask = pd.isna(onsets)
        if not onset_mask.any():
            return []
        filtered = assembled[onset_mask]
        issues = []
        for index, value in filtered.items():
            if not bool(self.TEMPORAL_ANCHORS.search(value.casefold())):
                continue
            hed_obj = HedString(value, hed_schema)
            error_handler.push_error_context(ErrorContext.ROW, index + row_offset)
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_obj)
            for tag in hed_obj.find_top_level_tags(
                anchor_tags=DefTagNames.TIMELINE_KEYS, include_groups=TopTagReturnType.TAGS
            ):
                issues += error_handler.format_error_with_context(TemporalErrors.TEMPORAL_TAG_NO_TIME, tag=tag)
            error_handler.pop_error_context()
            error_handler.pop_error_context()
        return issues
