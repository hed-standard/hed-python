import copy

from hed.schema.schema_io import schema_util
from hed.errors.exceptions import HedFileError, HedExceptions

from hed.schema.hed_schema import HedSchema
from hed.schema import hed_schema_constants as constants
from hed.schema.hed_schema_constants import HedKey
from abc import abstractmethod, ABC
from hed.schema import schema_header_util
from hed.schema import hed_schema_constants
from hed.schema.schema_io import df_constants


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
            schema(HedSchema or None): A HED schema to merge this new file into
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
        schema_header_util.validate_attributes(hed_attributes, name=self.name)

        with_standard = hed_attributes.get(hed_schema_constants.WITH_STANDARD_ATTRIBUTE, "")
        self.library = hed_attributes.get(hed_schema_constants.LIBRARY_ATTRIBUTE, "")
        version_number = hed_attributes.get(hed_schema_constants.VERSION_ATTRIBUTE, "")
        if not schema:
            self._schema = HedSchema()
        else:
            self._schema = schema
            self.appending_to_schema = True
            if not self._schema.with_standard:
                raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_PREFIX,
                                   "Loading multiple normal schemas as a merged one with the same namespace.  "
                                   "Ensure schemas have the withStandard header attribute set",
                                   self.name)
            elif with_standard != self._schema.with_standard:
                raise HedFileError(HedExceptions.BAD_WITH_STANDARD_MULTIPLE_VALUES,
                   f"Merging schemas requires same withStandard value ({with_standard} != {self._schema.with_standard}).",
                                   self.name)
            hed_attributes[hed_schema_constants.VERSION_ATTRIBUTE] = self._schema.version_number + f",{version_number}"
            hed_attributes[hed_schema_constants.LIBRARY_ATTRIBUTE] = self._schema.library + f",{self.library}"
        if name:
            self._schema.name = name
        self._schema.filename = filename
        self._schema.header_attributes = hed_attributes
        self._loading_merged = False
        self.fatal_errors = []

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
            schema(HedSchema or None): A HED schema to merge this new file into
                           It must be a with-standard schema with the same value.
            file_format(str or None): If this is an owl file being loaded, this is the format.
                Allowed values include: turtle, json-ld, and owl(xml)
            name(str or None): Optional user supplied identifier, by default uses filename

        Returns:
            HedSchema: The new schema
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
            saved_format = self._schema.source_format
            try:
                base_version = load_schema_version(self._schema.with_standard)
            except HedFileError as e:
                raise HedFileError(HedExceptions.BAD_WITH_STANDARD,
                                   message=f"Cannot load withStandard schema '{self._schema.with_standard}'",
                                   filename=e.filename)
            # Copy the non-alterable cached schema
            self._schema = copy.deepcopy(base_version)
            self._schema.filename = self.filename
            self._schema.name = self.name  # Manually set name here as we don't want to pass it to load_schema_version
            self._schema.header_attributes = saved_attr
            self._schema.source_format = saved_format
            self._loading_merged = False

        self._parse_data()
        self._schema.finalize_dictionaries()
        self.fix_extras()
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

        if self.library and (
                not self._schema.with_standard or (not self._schema.merged and self._schema.with_standard)):
            # only add it if not already present - This is a rare case
            if not entry.has_attribute(HedKey.InLibrary):
                entry._set_attribute_value(HedKey.InLibrary, self.library)

        return self._schema._add_tag_to_dict(entry.name, entry, key_class)

    @staticmethod
    def find_rooted_entry(tag_entry, schema, loading_merged):
        """ This semi-validates rooted tags, raising an exception on major errors

        Parameters:
            tag_entry(HedTagEntry): the possibly rooted tag
            schema(HedSchema): The schema being loaded
            loading_merged(bool): If this schema was already merged before loading

        Returns:
            Union[HedTagEntry, None]: The base tag entry from the standard schema
                Returns None if this tag isn't rooted

        :raises HedFileError:
            - A rooted attribute is found in a non-paired schema
            - A rooted attribute is not a string
            - A rooted attribute was found on a non-root node in an unmerged schema.
            - A rooted attribute is found on a root node in a merged schema.
            - A rooted attribute indicates a tag that doesn't exist in the base schema.
        """
        rooted_tag = tag_entry.has_attribute(constants.HedKey.Rooted, return_value=True)
        if rooted_tag is not None:
            if not schema.with_standard:
                raise HedFileError(HedExceptions.ROOTED_TAG_INVALID,
                                   f"Rooted tag attribute found on '{tag_entry.short_tag_name}' in a standard schema.",
                                   schema.name)

            if not isinstance(rooted_tag, str):
                raise HedFileError(HedExceptions.ROOTED_TAG_INVALID,
                                   f'Rooted tag \'{tag_entry.short_tag_name}\' is not a string."',
                                   schema.name)

            if tag_entry.parent_name and not loading_merged:
                raise HedFileError(HedExceptions.ROOTED_TAG_INVALID,
                                   f'Found rooted tag \'{tag_entry.short_tag_name}\' as a non root node.',
                                   schema.name)

            if not tag_entry.parent_name and loading_merged:
                raise HedFileError(HedExceptions.ROOTED_TAG_INVALID,
                                   f'Found rooted tag \'{tag_entry.short_tag_name}\' as a root node in a merged schema.',
                                   schema.name)

            rooted_entry = schema.tags.get(rooted_tag)
            if not rooted_entry or rooted_entry.has_attribute(constants.HedKey.InLibrary):
                raise HedFileError(HedExceptions.ROOTED_TAG_DOES_NOT_EXIST,
                                   f"Rooted tag '{tag_entry.short_tag_name}' not found in paired standard schema",
                                   schema.name)

            if loading_merged:
                return None

            return rooted_entry
        return None

    def _add_fatal_error(self, line_number, line, warning_message="Schema term is empty or the line is malformed",
                         error_code=HedExceptions.WIKI_DELIMITERS_INVALID):
        self.fatal_errors += schema_util.format_error(line_number, line, warning_message, error_code)


    def fix_extras(self):
        """ Fixes the extras after loading the schema, to ensure they are in the correct format."""
        if not self._schema or not hasattr(self._schema, 'extras') or not self._schema.extras:
            return

        for key, extra in self._schema.extras.items():
            self._schema.extras[key] = extra.rename(columns=df_constants.EXTRAS_CONVERSIONS)
            if key in df_constants.extras_column_dict:
               self._schema.extras[key] = self.fix_extra(key)

    def fix_extra(self, key):
        df = self._schema.extras[key]
        priority_cols = df_constants.extras_column_dict[key]
        col_to_add = [col for col in priority_cols if col not in df.columns]
        if col_to_add:
            df[col_to_add] = ""
        other_cols = sorted(set(df.columns) - set(priority_cols))
        df = df[priority_cols + other_cols]
        df = df.sort_values(by=list(df.columns))
        return df