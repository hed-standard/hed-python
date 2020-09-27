import os
import xlrd
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
                 has_column_names=True, column_prefix_dictionary=None):
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
         column_prefix_dictionary: dict
             A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
             prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
             4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/ prepended to them,
             the fourth column contains tags that need Event/Label/ prepended to them, and the fifth column contains tags
             that needs Event/Category/ prepended to them.
         """
        if tag_columns is None:
            tag_columns = [2]
        if column_prefix_dictionary is None:
            column_prefix_dictionary = {}

        self._column_prefix_dictionary = self._subtract_1_from_dictionary_keys(column_prefix_dictionary)
        self._tag_columns = self._convert_tag_columns_to_processing_format(tag_columns, self._column_prefix_dictionary)
        self._filename = filename
        self._worksheet_name = worksheet_name
        self._has_column_names = has_column_names
        self._parse_hed_tags_function = None
        self._text_file = None
        self._workbook = None
        self._worksheet = None
        if self.is_spreadsheet_file():
            self._parse_hed_tags_function = self._parse_spreadsheet
            self._workbook = self._open_workbook(self._filename)
            self._worksheet = self.get_worksheet(self._worksheet_name)
        elif self.is_text_file():
            self._parse_hed_tags_function = self._parse_text
            self._text_file = self._open_text_file(self._filename)

    def save(self, filename):
        if self._workbook:
            final_filename = filename + ".xlsx"
            self._workbook.save(final_filename)
        elif self._text_file:
            final_filename = filename + ".tsv"
            with open(final_filename, 'w') as f:
                for text_file_row in self._text_file:
                    row_to_write = self.TAB_DELIMITER.join(text_file_row)
                    f.write(row_to_write)
                    f.write('\n')

    # Make filename read only.
    @property
    def filename(self):
        return self._filename

    def __iter__(self):
        return self._parse_hed_tags_function()

    def _parse_spreadsheet(self):
        if self._worksheet is None:
            return
        if self._worksheet:
            for row_number, row in enumerate(self._worksheet.rows):
                if self.row_contains_headers(self._has_column_names, row_number):
                    continue
                row_hed_string, column_to_hed_tags_dictionary = self.get_hed_tags_from_worksheet_row(row)
                yield row_number, row_hed_string, column_to_hed_tags_dictionary

    def _parse_text(self):
        for row_number, text_file_row in enumerate(self._text_file):
            if self.row_contains_headers(self._has_column_names, row_number):
                continue
            row_hed_string, column_to_hed_tags_dictionary = self.get_hed_string_from_text_file_row(text_file_row)
            yield row_number, row_hed_string, column_to_hed_tags_dictionary

    def set_cell(self, row_number, column_number, new_text):
        if self._workbook:
            # Cells are 1 based rather than 0 based, so add 1
            self._worksheet.cell(row_number + 1, column_number + 1).value = new_text
        elif self._text_file:
            text_file_row = self._text_file[row_number]
            text_file_row[column_number] = new_text


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

    def get_hed_string_from_text_file_row(self, text_file_row):
        """Reads in the current row of HED tags from the text file. The hed tag columns will be concatenated to form a
           HED string.

        Parameters
        ----------
        text_file_row: str
            A list containing strings for the row.
        Returns
        -------
        string
            A HED string containing the concatenated HED tag columns.

        """
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
            elif hed_tag_column in self._column_prefix_dictionary:
                column_hed_tags = self._prepend_prefix_to_required_tag_column_if_needed(
                    column_hed_tags, self._column_prefix_dictionary[hed_tag_column])
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

    def _convert_tag_columns_to_processing_format(self, tag_columns, column_prefix_dictionary):
        """Converts the tag columns list to a list that allows it to be internally processed. 1 is subtracted from
           each tag column making it 0 based. Then the tag columns are combined with the prefix needed tag columns.

        Parameters
        ----------
        tag_columns: list
            A list of ints containing the columns that contain the HED tags.
        column_prefix_dictionary:
            A dict where keys are column numbers, and values are the prefix to append to tags
                in that column if not present
        Returns
        -------
        list
            A list containing the modified list of tag columns that's used for processing.

        """
        tag_columns = self._subtract_1_from_list_elements(tag_columns)
        tag_columns = self._add_required_tag_columns_to_tag_columns(tag_columns, column_prefix_dictionary)
        return tag_columns

    @staticmethod
    def _add_required_tag_columns_to_tag_columns(tag_columns, column_prefix_dictionary):
        """Adds the required tag columns to the tag columns.

         Parameters
         ----------
        tag_columns: list
            A list containing the tag column indices.
         column_prefix_dictionary: dict
            A dictionary containing the required tag columns.
         Returns
         -------
         list
             A list containing the combined required tag columns and the tag columns.

         """
        return tag_columns + list(set(column_prefix_dictionary.keys()) - set(tag_columns))

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

    def get_worksheet(self, worksheet_name=None):
        if not worksheet_name:
            return self._workbook.worksheets[0]
        return self._workbook.get_sheet_by_name(worksheet_name)

    @staticmethod
    def _open_workbook(workbook_path):
        return openpyxl.load_workbook(workbook_path)

    @staticmethod
    def _open_text_file(textfile_path):
        column_delimiter = HedFileInput.TAB_DELIMITER
        text_file = []
        with open(textfile_path, 'r', encoding='utf-8') as opened_text_file:
            for text_file_row in opened_text_file:
                text_file_row = [x.strip() for x in text_file_row.split(column_delimiter)]
                text_file.append(text_file_row)

        return text_file