import copy
from hed.errors import ErrorHandler, ErrorContext, SidecarErrors
from hed.models import ColumnType
from hed import HedString
from hed import Sidecar
from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_reporter import sort_issues


class SidecarValidator:
    reserved_column_names = ["HED"]
    reserved_category_values = ["n/a"]

    def __init__(self, hed_schema):
        """
        Constructor for the HedValidator class.

        Parameters:
            hed_schema (HedSchema): HED schema object to use for validation.
        """
        self._schema = hed_schema

    def validate(self, sidecar, extra_def_dicts=None, name=None, error_handler=None):
        """Validate the input data using the schema

        Parameters:
            sidecar (Sidecar): Input data to be validated.
            extra_def_dicts(list or DefinitionDict): extra def dicts in addition to sidecar
            name(str): The name to report this sidecar as
            error_handler (ErrorHandler): Error context to use.  Creates a new one if None
        Returns:
            issues (list of dict): A list of issues associated with each level in the HED string.
        """
        from hed.validator import HedValidator
        issues = []
        if error_handler is None:
            error_handler = ErrorHandler()

        error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        sidecar_def_dict = sidecar.get_def_dict(hed_schema=self._schema, extra_def_dicts=extra_def_dicts)
        hed_validator = HedValidator(self._schema,
                                     def_dicts=sidecar_def_dict,
                                     run_full_onset_checks=False)

        issues += self.validate_structure(sidecar, error_handler=error_handler)
        issues += sidecar._extract_definition_issues
        issues += sidecar_def_dict.issues
        # todo: Add the definition validation.

        for hed_string, column_data, position in sidecar.hed_string_iter(error_handler):
            hed_string_obj = HedString(hed_string, hed_schema=self._schema, def_dict=sidecar_def_dict)

            error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj)
            new_issues = hed_validator.run_basic_checks(hed_string_obj, allow_placeholders=True)
            if not new_issues:
                new_issues = hed_validator.run_full_string_checks(hed_string_obj)
            if not new_issues:
                new_issues = self._validate_pound_sign_count(hed_string_obj, column_type=column_data.column_type)
            error_handler.add_context_and_filter(new_issues)
            issues += new_issues
            error_handler.pop_error_context()

        error_handler.pop_error_context()
        issues = sort_issues(issues)
        return issues

    def validate_structure(self, sidecar, error_handler):
        """ Validate the raw structure of this sidecar.

        Parameters:
            sidecar(Sidecar): the sidecar to validate
            error_handler(ErrorHandler): The error handler to use for error context

        Returns:
            issues(list): A list of issues found with the structure
        """
        all_validation_issues = []
        for column_name, dict_for_entry in sidecar.loaded_dict.items():
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
            all_validation_issues += self._validate_column_structure(column_name, dict_for_entry, error_handler)
            error_handler.pop_error_context()
        return all_validation_issues

    @staticmethod
    def _check_for_key(key, data):
        if isinstance(data, dict):
            if key in data:
                return bool(data[key])
            else:
                for sub_data in data.values():
                    result = SidecarValidator._check_for_key(key, sub_data)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for sub_data in data:
                result = SidecarValidator._check_for_key(key, sub_data)
                if result is not None:
                    return result
        return None

    def _validate_column_structure(self, column_name, dict_for_entry, error_handler):
        """ Checks primarily for type errors such as expecting a string and getting a list in a json sidecar.

        Parameters:
            error_handler (ErrorHandler)  Sets the context for the error reporting. Cannot be None.

        Returns:
            list:  Issues in performing the operations. Each issue is a dictionary.

        """
        val_issues = []
        if column_name in self.reserved_column_names:
            val_issues += error_handler.format_error_with_context(SidecarErrors.SIDECAR_HED_USED_COLUMN)
            return val_issues

        column_type = Sidecar._detect_column_type(dict_for_entry=dict_for_entry)
        if column_type is None:
            val_issues += error_handler.format_error_with_context(SidecarErrors.UNKNOWN_COLUMN_TYPE,
                                                                  column_name=column_name)
        elif column_type == ColumnType.Ignore:
            found_hed = self._check_for_key("HED", dict_for_entry)
            if found_hed:
                val_issues += error_handler.format_error_with_context(SidecarErrors.SIDECAR_HED_USED)
        elif column_type == ColumnType.Categorical:
            raw_hed_dict = dict_for_entry["HED"]
            if not raw_hed_dict:
                val_issues += error_handler.format_error_with_context(SidecarErrors.BLANK_HED_STRING)
            if not isinstance(raw_hed_dict, dict):
                val_issues += error_handler.format_error_with_context(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                                      given_type=type(raw_hed_dict),
                                                                      expected_type="dict")
            for key_name, hed_string in raw_hed_dict.items():
                error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
                if not isinstance(hed_string, str):
                    val_issues += error_handler.format_error_with_context(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                                          given_type=type(hed_string),
                                                                          expected_type="str")
                if not hed_string:
                    val_issues += error_handler.format_error_with_context(SidecarErrors.BLANK_HED_STRING)
                if key_name in self.reserved_category_values:
                    val_issues += error_handler.format_error_with_context(SidecarErrors.SIDECAR_NA_USED, column_name)
                error_handler.pop_error_context()

        return val_issues

    def _validate_pound_sign_count(self, hed_string, column_type):
        """ Check if a given hed string in the column has the correct number of pound signs.

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

        if hed_string_copy.lower().count("#") != expected_count:
            return ErrorHandler.format_error(error_type, pound_sign_count=str(hed_string_copy).count("#"))

        return []
