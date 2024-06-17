"""
Superclass representing a basic columnar file.
"""
import os

import openpyxl
import pandas as pd

from hed.models.column_mapper import ColumnMapper
from hed.errors.exceptions import HedFileError, HedExceptions

from hed.models.df_util import _handle_curly_braces_refs, filter_series_by_onset


class BaseInput:
    """ Superclass representing a basic columnar file. """

    TEXT_EXTENSION = ['.tsv', '.txt']
    EXCEL_EXTENSION = ['.xlsx']

    def __init__(self, file, file_type=None, worksheet_name=None, has_column_names=True, mapper=None, name=None,
                 allow_blank_names=True):
        """ Constructor for the BaseInput class.

        Parameters:
            file (str or file-like or pd.Dataframe): An xlsx/tsv file to open.
            file_type (str or None): ".xlsx" (Excel), ".tsv" or ".txt" (tab-separated text).
                Derived from file if file is a filename.  Ignored if pandas dataframe.
            worksheet_name (str or None): Name of Excel workbook worksheet name to use.
                (Not applicable to tsv files.)
            has_column_names (bool): True if file has column names.
                This value is ignored if you pass in a pandas dataframe.
            mapper (ColumnMapper or None):  Indicates which columns have HED tags.
                See SpreadsheetInput or TabularInput for examples of how to use built-in a ColumnMapper.
            name (str or None): Optional field for how this file will report errors.
            allow_blank_names(bool): If True, column names can be blank

        :raises HedFileError:
            - file is blank.
            - An invalid dataframe was passed with size 0.
            - An invalid extension was provided.
            - A duplicate or empty column name appears.
            - Cannot open the indicated file.
            - The specified worksheet name does not exist.
            - If the sidecar file or tabular file had invalid format and could not be read.

         """
        if mapper is None:
            mapper = ColumnMapper()
        self._mapper = mapper
        self._has_column_names = has_column_names
        self._name = name
        # This is the loaded workbook if we loaded originally from an Excel file.
        self._loaded_workbook = None
        self._worksheet_name = worksheet_name
        self._dataframe = None

        input_type = file_type
        if isinstance(file, str):
            if file_type is None:
                _, input_type = os.path.splitext(file)
            if self.name is None:
                self._name = file

        self._open_dataframe_file(file, has_column_names, input_type)

        column_issues = ColumnMapper.check_for_blank_names(self.columns, allow_blank_names=allow_blank_names)
        if column_issues:
            raise HedFileError(HedExceptions.BAD_COLUMN_NAMES, "Duplicate or blank columns found. See issues.",
                               self.name, issues=column_issues)

        self.reset_mapper(mapper)

    def reset_mapper(self, new_mapper):
        """ Set mapper to a different view of the file.

        Parameters:
            new_mapper (ColumnMapper): A column mapper to be associated with this base input.
        """
        self._mapper = new_mapper
        if not self._mapper:
            self._mapper = ColumnMapper()

        if self._dataframe is not None and self._has_column_names:
            columns = self._dataframe.columns
            self._mapper.set_column_map(columns)

    @property
    def dataframe(self):
        """ The underlying dataframe. """
        return self._dataframe

    @property
    def dataframe_a(self):
        """Return the assembled dataframe Probably a placeholder name.

        Returns:
            Dataframe: the assembled dataframe"""
        return self.assemble()

    @property
    def series_a(self):
        """Return the assembled dataframe as a series.

        Returns:
            Series: the assembled dataframe with columns merged.
        """
        return self.combine_dataframe(self.assemble())

    @property
    def series_filtered(self):
        """Return the assembled dataframe as a series, with rows that have the same onset combined.

        Returns:
            Series or None: the assembled dataframe with columns merged, and the rows filtered together.
        """
        if self.onsets is not None:
            return filter_series_by_onset(self.series_a, self.onsets)

    @property
    def onsets(self):
        """Return the onset column if it exists. """
        if "onset" in self.columns:
            return self._dataframe["onset"]

    @property
    def needs_sorting(self):
        """Return True if this both has an onset column, and it needs sorting."""
        onsets = self.onsets
        if onsets is not None:
            onsets = pd.to_numeric(self.dataframe['onset'], errors='coerce')
            return not onsets.is_monotonic_increasing

    @property
    def name(self):
        """ Name of the data. """
        return self._name

    @property
    def has_column_names(self):
        """ True if dataframe has column names. """
        return self._has_column_names

    @property
    def loaded_workbook(self):
        """ The underlying loaded workbooks. """
        return self._loaded_workbook

    @property
    def worksheet_name(self):
        """ The worksheet name. """
        return self._worksheet_name

    def convert_to_form(self, hed_schema, tag_form):
        """ Convert all tags in underlying dataframe to the specified form.

        Parameters:
            hed_schema (HedSchema): The schema to use to convert tags.
            tag_form(str): HedTag property to convert tags to.
                Most cases should use convert_to_short or convert_to_long below.
        """
        from hed.models.df_util import convert_to_form
        convert_to_form(self._dataframe, hed_schema, tag_form, self._mapper.get_tag_columns())

    def convert_to_short(self, hed_schema):
        """ Convert all tags in underlying dataframe to short form.

        Parameters:
            hed_schema (HedSchema): The schema to use to convert tags.
        """
        return self.convert_to_form(hed_schema, "short_tag")

    def convert_to_long(self, hed_schema):
        """ Convert all tags in underlying dataframe to long form.

        Parameters:
            hed_schema (HedSchema or None): The schema to use to convert tags.
        """
        return self.convert_to_form(hed_schema, "long_tag")

    def shrink_defs(self, hed_schema):
        """ Shrinks any def-expand found in the underlying dataframe.

        Parameters:
            hed_schema (HedSchema or None): The schema to use to identify defs.
        """
        from df_util import shrink_defs
        shrink_defs(self._dataframe, hed_schema=hed_schema, columns=self._mapper.get_tag_columns())

    def expand_defs(self, hed_schema, def_dict):
        """ Shrinks any def-expand found in the underlying dataframe.

        Parameters:
            hed_schema (HedSchema or None): The schema to use to identify defs.
            def_dict (DefinitionDict): The definitions to expand.
        """
        from df_util import expand_defs
        expand_defs(self._dataframe, hed_schema=hed_schema, def_dict=def_dict, columns=self._mapper.get_tag_columns())

    def to_excel(self, file):
        """ Output to an Excel file.

        Parameters:
            file (str or file-like): Location to save this base input.

        :raises ValueError:
            - If empty file object was passed.

        :raises OSError:
            - Cannot open the indicated file.
        """
        if not file:
            raise ValueError("Empty file name or object passed in to BaseInput.save.")

        dataframe = self._dataframe
        if self._loaded_workbook:
            old_worksheet = self.get_worksheet(self._worksheet_name)
            # Excel spreadsheets are 1 based, then add another 1 for column names if present
            adj_row_for_col_names = 1
            if self._has_column_names:
                adj_row_for_col_names += 1
            adj_for_one_based_cols = 1
            for row_number, text_file_row in dataframe.iterrows():
                for column_number, column_text in enumerate(text_file_row):
                    cell_value = dataframe.iloc[row_number, column_number]
                    old_worksheet.cell(row_number + adj_row_for_col_names,
                                       column_number + adj_for_one_based_cols).value = cell_value

            self._loaded_workbook.save(file)
        else:
            dataframe.to_excel(file, header=self._has_column_names)

    def to_csv(self, file=None):
        """ Write to file or return as a string.

        Parameters:
            file (str, file-like, or None): Location to save this file. If None, return as string.
        Returns:
            None or str:  None if file is given or the contents as a str if file is None.

        :raises OSError:
            - Cannot open the indicated file.
        """
        dataframe = self._dataframe
        csv_string_if_filename_none = dataframe.to_csv(file, sep='\t', index=False, header=self._has_column_names)
        return csv_string_if_filename_none

    @property
    def columns(self):
        """ Returns a list of the column names.

            Empty if no column names.

        Returns:
            columns(list): The column names.
        """
        columns = []
        if self._dataframe is not None and self._has_column_names:
            columns = list(self._dataframe.columns)
        return columns

    def column_metadata(self):
        """ Return the metadata for each column.

        Returns:
            dict: Number/ColumnMeta pairs.
        """
        if self._mapper:
            return self._mapper._final_column_map
        return {}

    def set_cell(self, row_number, column_number, new_string_obj, tag_form="short_tag"):
        """ Replace the specified cell with transformed text.

        Parameters:
            row_number (int):    The row number of the spreadsheet to set.
            column_number (int): The column number of the spreadsheet to set.
            new_string_obj (HedString): Object with text to put in the given cell.
            tag_form (str): Version of the tags (short_tag, long_tag, base_tag, etc)

        Notes:
             Any attribute of a HedTag that returns a string is a valid value of tag_form.

        :raises ValueError:
            - There is not a loaded dataframe.

        :raises KeyError:
            - The indicated row/column does not exist.

        :raises AttributeError:
            - The indicated tag_form is not an attribute of HedTag.
        """
        if self._dataframe is None:
            raise ValueError("No data frame loaded")

        new_text = new_string_obj.get_as_form(tag_form)
        self._dataframe.iloc[row_number, column_number] = new_text

    def get_worksheet(self, worksheet_name=None):
        """ Get the requested worksheet.

        Parameters:
            worksheet_name (str or None): The name of the requested worksheet by name or the first one if None.

        Returns:
            openpyxl.workbook.Workbook: The workbook request.

        Notes:
            If None, returns the first worksheet.

        :raises KeyError:
            - The specified worksheet name does not exist.
        """
        if worksheet_name and self._loaded_workbook:
            # return self._loaded_workbook.get_sheet_by_name(worksheet_name)
            return self._loaded_workbook[worksheet_name]
        elif self._loaded_workbook:
            return self._loaded_workbook.worksheets[0]
        else:
            return None

    @staticmethod
    def _get_dataframe_from_worksheet(worksheet, has_headers):
        """ Create a dataframe from the worksheet.

        Parameters:
            worksheet (Worksheet): The loaded worksheet to convert.
            has_headers (bool): True if this worksheet has column headers.

        Returns:
            DataFrame: The converted data frame.

        """
        if has_headers:
            data = worksheet.values
            # first row is columns
            cols = next(data)
            data = list(data)
            return pd.DataFrame(data, columns=cols, dtype=str)
        else:
            return pd.DataFrame(worksheet.values, dtype=str)

    def validate(self, hed_schema, extra_def_dicts=None, name=None, error_handler=None):
        """Creates a SpreadsheetValidator and returns all issues with this file.

        Parameters:
            hed_schema(HedSchema): The schema to use for validation.
            extra_def_dicts(list of DefDict or DefDict): All definitions to use for validation.
            name(str): The name to report errors from this file as.
            error_handler (ErrorHandler): Error context to use.  Creates a new one if None.

        Returns:
            issues (list of dict): A list of issues for a HED string.
        """
        from hed.validator.spreadsheet_validator import SpreadsheetValidator
        if not name:
            name = self.name
        tab_validator = SpreadsheetValidator(hed_schema)
        validation_issues = tab_validator.validate(self, self._mapper.get_def_dict(hed_schema, extra_def_dicts), name,
                                                   error_handler=error_handler)
        return validation_issues

    @staticmethod
    def _dataframe_has_names(dataframe):
        for column in dataframe.columns:
            if isinstance(column, str):
                return True
        return False

    def assemble(self, mapper=None, skip_curly_braces=False):
        """ Assembles the HED strings.

        Parameters:
            mapper(ColumnMapper or None): Generally pass none here unless you want special behavior.
            skip_curly_braces (bool): If True, don't plug in curly brace values into columns.
        Returns:
            Dataframe: The assembled dataframe.
        """
        if mapper is None:
            mapper = self._mapper

        all_columns = self._handle_transforms(mapper)
        if skip_curly_braces:
            return all_columns
        transformers, _ = mapper.get_transformers()
        refs = self.get_column_refs()
        column_names = list(transformers)
        return _handle_curly_braces_refs(all_columns, refs, column_names)

    def _handle_transforms(self, mapper):
        transformers, need_categorical = mapper.get_transformers()
        if transformers:
            all_columns = self._dataframe
            if need_categorical:
                all_columns[need_categorical] = all_columns[need_categorical].astype('category')

            all_columns = all_columns.transform(transformers)

            if need_categorical:
                all_columns[need_categorical] = all_columns[need_categorical].astype('str')
        else:
            all_columns = self._dataframe

        return all_columns

    @staticmethod
    def combine_dataframe(dataframe):
        """ Combine all columns in the given dataframe into a single HED string series,
            skipping empty columns and columns with empty strings.

        Parameters:
            dataframe(Dataframe): The dataframe to combine

        Returns:
            Series: The assembled series.
        """
        dataframe = dataframe.apply(
            lambda x: ', '.join(filter(lambda e: bool(e) and e != "n/a", map(str, x))),
            axis=1
        )
        return dataframe

    def get_def_dict(self, hed_schema, extra_def_dicts=None):
        """ Return the definition dict for this file.

        Note: Baseclass implementation returns just extra_def_dicts.

        Parameters:
            hed_schema(HedSchema): Identifies tags to find definitions(if needed).
            extra_def_dicts (list, DefinitionDict, or None): Extra dicts to add to the list.

        Returns:
            DefinitionDict:   A single definition dict representing all the data(and extra def dicts).
        """
        from hed.models.definition_dict import DefinitionDict
        return DefinitionDict(extra_def_dicts, hed_schema)

    def get_column_refs(self):
        """ Return a list of column refs for this file.

            Default implementation returns none.

        Returns:
            column_refs(list): A list of unique column refs found.
        """
        return []

    def _open_dataframe_file(self, file, has_column_names, input_type):
        pandas_header = 0
        if not has_column_names:
            pandas_header = None

        if isinstance(file, pd.DataFrame):
            self._dataframe = file.astype(str)
            self._has_column_names = self._dataframe_has_names(self._dataframe)
        elif not file:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty file passed to BaseInput.", file)
        elif input_type in self.TEXT_EXTENSION:
            try:
                self._dataframe = pd.read_csv(file, delimiter='\t', header=pandas_header,
                                              dtype=str, keep_default_na=True, na_values=("", "null"))
            except Exception as e:
                raise HedFileError(HedExceptions.INVALID_FILE_FORMAT, str(e), self.name) from e
            # Convert nan values to a known value
            self._dataframe = self._dataframe.fillna("n/a")
        elif input_type in self.EXCEL_EXTENSION:
            try:
                self._loaded_workbook = openpyxl.load_workbook(file)
                loaded_worksheet = self.get_worksheet(self._worksheet_name)
                self._dataframe = self._get_dataframe_from_worksheet(loaded_worksheet, has_column_names)
            except Exception as e:
                raise HedFileError(HedExceptions.GENERIC_ERROR, str(e), self.name) from e
        else:
            raise HedFileError(HedExceptions.INVALID_EXTENSION, "", file)

        if self._dataframe.size == 0:
            raise HedFileError(HedExceptions.INVALID_DATAFRAME, "Invalid dataframe(malformed datafile, etc)", file)
