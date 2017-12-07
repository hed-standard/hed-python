'''
This module contains the HedInputReader class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt, .csv, .xls, and .xlsx. To get the validation issues after creating a HedInputReader class call
the get_validation_issues() function.

Created on Oct 2, 2017

@author: Jeremy Cockfield

'''


import xlrd;
import os;
import error_reporter;
from hed_dictionary import HedDictionary
from tag_validator import TagValidator;
from hed_string_delimiter import HedStringDelimiter;

class HedInputReader:

    TSV_EXTENSION = ['tsv', 'txt'];
    CSV_EXTENSION = ['csv'];
    EXCEL_EXTENSION = ['xls', 'xlsx'];
    FILE_EXTENSION = ['csv', 'tsv', 'txt', 'xls', 'xlsx'];
    TEXT_EXTENSION = ['csv', 'tsv', 'txt'];
    STRING_INPUT = 'string';
    FILE_INPUT = 'file';
    TAB_DELIMITER = '\t';
    COMMA_DELIMITER = ',';
    HED_XML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hed/HED.xml');
    PREFIX_TAG_COLUMN_TO_PATH = {'Attribute': 'Attribute/', 'Category': 'Event/Category/',
                                 'Description': 'Event/Description/', 'Label': 'Event/Label/',
                                 'Long': 'Event/Long name/'};

    def __init__(self, hed_input, tag_columns=[2], has_headers=True, prefixed_needed_tag_columns={}, worksheet_name=''):
        """Constructor for the HedInputReader class.

        Parameters
        ----------
        hed_input: string
            A HED string or a spreadsheet file containing HED tags. If a string is passed in then no other arguments
            need to be specified.
        tag_columns: list
            A list of integers containing the columns that contain the HED tags. The default value is the 2nd column.
        has_headers: boolean
            True if file has headers. False, if otherwise.
        worksheet_name: string
            The name of the Excel workbook worksheet that contains the HED tags.
        prefixed_needed_tag_columns: dictionary
            A dictionary with keys pertaining to the HED tag columns that correspond to tags that need to be prefixed
            with a parent tag path. For example,
            prefixed_needed_tag_columns = {2: 'Long', 3: 'Description', 4: 'Label', 5: 'Category', 7: 'Attribute'};
            The second column contains tags that need Event/Long name/ prepended to them, the third column contains
            tags that need Event/Description/ prepended to them, the fourth column contains tags that need
            Event/Label/ prepended to them, the fifth column contains tags that needs Event/Category/ prepended to
            them, the seventh column contains tags that needs Attribute/ prepended to them.
        Returns
        -------
        HedInputReader object
            A HedInputReader object.

        """
        self._hed_input = hed_input;
        self._prefixed_needed_tag_columns = HedInputReader.subtract_1_from_dictionary_keys(prefixed_needed_tag_columns);
        self._tag_columns = self._convert_tag_columns_to_processing_format(tag_columns);
        self._has_headers = has_headers;
        self._worksheet_name = worksheet_name;
        self._hed_dictionary = HedDictionary(HedInputReader.HED_XML_FILE);
        self._tag_validator = TagValidator(self._hed_dictionary);
        self.validation_issues = self._validate_hed_input();

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
        tag_columns = HedInputReader.subtract_1_from_list_elements(tag_columns);
        tag_columns = HedInputReader.add_prefixed_needed_tag_columns_to_tag_columns(tag_columns,
                                                                                    self._prefixed_needed_tag_columns);
        return tag_columns;


    def _validate_hed_input(self):
        """Validates the HED tags in a string or a file.

         Parameters
         ----------
         Returns
         -------
         string
             The abc issues that were found.

         """
        if HedInputReader.hed_input_has_valid_file_extension(self._hed_input):
            validation_issues = self._validate_hed_tags_in_file();
        else:
            validation_issues = self._validate_hed_string(self._hed_input);
        return validation_issues;

    def _validate_hed_tags_in_file(self):
        """Validates the HED tags in a file.

         Parameters
         ----------
         Returns
         -------
         string
             The abc issues that were found.

         """
        file_extension = HedInputReader.get_file_extension(self._hed_input);
        if HedInputReader.file_is_a_text_file(file_extension):
            column_delimiter = HedInputReader.get_delimiter_from_text_file_extension(file_extension);
            validation_issues = self._validate_hed_tags_in_text_file(column_delimiter);
        else:
            validation_issues = self._validate_hed_tags_in_excel_worksheet();
        return validation_issues;

    def get_validation_issues(self):
        """Gets the abc issues.

         Parameters
         ----------
         Returns
         -------
         string
             The abc issues that were found.

         """
        return self.validation_issues;

    def _validate_hed_tags_in_text_file(self, column_delimiter):
        """Validates the HED tags in a text file.

         Parameters
         ----------
         Returns
         -------
         string
             The abc issues that were found in the text file.

         """
        validation_issues = '';
        with open(self._hed_input) as opened_text_file:
            for text_file_row_number, text_file_row in enumerate(opened_text_file):
                if HedInputReader.row_contains_headers(self._has_headers, text_file_row_number):
                    continue;
                hed_string = HedInputReader.get_hed_string_from_text_file_row(text_file_row, self._tag_columns,
                                                                              column_delimiter,
                                                                              self._prefixed_needed_tag_columns);
                validation_issues = self._append_validation_issues_if_found(validation_issues, text_file_row_number,
                                                                            hed_string);
        return validation_issues;

    def _validate_hed_tags_in_excel_worksheet(self):
        """Validates the HED tags in a excel worksheet.

         Parameters
         ----------
         Returns
         -------
         string
             The abc issues that were found in a excel worksheet.

         """
        validation_issues = '';
        opened_worksheet = HedInputReader.open_workbook_worksheet(self._hed_input, worksheet_name=self._worksheet_name);
        number_of_rows = opened_worksheet.nrows;
        for row_number in xrange(number_of_rows):
            worksheet_row = opened_worksheet.row(row_number);
            if HedInputReader.row_contains_headers(self._has_headers, row_number):
                continue;
            hed_string = HedInputReader.get_hed_string_from_worksheet_row(worksheet_row, self._tag_columns,
                                                                          self._prefixed_needed_tag_columns);
            validation_issues = self._append_validation_issues_if_found(validation_issues, row_number, hed_string);
        return validation_issues;

    def _append_validation_issues_if_found(self, validation_issues, row_number, hed_string):
        """Appends the abc issues associated with a particular row in a spreadsheet.

         Parameters
         ----------
        validation_issues: string
            A abc string that contains all the issues found in the spreadsheet.
         row_number: integer
            The row number that the issues are associated with.
        hed_string: string
            A HED string.
         Returns
         -------
         string
             The abc issues with the appended issues found in the particular row.

         """
        if hed_string:
            row_validation_issues = self._validate_hed_string(hed_string);
            if row_validation_issues:
                validation_issues += HedInputReader.generate_row_issue_message(row_number) + row_validation_issues;
        return validation_issues;

    def _validate_hed_string(self, hed_string):
        """Validates the tags in a HED string.

         Parameters
         ----------
         hed_string: string
            A HED string.
         Returns
         -------
         string
             The abc issues associated with the HED string.

         """
        validation_issues = '';
        hed_string_delimiter = HedStringDelimiter(hed_string);
        validation_issues += self._tag_validator.run_hed_string_validators(hed_string);
        if not validation_issues:
            validation_issues += self._validate_individual_tags_in_hed_string(hed_string_delimiter);
            validation_issues += self._validate_top_levels_in_hed_string(hed_string_delimiter);
            validation_issues += self._validate_tag_levels_in_hed_string(hed_string_delimiter);
            validation_issues += self._validate_groups_in_hed_string(hed_string_delimiter);
        return validation_issues;

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
             The abc issues associated with each level in the HED string.

         """
        validation_issues = '';
        tag_groups = hed_string_delimiter.get_tag_groups();
        formatted_tag_groups = hed_string_delimiter.get_formatted_tag_groups();
        original_and_formatted_tag_groups = zip(tag_groups, formatted_tag_groups);
        for original_tag_group, formatted_tag_group in original_and_formatted_tag_groups:
            validation_issues += self._tag_validator.run_tag_level_validators(original_tag_group, formatted_tag_group);
        top_level_tags = hed_string_delimiter.get_top_level_tags();
        formatted_top_level_tags = hed_string_delimiter.get_formatted_top_level_tags();
        validation_issues += self._tag_validator.run_tag_level_validators(top_level_tags, formatted_top_level_tags);
        return validation_issues;

    def _validate_top_levels_in_hed_string(self, hed_string_delimiter):
        """Validates the top-level tags in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter object
            A HEDStringDelimiter object.
         Returns
         -------
         string
             The abc issues associated with the top-level tags in the HED string.

         """
        validation_issues = '';
        formatted_top_level_tags = hed_string_delimiter.get_formatted_top_level_tags();
        validation_issues += self._tag_validator.run_top_level_validators(formatted_top_level_tags);
        return validation_issues;

    def _validate_groups_in_hed_string(self, hed_string_delimiter):
        """Validates the groups in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter object
            A HEDStringDelimiter object.
         Returns
         -------
         string
             The abc issues associated with the groups in the HED string.

         """
        validation_issues = '';
        tag_groups = hed_string_delimiter.get_tag_groups();
        formatted_tag_groups = hed_string_delimiter.get_formatted_tag_groups();
        original_and_formatted_tag_groups = zip(tag_groups, formatted_tag_groups);
        for original_tag_group, formatted_tag_group in original_and_formatted_tag_groups:
            validation_issues += self._tag_validator.run_tag_group_validators(original_tag_group);
        return validation_issues;

    def _validate_individual_tags_in_hed_string(self, hed_string_delimiter):
        """Validates the individual tags in a HED string.

         Parameters
         ----------
         hed_string_delimiter: HedStringDelimiter object
            A HEDStringDelimiter object.
         Returns
         -------
         string
             The abc issues associated with the individual tags in the HED string.

         """
        validation_issues = '';
        tag_set = hed_string_delimiter.get_tags();
        formatted_tag_set = hed_string_delimiter.get_formatted_tags();
        original_and_formatted_tags = zip(tag_set, formatted_tag_set);
        for original_tag, formatted_tag in original_and_formatted_tags:
            validation_issues += self._tag_validator.run_individual_tag_validators(original_tag, formatted_tag);
        return validation_issues;

    @staticmethod
    def add_prefixed_needed_tag_columns_to_tag_columns(tag_columns, prefixed_needed_tag_columns):
        return tag_columns + list(set(prefixed_needed_tag_columns.keys()) - set(tag_columns));

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
            row_number += 1;
        return error_reporter.report_error_type('row', error_row=row_number);

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
        return file_extension in HedInputReader.TEXT_EXTENSION;

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
        hed_input_has_extension = HedInputReader.file_path_has_extension(hed_input);
        hed_input_file_extension = HedInputReader.get_file_extension(hed_input);
        return hed_input_has_extension and hed_input_file_extension in HedInputReader.FILE_EXTENSION;

    @staticmethod
    def get_delimiter_from_text_file_extension(file_extension):
        """Gets the delimiter that is associated with the file extension.

        Parameters
        ----------
        file_extension: string
            A file extension.
        Returns
        -------
        string
            The delimiter that is associated with the file extension. For example, .txt and .tsv will return tab
            as the delimiter and .csv will return comma as the delimiter.

        """
        delimiter = '';
        if file_extension in HedInputReader.TSV_EXTENSION:
            delimiter = HedInputReader.TAB_DELIMITER;
        elif file_extension in HedInputReader.CSV_EXTENSION:
            delimiter = HedInputReader.COMMA_DELIMITER;
        return delimiter;

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
        workbook = xlrd.open_workbook(workbook_path);
        if not worksheet_name:
            return workbook.sheet_by_index(0);
        return workbook.sheet_by_name(worksheet_name);

    @staticmethod
    def get_hed_string_from_text_file_row(text_file_row, hed_tag_columns, column_delimiter,
                                          prefixed_needed_tag_columns={}):
        """Reads in the current row of HED tags from the text file. The hed tag columns will be concatenated to form a
           HED string.

        Parameters
        ----------
        text_file_row: string
            The row in the text file that contains the HED tags.
        hed_tag_columns: list
            A list of integers containing the columns that contain the HED tags.
        column_delimiter: string
            A delimiter used to split the columns.
        prefixed_needed_tag_columns: dictionary
            A dictionary containing the HED tag column names that corresponds to tags that need to be prefixed with a
            parent tag path.
        Returns
        -------
        string
            A HED string containing the concatenated HED tag columns.

        """
        hed_tags = [];
        split_row_list = HedInputReader.split_delimiter_separated_string_with_quotes(text_file_row, column_delimiter);
        row_column_count = len(split_row_list);
        hed_tag_columns = HedInputReader.remove_tag_columns_greater_than_row_column_count(row_column_count,
                                                                                          hed_tag_columns);
        for hed_tag_column in hed_tag_columns:
            row_hed_tags = split_row_list[hed_tag_column];
            if row_hed_tags:
                if hed_tag_column in prefixed_needed_tag_columns:
                    row_hed_tags = HedInputReader.prepend_path_to_prefixed_needed_tag_column(
                        row_hed_tags, prefixed_needed_tag_columns[hed_tag_column]);
                hed_tags.append(row_hed_tags);
        return ','.join(hed_tags);

    @staticmethod
    def get_hed_string_from_worksheet_row(worksheet_row, hed_tag_columns, prefixed_needed_tag_columns={}):
        """Reads in the current row of HED tags from the text file. The hed tag columns will be concatenated to form a
           HED string.

        Parameters
        ----------
        worksheet_row: list
            A list containing the values in the worksheet rows.
        hed_tag_columns: list
            A list of integers containing the columns that contain the HED tags.
        prefixed_needed_tag_columns: dictionary
            A dictionary containing the HED tag column names that corresponds to tags that need to be prefixed with a
            parent tag path.
        Returns
        -------
        string
            A HED string containing the concatenated HED tag columns.

        """
        hed_tags = [];
        row_column_count = len(worksheet_row);
        hed_tag_columns = HedInputReader.remove_tag_columns_greater_than_row_column_count(row_column_count,
                                                                                          hed_tag_columns);
        for hed_tag_column in hed_tag_columns:
            row_hed_tags = HedInputReader.convert_column_to_unicode_if_not(worksheet_row[hed_tag_column].value);
            if row_hed_tags:
                if hed_tag_column in prefixed_needed_tag_columns:
                    row_hed_tags = HedInputReader.prepend_path_to_prefixed_needed_tag_column(
                        row_hed_tags, prefixed_needed_tag_columns[hed_tag_column]);
                hed_tags.append(row_hed_tags);
        return ','.join(hed_tags);

    @staticmethod
    def convert_column_to_unicode_if_not(column_value):
        """Converts a column value to a unicode string if it is not.

          Parameters
          ----------
          column_value: scalar value
              A scalar column value. This will mostly be a numerical value.
          Returns
          -------
          string
              A unicode string representing the column value.

          """
        if not isinstance(column_value, unicode):
            column_value = unicode(column_value);
        return column_value;


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
        return sorted(filter(lambda x: x < row_column_count, hed_tag_columns));

    @staticmethod
    def prepend_path_to_prefixed_needed_tag_column(hed_tags, prefix_hed_tag_key):
        """Prepends the tag paths to the tag column tags that need them.

        Parameters
        ----------
        hed_tags: string
            A string containing HED tags associated with a particular column that needs a tag prefix prepended to its
            tags.
        prefix_hed_tag_key: string
            A string dictionary key that corresponds to the tag prefix that will be prepended to the column tags.
        Returns
        -------
        string
            A comma separated string that contains the HED tags with the tag prefix prepended to each of them.

        """
        prepended_hed_tags = [];
        split_hed_tags = hed_tags.split(',');
        split_hed_tags = [x.strip() for x in split_hed_tags];
        for hed_tag in split_hed_tags:
            if hed_tag:
                prepended_hed_tag = HedInputReader.PREFIX_TAG_COLUMN_TO_PATH[prefix_hed_tag_key] + hed_tag;
                prepended_hed_tags.append(prepended_hed_tag);
        return ','.join(prepended_hed_tags);

    @staticmethod
    def split_delimiter_separated_string_with_quotes(delimiter_separated_string, delimiter):
        """Splits a comma separated-string.

        Parameters
        ----------
        delimiter_separated_string
            A delimiter separated string.
        delimiter
            A delimiter used to split the string.
        Returns
        -------
        list
            A list containing the individual tags and tag groups in the HED string. Nested tag groups are not split.

        """
        split_string = [];
        number_of_double_quotes = 0;
        current_tag = '';
        for character in delimiter_separated_string:
            if character == HedStringDelimiter.DOUBLE_QUOTE_CHARACTER:
                number_of_double_quotes += 1;
            elif number_of_double_quotes % 2 == 0 and character == delimiter:
                split_string.append(current_tag.strip());
                current_tag = '';
            else:
                current_tag += character;
        split_string.append(current_tag.strip());
        return split_string;

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
        return [x-1 for x in integer_list];

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
        return {key-1: value for key, value in integer_key_dictionary.iteritems()};

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
            return True;
        return False;

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
        return file_path.rsplit('.', 1)[-1].lower();