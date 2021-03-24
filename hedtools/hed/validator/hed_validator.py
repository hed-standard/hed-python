"""
This module contains the HedValidator class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt, .xls, and .xlsx. To get the validation issues after creating a HedValidator class call
the get_validation_issues() function.

"""
from hed.util.error_types import ErrorContext
from hed.util import hed_cache
from hed.util import error_reporter
from hed import schema
from hed.util.hed_string import HedString
from hed.validator.tag_validator import TagValidator
from hed.util.hed_file_input import BaseFileInput


class HedValidator:
    def __init__(self, check_for_warnings=False, run_semantic_validation=True,
                 hed_xml_file='', xml_version_number=None,
                 hed_schema=None, error_handler=None):
        """Constructor for the HedValidator class.

        Parameters
        ----------
        check_for_warnings: bool
            True if the validator should check for warnings. False if the validator should only report errors.
        run_semantic_validation: bool
            True if the validator should check the HED data against a schema. False for syntax-only validation.
        hed_xml_file: str
            A path to a specific hed xml file, or a directory containing a hed xml file.
            Note: An invalid schema here will throw a HedFileError exception.  Use hed_schema to pass an already
            created schema.
        xml_version_number: str
            HED version format string. Expected format: 'X.Y.Z'  Only applies if hed_xml_file is empty,
                or does not point to a specific xml file.
        hed_schema: HedSchema
            Name of already prepared HedSchema to use.  This overrides hed_xml_file and xml_version_number.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        HedValidator object
            A HedValidator object.

        """
        self._tag_validator = None
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()
        self._error_handler = error_handler
        if run_semantic_validation:
            if hed_schema is None:
                self._hed_schema = self._get_hed_schema(hed_xml_file,
                                                        get_specific_version=xml_version_number)
            else:
                self._hed_schema = hed_schema
            self._tag_validator = TagValidator(hed_schema=self._hed_schema,
                                               check_for_warnings=check_for_warnings,
                                               run_semantic_validation=True,
                                               error_handler=self._error_handler)

        # Fall back to syntax validation if we don't have a tag validator at this point
        if self._tag_validator is None:
            self._tag_validator = TagValidator(check_for_warnings=check_for_warnings,
                                               run_semantic_validation=False,
                                               error_handler=self._error_handler)

        self._run_semantic_validation = run_semantic_validation

    def validate_input(self, hed_input, display_filename=None):
        """
            Validates any given hed_input string, file, or list and returns a list of issues.

        Parameters
        ----------
        hed_input: str or list or HedFileInput object
            A list of HED strings, a single HED string, or a HedFileInput object.
            If it is a single string or a list, validate them as hed strings.
        display_filename: str
            If present, will use this as the filename for context, rather than using the actual filename
            Useful for temp filenames.
        Returns
        -------
        validation_issues : [{}]
        """
        is_file = isinstance(hed_input, BaseFileInput)
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

    def get_tag_validator(self):
        """Gets a TagValidator object.

        Parameters
        ----------

        Returns
        -------
        TagValidator object
            A TagValidator object.

        """
        return self._tag_validator

    @staticmethod
    def _get_hed_schema(hed_xml_file, get_specific_version=None):
        """
        Gets a HedSchema object based on the hed xml file specified. If no HED file is specified then the latest
           file will be retrieved.

        Parameters
        ----------
        hed_xml_file: str
            A path to a specific hed xml file, or a directory containing a hed xml file.
        get_specific_version: str
            HED version format string. Expected format: 'X.Y.Z'  Only applies if hed_xml_file is empty,
                or does not point to a specific xml file.
        Returns
        -------
        HedSchema
            A HedSchema object.

        """
        # If we're not asking for a specific file, for ease of use cache the ones from github.
        if hed_xml_file is None and get_specific_version is None:
            hed_cache.cache_all_hed_xml_versions()
        final_hed_xml_file = hed_cache.get_local_file(hed_xml_file, get_specific_version)
        hed_schema = schema.load_schema(final_hed_xml_file)
        return hed_schema

    def _validate_hed_tags_in_file(self, hed_input):
        """

        Parameters
        ----------
        hed_input: HedFileInput object
            A file to validate.  This function does no type checking on this.
        Returns
        -------
        validation_issues : [{}]
        """
        validation_issues = []
        for row_number, row_hed_string, column_to_hed_tags_dictionary in hed_input:
            validation_issues = self._append_validation_issues_if_found(validation_issues, row_number, row_hed_string,
                                                                        column_to_hed_tags_dictionary)
        return validation_issues

    def _append_validation_issues_if_found(self, validation_issues, row_number, row_hed_string,
                                           column_to_hed_tags_dictionary):
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
        validation_issues = self._append_row_validation_issues_if_found(validation_issues, row_number,
                                                                        row_hed_string)
        validation_issues = self._append_column_validation_issues_if_found(validation_issues, row_number,
                                                                           column_to_hed_tags_dictionary)
        return validation_issues

    def _append_row_validation_issues_if_found(self, validation_issues, row_number, row_hed_string):
        """Appends the issues associated with a particular row in a spreadsheet.

         Parameters
         ----------
        validation_issues: str
            A  string that contains all the issues found in the spreadsheet.
        row_number: int
            The row number that the issues are associated with.
        row_hed_string: str
            The HED string associated with a row.
         Returns
         -------
         []
             The issues with the appended issues found in the particular row.

         """
        if row_hed_string:
            self._error_handler.push_error_context(ErrorContext.ROW, row_number)
            self._error_handler.push_error_context(ErrorContext.HED_STRING, row_hed_string, increment_depth_after=False)
            hed_string_delimiter = HedString(row_hed_string)
            row_validation_issues = self._validate_tags_in_hed_string(hed_string_delimiter)
            row_validation_issues += self._validate_tag_levels_in_hed_string(hed_string_delimiter)
            validation_issues += row_validation_issues
            self._error_handler.pop_error_context()
            self._error_handler.pop_error_context()
        return validation_issues

    def _append_column_validation_issues_if_found(self, validation_issues, row_number, column_to_hed_tags_dictionary):
        """Appends the issues associated with a particular row column in a spreadsheet.

         Parameters
         ----------
        validation_issues: str
            A  string that contains all the issues found in the spreadsheet.
        row_number: int
            The row number that the issues are associated with.
        column_to_hed_tags_dictionary: dict
            A dictionary which associates columns with HED tags
         Returns
         -------
         []
             The issues with the appended issues found in the particular row column.

         """
        if column_to_hed_tags_dictionary:
            self._error_handler.push_error_context(ErrorContext.ROW, row_number)
            for column_number in column_to_hed_tags_dictionary.keys():
                self._error_handler.push_error_context(ErrorContext.COLUMN, column_number)
                column_hed_string = column_to_hed_tags_dictionary[column_number]
                self._error_handler.push_error_context(ErrorContext.HED_STRING, column_hed_string,
                                                       increment_depth_after=False)
                validation_issues += self.validate_column_hed_string(column_hed_string)
                self._error_handler.pop_error_context()
                self._error_handler.pop_error_context()
            self._error_handler.pop_error_context()
        return validation_issues

    def validate_column_hed_string(self, column_hed_string):
        """Appends the issues associated with a particular row in a spreadsheet.

         Parameters
         ----------
        column_hed_string: str
            The HED string associated with a row column.
         Returns
         -------
         issues: list
             The issues associated with a particular row column.

         """
        validation_issues = []
        validation_issues += self._tag_validator.run_hed_string_validators(column_hed_string)
        if not validation_issues:
            hed_string_delimiter = HedString(column_hed_string)
            validation_issues += self._validate_individual_tags_in_hed_string(hed_string_delimiter)
            validation_issues += self._validate_groups_in_hed_string(hed_string_delimiter)
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
            self._error_handler.push_error_context(ErrorContext.HED_STRING, hed_string, increment_depth_after=False)
            validation_issues = self._tag_validator.run_hed_string_validators(hed_string)
            if not validation_issues:
                hed_string_delimiter = HedString(hed_string)
                validation_issues += self._validate_tags_in_hed_string(hed_string_delimiter)
                validation_issues += self._validate_tag_levels_in_hed_string(hed_string_delimiter)
                validation_issues += self._validate_individual_tags_in_hed_string(hed_string_delimiter)
                validation_issues += self._validate_groups_in_hed_string(hed_string_delimiter)
            eeg_issues.append(validation_issues)
            self._error_handler.pop_error_context()
        return eeg_issues

    def _validate_tag_levels_in_hed_string(self, hed_string_delimiter):
        """Validates the tags at each level in a HED string. This pertains to the top-level, all groups, and nested
           groups.

         Parameters
         ----------
         hed_string_delimiter: HedString
            A HedString object.
         Returns
         -------
         list
             The issues associated with each level in the HED string.

         """
        validation_issues = []
        tag_groups = hed_string_delimiter.get_all_groups()
        for original_tag_group in tag_groups:
            validation_issues += self._tag_validator.run_tag_level_validators(original_tag_group.tags())

        return validation_issues

    def _validate_tags_in_hed_string(self, hed_string_delimiter):
        """Validates the multi-tag properties in a hed string, eg required tags.

         Parameters
         ----------
         hed_string_delimiter: HedString
            A HedString  object.
         Returns
         -------
         list
             The issues associated with the tags in the HED string.

         """
        validation_issues = []
        tags = hed_string_delimiter.get_all_tags()
        validation_issues += self._tag_validator._run_tag_validators(tags)
        return validation_issues

    def _validate_groups_in_hed_string(self, hed_string_delimiter):
        """Validates the groups in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedString
            A HedString  object.
         Returns
         -------
         list
             The issues associated with the groups in the HED string.

         """
        validation_issues = []
        tag_groups = hed_string_delimiter.get_all_groups()
        for tag_group in tag_groups:
             validation_issues += self._tag_validator.run_tag_group_validators(tag_group)
        return validation_issues

    def _validate_individual_tags_in_hed_string(self, hed_string_delimiter):
        """Validates the individual tags in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedString
            A HedString  object.
         Returns
         -------
         list
             The issues associated with the individual tags in the HED string.

         """
        validation_issues = []
        tags = hed_string_delimiter.get_all_tags()
        previous_tag = None
        for hed_tag in tags:
            validation_issues += \
                self._tag_validator.run_individual_tag_validators(hed_tag,
                                                                  previous_original_tag=previous_tag)
            previous_tag = hed_tag

        return validation_issues