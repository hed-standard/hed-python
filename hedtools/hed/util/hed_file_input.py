import os
import pandas
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
        if self.is_spreadsheet_file():
            if self._worksheet_name is None:
                self._worksheet_name = 0
            self._dataframe = pandas.read_excel(filename, sheet_name=self._worksheet_name)
        elif self.is_text_file():
            self._dataframe = pandas.read_csv(filename, '\t')

    def save(self, filename):
        if self.is_spreadsheet_file():
            # !BFK! - To preserve styling information, we now open this as openpyxl, copy all the data over, then save it.
            old_workbook = openpyxl.load_workbook(self._filename)
            old_worksheet = self.get_worksheet(old_workbook, worksheet_name=self._worksheet_name)
            for row_number, text_file_row in self._dataframe.iterrows():
                for column_number, column_text in enumerate(text_file_row):
                    old_worksheet.cell(row_number + 1, column_number + 1).value = self._dataframe.iloc[row_number, column_number]
            final_filename = filename + ".xlsx"
            old_workbook.save(final_filename)
        elif self.is_text_file():
            final_filename = filename + ".tsv"
            self._dataframe.to_csv(final_filename, '\t', index=False)

    # Make filename read only.
    @property
    def filename(self):
        return self._filename

    def __iter__(self):
        return self.parse_dataframe()

    def parse_dataframe(self):
        for row_number, text_file_row in self._dataframe.iterrows():
            row_column_count = len(text_file_row)
            self._tag_columns = self._remove_tag_columns_greater_than_row_column_count(row_column_count,
                                                                                       self._tag_columns)
            # Skip any blank lines.
            if any(text_file_row.isnull()):
                continue

            row_hed_string, column_to_hed_tags_dictionary = self.get_row_hed_tags_from_array_like(text_file_row)
            yield row_number, row_hed_string, column_to_hed_tags_dictionary

    def set_cell(self, row_number, column_number, new_text, include_column_prefix_if_exist=False):
        """

        Parameters
        ----------
        row_number : int
            The row number of the spreadsheet to set
        column_number : int
            The column number of the spreadsheet to set
        new_text : str
            Text to enter in the given cell
        include_column_prefix_if_exist : bool
            If true and the column matches one from _column_prefix_dictionary, remove the prefix

        Returns
        -------

        """
        if not include_column_prefix_if_exist \
                and self._column_prefix_dictionary \
                and column_number in self._column_prefix_dictionary:
            prefix_to_remove = self._column_prefix_dictionary[column_number]
            if new_text.startswith(prefix_to_remove):
                new_text = new_text[len(prefix_to_remove):]

        if self._dataframe is None:
            raise ValueError("No data frame loaded")

        self._dataframe.iloc[row_number, column_number] = new_text


    def get_row_hed_tags_from_array_like(self, spreadsheet_row):
        column_to_hed_tags_dictionary = {}
        for hed_tag_column in self._tag_columns:
            column_hed_tags = spreadsheet_row[hed_tag_column]
            if not column_hed_tags:
                continue
            elif hed_tag_column in self._column_prefix_dictionary:
                column_hed_tags = self._prepend_prefix_to_required_tag_column_if_needed(
                    column_hed_tags, self._column_prefix_dictionary[hed_tag_column])
            column_to_hed_tags_dictionary[hed_tag_column] = str(column_hed_tags)
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

    @staticmethod
    def get_worksheet(workbook, worksheet_name=None):
        if not worksheet_name:
            return workbook.worksheets[0]
        return workbook.get_sheet_by_name(worksheet_name)
