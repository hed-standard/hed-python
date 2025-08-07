""" Contents of a JSON file or merged JSON files. """
import json
import re

from hed.models.column_metadata import ColumnMetadata
from hed.errors.error_types import ErrorContext
from hed.errors import ErrorHandler
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.models.hed_string import HedString
from hed.models.column_metadata import ColumnType
from hed.models.definition_dict import DefinitionDict


class Sidecar:
    """ Contents of a JSON file or JSON files.

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
        return iter(self.column_data.values())

    def __getitem__(self, column_name):
        if column_name not in self.loaded_dict:
            return None
        return ColumnMetadata(name=column_name)

    @property
    def all_hed_columns(self) -> list[str]:
        """ Return all columns that are HED compatible.

        Returns:
            list: A list of all valid HED columns by name.
        """
        possible_column_references = [column.column_name for column in self if column.column_type != ColumnType.Ignore]

        return possible_column_references

    @property
    def def_dict(self) -> 'DefinitionDict':
        """ Definitions from this sidecar.

            Generally you should instead call get_def_dict to get the relevant definitions.

        Returns:
            DefinitionDict: The definitions for this sidecar.
        """
        return self._def_dict

    @property
    def column_data(self):
        """ Generate the ColumnMetadata for this sidecar.

        Returns:
            dict({str:ColumnMetadata}): The column metadata defined by this sidecar.
        """
        return {col_name: ColumnMetadata(name=col_name, source=self.loaded_dict) for col_name in self.loaded_dict}

    def get_def_dict(self, hed_schema, extra_def_dicts=None) -> 'DefinitionDict':
        """ Return the definition dict for this sidecar.

        Parameters:
            hed_schema (HedSchema): Identifies tags to find definitions.
            extra_def_dicts (list, DefinitionDict, or None): Extra dicts to add to the list.

        Returns:
            DefinitionDict:  A single definition dict representing all the data(and extra def dicts).
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
            save_filename (str): Path to save file.

        """
        with open(save_filename, "w") as fp:
            json.dump(self.loaded_dict, fp, indent=4)

    def get_as_json_string(self) -> str:
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
            if not self.name:
                self.name = file
            try:
                with open(file, "r") as fp:
                    return self._load_json_file(fp)
            except OSError as e:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, file) from e
        else:
            return self._load_json_file(file)

    def load_sidecar_files(self, files):
        """ Load json from a given file or list.

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

    def validate(self, hed_schema, extra_def_dicts=None, name=None, error_handler=None) -> list[dict]:
        """Create a SidecarValidator and validate this sidecar with the schema.

        Parameters:
            hed_schema (HedSchema): Input data to be validated.
            extra_def_dicts (list or DefinitionDict): Extra def dicts in addition to sidecar.
            name (str): The name to report this sidecar as.
            error_handler (ErrorHandler): Error context to use.  Creates a new one if None.

        Returns:
            list[dict]: A list of issues associated with each level in the HED string.
        """
        from hed.validator.sidecar_validator import SidecarValidator

        if error_handler is None:
            error_handler = ErrorHandler()

        validator = SidecarValidator(hed_schema)
        issues = validator.validate(self, extra_def_dicts, name, error_handler=error_handler)
        return issues

    def _load_json_file(self, fp):
        """ Load the raw json of a given file.

        Parameters:
            fp (File-like): The JSON source stream.

        Raises:
            HedFileError: If the file cannot be parsed.
        """
        try:
            return json.load(fp)
        except (json.decoder.JSONDecodeError, AttributeError) as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), self.name) from e

    def extract_definitions(self, hed_schema, error_handler=None) -> 'DefinitionDict':
        """ Gather and validate definitions in metadata.

        Parameters:
            hed_schema (HedSchema): The schema to used to identify tags.
            error_handler (ErrorHandler or None): The error handler to use for context, uses a default one if None.

        Returns:
            DefinitionDict: Contains all the definitions located in the sidecar.

        """
        if error_handler is None:
            error_handler = ErrorHandler()
        def_dict = DefinitionDict()

        self._extract_definition_issues = []
        if hed_schema:
            for column_data in self:
                error_handler.push_error_context(ErrorContext.SIDECAR_COLUMN_NAME, column_data.column_name)
                hed_strings = column_data.get_hed_strings()
                for key_name, hed_string in hed_strings.items():
                    hed_string_obj = HedString(hed_string, hed_schema)
                    if len(hed_strings) > 1:
                        error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
                    error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj)
                    self._extract_definition_issues += def_dict.check_for_definitions(hed_string_obj, error_handler)
                    error_handler.pop_error_context()
                    if len(hed_strings) > 1:
                        error_handler.pop_error_context()

                error_handler.pop_error_context()

        return def_dict

    def get_column_refs(self) -> list[str]:
        """ Returns a list of column refs found in this sidecar.

            This does not validate

        Returns:
            list[str]: A list of unique column refs found.
        """
        found_vals = set()
        for column_data in self:
            if column_data.column_type == ColumnType.Ignore:
                continue
            hed_strings = column_data.get_hed_strings()
            matches = hed_strings.str.findall(r"\{([a-z_\-0-9]+)\}", re.IGNORECASE)
            u_vals = [match for sublist in matches for match in sublist]

            found_vals.update(u_vals)

        return list(found_vals)
