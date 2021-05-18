import os
import openpyxl
import pandas
import copy
import io

from hed.util.def_dict import DefDict
from hed.util.column_mapper import ColumnMapper
from hed.util.exceptions import HedFileError, HedExceptions
from hed.util.error_types import ErrorContext
from hed.util.error_reporter import ErrorHandler
from hed.util import util_constants


class BaseFileInput:
    """Handles parsing the actual on disk hed files to a more general format."""
    TEXT_EXTENSION = ['.tsv', '.txt']
    EXCEL_EXTENSION = ['.xls', '.xlsx']
    FILE_EXTENSION = [*TEXT_EXTENSION, *EXCEL_EXTENSION]
    STRING_INPUT = 'string'
    FILE_INPUT = 'file'
    TAB_DELIMITER = '\t'
    COMMA_DELIMITER = ','

    def __init__(self, filename, worksheet_name=None, has_column_names=True, mapper=None,
                 data_as_csv_string=None):
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
         mapper: ColumnMapper
             Pass in a built column mapper(see HedFileInput or EventFileInput for examples), or None to just
             retrieve all columns as hed tags.
         data_as_csv_string: str or None
            The data to treat as this file.  eg web services passing a string.
         """
        if mapper is None:
            mapper = ColumnMapper()
        self._mapper = mapper
        self._filename = filename
        self._worksheet_name = worksheet_name
        self._has_column_names = has_column_names
        pandas_header = 0
        if not self._has_column_names:
            pandas_header = None

        self._dataframe = None
        if self.is_spreadsheet_file():
            worksheet_to_load = self._worksheet_name
            if worksheet_to_load is None:
                worksheet_to_load = 0
            self._dataframe = pandas.read_excel(filename, sheet_name=worksheet_to_load, header=pandas_header)
        elif self.is_text_file():
            csv_filename_or_data = filename
            if data_as_csv_string:
                csv_filename_or_data = io.StringIO(data_as_csv_string)
            self._dataframe = pandas.read_csv(csv_filename_or_data, '\t', header=pandas_header)
        else:
            raise HedFileError(HedExceptions.INVALID_EXTENSION, "", filename)

        # Finalize mapping information if we have columns
        if self._dataframe is not None and self._has_column_names:
            columns = self._dataframe.columns
            self._mapper.set_column_map(columns)

        # Now that the file is fully initialized, gather the definitions from it.
        self.file_def_dict, self.file_def_dict_issues = self.extract_definitions()
        # finally add the new file dict to the mapper.
        mapper.update_definition_mapper_with_file(self.file_def_dict)

    def convert_to_short(self, hed_schema, error_handler=None):
        """
        Converts all tags in a given spreadsheet to short form

        Parameters
        ----------
        hed_schema : HedSchema
            The schema to use to convert tags.
        error_handler : ErrorHandler
            The error handler to use for context, uses a default one if none.

        Returns
        -------
        issues_list: [{}]
            A list of issues found during conversion
        """
        if error_handler is None:
            error_handler = ErrorHandler()
        error_list = []
        for row_number, column_to_hed_tags_dictionary in self:
            error_handler.push_error_context(ErrorContext.ROW, row_number)
            for column_number in column_to_hed_tags_dictionary:
                error_handler.push_error_context(ErrorContext.COLUMN, column_number)
                column_hed_string = column_to_hed_tags_dictionary[column_number]
                error_list += column_hed_string.convert_to_short(hed_schema, error_handler=error_handler)
                self.set_cell(row_number, column_number, column_hed_string,
                              include_column_prefix_if_exist=False)
                error_handler.pop_error_context()
            error_handler.pop_error_context()
        return error_list

    def convert_to_long(self, hed_schema, error_handler=None):
        """
        Converts all tags in a given spreadsheet to long form

        Parameters
        ----------
        hed_schema : HedSchema
            The schema to use to convert tags.
        error_handler : ErrorHandler
            The error handler to use for context, uses a default one if none.

        Returns
        -------
        issues_list: [{}]
            A list of issues found during conversion
        """
        if error_handler is None:
            error_handler = ErrorHandler()
        error_list = []
        for row_number, column_to_hed_tags_dictionary in self:
            error_handler.push_error_context(ErrorContext.ROW, row_number)
            for column_number in column_to_hed_tags_dictionary:
                error_handler.push_error_context(ErrorContext.COLUMN, column_number)
                column_hed_string = column_to_hed_tags_dictionary[column_number]
                error_list += column_hed_string.convert_to_long(hed_schema, error_handler=error_handler)
                self.set_cell(row_number, column_number, column_hed_string,
                              include_column_prefix_if_exist=False)
                error_handler.pop_error_context()
            error_handler.pop_error_context()

        return error_list

    def extract_definitions(self, error_handler=None):
        """
        Gathers and validates all definitions found in this spreadsheet

        Parameters
        ----------
        hed_schema : HedSchema
            Used to know where definition tags are located in the schema
        error_handler : ErrorHandler
            The error handler to use for context, uses a default one if none.

        Returns
        -------
        def_dict: DefDict
            Contains all the definitions located in the file
        validation_issues: [{}]
            A list of all issues found with the definitions.
        """
        if error_handler is None:
            error_handler = ErrorHandler()
        new_def_dict = DefDict()
        validation_issues = []
        for row_number, column_to_hed_tags in self.iter_raw():
            error_handler.push_error_context(ErrorContext.ROW, row_number)
            for column_number, hed_string_obj in column_to_hed_tags.items():
                error_handler.push_error_context(ErrorContext.COLUMN, column_number)
                validation_issues += new_def_dict.check_for_definitions(hed_string_obj, error_handler=error_handler)
                error_handler.pop_error_context()
            error_handler.pop_error_context()

        return new_def_dict, validation_issues

    def save(self, filename=None, include_formatting=False, output_processed_file=False,
             add_suffix=None):
        """

        Parameters
        ----------
        filename : str or None
            if filename is empty, use the original filename that the file was opened from.
        include_formatting : bool
            If it's a spreadsheet, this will attempt to reopen the file and preserve formatting lost from pandas.
        output_processed_file : bool
            Replace all definitions and labels in HED columns as appropriate.  Also fills in things like categories.
        add_suffix: str
            if present, adds a suffix to the passed in filename(before extension)
        Returns
        -------

        """
        if not filename:
            filename = self._filename
        base_filename, extension = os.path.splitext(filename)
        final_filename = base_filename
        if add_suffix:
            final_filename += add_suffix
        final_filename += extension

        # For now just make a copy if we want to save a formatted copy.  Could optimize this further.
        if output_processed_file:
            output_file = self._get_processed_copy()
        else:
            output_file = self

        if output_file.is_spreadsheet_file():
            if include_formatting:
                # To preserve styling information, we now open this as openpyxl, copy all the data over, then save it.
                # this is not ideal
                old_workbook = openpyxl.load_workbook(self._filename)
                old_worksheet = self.get_worksheet(old_workbook, worksheet_name=self._worksheet_name)
                # excel spreadsheets are 1 based, then add another 1 for column names if present
                adj_row_for_col_names = 1
                if self._has_column_names:
                    adj_row_for_col_names += 1
                adj_for_one_based_cols = 1
                for row_number, text_file_row in output_file._dataframe.iterrows():
                    for column_number, column_text in enumerate(text_file_row):
                        old_worksheet.cell(row_number + adj_row_for_col_names,
                                           column_number + adj_for_one_based_cols).value = \
                            output_file._dataframe.iloc[row_number, column_number]
                old_workbook.save(final_filename)
            else:
                output_file._dataframe.to_excel(final_filename, header=self._has_column_names)
        elif self.is_text_file():
            output_file._dataframe.to_csv(final_filename, '\t', index=False, header=output_file._has_column_names)

    def to_csv(self, output_processed_file=False):
        """
            Returns the file as a csv string.

        Parameters
        ----------
        output_processed_file : bool
            Replace all definitions and labels in HED columns as appropriate.  Also fills in things like categories.
        Returns
        -------
        """
        # For now just make a copy if we want to save a formatted copy.  Could optimize this further.
        if output_processed_file:
            output_file = self._get_processed_copy()
        else:
            output_file = self
        csv_string = output_file._dataframe.to_csv(None, '\t', index=False, header=output_file._has_column_names)
        return csv_string

    # Make filename read only.
    @property
    def filename(self):
        return self._filename

    def __iter__(self):
        return self.parse_dataframe()

    def iter_raw(self):
        """Generates an iterator that goes over every row in the file without modification.

           This is primarily for altering or re-saving the original file.(eg convert short tags to long)

        Yields
        -------
        row_number: int
            The current row number
        row_hed_string: HedString
            parsed and combined hed string for the row, gathered from all specified columns
        column_to_hed_tags_dictionary: dict
            A dict with keys column_number, value the cell at that position.
        """
        default_mapper = ColumnMapper()
        return self.parse_dataframe(default_mapper)

    def parse_dataframe(self, mapper=None, return_row_dict=False):
        """
        Generates a list of parsed rows based on the given column mapper.

        Parameters
        ----------
        mapper : ColumnMapper
            The column name to column number mapper
        return_row_dict: bool
            If True, this returns the full row_dict including issues.
            If False, returns just the HedStrings for each column
        Yields
        -------
        row_number: int
            The current row number
        row_dict: dict
            A dict containing the parsed row, including: "HED", "column_to_hed_tags", and possibly "column_issues"
        """
        if mapper is None:
            mapper = self._mapper

        start_at_one = 1
        if self._has_column_names:
            start_at_one += 1
        for row_number, text_file_row in self._dataframe.iterrows():
            # Skip any blank lines.
            if all(text_file_row.isnull()):
                continue

            row_dict = self._get_dict_from_row_hed_tags(text_file_row, mapper)
            if return_row_dict:
                yield row_number + start_at_one, row_dict
            else:
                yield row_number + start_at_one, row_dict[util_constants.COLUMN_TO_HED_TAGS]

    def set_cell(self, row_number, column_number, new_text, include_column_prefix_if_exist=False):
        """

        Parameters
        ----------
        row_number : int
            The row number of the spreadsheet to set
        column_number : int
            The column number of the spreadsheet to set
        new_text : HedString
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

        adj_row_number = 1
        if self._has_column_names:
            adj_row_number += 1
        self._dataframe.iloc[row_number - adj_row_number, column_number - 1] = str(new_text)

    @staticmethod
    def _get_dict_from_row_hed_tags(spreadsheet_row, mapper):
        row_dict = mapper.expand_row_tags(spreadsheet_row)
        return row_dict

    @staticmethod
    def _get_row_hed_tags_from_dict(row_dict):
        """Reads in the current row of HED tags from the Excel file. The hed tag columns will be concatenated to form a
           HED string.

        Parameters
        ----------
        row_dict: dict
            Contains the parsed info from a specific worksheet row.
            the "HED" entry contains the combined hed string for a given row
        Returns
        -------
        hed_string: str
            a HED string containing the concatenated HED tag columns.
        column_tags_dict: dict
            dictionary which associates columns with HED tags

        """
        return row_dict[util_constants.ROW_HED_STRING], row_dict[util_constants.COLUMN_TO_HED_TAGS]

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
        """
            Returns the requested worksheet from the workbook by name

        Parameters
        ----------
        workbook : openpyxl.workbook.Workbook

        worksheet_name : str
            Returns the requested worksheet by name, or the first one if no name passed in.
        Returns
        -------
        worksheet
        """
        if not worksheet_name:
            return workbook.worksheets[0]
        return workbook.get_sheet_by_name(worksheet_name)

    def _get_processed_copy(self):
        """
        Returns a copy of this file with processing applied(definitions replaced, columns expanded, etc)

        Returns
        -------
        file_copy: BaseFileInput
            The copy.
        """
        output_file = copy.deepcopy(self)
        for row_number, column_to_hed_tags_dictionary in self:
            for column_number in column_to_hed_tags_dictionary:
                new_text = column_to_hed_tags_dictionary[column_number]
                output_file.set_cell(row_number, column_number, new_text)

        return output_file