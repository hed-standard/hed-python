import os
import openpyxl
import pandas
from hed.util.hed_event_mapper import EventMapper

class BaseFileInput:
    """Handles parsing the actual on disk hed files to a more general format."""
    TEXT_EXTENSION = ['.tsv', '.txt']
    EXCEL_EXTENSION = ['.xls', '.xlsx']
    FILE_EXTENSION = [*TEXT_EXTENSION, *EXCEL_EXTENSION]
    STRING_INPUT = 'string'
    FILE_INPUT = 'file'
    TAB_DELIMITER = '\t'
    COMMA_DELIMITER = ','

    def __init__(self, filename, worksheet_name=None, has_column_names=True, mapper=None):
        """Constructor for the BaseFileInput class.

         Parameters
         ----------
         filename: str
             An xml/tsv file to open.
         worksheet_name: str
             The name of the Excel workbook worksheet that contains the HED tags.  Not applicable to tsv files.
         has_column_names: bool
             True if file has column names. The validation will skip over the first line of the file. False, if
             otherwise.
         mapper: EventMapper object
             Pass in a built event mapper(see HedFileInput or EventFileInput for examples), or None to just
             retrieve all columns as hed tags.
         """
        if mapper is None:
            mapper = EventMapper()
        self._mapper = mapper
        self._filename = filename
        self._worksheet_name = worksheet_name
        self._has_column_names = has_column_names
        pandas_header = 0
        if not self._has_column_names:
            pandas_header = None

        if self.is_spreadsheet_file():
            if self._worksheet_name is None:
                self._worksheet_name = 0
            self._dataframe = pandas.read_excel(filename, sheet_name=self._worksheet_name, header=pandas_header)
        elif self.is_text_file():
            self._dataframe = pandas.read_csv(filename, '\t', header=pandas_header)

    def save(self, filename, include_formatting=False):
        if self.is_spreadsheet_file():
            final_filename = filename + ".xlsx"
            if include_formatting:
                # To preserve styling information, we now open this as openpyxl, copy all the data over, then save it.
                # this is not ideal
                old_workbook = openpyxl.load_workbook(self._filename)
                old_worksheet = self.get_worksheet(old_workbook, worksheet_name=self._worksheet_name)
                for row_number, text_file_row in self._dataframe.iterrows():
                    for column_number, column_text in enumerate(text_file_row):
                        old_worksheet.cell(row_number + 1, column_number + 1).value = self._dataframe.iloc[row_number, column_number]
                old_workbook.save(final_filename)
            else:
                self._dataframe.to_excel(final_filename)
        elif self.is_text_file():
            final_filename = filename + ".tsv"
            self._dataframe.to_csv(final_filename, '\t', index=False)

    # Make filename read only.
    @property
    def filename(self):
        return self._filename

    def __iter__(self):
        return self.parse_dataframe()

    def iter_raw(self):
        default_mapper = EventMapper()
        return self.parse_dataframe(default_mapper)

    def parse_dataframe(self, mapper=None):
        if mapper is None:
            mapper = self._mapper

        for row_number, text_file_row in self._dataframe.iterrows():
            # Skip any blank lines.
            if any(text_file_row.isnull()):
                continue

            row_dict = self._get_dict_from_row_hed_tags(text_file_row, mapper)
            row_hed_string, column_to_hed_tags_dictionary = self._get_row_hed_tags_from_dict(row_dict)
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
            If true and the column matches one from mapper _column_prefix_dictionary, remove the prefix

        Returns
        -------

        """
        if not include_column_prefix_if_exist:
            new_text = self._mapper.remove_prefix_if_needed(column_number, new_text)

        if self._dataframe is None:
            raise ValueError("No data frame loaded")

        self._dataframe.iloc[row_number, column_number] = new_text

    def _get_dict_from_row_hed_tags(self, spreadsheet_row, mapper):
        row_dict = mapper.expand_row_tags(spreadsheet_row)
        return row_dict

    def _get_row_hed_tags_from_dict(self, row_dict):
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
        return row_dict["HED"], row_dict["column_to_hed_tags"]

    @staticmethod
    def _is_extension_type(filename, allowed_exts):
        filename, ext = os.path.splitext(filename)
        return ext in allowed_exts

    def is_spreadsheet_file(self):
        return BaseFileInput._is_extension_type(self._filename, BaseFileInput.EXCEL_EXTENSION)

    def is_text_file(self):
        return BaseFileInput._is_extension_type(self._filename, BaseFileInput.TEXT_EXTENSION)

    def is_valid_extension(self):
        return self._is_extension_type(self._filename, BaseFileInput.FILE_EXTENSION)

    @staticmethod
    def get_worksheet(workbook, worksheet_name=None):
        if not worksheet_name:
            return workbook.worksheets[0]
        return workbook.get_sheet_by_name(worksheet_name)



if __name__ == '__main__':
    event_file = BaseFileInput("examples/data/basic_events_test.xlsx")

    for stuff in event_file:
        print(stuff)