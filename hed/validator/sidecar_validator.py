""" Validates sidecars. """
from __future__ import annotations
import copy
import re
import itertools

from hed.errors import ErrorHandler, ErrorContext, SidecarErrors, DefinitionErrors, ColumnErrors
from hed.models.column_mapper import ColumnType
from hed.models.hed_string import HedString
from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_reporter import sort_issues
from hed.models.model_constants import DefTagNames
from hed.errors.error_reporter import check_for_any_errors
from hed.models import df_util


# todo: Add/improve validation for definitions being in known columns(right now it just assumes they aren't)
class SidecarValidator:
    reserved_column_names = ["HED"]
    reserved_category_values = ["n/a"]

    def __init__(self, hed_schema):
        """
        Constructor for the SidecarValidator class.

        Parameters:
            hed_schema (HedSchema): HED schema object to use for validation.
        """
        self._schema = hed_schema

    def validate(self, sidecar, extra_def_dicts=None, name=None, error_handler=None) -> list[dict]:
        """Validate the input data using the schema

        Parameters:
            sidecar (Sidecar): Input data to be validated.
            extra_def_dicts (list or DefinitionDict): extra def dicts in addition to sidecar
            name (str): The name to report this sidecar as
            error_handler (ErrorHandler): Error context to use.  Creates a new one if None.

        Returns:
            list[dict]: A list of issues associated with each level in the HED string.
        """
        from hed.validator import HedValidator
        issues = []
        if error_handler is None:
            error_handler = ErrorHandler()

        error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        issues += self.validate_structure(sidecar, error_handler=error_handler)
        issues += self._validate_refs(sidecar, error_handler)

        # only allowed early out, something is very wrong with structure or refs
        if check_for_any_errors(issues):
            error_handler.pop_error_context()
            return issues
        sidecar_def_dict = sidecar.get_def_dict(hed_schema=self._schema, extra_def_dicts=extra_def_dicts)
        hed_validator = HedValidator(self._schema, def_dicts=sidecar_def_dict,  definitions_allowed=True)

        issues += sidecar._extract_definition_issues
        issues += sidecar_def_dict.issues

        # todo: Break this function up
        all_ref_columns = sidecar.get_column_refs()
        definition_checks = {}
        for column_data in sidecar:
            column_name = column_data.column_name
            column_data = column_data._get_unvalidated_data()
            hed_strings = column_data.get_hed_strings()
            is_ref_column = column_name in all_ref_columns
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
            for key_name, hed_string in hed_strings.items():
                new_issues = []
                if len(hed_strings) > 1:
                    error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
                hed_string_obj = HedString(hed_string, hed_schema=self._schema, def_dict=sidecar_def_dict)
                hed_string_obj.remove_refs()

                error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj)
                new_issues += hed_validator.run_basic_checks(hed_string_obj, allow_placeholders=True)
                def_check_list = definition_checks.setdefault(column_name, [])
                def_check_list.append(hed_string_obj.find_tags({DefTagNames.DEFINITION_KEY}, recursive=True,
                                                               include_groups=0))

                # Might refine this later - for now just skip checking placeholder counts in definition columns.
                if not def_check_list[-1]:
                    new_issues += self._validate_pound_sign_count(hed_string_obj, column_type=column_data.column_type)

                error_handler.add_context_and_filter(new_issues)
                issues += new_issues
                error_handler.pop_error_context()  # Hed String

                # Only do full string checks on full columns, not partial ref columns.
                if not is_ref_column:
                    # TODO: Figure out why this pattern is giving lint errors.
                    refs = re.findall(r"\{([a-z_\-0-9]+)\}", hed_string, re.IGNORECASE)
                    refs_strings = {data.column_name: data.get_hed_strings() for data in sidecar}
                    if "HED" not in refs_strings:
                        refs_strings["HED"] = ["n/a"]
                    for combination in itertools.product(*[refs_strings[key] for key in refs]):
                        new_issues = []
                        ref_dict = dict(zip(refs, combination))
                        modified_string = hed_string
                        for ref in refs:
                            modified_string = df_util.replace_ref(modified_string, f"{{{ref}}}", ref_dict[ref])
                        hed_string_obj = HedString(modified_string, hed_schema=self._schema, def_dict=sidecar_def_dict)

                        error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj)
                        new_issues += hed_validator.run_full_string_checks(hed_string_obj)
                        error_handler.add_context_and_filter(new_issues)
                        issues += new_issues
                        error_handler.pop_error_context()  # Hed string
                if len(hed_strings) > 1:
                    error_handler.pop_error_context()  # Category key

            error_handler.pop_error_context()  # Column Name
        issues += self._check_definitions_bad_spot(definition_checks, error_handler)
        issues = sort_issues(issues)

        error_handler.pop_error_context()  # Filename

        return issues

    def validate_structure(self, sidecar, error_handler) -> list[dict]:
        """ Validate the raw structure of this sidecar.

        Parameters:
            sidecar (Sidecar): the sidecar to validate
            error_handler (ErrorHandler): The error handler to use for error context.

        Returns:
            list[dict]: A list of issues found with the structure.
        """
        all_validation_issues = []
        for column_name, dict_for_entry in sidecar.loaded_dict.items():
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
            all_validation_issues += self._validate_column_structure(column_name, dict_for_entry, error_handler)
            error_handler.pop_error_context()
        return all_validation_issues

    def _validate_refs(self, sidecar, error_handler):
        possible_column_refs = sidecar.all_hed_columns

        if "HED" not in possible_column_refs:
            possible_column_refs.append("HED")

        issues = []
        found_column_references = {}
        for column_data in sidecar:
            column_name = column_data.column_name
            if column_data.column_type == ColumnType.Ignore:
                continue
            hed_strings = column_data.get_hed_strings()
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
            matches = []
            for key_name, hed_string in hed_strings.items():
                new_issues = []
                if len(hed_strings) > 1:
                    error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)

                error_handler.push_error_context(ErrorContext.HED_STRING,
                                                 HedString(hed_string, hed_schema=self._schema))
                invalid_locations = self._find_non_matching_braces(hed_string)
                for loc in invalid_locations:
                    bad_symbol = hed_string[loc]
                    new_issues += error_handler.format_error_with_context(ColumnErrors.MALFORMED_COLUMN_REF,
                                                                          column_name, loc, bad_symbol)

                sub_matches = re.findall(r"\{([a-z_\-0-9]+)\}", hed_string, re.IGNORECASE)
                matches.append(sub_matches)
                for match in sub_matches:
                    if match not in possible_column_refs:
                        new_issues += error_handler.format_error_with_context(ColumnErrors.INVALID_COLUMN_REF, match)

                error_handler.pop_error_context()
                if len(hed_strings) > 1:
                    error_handler.pop_error_context()
                error_handler.add_context_and_filter(new_issues)
                issues += new_issues
            error_handler.pop_error_context()
            references = [match for sublist in matches for match in sublist]
            if references:
                found_column_references[column_name] = references
            if column_name in references:
                issues += error_handler.format_error_with_context(ColumnErrors.SELF_COLUMN_REF, column_name)

        for column_name, refs in found_column_references.items():
            for ref in refs:
                if ref in found_column_references and ref != column_name:
                    issues += error_handler.format_error_with_context(ColumnErrors.NESTED_COLUMN_REF, column_name, ref)
        return issues

    @staticmethod
    def _find_non_matching_braces(hed_string):
        issues = []
        open_brace_index = -1

        for i, char in enumerate(hed_string):
            if char == '{':
                if open_brace_index >= 0:  # Nested brace detected
                    issues.append(open_brace_index)
                open_brace_index = i
            elif char == '}':
                if open_brace_index >= 0:
                    open_brace_index = -1
                else:
                    issues.append(i)

        if open_brace_index >= 0:
            issues.append(open_brace_index)

        return issues

    @staticmethod
    def _check_for_key(key, data):
        # Probably can be cleaned up more -> Return True if any data or subdata is key
        if isinstance(data, dict):
            return SidecarValidator._check_dict(key, data)
        elif isinstance(data, list):
            return SidecarValidator._check_list(key, data)
        return False

    @staticmethod
    def _check_dict(key, data_dict):
        if key in data_dict:
            return True
        for sub_data in data_dict.values():
            if SidecarValidator._check_for_key(key, sub_data):
                return True
        return False

    @staticmethod
    def _check_list(key, data_list):
        for sub_data in data_list:
            if SidecarValidator._check_for_key(key, sub_data):
                return True
        return False

    def _validate_column_structure(self, column_name, dict_for_entry, error_handler):
        """ Checks primarily for type errors such as expecting a string and getting a list in a json sidecar.

        Parameters:
            error_handler (ErrorHandler)  Sets the context for the error reporting. Cannot be None.

        Returns:
            list:  Issues in performing the operations. Each issue is a dictionary.

        """
        val_issues = []
        if column_name in self.reserved_column_names:
            val_issues += error_handler.format_error_with_context(SidecarErrors.SIDECAR_HED_USED)
            return val_issues

        column_type = ColumnMetadata._detect_column_type(dict_for_entry=dict_for_entry, basic_validation=False)
        if column_type is None:
            val_issues += error_handler.format_error_with_context(SidecarErrors.UNKNOWN_COLUMN_TYPE,
                                                                  column_name=column_name)
        elif column_type == ColumnType.Ignore:
            found_hed = self._check_for_key("HED", dict_for_entry)
            if found_hed:
                val_issues += error_handler.format_error_with_context(SidecarErrors.SIDECAR_HED_USED)
        elif column_type == ColumnType.Categorical:
            val_issues += self._validate_categorical_column(column_name, dict_for_entry, error_handler)

        return val_issues

    def _validate_categorical_column(self, column_name, dict_for_entry, error_handler):
        """Validates a categorical column in a json sidecar."""
        val_issues = []
        raw_hed_dict = dict_for_entry["HED"]
        if not raw_hed_dict:
            val_issues += error_handler.format_error_with_context(SidecarErrors.BLANK_HED_STRING)
        for key_name, hed_string in raw_hed_dict.items():
            error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
            if not hed_string:
                val_issues += error_handler.format_error_with_context(SidecarErrors.BLANK_HED_STRING)
            elif not isinstance(hed_string, str):
                val_issues += error_handler.format_error_with_context(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                                      given_type=type(hed_string),
                                                                      expected_type="str")
            elif key_name in self.reserved_category_values:
                val_issues += error_handler.format_error_with_context(SidecarErrors.SIDECAR_NA_USED, column_name)
            error_handler.pop_error_context()
        return val_issues

    def _validate_pound_sign_count(self, hed_string, column_type):
        """ Check if a given HED string in the column has the correct number of pound signs.

        Parameters:
            hed_string (str or HedString): HED string to be checked.

        Returns:
            list: Issues due to pound sign errors. Each issue is a dictionary.

        Notes:
            Normally the number of # should be either 0 or 1, but sometimes will be higher due to the
            presence of definition tags.

        """
        # Make a copy without definitions to check placeholder count.
        expected_count, error_type = ColumnMetadata.expected_pound_sign_count(column_type)
        hed_string_copy = copy.deepcopy(hed_string)
        hed_string_copy.remove_definitions()
        hed_string_copy.shrink_defs()

        if str(hed_string_copy).count("#") != expected_count:
            return ErrorHandler.format_error(error_type, pound_sign_count=str(hed_string_copy).count("#"))

        return []

    def _check_definitions_bad_spot(self, definition_checks, error_handler):
        issues = []
        # This could be simplified now
        for col_name, has_def in definition_checks.items():
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, col_name)
            def_check = set(bool(d) for d in has_def)
            if len(def_check) != 1:
                flat_def_list = [d for defs in has_def for d in defs]
                for d in flat_def_list:
                    issues += error_handler.format_error_with_context(DefinitionErrors.BAD_DEFINITION_LOCATION, d)
            error_handler.pop_error_context()

        return issues
