"""
"""

# todo: Switch various properties to this cached_property once we require python 3.8

import json
from hed.errors.exceptions import HedExceptions, HedFileError
from hed.errors import ErrorHandler, ValidationErrors
from hed.schema.hed_schema_constants import HedSectionKey


class HedSchemaGroup:
    """ Container for multiple HedSchema objects.

    Notes:
        - The container class is useful when library schema are included.
        - You cannot save/load/etc the combined schema object directly.

    """
    def __init__(self, schema_list):
        """ Combine multiple HedSchema objects from a list.

        Parameters:
            schema_list (list): A list of HedSchema for the container.

        Returns:
            HedSchemaGroup: the container created.

        Raises:
            HedFileError:  If multiple schemas have the same library prefixes.

        """
        if len(schema_list) == 0:
            raise HedFileError(HedExceptions.BAD_PARAMETERS, "Empty list passed to HedSchemaGroup constructor.",
                               filename="Combined Schema")
        schema_prefixes = [hed_schema._schema_prefix for hed_schema in schema_list]
        if len(set(schema_prefixes)) != len(schema_prefixes):
            raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_PREFIX,
                               "Multiple schema share the same tag name_prefix.  This is not allowed.",
                               filename="Combined Schema")
        self._schemas = {hed_schema._schema_prefix: hed_schema for hed_schema in schema_list}

    # ===============================================
    # General schema properties/functions
    # ===============================================

    def get_formatted_version(self, as_string=True):
        x = [schema.get_formatted_version() for schema in self._schemas.values()]
        if as_string:
            return json.dumps(x)
        return x

    @property
    def has_duplicate_tags(self):
        """ Return True if valid hed3 schema with no duplicate short tags.

        Returns:
            bool: True if this is a valid hed3 schema with no duplicate short tags.

        """
        return any([schema.has_duplicate_tags for schema in self._schemas.values()])

    @property
    def unit_classes(self):
        """ A list of all unit classes represented in this group. """
        return all([schema.unit_classes for schema in self._schemas.values()])

    @property
    def is_hed3_compatible(self):
        """ A list of HED3-compliant schemas in this group. """
        return all([schema.is_hed3_compatible for schema in self._schemas.values()])

    @property
    def is_hed3_schema(self):
        """ HedSchemaGroup objects are always HED3."""
        return True

    @property
    def unit_modifiers(self):
        """ Return a list of all unit modifiers for all schema. """
        return all([schema.unit_modifiers for schema in self._schemas.values()])

    @property
    def value_classes(self):
        return all([schema.value_classes for schema in self._schemas.values()])

    def __eq__(self, other):
        return self._schemas == other._schemas

    def schema_for_prefix(self, prefix):
        """ Return the HedSchema for the library prefix.

        Parameters:
            prefix (str): A schema library name prefix.

        Returns:
            HedSchema or None: The specific schema for this library name prefix if exists.

        """
        schema = self._schemas.get(prefix)
        return schema

    @property
    def valid_prefixes(self):
        """ Return a list of all prefixes this group will accept.

        Returns:
            list:  A list of strings representing valid prefixes for this group.

        """
        return list(self._schemas.keys())

    def check_compliance(self, check_for_warnings=True, name=None, error_handler=None):
        """ Check for hed3 compliance of this schema.

        Parameters:
            check_for_warnings (bool): If True, checks for formatting issues like invalid characters, capitalization.
            name (str): If present, use as the filename for context, rather than using the actual filename.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.

        Returns:
            list: A list of all warnings and errors found in the file. Each issue is a dictionary.

        Notes:
            - Useful for temp filenames when supporting web services.

        """
        issues_list = []
        for schema in self._schemas.values():
            issues_list += schema.check_compliance(check_for_warnings, name, error_handler)
        return issues_list

    def get_tags_with_attribute(self, key):
        """ Return the tags with this attribute.

        Parameters:
            key (str): The attributes.

        """
        all_tags = set()
        for schema in self._schemas.values():
            all_tags.update(schema.get_tags_with_attribute(key))
        return all_tags

    # todo: maybe tweak this API so you don't have to pass in library prefix?
    def get_tag_entry(self, name, key_class=HedSectionKey.AllTags, schema_prefix=""):
        """ Return the schema entry for this tag, if one exists.

        Parameters:
            name (str): Any form of basic tag(or other section entry) to look up.
            key_class (HedSectionKey): The tag section to search.
            schema_prefix (str or None): An optional prefix associated with this tag.

        Returns:
            HedSchemaEntry:  The schema entry for the given tag.

        Notes:
            - This will not handle extensions or similar.

        """
        specific_schema = self.schema_for_prefix(schema_prefix)
        if not specific_schema:
            return None

        return specific_schema.get_tag_entry(name, key_class, schema_prefix)

    def find_tag_entry(self, tag, schema_prefix=""):
        """ Find a schema entry for a source tag.

        Parameters:
            tag (str or HedTag): Any form of tag to look up.  Can have an extension, value, etc.
            schema_prefix (str): The prefix the library, if any.

        Returns:
            tuple:
                - HedTagEntry: The located tag entry for this tag.
                - str: The remainder of the tag that isn't part of the base tag.
                - list: A list of errors while converting.

        Notes:
            - Works right to left.(mostly relevant for errors).

        """
        specific_schema = self.schema_for_prefix(schema_prefix)
        if not specific_schema:
            validation_issues = ErrorHandler.format_error(ValidationErrors.HED_LIBRARY_UNMATCHED, tag,
                                                          schema_prefix, self.valid_prefixes)
            return None, None, validation_issues

        return specific_schema._find_tag_entry(tag, schema_prefix)
