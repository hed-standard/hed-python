import os
import openpyxl
import pandas
import copy

from hed.models.definition_dict import DefinitionDict
from hed.models.column_mapper import ColumnMapper
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.errors.error_types import ErrorContext, ErrorSeverity
from hed.errors.error_reporter import ErrorHandler
from hed.models import model_constants
from hed.models.hed_ops import translate_ops
from hed.models.onset_mapper import OnsetMapper
from hed.models.hed_string import HedString
from hed.models.hed_string_group import HedStringGroup
from hed.models.def_mapper import DefMapper


class BaseInput:
    """ Superclass representing a basic columnar file. """

    TEXT_EXTENSION = ['.tsv', '.txt']
    EXCEL_EXTENSION = ['.xlsx']
    FILE_EXTENSION = [*TEXT_EXTENSION, *EXCEL_EXTENSION]
    STRING_INPUT = 'string'
    FILE_INPUT = 'file'
    TAB_DELIMITER = '\t'
    COMMA_DELIMITER = ','

    def __init__(self, file, file_type=None, worksheet_name=None, has_column_names=True, mapper=None, def_mapper=None,
                 definition_columns=None, name=None, allow_blank_names=True, hed_schema=None):
        """ Constructor for the BaseInput class.

        Parameters:
            file (str or file-like or pandas dataframe): An xlsx/tsv file to open.
            file_type (str or None): ".xlsx" (Excel), ".tsv" or ".txt" (tab-separated text).
                Derived from file if file is a filename.  Ignored if pandas dataframe.
            worksheet_name (str or None): Name of Excel workbook worksheet name to use.
                (Not applicable to tsv files.)
            has_column_names (bool): True if file has column names.
                This value is ignored if you pass in a pandas dataframe.
            mapper (ColumnMapper or None):  Indicates which columns have HED tags.
            definition_columns(list or None): A list of columns to check for definitions.  Explicit 'None' means all.
            name (str or None): Optional field for how this file will report errors.
            allow_blank_names(bool): If True, column names can be blank
            hed_schema(HedSchema or None): The schema to use by default in identifying tags
        Notes:
            - See SpreadsheetInput or TabularInput for examples of how to use built-in a ColumnMapper.

         """
        if mapper is None:
            mapper = ColumnMapper()
        self._mapper = mapper
        if def_mapper is None:
            def_mapper = DefMapper(mapper.get_def_dicts())
        self._def_mapper = def_mapper
        self._has_column_names = has_column_names
        self._name = name
        # This is the loaded workbook if we loaded originally from an excel file.
        self._loaded_workbook = None
        self._worksheet_name = worksheet_name
        self._def_columns = definition_columns
        self._schema = hed_schema
        self.file_def_dict = None
        pandas_header = 0
        if not self._has_column_names:
            pandas_header = None

        input_type = file_type
        if isinstance(file, str):
            if file_type is None:
                _, input_type = os.path.splitext(file)
            if self.name is None:
                self._name = file

        self._dataframe = None

        if isinstance(file, pandas.DataFrame):
            self._dataframe = file
            self._has_column_names = self._dataframe_has_names(self._dataframe)
        elif not file:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty file passed to BaseInput.", file)
        elif input_type in self.TEXT_EXTENSION:
            self._dataframe = pandas.read_csv(file, delimiter='\t', header=pandas_header,
                                              dtype=str, keep_default_na=False, na_values=None)
        elif input_type in self.EXCEL_EXTENSION:
            self._loaded_workbook = openpyxl.load_workbook(file)
            loaded_worksheet = self.get_worksheet(self._worksheet_name)
            self._dataframe = self._get_dataframe_from_worksheet(loaded_worksheet, has_column_names)
        else:
            raise HedFileError(HedExceptions.INVALID_EXTENSION, "", file)

        column_issues = ColumnMapper.validate_column_map(self.columns,
                                                         allow_blank_names=allow_blank_names)
        if column_issues:
            raise HedFileError(HedExceptions.BAD_COLUMN_NAMES, "Duplicate or blank columns found.  See issues.",
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

        self.file_def_dict = self.extract_definitions()

        self.update_definition_mapper(self.file_def_dict)

    @property
    def dataframe(self):
        """ The underlying dataframe. """
        return self._dataframe

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

    def get_definitions(self, as_strings=False):
        if as_strings:
            return DefinitionDict.get_as_strings(self._def_mapper.gathered_defs)
        else:
            return self._def_mapper

    def _convert_to_form(self, hed_schema, tag_form, error_handler):
        """ Convert all tags to the specified form.

        Parameters:
            hed_schema (HedSchema or None): The schema to use to convert tags.
                If None, uses the one used to open the file.
            tag_form (str): The form to convert the tags to (short_tag, long_tag, base_tag, etc).
            error_handler (ErrorHandler or None): The error handler to use for context or default if none.

        Returns:
            dict: A list of issue dictionaries corresponding to issues found during conversion.

        """
        error_list = []
        if hed_schema is None:
            hed_schema = self._schema
        if hed_schema is None:
            raise ValueError("Cannot convert between tag forms without a schema.")
        for row_number, row_dict in enumerate(self.iter_dataframe(hed_ops=hed_schema,
                                                                  return_string_only=False,
                                                                  remove_definitions=False,
                                                                  requested_columns=self._mapper.get_tag_columns(),
                                                                  error_handler=error_handler)):
            column_to_hed_tags_dictionary = row_dict[model_constants.COLUMN_TO_HED_TAGS]
            error_list += row_dict[model_constants.ROW_ISSUES]
            for column_number in column_to_hed_tags_dictionary:
                column_hed_string = column_to_hed_tags_dictionary[column_number]
                self.set_cell(row_number, column_number, column_hed_string,
                              include_column_prefix_if_exist=False, tag_form=tag_form)

        return error_list

    def convert_to_short(self, hed_schema=None, error_handler=None):
        """ Convert all tags to short form.

        Parameters:
            hed_schema (HedSchema or None): The schema to use to convert tags.
                If None, uses the one used to open the file.
            error_handler (ErrorHandler): The error handler to use for context, uses a default if none.

        Returns:
            dict: A list of issue dictionaries corresponding to issues found during conversion.

        """
        return self._convert_to_form(hed_schema, "short_tag", error_handler)

    def convert_to_long(self, hed_schema=None, error_handler=None):
        """ Convert all tags to long form.

        Parameters:
            hed_schema (HedSchema or None): The schema to use to convert tags.
                If None, uses the one used to open the file.
            error_handler (ErrorHandler): The error handler to use for context, uses a default if none.

        Returns:
            dict: A list of issue dictionaries corresponding to issues found during conversion.

        """
        return self._convert_to_form(hed_schema, "long_tag", error_handler)

    def to_excel(self, file, output_processed_file=False):
        """ Output to an Excel file.

        Parameters:
            file (str or file-like):      Location to save this base input.
            output_processed_file (bool): If True, replace definitions and labels in HED columns.
                                          Also fills in things like categories.
        Raises:
            HedFileError if empty file object or file cannot be opened.
        """
        if not file:
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
            self._loaded_workbook.save(file)
        else:
            output_file._dataframe.to_excel(file, header=self._has_column_names)

    def to_csv(self, file=None, output_processed_file=False):
        """ Write to file or return as a string.

        Parameters:
            file (str, file-like, or None): Location to save this file. If None, return as string.
            output_processed_file (bool): Replace all definitions and labels in HED columns as appropriate.
                                          Also fills in things like categories.
        Returns:
            None or str:  None if file is given or the contents as a str if file is None.

        """
        # For now just make a copy if we want to save a formatted copy.  Could optimize this further.
        if output_processed_file:
            output_file = self._get_processed_copy()
        else:
            output_file = self
        csv_string_if_filename_none = output_file._dataframe.to_csv(file, '\t', index=False,
                                                                    header=output_file._has_column_names)
        return csv_string_if_filename_none

    @property
    def columns(self):
        """ Returns a list of the column names.

            Empty if no column names.

        Returns:
            columns(dict): The column number:name pairs
        """
        columns = {}
        if self._dataframe is not None and self._has_column_names:
            columns = list(self._dataframe.columns)
        return columns

    @property
    def def_dict(self):
        """  Returns a dict of all the definitions found in this and sidecars

        Returns:
            def_dict(dict): {str: DefinitionEntry} pairs for each found definition
        """
        if self._def_mapper:
            return self._def_mapper.gathered_defs
        return {}

    def __iter__(self):
        """ Iterate over the underlying dataframe. """
        return self.iter_dataframe()

    def iter_dataframe(self, hed_ops=None, mapper=None, requested_columns=None, return_string_only=True,
                       run_string_ops_on_columns=False, error_handler=None, expand_defs=False, remove_definitions=True,
                       **kwargs):
        """ Iterate rows based on the given column mapper.

        Parameters:
            hed_ops (list, func, HedOps, or None):  A func, a HedOps or a list of these to apply to the
                                                    hed strings before returning.
            mapper (ColumnMapper or None): The column name to column number mapper (or internal mapper if None).
            requested_columns(list or None): If this is not None, return ONLY these columns.  Names or numbers allowed.
            return_string_only (bool): If True, do not return issues list, individual columns, attribute columns, etc.
            run_string_ops_on_columns (bool):   If true, run all tag and string ops on columns,
                                                rather than columns then rows.
            error_handler (ErrorHandler or None):   The error handler to use for context or a default if None.
            expand_defs (bool):  If True, expand def tags into def-expand groups.
            remove_definitions (bool): If true, remove all definition tags found.
            kwargs (kwargs):  See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Yields:
            dict:  A dict with parsed row, including keys: "HED", "column_to_hed_tags", and possibly "column_issues".

        """
        if error_handler is None:
            error_handler = ErrorHandler()

        if mapper is None:
            mapper = self._mapper

        if requested_columns:
            # Make a copy to ensure we don't alter the actual mapper
            mapper = copy.deepcopy(mapper)
            mapper.set_requested_columns(requested_columns)

        tag_funcs, string_funcs = self._translate_ops(hed_ops, run_string_ops_on_columns=run_string_ops_on_columns,
                                                      expand_defs=expand_defs, remove_definitions=remove_definitions,
                                                      error_handler=error_handler, **kwargs)

        # Iter tuples is ~ 25% faster compared to iterrows in our use case
        for row_number, text_file_row in enumerate(self._dataframe.itertuples(index=False)):
            error_handler.push_error_context(ErrorContext.ROW, row_number)
            yield self._expand_row_internal(text_file_row, tag_funcs, string_funcs,
                                            error_handler=error_handler,
                                            mapper=mapper, return_string_only=return_string_only)
            error_handler.pop_error_context()

    def _expand_row_internal(self, text_file_row, tag_funcs, string_funcs, error_handler,
                             mapper=None, return_string_only=False):
        row_dict = mapper.expand_row_tags(text_file_row)
        column_to_hed_tags = row_dict[model_constants.COLUMN_TO_HED_TAGS]
        expansion_column_issues = row_dict.get(model_constants.COLUMN_ISSUES, {})

        row_issues = []
        if tag_funcs:
            row_issues += self._run_column_ops(column_to_hed_tags, tag_funcs,
                                               expansion_column_issues,
                                               error_handler)

        # Return a combined string if we're also returning columns.
        if not return_string_only:
            final_hed_string = HedStringGroup(column_to_hed_tags.values())
        else:
            final_hed_string = HedString.from_hed_strings(contents=column_to_hed_tags.values())

        if string_funcs:
            row_issues += self._run_row_ops(final_hed_string, string_funcs, error_handler)

        if not return_string_only:
            row_dict[model_constants.ROW_ISSUES] = row_issues
            row_dict[model_constants.ROW_HED_STRING] = final_hed_string
            return row_dict
        # Return a HedString rather than a HedStringGroup
        return final_hed_string

    def set_cell(self, row_number, column_number, new_string_obj, include_column_prefix_if_exist=False,
                 tag_form="short_tag"):
        """ Replace the specified cell with transformed text.

        Parameters:
            row_number (int):    The row number of the spreadsheet to set.
            column_number (int): The column number of the spreadsheet to set.
            new_string_obj (HedString): Object with text to put in the given cell.
            include_column_prefix_if_exist (bool): If True and the column matches one from mapper
                _column_prefix_dictionary, remove the prefix.
            tag_form (str): Version of the tags (short_tag, long_tag, base_tag, etc)

        Notes:
             Any attribute of a HedTag that returns a string is a valid value of tag_form.

        """
        if self._dataframe is None:
            raise ValueError("No data frame loaded")

        transform_func = None
        if not include_column_prefix_if_exist:
            transform_func = self._mapper.get_prefix_remove_func(column_number)

        new_text = new_string_obj.get_as_form(tag_form, transform_func)
        self._dataframe.iloc[row_number, column_number] = new_text

    def get_worksheet(self, worksheet_name=None):
        """ Get the requested worksheet.

        Parameters:
            worksheet_name (str or None): The name of the requested worksheet by name or the first one if None.

        Returns:
            openpyxl.workbook.Workbook: The workbook request.

        Notes:
            If None, returns the first worksheet.

        """
        if worksheet_name and self._loaded_workbook:
            # return self._loaded_workbook.get_sheet_by_name(worksheet_name)
            return self._loaded_workbook[worksheet_name]
        elif self._loaded_workbook:
            return self._loaded_workbook.worksheets[0]
        else:
            return None

    def get_def_and_mapper_issues(self, error_handler, check_for_warnings=False):
        """ Return definition and column issues.

        Parameters:
            error_handler (ErrorHandler): The error handler to use.
            check_for_warnings (bool): If True check for and return warnings as well as errors.

        Returns:
            dict: A list of definition and mapping issues. Each issue is a dictionary.

        """
        issues = []
        issues += self.file_def_dict.get_definition_issues()

        # Gather any issues from the mapper for things like missing columns.
        mapper_issues = self._mapper.get_column_mapping_issues()
        error_handler.add_context_to_issues(mapper_issues)
        issues += mapper_issues
        if not check_for_warnings:
            issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
        return issues

    def _get_processed_copy(self):
        """ Return a processed copy of this file.

        Returns:
            BaseInput: The copy.

        Notes:
             Processing includes definitions replaced, columns expanded, etc.

        """
        output_file = copy.deepcopy(self)
        for row_number, row_dict in enumerate(self.iter_dataframe(return_string_only=False)):
            column_to_hed_tags_dictionary = row_dict[model_constants.COLUMN_TO_HED_TAGS]
            for column_number in column_to_hed_tags_dictionary:
                new_text = column_to_hed_tags_dictionary[column_number]
                output_file.set_cell(row_number, column_number, new_text, tag_form="short_tag")

        return output_file

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
            return pandas.DataFrame(data, columns=cols, dtype=str)
        else:
            return pandas.DataFrame(worksheet.values, dtype=str)

    def _run_validators(self, hed_ops, error_handler, expand_defs=False, **kwargs):
        validation_issues = []
        for row_dict in self.iter_dataframe(hed_ops=hed_ops,
                                            return_string_only=False,
                                            error_handler=error_handler, expand_defs=expand_defs,
                                            **kwargs):
            validation_issues += row_dict[model_constants.ROW_ISSUES]

        return validation_issues

    def _run_column_ops(self, column_to_hed_tags_dictionary, column_ops, expansion_column_issues, error_handler):
        validation_issues = []
        if column_to_hed_tags_dictionary:
            for column_number, column_hed_string in column_to_hed_tags_dictionary.items():
                new_column_issues = []
                error_handler.push_error_context(ErrorContext.COLUMN, column_number)
                if column_hed_string is not None:
                    error_handler.push_error_context(ErrorContext.HED_STRING, column_hed_string,
                                                     increment_depth_after=False)
                if column_number in expansion_column_issues:
                    new_column_issues += expansion_column_issues[column_number]

                if column_hed_string is not None:
                    new_column_issues += column_hed_string.apply_funcs(column_ops)
                error_handler.add_context_to_issues(new_column_issues)
                if column_hed_string is not None:
                    error_handler.pop_error_context()
                error_handler.pop_error_context()
                validation_issues += new_column_issues

        return validation_issues

    def _run_row_ops(self, row_hed_string, row_ops, error_handler):
        error_handler.push_error_context(ErrorContext.HED_STRING, row_hed_string, increment_depth_after=False)
        row_issues = row_hed_string.apply_funcs(row_ops)
        error_handler.add_context_to_issues(row_issues)
        error_handler.pop_error_context()
        return row_issues

    def validate_file(self, hed_ops, name=None, error_handler=None, check_for_warnings=True, **kwargs):
        """ Run the hed_ops on columns and rows.

        Parameters:
            hed_ops (func, HedOps, or list of func and/or HedOps): The HedOps of funcs to apply.
            name (str): If present, use this as the filename for context, rather than using the actual filename
                Useful for temp filenames.
            error_handler (ErrorHandler or None): Used to report errors a default one if None.
            check_for_warnings (bool): If True check for and return warnings as well as errors.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Returns:
            list: The list of validation issues found. The list elements are dictionaries.

        """
        if not name:
            name = self.name
        if not isinstance(hed_ops, list):
            hed_ops = [hed_ops]

        if error_handler is None:
            error_handler = ErrorHandler()

        error_handler.push_error_context(ErrorContext.FILE_NAME, name)
        validation_issues = self.get_def_and_mapper_issues(error_handler, check_for_warnings=check_for_warnings)
        validation_issues += self._run_validators(hed_ops, error_handler=error_handler,
                                                  check_for_warnings=check_for_warnings, **kwargs)
        error_handler.pop_error_context()

        return validation_issues

    def extract_definitions(self, error_handler=None):
        """ Gather and validate all definitions.

        Parameters:
            error_handler (ErrorHandler): The error handler to use for context or a default if None.

        Returns:
            DefinitionDict: Contains all the definitions located in the file.

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        new_def_dict = DefinitionDict()
        hed_ops = [self._schema, new_def_dict]
        for _ in self.iter_dataframe(hed_ops=hed_ops,
                                     return_string_only=False,
                                     requested_columns=self._def_columns,
                                     run_string_ops_on_columns=True,
                                     remove_definitions=False,
                                     error_handler=error_handler):
            pass

        return new_def_dict

    def update_definition_mapper(self, def_dict):
        """ Add definitions from dict(s) if mapper exists.

        Parameters:
            def_dict (list or DefinitionDict): Add the DefDict or list of DefDict to the internal definition mapper.

        """
        if self._def_mapper is not None:
            self._def_mapper.add_definitions(def_dict)

    def _translate_ops(self, hed_ops, run_string_ops_on_columns, expand_defs, remove_definitions, **kwargs):

        tag_funcs = []
        string_funcs = []
        if hed_ops or expand_defs or remove_definitions:
            if not isinstance(hed_ops, list):
                hed_ops = [hed_ops]
            hed_ops = hed_ops.copy()
            if not run_string_ops_on_columns:
                self._add_def_onset_mapper(hed_ops)
                tag_funcs, string_funcs = translate_ops(hed_ops, split_ops=True, hed_schema=self._schema,
                                                        expand_defs=expand_defs,
                                                        remove_definitions=remove_definitions,
                                                        **kwargs)
            else:
                tag_funcs = translate_ops(hed_ops, hed_schema=self._schema, expand_defs=expand_defs, **kwargs)

        return tag_funcs, string_funcs

    def _add_def_onset_mapper(self, hed_ops):
        if not any(isinstance(hed_op, DefMapper) for hed_op in hed_ops):
            if self._def_mapper:
                hed_ops.append(self._def_mapper)
                hed_ops.append(OnsetMapper(self._def_mapper))
        return hed_ops

    @staticmethod
    def _dataframe_has_names(dataframe):
        for column in dataframe.columns:
            if isinstance(column, str):
                return True
        return False
