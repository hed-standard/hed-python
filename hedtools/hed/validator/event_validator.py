"""
This module contains the EventValidator class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt, .xls, and .xlsx. To get the validation issues after creating a EventValidator class call
the get_validation_issues() function.

"""
from hed.errors.error_types import ErrorContext
from hed.errors import error_reporter

from hed.models.hed_string import HedString
from hed.validator.tag_validator import TagValidator
from hed.models.hed_input import BaseInput
from hed.models import model_constants


class EventValidator:
    def __init__(self, check_for_warnings=False, run_semantic_validation=True,
                 hed_schema=None, allow_numbers_to_be_pound_sign=False, error_handler=None):
        """Constructor for the EventValidator class.

        Parameters
        ----------
        check_for_warnings: bool
            True if the validator should check for warnings. False if the validator should only report errors.
        run_semantic_validation: bool
            True if the validator should check the HED data against a schema. False for syntax-only validation.
        hed_schema: HedSchema
            HedSchema object to use to use for validation
        allow_numbers_to_be_pound_sign: bool
            If true, considers # equal to a number for validation purposes.  This is so it can validate templates.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        EventValidator object
            A EventValidator object.

        """
        self._tag_validator = None
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()
        self._error_handler = error_handler
        self._hed_schema = hed_schema
        if run_semantic_validation:
            self._tag_validator = TagValidator(hed_schema=self._hed_schema,
                                               check_for_warnings=check_for_warnings,
                                               run_semantic_validation=True,
                                               allow_numbers_to_be_pound_sign=allow_numbers_to_be_pound_sign,
                                               error_handler=self._error_handler)

        # Fall back to syntax validation if we don't have a tag validator at this point
        if self._tag_validator is None:
            self._tag_validator = TagValidator(check_for_warnings=check_for_warnings,
                                               run_semantic_validation=False,
                                               allow_numbers_to_be_pound_sign=allow_numbers_to_be_pound_sign,
                                               error_handler=self._error_handler)

        self._run_semantic_validation = run_semantic_validation

    def validate_input(self, hed_input, display_filename=None):
        """
            Validates any given hed_input string, file, or list and returns a list of issues.

        Parameters
        ----------
        hed_input: str or list or HedInput object
            A list of HED strings, a single HED string, or a HedInput object.
            If it is a single string or a list, validate them as hed strings.
        display_filename: str
            If present, will use this as the filename for context, rather than using the actual filename
            Useful for temp filenames.
        Returns
        -------
        validation_issues : [{}]
        """
        is_file = isinstance(hed_input, BaseInput)
        if not display_filename and is_file:
            display_filename = hed_input.filename

        if isinstance(hed_input, list):
            validation_issues = self._validate_hed_strings(hed_input)
        elif is_file:
            self._error_handler.push_error_context(ErrorContext.FILE_NAME, display_filename)
            validation_issues = self._validate_hed_tags_in_file(hed_input)
        else:
            validation_issues = self._validate_hed_strings([hed_input])[0]

        if is_file:
            # If we have a custom title and found no issues, we need to still print the title.
            self._error_handler.pop_error_context()
        return validation_issues

    def _validate_hed_strings(self, hed_strings):
        """Validates the tags in an array of HED strings

         Parameters
         ----------
         hed_strings: [str]
            An array of HED strings.
         Returns
         -------
         []
             The issues associated with the HED strings.

         """
        eeg_issues = []
        for i in range(0, len(hed_strings)):
            hed_string = hed_strings[i]
            hed_string_obj = HedString(hed_string)
            self._error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj, increment_depth_after=False)
            validation_issues = self._tag_validator.run_hed_string_validators(hed_string_obj)
            if not validation_issues:
                validation_issues += hed_string_obj.convert_to_canonical_forms(self._hed_schema, self._error_handler)
                if not validation_issues:
                    validation_issues += self._validate_tags_in_hed_string(hed_string_obj)
                    validation_issues += self._validate_groups_in_hed_string(hed_string_obj)
                    validation_issues += self._validate_individual_tags_in_hed_string(hed_string_obj)
            eeg_issues.append(validation_issues)
            self._error_handler.pop_error_context()
        return eeg_issues

    def _validate_hed_tags_in_file(self, hed_input):
        """

        Parameters
        ----------
        hed_input: HedInput object
            A file to validate.  This function does no type checking on this.
        Returns
        -------
        validation_issues : [{}]
        """
        validation_issues = []
        validation_issues += hed_input.file_def_dict_issues
        for row_number, row_dict in hed_input.iter_dataframe(return_row_dict=True):
            validation_issues = self._append_validation_issues_if_found(validation_issues, row_number, row_dict)
        return validation_issues

    def _append_validation_issues_if_found(self, validation_issues, row_number, row_dict):
        """Appends the issues associated with a particular row and/or column in a spreadsheet.

         Parameters
         ----------
        validation_issues: str
            A  string that contains all the issues found in the spreadsheet.
        row_number: int
            The row number that the issues are associated with.
        row_hed_string: str
            The HED string associated with a row.
        column_to_hed_tags_dictionary: dict
            A dictionary which associates columns with HED tags
         Returns
         -------
         list
             The issues with the appended issues found in the particular row.

         """
        row_hed_string = row_dict[model_constants.ROW_HED_STRING]
        column_to_hed_tags_dictionary = row_dict[model_constants.COLUMN_TO_HED_TAGS]
        expansion_column_issues = row_dict.get(model_constants.COLUMN_ISSUES, {})
        self._append_row_validation_issues_if_found(validation_issues, row_number, column_to_hed_tags_dictionary,
                                                    row_hed_string, expansion_column_issues)
        return validation_issues

    def _append_row_validation_issues_if_found(self, validation_issues, row_number, column_to_hed_tags_dictionary,
                                               row_hed_string, expansion_issues):
        """Appends the issues associated with a particular row column in a spreadsheet.

         Parameters
         ----------
        validation_issues: str
            A  string that contains all the issues found in the spreadsheet.
        row_number: int
            The row number that the issues are associated with.
        column_to_hed_tags_dictionary: dict
            A dictionary which associates columns with HED tags
        row_hed_string: str
            The HED string associated with a row.
        expansion_issues: {int: {}}
            A dict containing an issue expanding a column that should be added as an error.
            This is primarily a missing category key in a json file.
         Returns
         -------
         []
             The issues with the appended issues found in the particular row column.
         """
        if column_to_hed_tags_dictionary:
            self._error_handler.push_error_context(ErrorContext.ROW, row_number)
            column_failed = False
            for column_number in column_to_hed_tags_dictionary:
                new_column_issues = []
                self._error_handler.push_error_context(ErrorContext.COLUMN, column_number)
                if column_number in expansion_issues:
                    column_issues = expansion_issues[column_number]
                    for issue in column_issues:
                        new_column_issues += self._error_handler.format_error(**issue)
                column_hed_string = column_to_hed_tags_dictionary[column_number]
                self._error_handler.push_error_context(ErrorContext.HED_STRING, column_hed_string,
                                                       increment_depth_after=False)
                new_column_issues += self._tag_validator.run_hed_string_validators(column_hed_string)
                if not new_column_issues:
                    new_column_issues += column_hed_string.convert_to_canonical_forms(self._hed_schema,
                                                                                     self._error_handler)

                if not new_column_issues:
                    new_column_issues += self._validate_individual_tags_in_hed_string(column_hed_string)
                else:
                    column_failed = True

                self._error_handler.pop_error_context()
                self._error_handler.pop_error_context()
                validation_issues += new_column_issues

            if not column_failed:
                self._error_handler.push_error_context(ErrorContext.HED_STRING, row_hed_string,
                                                       increment_depth_after=False)
                row_validation_issues = self._validate_tags_in_hed_string(row_hed_string)
                row_validation_issues += self._validate_groups_in_hed_string(row_hed_string)
                validation_issues += row_validation_issues
                self._error_handler.pop_error_context()
            self._error_handler.pop_error_context()
        return validation_issues

    def _validate_groups_in_hed_string(self, hed_string_obj):
        """Validates the tags at each level in a HED string. This pertains to the top-level, all groups, and nested
           groups.

         Parameters
         ----------
         hed_string_obj: HedString
            A HedString object.
         Returns
         -------
         list
             The issues associated with each level in the HED string.

         """
        validation_issues = []
        for original_tag_group, is_top_level in hed_string_obj.get_all_groups(also_return_depth=True):
            is_group = original_tag_group.is_group()
            validation_issues += self._tag_validator.run_tag_level_validators(original_tag_group.tags(), is_top_level,
                                                                              is_group)

        return validation_issues

    def _validate_tags_in_hed_string(self, hed_string_obj):
        """Validates the multi-tag properties in a hed string, eg required tags.

         Parameters
         ----------
         hed_string_obj: HedString
            A HedString  object.
         Returns
         -------
         list
             The issues associated with the tags in the HED string.

         """
        validation_issues = []
        tags = hed_string_obj.get_all_tags()
        validation_issues += self._tag_validator.run_all_tags_validators(tags)
        return validation_issues

    def _validate_individual_tags_in_hed_string(self, hed_string_obj):
        """Validates the individual tags in a HED string.

         Parameters
         ----------
         hed_string_obj: HedString
            A HedString  object.
         Returns
         -------
         list
             The issues associated with the individual tags in the HED string.

         """
        validation_issues = []
        tags = hed_string_obj.get_all_tags()
        for hed_tag in tags:
            validation_issues += \
                self._tag_validator.run_individual_tag_validators(hed_tag)

        return validation_issues
