import json
from hed.util.column_definition import ColumnDef
from hed.util.error_types import ErrorContext
from hed.util.error_reporter import push_error_context, pop_error_context
from hed.util.exceptions import HedFileError, HedExceptions


class ColumnDefGroup:
    """This stores column definitions for parsing hed spreadsheets, generally loaded from a single json file."""
    def __init__(self, json_filename):
        """

        Parameters
        ----------
        json_filename: str
            The actual filename to be loaded
        """
        self._json_filename = json_filename
        self._column_settings = {}
        self.add_json_file_defs(json_filename)

    def __iter__(self):
        """
            Creates an iterator to go over the individual column definitions
        Returns
        -------
        column_defs: iterator
        """
        return iter(self._column_settings.values())

    def save_as_json(self, save_filename):
        """
            Saves out a column definition group to a json file
        Parameters
        ----------
        save_filename : str
            Path to save file
        """
        output_dict = {}
        for entry in self._column_settings.values():
            output_dict[entry.column_name] = entry.hed_dict
        with open(save_filename, "w") as fp:
            json.dump(output_dict, fp, indent=4)

    def add_json_file_defs(self, json_filename):
        """
            Loads column definitions from a given json file
            Will add errors related to opening or parsing the file to validation issues.

        Parameters
        ----------
        json_filename : str
            path to file to load
        """
        try:
            with open(json_filename, "r") as fp:
                loaded_defs = json.load(fp)
                for col_def, col_dict in loaded_defs.items():
                    self._add_single_col_type(col_def, col_dict)
        except json.decoder.JSONDecodeError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), json_filename)
        except FileNotFoundError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, json_filename)
        except TypeError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), json_filename)

    @staticmethod
    def load_multiple_json_files(json_file_input_list):
        """
            Utility function for easily loading multiple json files at once
            This takes a list of filenames or ColumnDefinitionGroups and returns a list of ColumnDefinitionGroups.

            Note: it will completely fail and raise a HedFileError if any of the files are not found.

        Parameters
        ----------
        json_file_input_list : [str or ColumnDefinitionGroup]
            A list of filenames or loaded files in any mix
        Returns
        -------
        column_def_groups: [ColumnDefinitionGroup]
            A list of all input files, loaded into column definition groups if needed.
        """
        if not isinstance(json_file_input_list, list):
            json_file_input_list = [json_file_input_list]

        loaded_files = []
        for json_file in json_file_input_list:
            if isinstance(json_file, str):
                json_file = ColumnDefGroup(json_file)
            loaded_files.append(json_file)
        return loaded_files

    def hed_string_iter(self, include_position=False):
        """
        Return iterator to loop over all hed strings in all column definitions

        Returns a tuple of (string, position) if include_position is true.
        Pass position to set_hed_string to change one.

        Parameters
        ----------
        include_position : bool
            If true, this returns a tuple including a position element you can pass back in to set_hed_string

        Yields
        -------
        hed_string : str
            hed_string at a given column and key position
        position: tuple, optional
            Indicates where hed_string was loaded from so it can be later set by the user
        """
        for key, entry in self._column_settings.items():
            for hed_string in entry.hed_string_iter(include_position):
                if include_position:
                    yield hed_string[0], (key, hed_string[1])
                else:
                    yield hed_string

    def set_hed_string(self, new_hed_string, position):
        """Set a hed string in a provided column/category key/etc

        Parameters
        ----------
        new_hed_string : str
            The new hed_string to replace the value at position.
        position : tuple
            This should only be a value returned from hed_string_iter
        """
        column_name, position = position
        entry = self._column_settings[column_name]
        entry.set_hed_string(new_hed_string, position)

    # Figure out later if we want support like this...
    # def add_value_column(self, column_name, hed):
    #     new_entry = {
    #         "HED": hed
    #     }
    #     new_entry = ColumnDef(new_entry, column_name, ColumnType.Value)
    #     self._column_settings[column_name] = column_entry
    #
    # def add_categorical_column(self, column_name, hed_category_dict):
    #     new_entry = {
    #         "HED": hed_category_dict
    #     }
    #     new_entry = ColumnDef(new_entry, column_name, ColumnType.Categorical)
    #     self._column_settings[column_name] = column_entry
    #
    # def add_attribute_columns(self, column_names):
    #     self._add_multiple_columns(column_names, ColumnType.Attribute)

    # def add_hedtag_columns(self, column_names):
    #     self._add_multiple_columns(column_names, ColumnType.HEDTags)
    #
    # def add_ignore_columns(self, column_names):
    #     self._add_multiple_columns(column_names, ColumnType.Ignore)

    # def _add_multiple_columns(self, column_names, column_type):
    #     if isinstance(column_names, str):
    #         column_names = [column_names]
    #     for column_name in column_names:
    #         self._add_single_col_type(column_name, None, column_type)

    def _add_single_col_type(self, column_name, dict_for_entry, column_type=None):
        """
        Creates a single column definition with the given parameters.

        Parameters
        ----------
        column_name : str or int
            The column name or number
        dict_for_entry : dict
            The loaded dictionary for a given column entry.  Generally needs the "HED" key if nothing else.
        column_type : ColumnType, optional
            How it should treat this column.  This overrides auto detection from the dict_for_entry.
        """
        column_entry = ColumnDef(column_type, column_name, dict_for_entry)
        self._column_settings[column_name] = column_entry

    def validate_entries(self, hed_schema=None, display_filename=None):
        """Validate the column entries, and also hed strings in the column entries if a hed_schema is passed.

        Parameters
        ----------
        hed_schema : HedSchema, optional
            The dictionary to use to validate individual hed strings.
        display_filename: str
            If present, it will display errors as coming from this filename instead of the actual source.
            Useful for temporary files and similar.
        Returns
        -------
        validation_issues: [{}]
            The list of validation issues found

        """
        if not display_filename:
            display_filename = self._json_filename
        all_validation_issues = []
        push_error_context(ErrorContext.FILE_NAME, display_filename, False)
        for column_entry in self:
            push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_entry.column_name)
            all_validation_issues += column_entry.validate_column_entry(hed_schema)
            pop_error_context()
        pop_error_context(False)
        return all_validation_issues
