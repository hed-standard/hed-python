"""
"""

# todo: Switch various properties to this cached_property once we require python 3.8

from hed.errors.exceptions import HedExceptions, HedFileError
from hed.errors import ErrorHandler, ValidationErrors
from hed.schema.hed_schema_constants import HedSectionKey


class HedSchemaGroup:
    """
        This class handles combining multiple HedSchema objects for validation and analysis.

        You cannot save/load/etc the combined schema object directly.
    """
    def __init__(self, schema_list):
        """
        Create combination of multiple HedSchema objects you can use with the hed tags.

        Note: will raise HedFileError if two schemas share the same name_prefix

        Parameters
        ----------
        Returns
        -------
        HedSchemaGroup
            A HedSchemaCombined object.
        """
        library_prefixes = [hed_schema._library_prefix for hed_schema in schema_list]
        if len(set(library_prefixes)) != len(library_prefixes):
            raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_PREFIX,
                               "Multiple schemas share the same tag name_prefix.  This is not allowed.",
                               filename="Combined Schema")
        self._schemas = {hed_schema._library_prefix: hed_schema for hed_schema in schema_list}

    # ===============================================
    # General schema properties/functions
    # ===============================================
    @property
    def has_duplicate_tags(self):
        """
        Returns True if this is a valid hed3 schema with no duplicate short tags.

        Returns
        -------
        bool
            Returns True if this is a valid hed3 schema with no duplicate short tags.
        """
        return any([schema.has_duplicate_tags for schema in self._schemas.values()])

    @property
    def unit_classes(self):
        return all([schema.unit_classes for schema in self._schemas.values()])

    @property
    def is_hed3_compatible(self):
        return all([schema.is_hed3_compatible for schema in self._schemas.values()])

    @property
    def is_hed3_schema(self):
        # All combined schemas are implicitly hed3.
        return True

    @property
    def unit_modifiers(self):
        return all([schema.unit_modifiers for schema in self._schemas.values()])

    @property
    def value_classes(self):
        return all([schema.value_classes for schema in self._schemas.values()])

    def __eq__(self, other):
        return self._schemas == other._schemas

    def schema_for_prefix(self, prefix):
        """
            Return the specific HedSchema object for the given tag name_prefix.

            Returns None if name_prefix is invalid.

        Parameters
        ----------
        prefix : str
            A schema library name_prefix to get the schema for.

        Returns
        -------
        schema: HedSchema
            The specific schema for this library name_prefix
        """
        schema = self._schemas.get(prefix)
        return schema

    @property
    def valid_prefixes(self):
        """
            Gets a list of all prefixes this schema will accept.

        Returns
        -------
        valid_prefixes: [str]
            A list of valid tag prefixes for this schema.
        """
        return list(self._schemas.keys())

    def check_compliance(self, also_check_for_warnings=True, name=None,
                         error_handler=None):
        """
            Checks for hed3 compliance of this schema.

        Parameters
        ----------
        also_check_for_warnings : bool, default True
            If True, also checks for formatting issues like invalid characters, capitalization, etc.
        name: str
            If present, will use this as the filename for context, rather than using the actual filename
            Useful for temp filenames.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        issue_list : [{}]
            A list of all warnings and errors found in the file.
        """
        issues_list = []
        for schema in self._schemas.values():
            issues_list += schema.check_compliance(also_check_for_warnings, name, error_handler)
        return issues_list

    def get_all_tags_with_attribute(self, key):
        all_tags = set()
        for schema in self._schemas.values():
            all_tags.update(schema.get_all_tags_with_attribute(key))
        return all_tags

    # todo: maybe tweak this API so you don't have to pass in library prefix?
    def get_tag_entry(self, name, key_class=HedSectionKey.AllTags, library_prefix=""):
        """
            Returns the schema entry for this tag, if one exists.

        Parameters
        ----------
        name : str
            Any form of basic tag(or other section entry) to look up.  This will not handle extensions or similar.
        key_class : HedSectionKey

        Returns
        -------
        tag_entry: HedSchemaEntry
            The schema entry for the given tag.
        """
        specific_schema = self.schema_for_prefix(library_prefix)
        if not specific_schema:
            validation_issues = ErrorHandler.format_error(ValidationErrors.HED_UNKNOWN_PREFIX, name,
                                                          library_prefix, self.valid_prefixes)
            return None, None, validation_issues

        return specific_schema.get_tag_entry(name, key_class, library_prefix)

    def find_tag_entry(self, tag, library_prefix=""):
        """
        This takes a source tag and finds the schema entry for it.

        Works right to left.(mostly relevant for errors)

        Parameters
        ----------
        tag : str or HedTag
            Any form of tag to look up.  Can have an extension, value, etc.
        library_prefix: str
            The prefix the library, if any.

        Returns
        -------
        tag_entry: HedTagEntry
            The located tag entry for this tag.
        remainder: str
            The remainder of the tag that isn't part of the base tag.
        errors: list
            a list of errors while converting
        """
        specific_schema = self.schema_for_prefix(library_prefix)
        if not specific_schema:
            validation_issues = ErrorHandler.format_error(ValidationErrors.HED_UNKNOWN_PREFIX, tag,
                                                          library_prefix, self.valid_prefixes)
            return None, None, validation_issues

        return specific_schema.find_tag_entry(tag, library_prefix)
