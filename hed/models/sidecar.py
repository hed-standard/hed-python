import json
from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_types import ErrorContext
from hed.errors import ErrorHandler
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.models.hed_string import HedString
from hed.models.column_metadata import ColumnType
from hed.models.definition_dict import DefinitionDict


# todo: Add/improve validation for definitions being in known columns(right now it just assumes they aren't)
class Sidecar:
    """ Contents of a JSON file or merged file.

    """

    def __init__(self, files, name=None):
        """ Construct a Sidecar object representing a JSON file.

        Parameters:
            files (str or FileLike or list): A string or file-like object representing a JSON file, or a list of such.
            name (str or None): Optional name identifying this sidecar, generally a filename.
        """
        self.name = name
        self.loaded_dict = self.load_sidecar_files(files)
        self._def_dict = None
        self._extract_definition_issues = []

    def __iter__(self):
        """ An iterator to go over the individual column metadata.

        Returns:
            iterator: An iterator over the column metadata values.

        """
        return iter(self.column_data)

    @property
    def def_dict(self):
        """This is the definitions from this sidecar.

            Generally you should instead call get_def_dict to get the relevant definitions

        Returns:
            DefinitionDict: The definitions for this sidecar
        """
        return self._def_dict

    @property
    def column_data(self):
        """ Generates the list of ColumnMetadata for this sidecar

        Returns:
            list(ColumnMetadata): the list of column metadata defined by this sidecar
        """
        for col_name, col_dict in self.loaded_dict.items():
            yield self._generate_single_column(col_name, col_dict)

    def set_hed_string(self, new_hed_string, position):
        """ Set a provided column/category key/etc.

        Parameters:
            new_hed_string (str or HedString): The new hed_string to replace the value at position.
            position (tuple):   The (HedString, str, list) tuple returned from hed_string_iter.

        """
        column_name, position = position
        hed_dict = self.loaded_dict[column_name]
        hed_dict["HED"] = self._set_hed_string_low(new_hed_string, hed_dict["HED"], position)

    def get_def_dict(self, hed_schema=None, extra_def_dicts=None):
        """ Returns the definition dict for this sidecar.

        Parameters:
            hed_schema(HedSchema): used to identify tags to find definitions
            extra_def_dicts (list, DefinitionDict, or None): Extra dicts to add to the list.

        Returns:
            DefinitionDict:   A single definition dict representing all the data(and extra def dicts)
        """
        if self._def_dict is None and hed_schema:
            self._def_dict = self.extract_definitions(hed_schema)
        def_dicts = []
        if self.def_dict:
            def_dicts.append(self.def_dict)
        if extra_def_dicts:
            if not isinstance(extra_def_dicts, list):
                extra_def_dicts = [extra_def_dicts]
            def_dicts += extra_def_dicts
        return DefinitionDict(def_dicts)

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

    def validate(self, hed_schema, extra_def_dicts=None, name=None, error_handler=None):
        """Create a SidecarValidator and validate this sidecar with the schema.

        Parameters:
            hed_schema (HedSchema): Input data to be validated.
            extra_def_dicts(list or DefinitionDict): Extra def dicts in addition to sidecar.
            name(str): The name to report this sidecar as.
            error_handler (ErrorHandler): Error context to use.  Creates a new one if None.
            
        Returns:
            issues (list of dict): A list of issues associated with each level in the HED string.
        """
        from hed.validator.sidecar_validator import SidecarValidator

        if error_handler is None:
            error_handler = ErrorHandler()

        validator = SidecarValidator(hed_schema)
        issues = validator.validate(self, extra_def_dicts, name, error_handler=error_handler)
        return issues

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
        column_entry = ColumnMetadata(column_type, column_name, hed_dict)
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

    def extract_definitions(self, hed_schema=None, error_handler=None):
        """ Gather and validate definitions in metadata.

        Parameters:
            error_handler (ErrorHandler): The error handler to use for context, uses a default one if None.
            hed_schema (HedSchema or None): The schema to used to identify tags.

        Returns:
            DefinitionDict: Contains all the definitions located in the sidecar.

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        def_dict = DefinitionDict()

        self._extract_definition_issues = []
        if hed_schema:
            for hed_string, column_data, _ in self.hed_string_iter(error_handler):
                hed_string_obj = HedString(hed_string, hed_schema)
                error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj)
                self._extract_definition_issues += def_dict.check_for_definitions(hed_string_obj, error_handler)
                error_handler.pop_error_context()

        return def_dict

    def hed_string_iter(self, error_handler=None):
        """ Gather and validate definitions in metadata.

        Parameters:
            error_handler (ErrorHandler): The error handler to use for context, uses a default one if None.

        Yields:
            str: The hed string at a given column and key position.
            column_data: the column data for the given string.
            position: blackbox(pass back to set this string to a new value)

        """
        if error_handler is None:
            error_handler = ErrorHandler()

        for column_data in self.column_data:
            error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_data.column_name)
            hed_dict = column_data.hed_dict
            for (hed_string, position) in self._hed_string_iter(hed_dict, error_handler):
                yield hed_string, column_data, position
            error_handler.pop_error_context()

    @staticmethod
    def _hed_string_iter(hed_strings, error_handler):
        """ Iterate over the given dict of strings

        Parameters:
            hed_strings(dict or str): A hed_string or dict of hed strings
            error_handler (ErrorHandler): The error handler to use for context, uses a default one if none.

        Yields:
            tuple:
                - str: The hed string at a given column and key position.
                - str: Indication of the where hed string was loaded from, so it can be later set by the user.

        """
        for hed_string, key_name in Sidecar._hed_iter_low(hed_strings):
            if key_name:
                error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
            yield hed_string, key_name
            if key_name:
                error_handler.pop_error_context()

    @staticmethod
    def _hed_iter_low(hed_strings):
        """ Iterate over the hed string entries.

            Used by hed_string_iter

        Parameters:
            hed_strings(dict or str): A hed_string or dict of hed strings

        Yields:
            tuple:
                - str: Individual hed strings for different entries.
                - str: The position to pass back to set this string.

        """
        if isinstance(hed_strings, dict):
            for key, hed_string in hed_strings.items():
                if not isinstance(hed_string, str):
                    continue
                yield hed_string, key
        elif isinstance(hed_strings, str):
            yield hed_strings, None

    @staticmethod
    def _set_hed_string_low(new_hed_string, hed_strings, position=None):
        """ Set a hed string for a category key/etc.

        Parameters:
            new_hed_string (str or HedString): The new hed_string to replace the value at position.
            hed_strings(dict or str or HedString): The hed strings we want to update
            position (str, optional): This should only be a value returned from hed_string_iter.

        Returns:
            updated_string (str or dict): The newly updated string/dict.
        Raises:
            TypeError: If the mapping cannot occur.

        """
        if isinstance(hed_strings, dict):
            if position is None:
                raise TypeError("Error: Trying to set a category HED string with no category")
            if position not in hed_strings:
                raise TypeError("Error: Not allowed to add new categories to a column")
            hed_strings[position] = str(new_hed_string)
        elif isinstance(hed_strings, (str, HedString)):
            if position is not None:
                raise TypeError("Error: Trying to set a value HED string with a category")
            hed_strings = str(new_hed_string)
        else:
            raise TypeError("Error: Trying to set a HED string on a column_type that doesn't support it.")

        return hed_strings
