import copy
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema import HedSchema
from abc import abstractmethod, ABC
from hed.schema import schema_validation_util


class SchemaLoader(ABC):
    """ Baseclass for schema loading, to handle basic errors and partnered schemas

        Expected usage is SchemaLoaderXML.load(filename)

        SchemaLoaderXML(filename) will load just the header_attributes
    """
    def __init__(self, filename, schema_as_string=None):
        """Loads the given schema from one of the two parameters.

        Parameters:
            filename(str or None): A valid filepath or None
            schema_as_string(str or None): A full schema as text or None
        """
        if schema_as_string and filename:
            raise HedFileError(HedExceptions.BAD_PARAMETERS, "Invalid parameters to schema creation.",
                               filename)

        self.filename = filename
        self.schema_as_string = schema_as_string

        try:
            self.input_data = self._open_file()
        except OSError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, filename)
        except TypeError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), filename)
        except ValueError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), filename)
        
        self._schema = HedSchema()
        self._schema.filename = filename
        hed_attributes = self._get_header_attributes(self.input_data)
        schema_validation_util.validate_attributes(hed_attributes, filename=self.filename)
        self._schema.header_attributes = hed_attributes
        self._loading_merged = False

    @property
    def schema(self):
        """ The partially loaded schema if you are after just header attributes."""
        return self._schema

    @classmethod
    def load(cls, filename=None, schema_as_string=None):
        """ Loads and returns the schema, including partnered schema if applicable.

        Parameters:
            filename(str or None): A valid filepath or None
            schema_as_string(str or None): A full schema as text or None
        Returns:
            schema(HedSchema): The new schema
        """
        loader = cls(filename, schema_as_string)
        return loader._load()

    def _load(self):
        """ Parses the previously loaded data, including loading a partnered schema if needed.

        Returns:
            schema(HedSchema): The new schema
        """
        self._loading_merged = True
        # Do a full load of the standard schema if this is a partnered schema
        if self._schema.with_standard and not self._schema.merged:
            from hed.schema.hed_schema_io import load_schema_version
            saved_attr = self._schema.header_attributes
            try:
                base_version = load_schema_version(self._schema.with_standard)
            except HedFileError as e:
                raise HedFileError(HedExceptions.BAD_WITH_STANDARD_VERSION,
                                   message=f"Cannot load withStandard schema '{self._schema.with_standard}'",
                                   filename=e.filename)
            # Copy the non-alterable cached schema
            self._schema = copy.deepcopy(base_version)
            self._schema.filename = self.filename
            self._schema.header_attributes = saved_attr
            self._loading_merged = False

        self._parse_data()
        self._schema.finalize_dictionaries()

        return self._schema

    @abstractmethod
    def _open_file(self):
        """Overloaded versions should retrieve the input from filename/schema_as_string"""
        pass

    @abstractmethod
    def _get_header_attributes(self, input_data):
        """Overloaded versions should return the header attributes from the input data."""
        pass

    @abstractmethod
    def _parse_data(self):
        """Puts the input data into the new schema"""
        pass
