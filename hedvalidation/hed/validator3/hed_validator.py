"""
This module contains the HedInputReader class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt, .xls, and .xlsx. To get the validation issues after creating a HedInputReader class call
the get_validation_issues() function.

"""


from hed.validator3 import error_reporter
from hed.validator3.hed_dictionary import HedDictionary
from hed.validator3.hed_string_delimiter import HedStringDelimiter
from hed.validator3.tag_validator import TagValidator
from hed.validator3 import hed_cache
from hed.validator3.hed_file_input import HedFileInput

class HedValidator:
    def __init__(self, hed_input, check_for_warnings=False, run_semantic_validation=True,
                 hed_xml_file='', xml_version_number=None,
                 hed_dictionary=None):
        """Constructor for the HedValidator class.

        Parameters
        ----------
        hed_input: str or list or HedFileInput object
            A list of HED strings, a single HED string, or a HedFileInput object.
            If it is a single string or a list, validate them as hed strings.
        check_for_warnings: bool
            True if the validator should check for warnings. False if the validator should only report errors.
        run_semantic_validation: bool
            True if the validator should check the HED data against a schema. False for syntax-only validation.
        hed_xml_file: str
            A path to a specific hed xml file, or a directory containing a hed xml file.
        xml_version_number: str
            HED version format string. Expected format: 'X.Y.Z'  Only applies if hed_xml_file is empty,
                or does not point to a specific xml file.
        hed_dictionary: HedDictionary
            Name of already prepared HedDictionary to use.  This overrides hed_xml_url_or_file
        Returns
        -------
        HedValidator object
            A HedValidator object.

        """
        if isinstance(hed_input, HedFileInput):
            self._is_file = True
        self._hed_input = hed_input
        if run_semantic_validation:
            if hed_dictionary is None:
                self._hed_dictionary = self._get_hed_dictionary(hed_xml_file,
                                                                get_specific_version=xml_version_number)
            else:
                self._hed_dictionary = hed_dictionary
            self._tag_validator = TagValidator(hed_dictionary=self._hed_dictionary,
                                               check_for_warnings=check_for_warnings,
                                               run_semantic_validation=True)
        else:
            self._tag_validator = TagValidator(check_for_warnings=check_for_warnings,
                                               run_semantic_validation=False)

        self._validation_issues = self._validate_hed_input()
        self._run_semantic_validation = run_semantic_validation

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
    def _get_hed_dictionary(hed_xml_file, get_specific_version=None):
        """Gets a HEDDictionary object based on the hed xml file specified. If no HED file is specified then the latest
           file will be retrieved.

        Parameters
        ----------
        hed_xml_file: str
            A path to a specific hed xml file, or a directory containing a hed xml file.
        xml_version_number: str
            HED version format string. Expected format: 'X.Y.Z'  Only applies if hed_xml_file is empty,
                or does not point to a specific xml file.
        Returns
        -------
        HedDictionary object
            A HedDictionary object.

        """
        final_hed_xml_file = hed_cache.get_local_file(hed_xml_file, get_specific_version)
        hed_dictionary = HedDictionary(final_hed_xml_file)
        return hed_dictionary

    def _validate_hed_input(self):
        """Validates the HED tags in a string or a file.

         Parameters
         ----------
         Returns
         -------
         list
             The issues that were found.
        """
        if isinstance(self._hed_input, list):
            validation_issues = self._validate_hed_strings(self._hed_input)
        elif self._is_file:
            if self._hed_input and self._hed_input.is_valid_extension():
                validation_issues = self._validate_hed_tags_in_file()
            else:
                validation_issues = error_reporter.report_error_type('invalidFileName', file_name=self._hed_input.filename)
        else:
            validation_issues = self._validate_hed_strings([self._hed_input])[0]
        return validation_issues

    def _validate_hed_tags_in_file(self):
        validation_issues = []

        for row_number, row_hed_string, column_to_hed_tags_dictionary in self._hed_input:
            validation_issues = self._append_validation_issues_if_found(validation_issues, row_number, row_hed_string,
                                                                        column_to_hed_tags_dictionary)

        return validation_issues

    def get_validation_issues(self):
        """Gets the issues.

         Parameters
         ----------
         Returns
         -------
         list
             The issues that were found.

         """
        return self._validation_issues

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
         list
             The issues with the appended issues found in the particular row.

         """
        if row_hed_string:
            hed_string_delimiter = HedStringDelimiter(row_hed_string)
            row_validation_issues = self._validate_top_level_in_hed_string(hed_string_delimiter)
            row_validation_issues += self._validate_tag_levels_in_hed_string(hed_string_delimiter)
            if row_validation_issues:
                validation_issues += HedValidator.generate_row_issue_message(row_number) + row_validation_issues
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
         list
             The issues with the appended issues found in the particular row column.

         """
        if column_to_hed_tags_dictionary:
            for column_number in column_to_hed_tags_dictionary.keys():
                column_hed_string = column_to_hed_tags_dictionary[column_number]
                column_validation_issues = self.validate_column_hed_string(column_hed_string)
                if column_validation_issues:
                    validation_issues += HedValidator.generate_column_issue_message(row_number, column_number) + \
                                         column_validation_issues
        return validation_issues

    def validate_column_hed_string(self, column_hed_string):
        """Appends the issues associated with a particular row in a spreadsheet.

         Parameters
         ----------
        column_hed_string: str
            The HED string associated with a row column.
         Returns
         -------
         list
             The issues associated with a particular row column.

         """
        validation_issues = []
        validation_issues += self._tag_validator.run_hed_string_validators(column_hed_string)
        if not validation_issues:
            hed_string_delimiter = HedStringDelimiter(column_hed_string)
            validation_issues += self._validate_individual_tags_in_hed_string(hed_string_delimiter)
            validation_issues += self._validate_groups_in_hed_string(hed_string_delimiter)
        return validation_issues

    def _validate_hed_strings(self, hed_strings):
        """Validates the tags in an array of HED strings

         Parameters
         ----------
         hed_strings: list of str
            An array of HED strings.
         Returns
         -------
         list
             The issues associated with the HED strings.

         """
        eeg_issues = []
        for i in range(0, len(hed_strings)):
            hed_string = hed_strings[i]
            validation_issues = self._tag_validator.run_hed_string_validators(hed_string)
            if not validation_issues:
                hed_string_delimiter = HedStringDelimiter(hed_string)
                validation_issues += self._validate_top_level_in_hed_string(hed_string_delimiter)
                validation_issues += self._validate_tag_levels_in_hed_string(hed_string_delimiter)
                validation_issues += self._validate_individual_tags_in_hed_string(hed_string_delimiter)
                validation_issues += self._validate_groups_in_hed_string(hed_string_delimiter)
            eeg_issues.append(validation_issues)
        return eeg_issues

    def _validate_tag_levels_in_hed_string(self, hed_string_delimiter):
        """Validates the tags at each level in a HED string. This pertains to the top-level, all groups, and nested
           groups.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter
            A HEDStringDelimiter object.
         Returns
         -------
         list
             The issues associated with each level in the HED string.

         """
        validation_issues = []
        tag_groups = hed_string_delimiter.get_tag_groups()
        formatted_tag_groups = hed_string_delimiter.get_formatted_tag_groups()
        original_and_formatted_tag_groups = zip(tag_groups, formatted_tag_groups)
        for original_tag_group, formatted_tag_group in original_and_formatted_tag_groups:
            validation_issues += self._tag_validator.run_tag_level_validators(original_tag_group, formatted_tag_group)
        top_level_tags = hed_string_delimiter.get_top_level_tags()
        formatted_top_level_tags = hed_string_delimiter.get_formatted_top_level_tags()
        validation_issues += self._tag_validator.run_tag_level_validators(top_level_tags, formatted_top_level_tags)
        return validation_issues

    def _validate_top_level_in_hed_string(self, hed_string_delimiter):
        """Validates the top-level tags in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter
            A HEDStringDelimiter object.
         Returns
         -------
         list
             The issues associated with the top-level tags in the HED string.

         """
        validation_issues = []
        formatted_top_level_tags = hed_string_delimiter.get_formatted_top_level_tags()
        validation_issues += self._tag_validator.run_top_level_validators(formatted_top_level_tags)
        return validation_issues

    def _validate_groups_in_hed_string(self, hed_string_delimiter):
        """Validates the groups in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter
            A HEDStringDelimiter object.
         Returns
         -------
         list
             The issues associated with the groups in the HED string.

         """
        validation_issues = []
        tag_groups = hed_string_delimiter.get_tag_groups()
        tag_group_strings = hed_string_delimiter.get_tag_group_strings()
        tag_groups_with_strings = zip(tag_groups, tag_group_strings)
        for tag_group, tag_group_string in tag_groups_with_strings:
            validation_issues += self._tag_validator.run_tag_group_validators(tag_group, tag_group_string)
        return validation_issues

    def _validate_individual_tags_in_hed_string(self, hed_string_delimiter):
        """Validates the individual tags in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter
            A HEDStringDelimiter object.
         Returns
         -------
         list
             The issues associated with the individual tags in the HED string.

         """
        validation_issues = []
        tag_set = hed_string_delimiter.get_tags()
        formatted_tag_set = hed_string_delimiter.get_formatted_tags()
        original_and_formatted_tags = list(zip(tag_set, formatted_tag_set))
        for index, (original_tag, formatted_tag) in enumerate(original_and_formatted_tags):
            previous_original_tag, previous_formatted_tag = HedValidator.get_previous_original_and_formatted_tag(
                original_and_formatted_tags, index)
            validation_issues += \
                self._tag_validator.run_individual_tag_validators(original_tag, formatted_tag,
                                                                  previous_original_tag=previous_original_tag,
                                                                  previous_formatted_tag=previous_formatted_tag)
        return validation_issues

    def get_printable_issue_string(self, title=''):
        """Return a string with identifying title and issues in string form one per line.

          Parameters
          ----------
         title: str
             String used as a title for the issues.

          Returns
          -------
          str
              A str containing printable version of the issues or '[]'.

          """

        if not self._validation_issues:
            issue_string = "\t[]\n"
        else:
            issue_string = "\n"
            for el in self._validation_issues:
                issue_string = issue_string + "\t" + el["code"] + el["message"]
        if title:
            issue_string = title + ":" + issue_string
        return issue_string

    @staticmethod
    def get_previous_original_and_formatted_tag(original_and_formatted_tags, loop_index):
        """Retrieves the previous original and formatted tag from a list of tuples.

         Parameters
         ----------
        original_and_formatted_tags: list
            A list of tuples containing the original and formatted tags.
        loop_index: int
            The current index in the loop.
         Returns
         -------
         tuple
             A tuple containing the previous original and formatted tag.

         """
        previous_original_tag = ''
        previous_formatted_tag = ''
        if loop_index > 0:
            previous_original_tag = original_and_formatted_tags[loop_index - 1][0]
            previous_formatted_tag = original_and_formatted_tags[loop_index - 1][1]
        return previous_original_tag, previous_formatted_tag

    @staticmethod
    def generate_row_issue_message(row_number, has_headers=True):
        """Generates a row issue message that is associated with a particular row in a spreadsheet.

         Parameters
         ----------
         row_number: int
            The row number that the issue is associated with.
         has_headers: bool
            If true, adjusts the row number to account for one line header.
         Returns
         -------
         list
             A singleton list containing the row issue message.

         """
        if has_headers:
            row_number += 1
        return error_reporter.report_error_type('row', error_row=row_number)

    @staticmethod
    def generate_column_issue_message(row_number, column_number, has_headers=True):
        """Generates a column issue message that is associated with a particular column in a spreadsheet.

         Parameters
         ----------
         row_number: int
            The row number that the issue is associated with.
         column_number: int
            The column number that the issue is associated with.
         has_headers: bool
            If true, adjusts row number to account for one line header.

         Returns
         -------
         list
             A singleton list containing the column issue message.

         """
        if has_headers:
            row_number += 1
        column_number += 1
        return error_reporter.report_error_type('column', error_row=row_number, error_column=column_number)
