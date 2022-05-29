import json
from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_types import ErrorContext
from hed.errors import error_reporter
from hed.errors import ErrorHandler
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.models.hed_string import HedString
from hed.models.def_mapper import DefMapper


class Sidecar:
    """ Contents of a single JSON file with definition dictionaries. """

    def __init__(self, file, name=None):
        """ Constructs a Sidecar object representing a JSON file.

        Args:
            file (str or FileLike): A string or file-like object representing a JSON file.
            name (str or None): Optional name identifying this sidecar, generally a filename.

        """
        self._column_data = {}
        self.name = name
        if file:
            self.load_sidecar_file(file)

    def __iter__(self):
        """ An iterator to go over the individual column metadata.

        Returns:
            iterator: An iterator over the column metadata values.

        """
        return iter(self._column_data.values())

    def save_as_json(self, save_filename):
        """ Save column metadata to a JSON file.

        Args:
            save_filename (str): Path to save file

        """
        output_dict = {}
        for entry in self._column_data.values():
            output_dict[entry.column_name] = entry.hed_dict
        with open(save_filename, "w") as fp:
            json.dump(output_dict, fp, indent=4)

    def get_as_json_string(self):
        """ Return this sidecar's column metadata as a string.

        Returns:
            str: The json string representing this sidecar.

        """
        output_dict = {}
        for entry in self._column_data.values():
            output_dict[entry.column_name] = entry.hed_dict
        return json.dumps(output_dict, indent=4)

    def load_sidecar_file(self, file):
        """ Load column metadata from a given json file.

        Args:
            file (str or FileLike): If a string, this is a filename. Otherwise, it will be parsed as a file-like.

        Raises:
            HedFileError: If the file was not found or could not be parsed into JSON.

        Notes:
             You can load multiple files into one Sidecar, but it is discouraged.

        """
        if isinstance(file, str):
            try:
                with open(file, "r") as fp:
                    if not self.name:
                        self.name = file
                    self._load_json_columns(fp)
            except FileNotFoundError as e:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, file)
            except TypeError as e:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), file)
        else:
            self._load_json_columns(file)

    def _load_json_columns(self, fp):
        """ Parse a JSON file into columns and load in the column entry dictionary.

        Args:
            fp (File-like): The JSON source stream.

        Raises:
            HedFileError:  If the file cannot be parsed.

        """
        try:
            loaded_defs = json.load(fp)
            for col_name, col_dict in loaded_defs.items():
                self._add_single_column(col_name, col_dict)
        except json.decoder.JSONDecodeError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), self.name)

    @staticmethod
    def load_multiple_sidecars(input_list):
        """ Utility function for easily loading multiple json files at once
            This takes a list of filenames or ColumnDefinitionGroups and returns a list of ColumnDefinitionGroups.

            Note: it will completely fail and raise a HedFileError if any of the files are not found.

        Args:
            input_list (list): A list of filenames or Sidecar files in any mix. [

        Returns:
            list: A list sidecars.

        """
        if not isinstance(input_list, list):
            input_list = [input_list]

        loaded_files = []
        for json_file in input_list:
            if isinstance(json_file, str):
                json_file = Sidecar(json_file)
            loaded_files.append(json_file)
        return loaded_files

    def hed_string_iter(self, hed_ops=None, error_handler=None, expand_defs=False, remove_definitions=False,
                        allow_placeholders=True, extra_def_dicts=None, **kwargs):
        """ Get an iterator to loop over all hed strings in all column definitions.

        Returns a tuple of (string, position)
        Pass position to set_hed_string to change one.

        Args:
            hed_ops (func, HedOps, list): A HedOps, funcs or list of these to apply to the hed strings
                before returning
            error_handler (ErrorHandler): The error handler to use for context, uses a default one if none.
            expand_defs (bool): If True, expand all def tags located in the strings.
            remove_definitions (bool): If True, remove all definitions found in the string.
            allow_placeholders (bool): If False, placeholders will be marked as validation warnings.
            extra_def_dicts (DefinitionDict, list, None): Extra dicts to add to the list.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Yields:
            HedString: A HedString at a given column and key position.
            (tuple): Indicates where hed_string was loaded from so it can be later set by the user
            list: A list of issues found performing ops. Each issue is a dictionary.

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        hed_ops = self._standardize_ops(hed_ops)
        if expand_defs or remove_definitions:
            self._add_definition_mapper(hed_ops, extra_def_dicts)
        for column_name, entry in self._column_data.items():
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
            for (hed_string_obj, position, issues) in entry.hed_string_iter(hed_ops=hed_ops,
                                                                            error_handler=error_handler,
                                                                            expand_defs=expand_defs,
                                                                            allow_placeholders=allow_placeholders,
                                                                            remove_definitions=remove_definitions,
                                                                            **kwargs):
                yield hed_string_obj, (column_name, position), issues

            error_handler.pop_error_context()

    def set_hed_string(self, new_hed_string, position):
        """ Set a hed string in a provided column/category key/etc.

        Args:
            new_hed_string (str or HedString): The new hed_string to replace the value at position.
            position (tuple):   The (HedString, str, list) tuple returned from hed_string_iter.

        """
        column_name, position = position
        entry = self._column_data[column_name]
        entry.set_hed_string(new_hed_string, position)

    def _add_definition_mapper(self, hed_ops, extra_def_dicts=None):
        """ Add a DefMapper if the hed_ops list doesn't have one.

        Args:
            hed_ops (list):  A list of HedOps
            extra_def_dicts (list):  DefDicts from outside.

        Returns:
            DefMapper:  A shallow copy of the hed_ops list with a DefMapper added if there wasn't one.

        """
        if not any(isinstance(hed_op, DefMapper) for hed_op in hed_ops):
            def_dicts = self.get_def_dicts(extra_def_dicts)
            def_mapper = DefMapper(def_dicts)
            hed_ops.append(def_mapper)
            return def_mapper
        return None

    @staticmethod
    def _standardize_ops(hed_ops):
        if not isinstance(hed_ops, list):
            hed_ops = [hed_ops]
        return hed_ops.copy()

    def _add_single_column(self, column_name, dict_for_entry, column_type=None):
        """ Create a single column metadata entry and add to this sidecar.

        Args:
            column_name (str or int): The column name or number
            dict_for_entry (dict): The loaded dictionary for a given column entry (needs the "HED" key if nothing else).
            column_type (ColumnType): Optional indicator of how to treat the column.
                This overrides auto-detection from the dict_for_entry.

        """
        column_entry = ColumnMetadata(column_type, column_name, dict_for_entry)
        self._column_data[column_name] = column_entry

    def get_def_dicts(self, extra_def_dicts=None):
        """ Return a list of DefinitionDict for the columns in this sidecar.

        Args:
            extra_def_dicts (list, DefinitionDict, or None): Extra dicts to add to the list.

        Returns:
            list: A list of definition dicts for each column plus any found in extra_def_dicts.

        """
        def_dicts = [column_entry.def_dict for column_entry in self]
        if extra_def_dicts:
            if not isinstance(extra_def_dicts, list):
                extra_def_dicts = [extra_def_dicts]
            def_dicts += extra_def_dicts
        return def_dicts

    def validate_entries(self, hed_ops=None, name=None, extra_def_dicts=None,
                         error_handler=None, **kwargs):
        """ Run the given hed_ops on all columns in this sidecar.

        Args:
            hed_ops (list, func, or HedOps): A HedOps, func or list of these to apply to hed strings in this sidecar.
            name (str): If present, will use this as the filename for context, rather than using the actual filename
                Useful for temp filenames.
            extra_def_dicts: (DefinitionDict, list, or None): If present use these in addition to sidecar's def dicts.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.
            kwargs: See models.hed_ops.translate_ops or the specific hed_ops for additional options.

        Returns:
            list: The list of validation issues found. Individual issues are in the form of a dict.

        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()
        if not name:
            name = self.name
        if name:
            error_handler.push_error_context(ErrorContext.FILE_NAME, name, False)

        hed_ops = self._standardize_ops(hed_ops)
        def_mapper = self._add_definition_mapper(hed_ops, extra_def_dicts)

        all_validation_issues = []
        all_validation_issues += def_mapper.issues
        for column_data in self:
            all_validation_issues += column_data.validate_column(hed_ops, error_handler=error_handler, **kwargs)
        if name:
            error_handler.pop_error_context()
        return all_validation_issues
