import json
from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_types import ErrorContext
from hed.errors import error_reporter
from hed.errors import ErrorHandler
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
            Otherwise, it will be parsed as a file-like.
        name: str or None
            Optional name to identify this group.  Generally a filename.
        """
        self._column_data = {}
        self.name = name
        if file:
            self.add_sidecar_file(file)

    def __iter__(self):
        """
            Creates an iterator to go over the individual column metadata
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
            Otherwise, it will be parsed as a file-like.
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

    def hed_string_iter(self, validators=None, error_handler=None, expand_defs=False, remove_definitions=False,
                        allow_placeholders=True, extra_def_dicts=None, **kwargs):
        """
        Return iterator to loop over all hed strings in all column definitions

        Returns a tuple of (string, position)
        Pass position to set_hed_string to change one.

        Parameters
        ----------
        validators : [func or validator like] or func or validator like
            A validator or list of validators to apply to the hed strings before returning
        error_handler : ErrorHandler
            The error handler to use for context, uses a default one if none.
        expand_defs: bool
            If True, expand all def tags located in the strings.
        remove_definitions: bool
            If True, remove all definitions found in the string.
        allow_placeholders: bool
            If False, placeholders will be marked as validation warnings.
        extra_def_dicts: [DefDict] or DefDict or None
            Extra dicts to add to the list
        kwargs:
            See util.translate_ops or the specific validators for additional options

        Yields
        -------
        hed_string : HedString
            HedString at a given column and key position
        position: tuple
            Indicates where hed_string was loaded from so it can be later set by the user
        issues: []
            A list of issues found performing ops.
        """
        if error_handler is None:
            error_handler = ErrorHandler()
        if expand_defs or remove_definitions:
            validators = self._add_definition_mapper(validators, extra_def_dicts)
        else:
            if not isinstance(validators, list):
                validators = [validators]
            validators = validators.copy()
        for column_name, entry in self._column_data.items():
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
            for (hed_string_obj, position, issues) in entry.hed_string_iter(validators=validators,
                                                                            error_handler=error_handler,
                                                                            expand_defs=expand_defs,
                                                                            allow_placeholders=allow_placeholders,
                                                                            remove_definitions=remove_definitions,
                                                                            **kwargs):
                yield hed_string_obj, (column_name, position), issues

            error_handler.pop_error_context()

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

    def _add_definition_mapper(self, validators, extra_def_dicts=None):
        if not isinstance(validators, list):
            validators = [validators]
        validators = validators.copy()
        if not any(isinstance(validator, DefinitionMapper) for validator in validators):
            def_dicts = self.get_def_dicts(extra_def_dicts)
            def_mapper = DefinitionMapper(def_dicts)
            validators.append(def_mapper)
        return validators

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
            How it should treat this column.  This overrides auto-detection from the dict_for_entry.
        """
        column_entry = ColumnMetadata(column_type, column_name, dict_for_entry)
        self._column_data[column_name] = column_entry

    def get_def_dicts(self, extra_def_dicts=None):
        """
            Returns a list of def dicts for each column in this sidecar.

        Parameters
        ----------
        extra_def_dicts: [DefDict] or DefDict or None
            Extra dicts to add to the list
        Returns
        -------
        def_dicts: [DefDict]
            A list of def dicts for each column plus any found in extra_def_dicts.
        """
        def_dicts = [column_entry.def_dict for column_entry in self]
        if extra_def_dicts:
            if not isinstance(extra_def_dicts, list):
                extra_def_dicts = [extra_def_dicts]
            def_dicts += extra_def_dicts
        return def_dicts

    def validate_entries(self, validators=None, name=None, extra_def_dicts=None,
                         error_handler=None, **kwargs):
        """Run the given validators on all columns in this sidecar

        Parameters
        ----------

        validators : [func or validator like] or func or validator like
            A validator or list of validators to apply to the hed strings in this sidecar.
        name: str
            If present, will use this as the filename for context, rather than using the actual filename
            Useful for temp filenames.
        extra_def_dicts: [DefDict] or DefDict or None
            If present, also use these in addition to the sidecars def dicts.
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
        if name:
            error_handler.push_error_context(ErrorContext.FILE_NAME, name, False)

        validators = self._add_definition_mapper(validators, extra_def_dicts)

        all_validation_issues = []
        for column_data in self:
            all_validation_issues += column_data.validate_column(validators,
                                                                 error_handler=error_handler,
                                                                 **kwargs)
        if name:
            error_handler.pop_error_context()
        return all_validation_issues
