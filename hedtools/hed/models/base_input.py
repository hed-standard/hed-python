import os
import openpyxl
import pandas
import copy
import io

from itertools import islice
from hed.models.def_dict import DefDict
from hed.models.column_mapper import ColumnMapper
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.errors.error_types import ErrorContext
from hed.errors.error_reporter import ErrorHandler
from hed.models import model_constants


class BaseInput:
    """Handles parsing the actual on disk hed files to a more general format."""
    TEXT_EXTENSION = ['.tsv', '.txt']
    EXCEL_EXTENSION = ['.xlsx']
    FILE_EXTENSION = [*TEXT_EXTENSION, *EXCEL_EXTENSION]
    STRING_INPUT = 'string'
    FILE_INPUT = 'file'
    TAB_DELIMITER = '\t'
    COMMA_DELIMITER = ','

    def __init__(self, filename, file_type=None, worksheet_name=None, has_column_names=True,
                 mapper=None, display_name=None):
        """Constructor for the BaseInput class.

         Parameters
         ----------
         filename: str or file like
             An xlsx/tsv file to open.
         file_type: str
            ".xlsx" for excel, ".tsv" or ".txt" for tsv. data.  Derived from filename if filename is a str.
         worksheet_name: str
             The name of the Excel workbook worksheet that contains the HED tags.  Not applicable to tsv files.
         has_column_names: bool
             True if file has column names. The validation will skip over the first line of the file. False, if
             otherwise.
         mapper: ColumnMapper
             Pass in a built column mapper(see HedInput or EventsInput for examples), or None to just
             retrieve all columns as hed tags.
         display_name: str or None
            Optional field for how this file will report errors.
         """
        if mapper is None:
            mapper = ColumnMapper()
        self._mapper = mapper
        self._has_column_names = has_column_names
        self._display_name = display_name
        # This is the loaded workbook if we loaded originally from an excel file.
        self._loaded_workbook = None
        self._worksheet_name = worksheet_name
        pandas_header = 0
        if not self._has_column_names:
            pandas_header = None

        if not filename:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty filename passed to BaseInput.", filename)

        input_type = file_type
        if file_type is None and isinstance(filename, str):
            _, input_type = os.path.splitext(filename)

        self._dataframe = None

        if input_type in self.TEXT_EXTENSION:
            self._dataframe = pandas.read_csv(filename, delimiter='\t', header=pandas_header)
        elif input_type in self.EXCEL_EXTENSION:
            self._loaded_workbook = openpyxl.load_workbook(filename)
            loaded_worksheet = self.get_worksheet(self._worksheet_name)
            self._dataframe = self._get_dataframe_from_worksheet(loaded_worksheet, has_column_names)
        else:
            raise HedFileError(HedExceptions.INVALID_EXTENSION, "", filename)

        # Finalize mapping information if we have columns
        if self._dataframe is not None and self._has_column_names:
            columns = self._dataframe.columns
            self._mapper.set_column_map(columns)

        # Now that the file is fully initialized, gather the definitions from it.
        self.file_def_dict = self.extract_definitions()
        # finally add the new file dict to the mapper.
        mapper.update_definition_mapper_with_file(self.file_def_dict)

    @property
    def dataframe(self):
        return self._dataframe

    @property
    def display_name(self):
        return self._display_name

    @property
    def has_column_names(self):
        return self._has_column_names

    @property
    def loaded_workbook(self):
        return self._loaded_workbook

    @property
    def worksheet_name(self):
        return self._worksheet_name

    def _convert_to_form(self, hed_schema, tag_form, error_handler):
        """
        Converts all tags in a given spreadsheet to a given form

        Parameters
        ----------
        hed_schema : HedSchema
            The schema to use to convert tags.
        tag_form: str
            The form to convert the tags to.  (short_tag, long_tag, base_tag, etc)
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
                error_list += column_hed_string.convert_to_canonical_forms(hed_schema, error_handler=error_handler)
                self.set_cell(row_number, column_number, column_hed_string,
                              include_column_prefix_if_exist=False, tag_form=tag_form)
                error_handler.pop_error_context()
            error_handler.pop_error_context()

        return error_list

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
        return self._convert_to_form(hed_schema, "short_tag", error_handler)

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
        return self._convert_to_form(hed_schema, "long_tag", error_handler)

    def extract_definitions(self, error_handler=None):
        """
        Gathers and validates all definitions found in this spreadsheet

        Parameters
        ----------
        error_handler : ErrorHandler
            The error handler to use for context, uses a default one if none.

        Returns
        -------
        def_dict: DefDict
            Contains all the definitions located in the file
        """
        if error_handler is None:
            error_handler = ErrorHandler()
        new_def_dict = DefDict()
        for row_number, column_to_hed_tags in self.iter_raw():
            error_handler.push_error_context(ErrorContext.ROW, row_number)
            for column_number, hed_string_obj in column_to_hed_tags.items():
                error_handler.push_error_context(ErrorContext.COLUMN, column_number)
                error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj, increment_depth_after=False)
                new_def_dict.check_for_definitions(hed_string_obj, error_handler=error_handler)
                error_handler.pop_error_context()
                error_handler.pop_error_context()
            error_handler.pop_error_context()

        return new_def_dict

    def to_excel(self, filename, output_processed_file=False):
        """

        Parameters
        ----------
        filename : str or file like
            Location to save this file.  Can be filename, or stream/file like.
        output_processed_file : bool
            Replace all definitions and labels in HED columns as appropriate.  Also fills in things like categories.
        Returns
        -------

        """
        if not filename:
            raise ValueError("Empty file name or object passed in to BaseInput.save.")

        # For now just make a copy if we want to save a formatted copy.  Could optimize this further.
        if output_processed_file:
            output_file = self._get_processed_copy()
        else:
            output_file = self

        if self._loaded_workbook:
            old_worksheet = self.get_worksheet(self._worksheet_name)
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
            self._loaded_workbook.save(filename)
        else:
            output_file._dataframe.to_excel(filename, header=self._has_column_names)

    def to_csv(self, filename=None, output_processed_file=False):
        """
            Returns the file as a csv string.

        Parameters
        ----------
        filename : str or file like or None
            Location to save this file.  Can be filename, or stream/file like.
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
        csv_string_if_filename_none = output_file._dataframe.to_csv(filename, '\t', index=False,
                                                                    header=output_file._has_column_names)
        return csv_string_if_filename_none

    def __iter__(self):
        return self.iter_dataframe()

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
        return self.iter_dataframe(default_mapper)

    def iter_dataframe(self, mapper=None, return_row_dict=False, expand_defs=True):
        """
        Generates a list of parsed rows based on the given column mapper.

        Parameters
        ----------
        mapper : ColumnMapper
            The column name to column number mapper
        return_row_dict: bool
            If True, this returns the full row_dict including issues.
            If False, returns just the HedStrings for each column
        expand_defs: bool
            If False, this will still remove all definition/ tags, but will not expand label tags.

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

            row_dict = mapper.expand_row_tags(text_file_row, expand_defs)
            if return_row_dict:
                yield row_number + start_at_one, row_dict
            else:
                yield row_number + start_at_one, row_dict[model_constants.COLUMN_TO_HED_TAGS]

    def set_cell(self, row_number, column_number, new_string_obj, include_column_prefix_if_exist=False,
                 tag_form="short_tag"):
        """

        Parameters
        ----------
        row_number : int
            The row number of the spreadsheet to set
        column_number : int
            The column number of the spreadsheet to set
        new_string_obj : HedString
            Text to enter in the given cell
        include_column_prefix_if_exist : bool
            If true and the column matches one from mapper _column_prefix_dictionary, remove the prefix
        tag_form: str
            The version of the tags we would like to use from the hed string.(short_tag, long_tag, base_tag, etc)
            Any attribute of a HedTag that returns a string is valid.
        Returns
        -------

        """
        if self._dataframe is None:
            raise ValueError("No data frame loaded")

        transform_func = None
        if not include_column_prefix_if_exist:
            transform_func = self._mapper.get_prefix_remove_func(column_number)

        new_text = new_string_obj.get_as_form(tag_form, transform_func)
        adj_row_number = 1
        if self._has_column_names:
            adj_row_number += 1
        self._dataframe.iloc[row_number - adj_row_number, column_number - 1] = new_text

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
        return row_dict[model_constants.ROW_HED_STRING], row_dict[model_constants.COLUMN_TO_HED_TAGS]

    def get_worksheet(self, worksheet_name=None):
        """
            Returns the requested worksheet from the workbook by name

        Parameters
        ----------
        worksheet_name : str
            Returns the requested worksheet by name, or the first one if no name passed in.
        Returns
        -------
        worksheet
        """
        if worksheet_name and self._loaded_workbook:
            # return self._loaded_workbook.get_sheet_by_name(worksheet_name)
            return self._loaded_workbook[worksheet_name]
        elif self._loaded_workbook:
            return self._loaded_workbook.worksheets[0]
        else:
            return None

    def _get_processed_copy(self):
        """
        Returns a copy of this file with processing applied(definitions replaced, columns expanded, etc)

        Returns
        -------
        file_copy: BaseInput
            The copy.
        """
        output_file = copy.deepcopy(self)
        for row_number, column_to_hed_tags_dictionary in self:
            for column_number in column_to_hed_tags_dictionary:
                new_text = column_to_hed_tags_dictionary[column_number]
                output_file.set_cell(row_number, column_number, new_text)

        return output_file

    @staticmethod
    def _get_dataframe_from_worksheet(worksheet, has_headers):
        """
        Creates a pandas dataframe from the given worksheet object

        Parameters
        ----------
        worksheet : Worksheet
            The loaded worksheet to convert
        has_headers : bool
            If this worksheet has column headers or not.

        Returns
        -------
        dataframe: DataFrame
            The converted data frame.
        """
        if has_headers:
            data = worksheet.values
            # first row is columns
            cols = next(data)
            data = list(data)
            return pandas.DataFrame(data, columns=cols)
        else:
            return pandas.DataFrame(worksheet.values)