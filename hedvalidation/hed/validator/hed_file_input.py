import os
import openpyxl

class HedFileInput:
    """Handles parsing the actual on disk hed files to a more general format."""
    TEXT_EXTENSION = ['.tsv', '.txt']
    EXCEL_EXTENSION = ['.xls', '.xlsx']
    FILE_EXTENSION = [*TEXT_EXTENSION, *EXCEL_EXTENSION]
    STRING_INPUT = 'string'
    FILE_INPUT = 'file'
    TAB_DELIMITER = '\t'
    COMMA_DELIMITER = ','

    def __init__(self, filename, worksheet_name=None, tag_columns=None,
                 has_column_names=True, required_tag_columns=None):
        """Constructor for the HedFileInput class.

         Parameters
         ----------
         filename: str
             An xml/tsv file to open.
         worksheet_name: str
             The name of the Excel workbook worksheet that contains the HED tags.  Not applicable to tsv files.
         tag_columns: list
             A list of ints containing the columns that contain the HED tags. The default value is the 2nd column.
         has_column_names: bool
             True if file has column names. The validation will skip over the first line of the file. False, if
             otherwise.
         required_tag_columns: dict
             A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
             prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
             4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/ prepended to them,
             the fourth column contains tags that need Event/Label/ prepended to them, and the fifth column contains tags
             that needs Event/Category/ prepended to them.
         """
        if tag_columns is None:
            tag_columns = [2]
        if required_tag_columns is None:
            required_tag_columns = {}

        self._required_tag_columns = self._subtract_1_from_dictionary_keys(required_tag_columns)
        self._tag_columns = self._convert_tag_columns_to_processing_format(tag_columns, self._required_tag_columns)
        self._filename = filename
        self._worksheet_name = worksheet_name
        self._has_column_names = has_column_names
        self._parse_hed_tags_function = None
        if self.is_spreadsheet_file():
            self._parse_hed_tags_function = self._parse_spreadsheet
        elif self.is_text_file():
            self._parse_hed_tags_function = self._parse_text

    # Make filename read only.
    @property
    def filename(self):
        return self._filename

    def __iter__(self):
        return self._parse_hed_tags_function()

    def _parse_spreadsheet(self):
        worksheet = self._open_workbook_worksheet(self._filename, self._worksheet_name)
        if worksheet:
            for row in worksheet.rows:
                row_number = row[0].row - 1
                if self.row_contains_headers(self._has_column_names, row_number):
                    continue
                row_hed_string, column_to_hed_tags_dictionary = self.get_hed_tags_from_worksheet_row(row)
                yield row_number, row_hed_string, column_to_hed_tags_dictionary

    def _parse_text(self):
        column_delimiter = '\t'

        with open(self._filename, 'r', encoding='utf-8') as opened_text_file:
            for row_number, text_file_row in enumerate(opened_text_file):
                if self.row_contains_headers(self._has_column_names, row_number):
                    continue
                row_hed_string, column_to_hed_tags_dictionary = self.get_hed_string_from_text_file_row(
                    text_file_row, column_delimiter)
                yield row_number, row_hed_string, column_to_hed_tags_dictionary

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
        self._tag_columns = self._remove_tag_columns_greater_than_row_column_count(row_column_count, self._tag_columns)
        return self.get_row_hed_tags(worksheet_row)

    def get_hed_string_from_text_file_row(self, text_file_row, column_delimiter):
        """Reads in the current row of HED tags from the text file. The hed tag columns will be concatenated to form a
           HED string.

        Parameters
        ----------
        text_file_row: str
            The row in the text file that contains the HED tags.
        column_delimiter: str
            A delimiter used to split the columns.
        Returns
        -------
        string
            A HED string containing the concatenated HED tag columns.

        """
        text_file_row = [x.strip() for x in text_file_row.split(column_delimiter)]
        row_column_count = len(text_file_row)
        self._tag_columns = self._remove_tag_columns_greater_than_row_column_count(row_column_count,
                                                                                   self._tag_columns)
        return self.get_row_hed_tags(text_file_row, is_worksheet=False)

    def get_row_hed_tags(self, spreadsheet_row, is_worksheet=True):
        """Reads in the current row of HED tags from a spreadsheet file. The hed tag columns will be concatenated to
           form a HED string.

        Parameters
        ----------
        spreadsheet_row: list
            A list containing the values in the spreadsheet rows.
        is_worksheet: bool
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
                column_hed_tags = self._prepend_prefix_to_required_tag_column_if_needed(
                    column_hed_tags, self._required_tag_columns[hed_tag_column])
            column_to_hed_tags_dictionary[hed_tag_column] = column_hed_tags
        hed_string = ','.join(column_to_hed_tags_dictionary.values())
        return hed_string, column_to_hed_tags_dictionary

    @staticmethod
    def _subtract_1_from_dictionary_keys(int_key_dictionary):
        """Subtracts 1 from each dictionary key.

        Parameters
        ----------
        int_key_dictionary: dict
            A dictionary with int keys.
        Returns
        -------
        dictionary
            A dictionary with the keys subtracted by 1.

        """
        return {key - 1: value for key, value in int_key_dictionary.items()}

    def _convert_tag_columns_to_processing_format(self, tag_columns, required_tag_columns):
        """Converts the tag columns list to a list that allows it to be internally processed. 1 is subtracted from
           each tag column making it 0 based. Then the tag columns are combined with the prefix needed tag columns.

        Parameters
        ----------
        tag_columns: list
            A list of ints containing the columns that contain the HED tags.
        required_tag_columns: todo: add this
            ????
        Returns
        -------
        list
            A list containing the modified list of tag columns that's used for processing.

        """
        tag_columns = self._subtract_1_from_list_elements(tag_columns)
        tag_columns = self._add_required_tag_columns_to_tag_columns(tag_columns, required_tag_columns)
        return tag_columns

    @staticmethod
    def _add_required_tag_columns_to_tag_columns(tag_columns, required_tag_columns):
        """Adds the required tag columns to the tag columns.

         Parameters
         ----------
        tag_columns: list
            A list containing the tag column indices.
         required_tag_columns: dict
            A dictionary containing the required tag columns.
         Returns
         -------
         list
             A list containing the combined required tag columns and the tag columns.

         """
        return tag_columns + list(set(required_tag_columns.keys()) - set(tag_columns))

    @staticmethod
    def _remove_tag_columns_greater_than_row_column_count(row_column_count, hed_tag_columns):
        """Removes the HED tag columns that are greater than the row column count.

        Parameters
        ----------
        row_column_count: int
            The number of columns in the row.
        hed_tag_columns: list
            A list of ints containing the columns that contain the HED tags.
        Returns
        -------
        list
            A list that only contains the HED tag columns that are less than the row column count.

        """
        return sorted(filter(lambda x: x < row_column_count, hed_tag_columns))

    def _prepend_prefix_to_required_tag_column_if_needed(self, required_tag_column_tags, required_tag_prefix):
        """Prepends the tag paths to the required tag column tags that need them.

        Parameters
        ----------
        required_tag_column_tags: str
            A string containing HED tags associated with a required tag column that may need a tag prefix prepended to
            its tags.
        required_tag_prefix: str
            A string that will be added if missing to any given tag.
        Returns
        -------
        string
            A comma separated string that contains the required HED tags with the tag prefix prepended to them if
            needed.

        """
        required_tags_with_prefix = []
        required_tags = required_tag_column_tags.split(',')
        required_tags = [x.strip() for x in required_tags]
        for required_tag in required_tags:
            if required_tag and not required_tag.lower().startswith(required_tag_prefix.lower()):
                required_tag = required_tag_prefix + required_tag
            required_tags_with_prefix.append(required_tag)
        return ','.join(required_tags_with_prefix)

    @staticmethod
    def _subtract_1_from_list_elements(int_list):
        """Subtracts 1 from each int in a list.

        Parameters
        ----------
        int_list: list
            A list of ints.
        Returns
        -------
        list
            A list of containing each element subtracted by 1.

        """
        return [x - 1 for x in int_list]

    @staticmethod
    def row_contains_headers(has_headers, row_number):
        """Checks to see if the row contains headers.

         Parameters
         ----------
        has_headers: bool
            True if file has headers. False, if otherwise.
         row_number: int
            The row number of the spreadsheet.
         Returns
         -------
         bool
             True if the row contains the headers. False, if otherwise.

         """
        return has_headers and row_number == 0

    @staticmethod
    def _is_extension_type(filename, allowed_exts):
        filename, ext = os.path.splitext(filename)
        return ext in allowed_exts

    def is_spreadsheet_file(self):
        return HedFileInput._is_extension_type(self._filename, HedFileInput.EXCEL_EXTENSION)

    def is_text_file(self):
        return HedFileInput._is_extension_type(self._filename, HedFileInput.TEXT_EXTENSION)

    def is_valid_extension(self):
        return self._is_extension_type(self._filename, HedFileInput.FILE_EXTENSION)

    @staticmethod
    def _open_workbook_worksheet(workbook_path, worksheet_name=''):
        """Opens an Excel workbook worksheet.

        Parameters
        ----------
        workbook_path: str
            The path to an Excel workbook.
        worksheet_name: str
            The name of the workbook worksheet that will be opened. The default will be the first worksheet of the
            workbook.
        Returns
        -------
        Sheet object
            A Sheet object representing an Excel workbook worksheet.

        """

        workbook_t = openpyxl.open(workbook_path)
        if not worksheet_name:
            # Return first sheet
            for worksheet in workbook_t:
                return worksheet
        return workbook_t[worksheet_name]
