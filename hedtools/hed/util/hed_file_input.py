import os
import pandas
import openpyxl
from hed.util.hed_event_mapper import EventMapper

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

        self.mapper = EventMapper(tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary)

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
        if not include_column_prefix_if_exist:
            new_text = self.mapper.remove_prefix_if_needed(column_number, new_text)

        if self._dataframe is None:
            raise ValueError("No data frame loaded")

        self._dataframe.iloc[row_number, column_number] = new_text

    def get_row_hed_tags_from_array_like(self, spreadsheet_row):
        """Reads in the current row of HED tags from the Excel file. The hed tag columns will be concatenated to form a
           HED string.

        Parameters
        ----------
        spreadsheet_row: list
            A list containing the values in the worksheet rows.
        Returns
        -------
        string
            A tuple containing a HED string containing the concatenated HED tag columns and a dictionary which
            associates columns with HED tags.

        """
        expanded_row = self.mapper.expand_row_tags(spreadsheet_row)
        return expanded_row["HED"], expanded_row["column_to_hed_tags"]

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
