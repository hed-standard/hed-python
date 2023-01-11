import json
from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_types import ErrorContext, SidecarErrors
from hed.errors import ErrorHandler
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.models.hed_string import HedString
from hed.models.column_metadata import ColumnType
from hed.models.hed_ops import apply_ops, hed_string_iter, set_hed_string
from hed.models.sidecar_base import SidecarBase


class Sidecar(SidecarBase):
    """ Contents of a JSON file or merged file.

    """

    def __init__(self, files, name=None, hed_schema=None):
        """ Construct a Sidecar object representing a JSON file.

        Parameters:
            files (str or FileLike or list): A string or file-like object representing a JSON file, or a list of such.
            name (str or None): Optional name identifying this sidecar, generally a filename.
            hed_schema(HedSchema or None): The schema to use by default in identifying tags
        """
        super().__init__(name, hed_schema=hed_schema)
        self.loaded_dict = self.load_sidecar_files(files)
        self.def_dict = self.extract_definitions(hed_schema)

    @property
    def column_data(self):
        """ Generates the list of ColumnMetadata for this sidecar

        Returns:
            list(ColumnMetadata): the list of column metadata defined by this sidecar
        """
        for col_name, col_dict in self.loaded_dict.items():
            yield self._generate_single_column(col_name, col_dict)

    def _hed_string_iter(self, tag_funcs, error_handler):
        """ Low level function to retrieve hed string in sidecar

        Parameters:
            tag_funcs(list): A list of functions to apply to returned strings
            error_handler(ErrorHandler): Error handler to use for context

        Yields:
            tuple:
                string(HedString): The retrieved and modified string
                position(tuple): The location of this hed string.  Black box.
                issues(list): A list of issues running the tag_funcs.
        """
        for column_name, dict_for_entry in self.loaded_dict.items():
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
            hed_dict = dict_for_entry.get("HED", {})
            for (hed_string_obj, position, issues) in hed_string_iter(hed_dict, tag_funcs, error_handler):
                yield hed_string_obj, (column_name, position), issues

            error_handler.pop_error_context()

    def _set_hed_string(self, new_hed_string, position):
        """ Low level function to update hed string in sidecar

        Parameters:
            new_hed_string (str or HedString): The new hed_string to replace the value at position.
            position (tuple):   The value returned from hed_string_iter.
        """
        column_name, position = position
        hed_dict = self.loaded_dict[column_name]
        hed_dict["HED"] = set_hed_string(new_hed_string, hed_dict["HED"], position)

    def validate_structure(self, error_handler):
        """ Validate the raw structure of this sidecar.

        Parameters:
            error_handler(ErrorHandler): The error handler to use for error context

        Returns:
            issues(list): A list of issues found with the structure
        """
        all_validation_issues = []
        for column_name, dict_for_entry in self.loaded_dict.items():
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_name)
            all_validation_issues += self._validate_column_structure(column_name, dict_for_entry, error_handler)
            error_handler.pop_error_context()
        return all_validation_issues

    def save_as_json(self, save_filename):
        """ Save column metadata to a JSON file.

        Parameters:
            save_filename (str): Path to save file

        """
        with open(save_filename, "w") as fp:
            json.dump(self.loaded_dict, fp, indent=4)

    def get_as_json_string(self):
        """ Return this sidecar's column metadata as a string.

        Returns:
            str: The json string representing this sidecar.

        """
        return json.dumps(self.loaded_dict, indent=4)

    def load_sidecar_file(self, file):
        """ Load column metadata from a given json file.

        Parameters:
            file (str or FileLike): If a string, this is a filename. Otherwise, it will be parsed as a file-like.

        Raises:
            HedFileError: If the file was not found or could not be parsed into JSON.
        """
        if not file:
            return {}
        elif isinstance(file, str):
            try:
                with open(file, "r") as fp:
                    if not self.name:
                        self.name = file
                    return self._load_json_file(fp)
            except FileNotFoundError as e:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, file)
            except TypeError as e:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), file)
        else:
            return self._load_json_file(file)

    def load_sidecar_files(self, files):
        """ Load json from a given file or list

        Parameters:
            files (str or FileLike or list): A string or file-like object representing a JSON file, or a list of such.
        Raises:
            HedFileError: If the file was not found or could not be parsed into JSON.
        """
        if not files:
            return {}
        if not isinstance(files, list):
            files = [files]

        merged_dict = {}
        for file in files:
            loaded_json = self.load_sidecar_file(file)
            merged_dict.update(loaded_json)
        return merged_dict

    def _load_json_file(self, fp):
        """ Load the raw json of a given file

        Parameters:
            fp (File-like): The JSON source stream.

        Raises:
            HedFileError:  If the file cannot be parsed.
        """
        try:
            return json.load(fp)
        except json.decoder.JSONDecodeError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), self.name)

    def _generate_single_column(self, column_name, dict_for_entry, column_type=None):
        """ Create a single column metadata entry and add to this sidecar.

        Parameters:
            column_name (str or int): The column name or number
            dict_for_entry (dict): The loaded dictionary for a given column entry (needs the "HED" key if nothing else).
            column_type (ColumnType): Optional indicator of how to treat the column.
                This overrides auto-detection from the dict_for_entry.

        """
        if column_type is None:
            column_type = self._detect_column_type(dict_for_entry)
        if dict_for_entry:
            hed_dict = dict_for_entry.get("HED")
        else:
            hed_dict = None
        def_removed_dict, _ = apply_ops(hed_dict, HedString.remove_definitions)
        column_entry = ColumnMetadata(column_type, column_name, def_removed_dict)
        return column_entry

    @staticmethod
    def _detect_column_type(dict_for_entry):
        """ Determine the ColumnType of a given json entry.

        Parameters:
            dict_for_entry (dict): The loaded json entry a specific column.
                Generally has a "HED" entry among other optional ones.

        Returns:
            ColumnType: The determined type of given column.  Returns None if unknown.

        """
        if not dict_for_entry or not isinstance(dict_for_entry, dict):
            return ColumnType.Ignore

        minimum_required_keys = ("HED",)
        if not set(minimum_required_keys).issubset(dict_for_entry.keys()):
            return ColumnType.Ignore

        hed_entry = dict_for_entry["HED"]
        if isinstance(hed_entry, dict):
            return ColumnType.Categorical

        if not isinstance(hed_entry, str):
            return None

        if "#" not in dict_for_entry["HED"]:
            return None

        return ColumnType.Value

    def _validate_column_structure(self, column_name, dict_for_entry, error_handler):
        """ Checks primarily for type errors such as expecting a string and getting a list in a json sidecar.

        Parameters:
            error_handler (ErrorHandler)  Sets the context for the error reporting. Cannot be None.

        Returns:
            list:  Issues in performing the operations. Each issue is a dictionary.

        """
        val_issues = []
        column_type = self._detect_column_type(dict_for_entry=dict_for_entry)
        if column_type is None:
            val_issues += ErrorHandler.format_error(SidecarErrors.UNKNOWN_COLUMN_TYPE,
                                                    column_name=column_name)
        elif column_type == ColumnType.Categorical:
            raw_hed_dict = dict_for_entry["HED"]
            if not raw_hed_dict:
                val_issues += ErrorHandler.format_error(SidecarErrors.BLANK_HED_STRING)
            if not isinstance(raw_hed_dict, dict):
                val_issues += ErrorHandler.format_error(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                        given_type=type(raw_hed_dict),
                                                        expected_type="dict")
            for key_name, hed_string in raw_hed_dict.items():
                if not isinstance(hed_string, str):
                    error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
                    val_issues += ErrorHandler.format_error(SidecarErrors.WRONG_HED_DATA_TYPE,
                                                            given_type=type(hed_string),
                                                            expected_type="str")
                    error_handler.pop_error_context()
        error_handler.add_context_to_issues(val_issues)

        return val_issues
