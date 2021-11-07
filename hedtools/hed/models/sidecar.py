import json
from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_types import ErrorContext
from hed.errors import error_reporter
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.models.hed_string import HedString
from hed.models.def_mapper import DefinitionMapper


class Sidecar:
    """This stores column definitions for parsing hed spreadsheets, generally loaded from a single json file."""

    def __init__(self, file, name=None):
        """

        Parameters
        ----------
        file: str or FileLike
            If a string, this is a filename.
            Otherwise it will be parsed as a file-like.
        name: str or None
            Optional name to identify this group.  Generally a filename.
        """
        self._column_data = {}
        self.name = name
        if file:
            self.add_sidecar_file(file)

    def __iter__(self):
        """
            Creates an iterator to go over the individual column definitions
        Returns
        -------
        column_data: iterator
        """
        return iter(self._column_data.values())

    def save_as_json(self, save_filename):
        """
            Saves out a column definition group to a json file
        Parameters
        ----------
        save_filename : str
            Path to save file
        """
        output_dict = {}
        for entry in self._column_data.values():
            output_dict[entry.column_name] = entry.hed_dict
        with open(save_filename, "w") as fp:
            json.dump(output_dict, fp, indent=4)

    def get_as_json_string(self):
        """
        Returns this entire column definition group as a json string.
        Returns
        -------
        json_string: str
            The json string representing this column definition group.
        """
        output_dict = {}
        for entry in self._column_data.values():
            output_dict[entry.column_name] = entry.hed_dict
        return json.dumps(output_dict, indent=4)

    def add_sidecar_file(self, file):
        """
            Loads column definitions from a given json file.
            You can load multiple files into one Sidecar, but it is discouraged.

        Parameters
        ----------
        file: str or FileLike
            If a string, this is a filename.
            Otherwise it will be parsed as a file-like.
        """
        if isinstance(file, str):
            try:
                with open(file, "r") as fp:
                    if not self.name:
                        self.name = file
                    self._add_json_file_defs(fp)
            except FileNotFoundError as e:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, file)
            except TypeError as e:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), file)
        else:
            self._add_json_file_defs(file)

    def _add_json_file_defs(self, fp):
        """
            Takes a file like and parses it as json.

        Parameters
        ----------
        fp : file like
            The source for the json.

        Returns
        -------

        """
        try:
            loaded_defs = json.load(fp)
            for col_def, col_dict in loaded_defs.items():
                self._add_single_col_type(col_def, col_dict)
        except json.decoder.JSONDecodeError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), self.name)

    @staticmethod
    def load_multiple_sidecars(json_file_input_list):
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
        sidecars: [Sidecar]
            A list of all input files, loaded into column definition groups if needed.
        """
        if not isinstance(json_file_input_list, list):
            json_file_input_list = [json_file_input_list]

        loaded_files = []
        for json_file in json_file_input_list:
            if isinstance(json_file, str):
                json_file = Sidecar(json_file)
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
        for key, entry in self._column_data.items():
            for hed_string in entry.hed_string_iter(include_position):
                if include_position:
                    yield hed_string[0], (key, hed_string[1])
                else:
                    yield hed_string

    def set_hed_string(self, new_hed_string, position):
        """Set a hed string in a provided column/category key/etc

        Parameters
        ----------
        new_hed_string : str or HedString
            The new hed_string to replace the value at position.
        position : tuple
            This should only be a value returned from hed_string_iter
        """
        column_name, position = position
        entry = self._column_data[column_name]
        entry.set_hed_string(new_hed_string, position)

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
        column_entry = ColumnMetadata(column_type, column_name, dict_for_entry)
        self._column_data[column_name] = column_entry

    def validate_entries(self, validators=None, name=None, error_handler=None,
                         **kwargs):
        """Run the given validators on all columns in this sidecar

        Parameters
        ----------

        validators : [func or validator like] or func or validator like
            A validator or list of validators to apply to the hed strings in this sidecar.
        name: str
            If present, will use this as the filename for context, rather than using the actual filename
            Useful for temp filenames.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        kwargs:
            See util.translate_ops or the specific validators for additional options
        Returns
        -------
        validation_issues: [{}]
            The list of validation issues found
        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()
        if not name:
            name = self.name
        if not isinstance(validators, list):
            validators = [validators]
        if name:
            error_handler.push_error_context(ErrorContext.FILE_NAME, name, False)

        def_dicts = [column_entry.def_dict for column_entry in self]
        def_mapper = DefinitionMapper(def_dicts)
        validators.append(def_mapper)
        all_validation_issues = []
        for column_data in self:
            all_validation_issues += column_data.validate_column(validators, also_validate=True,
                                                                 error_handler=error_handler,
                                                                 **kwargs)

        if name:
            error_handler.pop_error_context()
        return all_validation_issues
