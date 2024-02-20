import copy
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema import HedSchema
from hed.schema.hed_schema_constants import HedKey
from abc import abstractmethod, ABC
from hed.schema import schema_validation_util
from hed.schema import hed_schema_constants


class SchemaLoader(ABC):
    """ Baseclass for schema loading, to handle basic errors and partnered schemas

        Expected usage is SchemaLoaderXML.load(filename)

        SchemaLoaderXML(filename) will load just the header_attributes
    """
    def __init__(self, filename, schema_as_string=None, schema=None, file_format=None, name=""):
        """Loads the given schema from one of the two parameters.

        Parameters:
            filename(str or None): A valid filepath or None
            schema_as_string(str or None): A full schema as text or None
            schema(HedSchema or None): A hed schema to merge this new file into
                                       It must be a with-standard schema with the same value.
            file_format(str or None): The format of this file if needed(only for owl currently)
            name(str or None): Optional user supplied identifier, by default uses filename
        """
        if schema_as_string and filename:
            raise HedFileError(HedExceptions.BAD_PARAMETERS, "Invalid parameters to schema creation.",
                               filename)
        self.file_format = file_format
        self.filename = filename
        self.name = name if name else filename
        self.schema_as_string = schema_as_string
        self.appending_to_schema = False
        try:
            self.input_data = self._open_file()
        except OSError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, self.name)
        except TypeError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), self.name)
        except ValueError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), self.name)

        # self._schema.filename = filename
        hed_attributes = self._get_header_attributes(self.input_data)
        schema_validation_util.validate_attributes(hed_attributes, name=self.name)

        withStandard = hed_attributes.get(hed_schema_constants.WITH_STANDARD_ATTRIBUTE, "")
        self.library = hed_attributes.get(hed_schema_constants.LIBRARY_ATTRIBUTE, "")
        version_number = hed_attributes.get(hed_schema_constants.VERSION_ATTRIBUTE, "")
        if not schema:
            self._schema = HedSchema()
        else:
            self._schema = schema
            self.appending_to_schema = True
            if not self._schema.with_standard:
                raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_PREFIX,
                                   "Trying to load multiple normal schemas as a merged one with the same namespace.  "
                                   "Ensure schemas have the withStandard header attribute set",
                                   self.name)
            elif withStandard != self._schema.with_standard:
                raise HedFileError(HedExceptions.BAD_WITH_STANDARD_VERSION,
                                   "When merging two schemas without a schema namespace, you they must have the same withStandard value.", self.name)
            hed_attributes[hed_schema_constants.VERSION_ATTRIBUTE] = self._schema.version_number + f",{version_number}"
            hed_attributes[hed_schema_constants.LIBRARY_ATTRIBUTE] = self._schema.library + f",{self.library}"
        if name:
            self._schema.name = name
        self._schema.filename = filename
        self._schema.header_attributes = hed_attributes
        self._loading_merged = False

    @property
    def schema(self):
        """ The partially loaded schema if you are after just header attributes."""
        return self._schema

    @classmethod
    def load(cls, filename=None, schema_as_string=None, schema=None, file_format=None, name=""):
        """ Loads and returns the schema, including partnered schema if applicable.

        Parameters:
            filename(str or None): A valid filepath or None
            schema_as_string(str or None): A full schema as text or None
            schema(HedSchema or None): A hed schema to merge this new file into
                           It must be a with-standard schema with the same value.
            file_format(str or None): If this is an owl file being loaded, this is the format.
                Allowed values include: turtle, json-ld, and owl(xml)
            name(str or None): Optional user supplied identifier, by default uses filename
        Returns:
            schema(HedSchema): The new schema
        """
        loader = cls(filename, schema_as_string, schema, file_format, name)
        return loader._load()

    def _load(self):
        """ Parses the previously loaded data, including loading a partnered schema if needed.

        Returns:
            schema(HedSchema): The new schema
        """
        self._loading_merged = True
        # Do a full load of the standard schema if this is a partnered schema
        if not self.appending_to_schema and self._schema.with_standard and not self._schema.merged:
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
            self._schema.name = self.name  # Manually set name here as we don't want to pass it to load_schema_version
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

    def _add_to_dict_base(self, entry, key_class):
        if not entry.has_attribute(HedKey.InLibrary) and self.appending_to_schema and self._schema.merged:
            return None

        if self.library and (not self._schema.with_standard or (not self._schema.merged and self._schema.with_standard)):
            # only add it if not already present - This is a rare case
            if not entry.has_attribute(HedKey.InLibrary):
                entry._set_attribute_value(HedKey.InLibrary, self.library)

        return self._schema._add_tag_to_dict(entry.name, entry, key_class)
