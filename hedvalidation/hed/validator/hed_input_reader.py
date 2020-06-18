"""
This module contains the HedInputReader class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt, .xls, and .xlsx. To get the validation issues after creating a HedInputReader class call
the get_validation_issues() function.

"""

import os
import re
import xlrd
from hed.validator import error_reporter
from hed.validator.hed_dictionary import HedDictionary
from hed.validator.hed_string_delimiter import HedStringDelimiter
from hed.validator.tag_validator import TagValidator
from distutils.version import StrictVersion


class HedInputReader:
    TSV_EXTENSION = ['tsv', 'txt']
    EXCEL_EXTENSION = ['xls', 'xlsx']
    FILE_EXTENSION = ['tsv', 'txt', 'xls', 'xlsx']
    TEXT_EXTENSION = ['tsv', 'txt']
    STRING_INPUT = 'string'
    FILE_INPUT = 'file'
    TAB_DELIMITER = '\t'
    COMMA_DELIMITER = ','
    HED_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hed/')
    DEFAULT_HED_XML_FILE = os.path.join(HED_DIRECTORY, 'HEDLatest.xml')
    REQUIRED_TAG_COLUMN_TO_PATH = {'Category': 'Event/Category/', 'Description': 'Event/Description/',
                                   'Label': 'Event/Label/', 'Long': 'Event/Long name/'}
    HED_VERSION_EXPRESSION = r'HED(\d+.\d+.\d+)'
    HED_XML_PREFIX = 'HED'
    HED_XML_EXTENSION = '.xml'

    def __init__(self, hed_input, is_file=True, check_for_warnings=False, run_semantic_validation=True, hed_xml_file='',
                 tag_columns=[2], has_column_names=True, required_tag_columns={}, worksheet_name=''):
        """Constructor for the HedInputReader class.

        Parameters
        ----------
        hed_input: str or list
            A list of HED strings, a single HED string, or the name of a spreadsheet file containing HED tags.
            If is_file is True and hed_input is a string, this tries to parse hed_input as a file name.
            If is_file is False or hed_input is not a valid file name, this will validate hed_input as a HED string.
        is_file: bool
            True if hed_input represents a file name. False if it represents a HED string.
        check_for_warnings: bool
            True if the validator should check for warnings. False if the validator should only report errors.
        run_semantic_validation: bool
            True if the validator should check the HED data against a schema. False for syntax-only validation.
        hed_xml_file: str
            A path to a HED XML file.
        tag_columns: list
            A list of integers containing the columns that contain the HED tags. The default value is the 2nd column.
        has_column_names: bool
            True if file has column names. The validation will skip over the first line of the file. False, if
            otherwise.
        required_tag_columns: dict
            A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
            prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Description',
            4: 'Label', 5: 'Category'}; The third column contains tags that need Event/Description/ prepended to them,
            the fourth column contains tags that need Event/Label/ prepended to them, and the fifth column contains tags
            that needs Event/Category/ prepended to them.
        worksheet_name: str
            The name of the Excel workbook worksheet that contains the HED tags.
        Returns
        -------
        HedInputReader object
            A HedInputReader object.

        """
        self._hed_input = hed_input
        self._required_tag_columns = HedInputReader.subtract_1_from_dictionary_keys(required_tag_columns)
        self._tag_columns = self._convert_tag_columns_to_processing_format(tag_columns)
        self._has_column_names = has_column_names
        self._worksheet_name = worksheet_name
        self._is_file = is_file
        if run_semantic_validation:
            self._hed_dictionary = self._get_hed_dictionary(hed_xml_file)
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

    def _get_hed_dictionary(self, hed_xml_file):
        """Gets a HEDDictionary object based on the hed xml file specified. If no HED file is specified then the latest
           file will be retrieved.

        Parameters
        ----------
        hed_xml_file: string
            A path to a HED XML file.
        Returns
        -------
        HedDictionary object
            A HedDictionary object.

        """
        if not hed_xml_file:
            hed_xml_file = HedInputReader.get_latest_hed_version_path()
        return HedDictionary(hed_xml_file)

    def _convert_tag_columns_to_processing_format(self, tag_columns):
        """Converts the tag columns list to a list that allows it to be internally processed. 1 is subtracted from
           each tag column making it 0 based. Then the tag columns are combined with the prefix needed tag columns.

        Parameters
        ----------
        tag_columns: list
            A list of integers containing the columns that contain the HED tags.
        Returns
        -------
        list
            A list containing the modified list of tag columns that's used for processing.

        """
        tag_columns = HedInputReader.subtract_1_from_list_elements(tag_columns)
        tag_columns = HedInputReader.add_required_tag_columns_to_tag_columns(tag_columns,
                                                                             self._required_tag_columns)
        return tag_columns

    def _validate_hed_input(self):
        """Validates the HED tags in a string or a file.

         Parameters
         ----------
         Returns
         -------
         string
             The issues that were found.
        """
        validation_issues = ''
        if isinstance(self._hed_input, list):
            validation_issues = self._validate_hed_strings(self._hed_input)
        elif self._is_file and HedInputReader.hed_input_has_valid_file_extension(self._hed_input):
            validation_issues = self._validate_hed_tags_in_file()
        else:
            validation_issues = self._validate_hed_strings([self._hed_input])
        return validation_issues

    def _validate_hed_tags_in_file(self):
        """Validates the HED tags in a file.

         Parameters
         ----------
         Returns
         -------
         string
             The issues that were found.

         """
        file_extension = HedInputReader.get_file_extension(self._hed_input)
        if HedInputReader.file_is_a_text_file(file_extension):
            validation_issues = self._validate_hed_tags_in_text_file(HedInputReader.TAB_DELIMITER)
        else:
            validation_issues = self._validate_hed_tags_in_excel_worksheet()
        return validation_issues

    def get_validation_issues(self):
        """Gets the issues.

         Parameters
         ----------
         Returns
         -------
         string
             The issues that were found.

         """
        return self._validation_issues

    def _validate_hed_tags_in_text_file(self, column_delimiter):
        """Validates the HED tags in a text file.

         Parameters
         ----------
         Returns
         -------
         string
             The issues that were found in the text file.

         """
        validation_issues = ''
        with open(self._hed_input, 'r', encoding='utf-8') as opened_text_file:
            for row_number, text_file_row in enumerate(opened_text_file):
                if HedInputReader.row_contains_headers(self._has_column_names, row_number):
                    continue
                row_hed_string, column_to_hed_tags_dictionary = self.get_hed_string_from_text_file_row(
                    text_file_row, column_delimiter)
                validation_issues = self._append_validation_issues_if_found(validation_issues, row_number,
                                                                            row_hed_string,
                                                                            column_to_hed_tags_dictionary)
        return validation_issues

    def _validate_hed_tags_in_excel_worksheet(self):
        """Validates the HED tags in a excel worksheet.

         Parameters
         ----------
         Returns
         -------
         string
             The issues that were found in a excel worksheet.

         """
        validation_issues = ''
        opened_worksheet = HedInputReader.open_workbook_worksheet(self._hed_input, worksheet_name=self._worksheet_name)
        number_of_rows = opened_worksheet.nrows
        for row_number in range(number_of_rows):
            worksheet_row = opened_worksheet.row(row_number)
            if HedInputReader.row_contains_headers(self._has_column_names, row_number):
                continue
            row_hed_string, column_to_hed_tags_dictionary = self.get_hed_tags_from_worksheet_row(worksheet_row)
            validation_issues = self._append_validation_issues_if_found(validation_issues, row_number, row_hed_string,
                                                                        column_to_hed_tags_dictionary)
        return validation_issues

    def _append_validation_issues_if_found(self, validation_issues, row_number, row_hed_string,
                                           column_to_hed_tags_dictionary):
        """Appends the issues associated with a particular row and/or column in a spreadsheet.

         Parameters
         ----------
        validation_issues: string
            A  string that contains all the issues found in the spreadsheet.
        row_number: integer
            The row number that the issues are associated with.
        row_hed_string: string
            The HED string associated with a row.
        column_to_hed_tags_dictionary
            A dictionary which associates columns with HED tags
         Returns
         -------
         string
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
        validation_issues: string
            A  string that contains all the issues found in the spreadsheet.
        row_number: integer
            The row number that the issues are associated with.
        row_hed_string: string
            The HED string associated with a row.
         Returns
         -------
         string
             The issues with the appended issues found in the particular row.

         """
        if row_hed_string:
            hed_string_delimiter = HedStringDelimiter(row_hed_string)
            row_validation_issues = self._validate_top_level_in_hed_string(hed_string_delimiter)
            row_validation_issues += self._validate_tag_levels_in_hed_string(hed_string_delimiter)
            if row_validation_issues:
                validation_issues += HedInputReader.generate_row_issue_message(row_number) + row_validation_issues
        return validation_issues

    def _append_column_validation_issues_if_found(self, validation_issues, row_number, column_to_hed_tags_dictionary):
        """Appends the issues associated with a particular row column in a spreadsheet.

         Parameters
         ----------
        validation_issues: string
            A  string that contains all the issues found in the spreadsheet.
        row_number: integer
            The row number that the issues are associated with.
        column_to_hed_tags_dictionary
            A dictionary which associates columns with HED tags
         Returns
         -------
         string
             The issues with the appended issues found in the particular row column.

         """
        if column_to_hed_tags_dictionary:
            for column_number in column_to_hed_tags_dictionary.keys():
                column_hed_string = column_to_hed_tags_dictionary[column_number]
                column_validation_issues = self.validate_column_hed_string(column_hed_string)
                if column_validation_issues:
                    validation_issues += HedInputReader.generate_column_issue_message(row_number, column_number) + \
                                         column_validation_issues
        return validation_issues

    def validate_column_hed_string(self, column_hed_string):
        """Appends the issues associated with a particular row in a spreadsheet.

         Parameters
         ----------
        column_hed_string: string
            The HED string associated with a row column.
         Returns
         -------
         string
             The issues associated with a particular row column.

         """
        validation_issues = ''
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
         hed_string: string array
            An array of HED string.
         Returns
         -------
         string
             The issues associated with the HED strings

         """
        eeg_issues = []
        for i in range(0, len(hed_strings)):
            hed_string = hed_strings[i]
            validation_issues = self._tag_validator.run_hed_string_validators(hed_string);
            if not validation_issues:
                hed_string_delimiter = HedStringDelimiter(hed_string);
                validation_issues += self._validate_top_level_in_hed_string(hed_string_delimiter);
                validation_issues += self._validate_tag_levels_in_hed_string(hed_string_delimiter);
                validation_issues += self._validate_individual_tags_in_hed_string(hed_string_delimiter);
                validation_issues += self._validate_groups_in_hed_string(hed_string_delimiter);
            if validation_issues:
                validation_issues = "Issue in event " + str(i+1) + ":\n" + validation_issues
                eeg_issues.append(validation_issues)
        return eeg_issues;

    def _validate_tag_levels_in_hed_string(self, hed_string_delimiter):
        """Validates the tags at each level in a HED string. This pertains to the top-level, all groups, and nested
           groups.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter object
            A HEDStringDelimiter object.
         Returns
         -------
         string
             The issues associated with each level in the HED string.

         """
        validation_issues = ''
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
         hed_string_delimiter: HedStringDelimiter object
            A HEDStringDelimiter object.
         Returns
         -------
         string
             The issues associated with the top-level tags in the HED string.

         """
        validation_issues = ''
        formatted_top_level_tags = hed_string_delimiter.get_formatted_top_level_tags()
        validation_issues += self._tag_validator.run_top_level_validators(formatted_top_level_tags)
        return validation_issues

    def _validate_groups_in_hed_string(self, hed_string_delimiter):
        """Validates the groups in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter object
            A HEDStringDelimiter object.
         Returns
         -------
         string
             The issues associated with the groups in the HED string.

         """
        validation_issues = ''
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
         hed_string_delimiter: HedStringDelimiter object
            A HEDStringDelimiter object.
         Returns
         -------
         string
             The issues associated with the individual tags in the HED string.

         """
        validation_issues = ''
        tag_set = hed_string_delimiter.get_tags()
        formatted_tag_set = hed_string_delimiter.get_formatted_tags()
        original_and_formatted_tags = list(zip(tag_set, formatted_tag_set))
        for index, (original_tag, formatted_tag) in enumerate(original_and_formatted_tags):
            previous_original_tag, previous_formatted_tag = HedInputReader.get_previous_original_and_formatted_tag(
                original_and_formatted_tags, index)
            validation_issues += \
                self._tag_validator.run_individual_tag_validators(original_tag, formatted_tag,
                                                                  previous_original_tag=previous_original_tag,
                                                                  previous_formatted_tag=previous_formatted_tag)
        return validation_issues

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
    def add_required_tag_columns_to_tag_columns(tag_columns, required_tag_columns):
        """Adds the required tag columns to the tag columns.

         Parameters
         ----------
        tag_columns: list
            A list containing the tag column indices.
         required_tag_columns: dictionary
            A dictionary containing the required tag columns.
         Returns
         -------
         list
             A list containing the combined required tag columns and the tag columns.

         """
        return tag_columns + list(set(required_tag_columns.keys()) - set(tag_columns))

    @staticmethod
    def row_contains_headers(has_headers, row_number):
        """Checks to see if the row contains headers.

         Parameters
         ----------
        has_headers: boolean
            True if file has headers. False, if otherwise.
         row_number: integer
            The row number of the spreadsheet.
         Returns
         -------
         boolean
             True if the row contains the headers. False, if otherwise.

         """
        return has_headers and row_number == 0

    @staticmethod
    def generate_row_issue_message(row_number, has_headers=True):
        """Generates a row issue message that is associated with a particular row in a spreadsheet.

         Parameters
         ----------
         row_number: integer
            The row number that the issue is associated with.
         Returns
         -------
         string
             The row issue message.

         """
        if has_headers:
            row_number += 1
        return error_reporter.report_error_type('row', error_row=row_number)

    @staticmethod
    def generate_column_issue_message(row_number, column_number, has_headers=True):
        """Generates a column issue message that is associated with a particular column in a spreadsheet.

         Parameters
         ----------
         row_number: integer
            The row number that the issue is associated with.
         column_number: integer
            The column number that the issue is associated with.
         Returns
         -------
         string
             The column issue message.

         """
        if has_headers:
            row_number += 1
        column_number += 1
        return error_reporter.report_error_type('column', error_row=row_number, error_column=column_number)

    @staticmethod
    def file_is_a_text_file(file_extension):
        """Checks to see if the file extension provided is one that corresponds to a text file.

         Parameters
         ----------
         file_extension: string
            A file extension.
         Returns
         -------
         boolean
             True if the file is a text file. False, if otherwise.

         """
        return file_extension in HedInputReader.TEXT_EXTENSION

    @staticmethod
    def hed_input_has_valid_file_extension(hed_input):
        """Checks to see if the hed input has a valid file extension.

        Parameters
        ----------
        Returns
        -------
        boolean
            True if the hed input has a valid file extension. False, if otherwise.

        """
        hed_input_has_extension = HedInputReader.file_path_has_extension(hed_input)
        hed_input_file_extension = HedInputReader.get_file_extension(hed_input)
        return hed_input_has_extension and hed_input_file_extension in HedInputReader.FILE_EXTENSION

    @staticmethod
    def open_workbook_worksheet(workbook_path, worksheet_name=''):
        """Opens an Excel workbook worksheet.

        Parameters
        ----------
        workbook_path: string
            The path to an Excel workbook.
        worksheet_name: string
            The name of the workbook worksheet that will be opened. The default will be the first worksheet of the
            workbook.
        Returns
        -------
        Sheet object
            A Sheet object representing an Excel workbook worksheet.

        """
        workbook = xlrd.open_workbook(workbook_path)
        if not worksheet_name:
            return workbook.sheet_by_index(0)
        return workbook.sheet_by_name(worksheet_name)

    def get_hed_string_from_text_file_row(self, text_file_row, column_delimiter):
        """Reads in the current row of HED tags from the text file. The hed tag columns will be concatenated to form a
           HED string.

        Parameters
        ----------
        text_file_row: string
            The row in the text file that contains the HED tags.
        column_delimiter: string
            A delimiter used to split the columns.
        Returns
        -------
        string
            A HED string containing the concatenated HED tag columns.

        """
        text_file_row = [x.strip() for x in text_file_row.split(column_delimiter)]
        row_column_count = len(text_file_row)
        self._tag_columns = HedInputReader.remove_tag_columns_greater_than_row_column_count(row_column_count,
                                                                                            self._tag_columns)
        return self.get_row_hed_tags(text_file_row, is_worksheet=False)

    def get_hed_tags_from_worksheet_row(self, worksheet_row):
        """Reads in the current row of HED tags from the Excel file. The hed tag columns will be concatenated to form a
           HED string.

        Parameters
        ----------
        worksheet_row: list
            A list containing the values in the worksheet rows.
        Returns
        -------
        string
            A tuple containing a HED string containing the concatenated HED tag columns and a dictionary which
            associates columns with HED tags.

        """
        row_column_count = len(worksheet_row)
        self._tag_columns = HedInputReader.remove_tag_columns_greater_than_row_column_count(row_column_count,
                                                                                            self._tag_columns)
        return self.get_row_hed_tags(worksheet_row)

    def get_row_hed_tags(self, spreadsheet_row, is_worksheet=True):
        """Reads in the current row of HED tags from a spreadsheet file. The hed tag columns will be concatenated to
           form a HED string.

        Parameters
        ----------
        spreadsheet_row: list
            A list containing the values in the spreadsheet rows.
        is_worksheet: boolean
            True if the spreadsheet is an Excel worksheet. False if it is a text file.
        Returns
        -------
        string
            A tuple containing a HED string containing the concatenated HED tag columns and a dictionary which
            associates columns with HED tags.

        """
        column_to_hed_tags_dictionary = {}
        for hed_tag_column in self._tag_columns:
            if is_worksheet:
                column_hed_tags = spreadsheet_row[hed_tag_column].value
            else:
                column_hed_tags = spreadsheet_row[hed_tag_column]
            if not column_hed_tags:
                continue
            elif hed_tag_column in self._required_tag_columns:
                column_hed_tags = self.prepend_prefix_to_required_tag_column_if_needed(
                    column_hed_tags, self._required_tag_columns[hed_tag_column])
            column_to_hed_tags_dictionary[hed_tag_column] = column_hed_tags
        hed_string = ','.join(column_to_hed_tags_dictionary.values())
        return hed_string, column_to_hed_tags_dictionary

    @staticmethod
    def remove_tag_columns_greater_than_row_column_count(row_column_count, hed_tag_columns):
        """Removes the HED tag columns that are greater than the row column count.

        Parameters
        ----------
        row_column_count: integer
            The number of columns in the row.
        hed_tag_columns: list
            A list of integers containing the columns that contain the HED tags.
        Returns
        -------
        list
            A list that only contains the HED tag columns that are less than the row column count.

        """
        return sorted(filter(lambda x: x < row_column_count, hed_tag_columns))

    def prepend_prefix_to_required_tag_column_if_needed(self, required_tag_column_tags, required_tag_prefix_key):
        """Prepends the tag paths to the required tag column tags that need them.

        Parameters
        ----------
        required_tag_column_tags: string
            A string containing HED tags associated with a required tag column that may need a tag prefix prepended to
            its tags.
        required_tag_prefix_key: string
            A string dictionary key that corresponds to the required tag prefix that may be prepended to the tags in a
            required tag column if needed.
        Returns
        -------
        string
            A comma separated string that contains the required HED tags with the tag prefix prepended to them if
            needed.

        """
        required_tag_prefix = HedInputReader.REQUIRED_TAG_COLUMN_TO_PATH[required_tag_prefix_key]
        if not self._tag_validator.tag_has_unique_prefix(required_tag_prefix):
            required_tags_with_prefix = []
            required_tags = required_tag_column_tags.split(',')
            required_tags = [x.strip() for x in required_tags]
            for required_tag in required_tags:
                if required_tag and not required_tag.lower().startswith(required_tag_prefix.lower()):
                    required_tag = required_tag_prefix + required_tag
                required_tags_with_prefix.append(required_tag)
            return ','.join(required_tags_with_prefix)
			
        if required_tag_prefix and not required_tag_column_tags.lower().startswith(required_tag_prefix.lower()):
            required_tag_column_tags = required_tag_prefix + required_tag_column_tags

        return required_tag_column_tags

    @staticmethod
    def subtract_1_from_list_elements(integer_list):
        """Subtracts 1 from each integer in a list.

        Parameters
        ----------
        integer_list: list
            A list of integers.
        Returns
        -------
        list
            A list of containing each element subtracted by 1.

        """
        return [x - 1 for x in integer_list]

    @staticmethod
    def subtract_1_from_dictionary_keys(integer_key_dictionary):
        """Subtracts 1 from each dictionary key.

        Parameters
        ----------
        integer_key_dictionary: dictionary
            A dictionary with integer keys.
        Returns
        -------
        dictionary
            A dictionary with the keys subtracted by 1.

        """
        return {key - 1: value for key, value in integer_key_dictionary.items()}

    @staticmethod
    def file_path_has_extension(file_path):
        """Checks to see if file path has an extension.

        Parameters
        ----------
        file_path: string
             A file path.
        Returns
        -------
        boolean
            Returns True if the file path has an extension. False, if otherwise.

        """
        if len(file_path.rsplit('.', 1)) > 1:
            return True
        return False

    @staticmethod
    def get_file_extension(file_path):
        """Reads the next row of HED tags from the text file.

        Parameters
        ----------
        file_path: string
             A file path.
        Returns
        -------
        string
            The extension of the file path.

        """
        return file_path.rsplit('.', 1)[-1].lower()

    @staticmethod
    def get_latest_hed_version_path():
        """Get the latest HED XML file path in the hed directory.

        Parameters
        ----------
        Returns
        -------
        string
            The path to the latest HED version the hed directory.

        """

        hed_versions = HedInputReader.get_all_hed_versions()
        latest_hed_version = HedInputReader.get_latest_semantic_version_in_list(hed_versions)
        return os.path.join(HedInputReader.HED_DIRECTORY,
                            HedInputReader.HED_XML_PREFIX + latest_hed_version + HedInputReader.HED_XML_EXTENSION)

    @staticmethod
    def get_path_from_hed_version(hed_version):
        """Gets the HED XML file path in the hed directory that corresponds to the hed version specified.

        Parameters
        ----------
        hed_version: string
             The HED version that is in the hed directory.
        Returns
        -------
        string
            The HED XML file path in the hed directory that corresponds to the hed version specified.

        """
        return os.path.join(HedInputReader.HED_DIRECTORY,
                            HedInputReader.HED_XML_PREFIX + hed_version + HedInputReader.HED_XML_EXTENSION)

    @staticmethod
    def get_all_hed_versions():
        """Get all the HED versions in the hed directory.

        Parameters
        ----------
        Returns
        -------
        string
            The path to the latest HED version the hed directory.

        """

        hed_versions = []
        compiled_expression = re.compile(HedInputReader.HED_VERSION_EXPRESSION)
        for _, _, hed_files in os.walk(HedInputReader.HED_DIRECTORY):
            for hed_file in hed_files:
                expression_match = compiled_expression.match(hed_file)
                if expression_match is not None:
                    hed_versions.append(expression_match.group(1))
        return sorted(hed_versions, key=StrictVersion, reverse=True)

    @staticmethod
    def get_latest_semantic_version_in_list(semantic_version_list):
        """Gets the latest semantic version in a list.

        Parameters
        ----------
        semantic_version_list: list
             A list containing semantic versions.
        Returns
        -------
        string
            The latest semantic version in the list.

        """
        if not semantic_version_list:
            return ''
        latest_semantic_version = semantic_version_list[0]
        if len(semantic_version_list) > 1:
            for semantic_version in semantic_version_list[1:]:
                latest_semantic_version = HedInputReader.compare_semantic_versions(latest_semantic_version,
                                                                                   semantic_version)
        return latest_semantic_version

    @staticmethod
    def compare_semantic_versions(first_semantic_version, second_semantic_version):
        """Compares two semantic versions.

        Parameters
        ----------
        first_semantic_version: string
             The first semantic version.
        second_semantic_version: string
             The second semantic version.
        Returns
        -------
        string
            The later semantic version.

        """
        return first_semantic_version if StrictVersion(first_semantic_version) > StrictVersion(
            second_semantic_version) else second_semantic_version
