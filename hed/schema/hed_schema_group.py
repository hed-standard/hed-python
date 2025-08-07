"""
"""


from __future__ import annotations

import json
from typing import Union

from hed.schema.hed_schema import HedSchema
from hed.errors.exceptions import HedExceptions, HedFileError
from hed.errors import ErrorHandler, ValidationErrors
from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.hed_schema_base import HedSchemaBase


class HedSchemaGroup(HedSchemaBase):
    """ Container for multiple HedSchema objects.

    Notes:
        - The container class is useful when library schema are included.
        - You cannot save/load/etc. the combined schema object directly.

    """
    def __init__(self, schema_list, name=""):
        """ Combine multiple HedSchema objects from a list.

        Parameters:
            schema_list (list): A list of HedSchema for the container.

        Returns:
            HedSchemaGroup: the container created.

        Raises
            HedFileError: If multiple schemas have the same library prefixes or empty list passed.

        """
        super().__init__()
        if len(schema_list) == 0:
            raise HedFileError(HedExceptions.BAD_PARAMETERS, "Empty list passed to HedSchemaGroup constructor.",
                               filename=self.name)
        schema_prefixes = [hed_schema._namespace for hed_schema in schema_list]
        if len(set(schema_prefixes)) != len(schema_prefixes):
            raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_PREFIX,
                               "Multiple schema share the same tag name_prefix.  This is not allowed.",
                               filename=self.name)
        self._schemas = {hed_schema._namespace: hed_schema for hed_schema in schema_list}
        source_formats = [hed_schema.source_format for hed_schema in schema_list]
        # All must be same source format or return None.
        self.source_format = source_formats[0] if len(set(source_formats)) == 1 else None
        self._name = name

    def get_schema_versions(self) -> list[str]:
        """ A list of HED version strings including namespace and library name if any for these schemas.

        Returns:
            list[str]: The complete version of this schema including library name and namespace.
        """
        return [schema.version for schema in self._schemas.values()]

    def get_formatted_version(self) -> str:
        """ The HED version string including namespace and library name if any of this schema.

        Returns:
            str: The complete version of this schema including library name and namespace.
        """
        return json.dumps(self.get_schema_versions())

    def __eq__(self, other):
        return self._schemas == other._schemas

    def schema_for_namespace(self, namespace) -> Union[HedSchema,None]:
        """ Return the HedSchema for the library namespace.

        Parameters:
            namespace (str): A schema library name namespace.

        Returns:
            Union[HedSchema, None]: The specific schema for this library name namespace if exists.

        """
        schema = self._schemas.get(namespace)
        return schema

    @property
    def valid_prefixes(self) -> list[str]:
        """ Return a list of all prefixes this group will accept.

        Returns:
            list[str]:  A list of strings representing valid prefixes for this group.

        """
        return list(self._schemas.keys())

    def check_compliance(self, check_for_warnings=True, name=None, error_handler=None) -> list[dict]:
        """ Check for HED3 compliance of this schema.

        Parameters:
            check_for_warnings (bool): If True, checks for formatting issues like invalid characters, capitalization.
            name (str): If present, use as the filename for context, rather than using the actual filename.
                        Useful for temp filenames when supporting web services.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.

        Returns:
            list[dict]: A list of all warnings and errors found in the file. Each issue is a dictionary.
        """
        issues_list = []
        for schema in self._schemas.values():
            issues_list += schema.check_compliance(check_for_warnings, name, error_handler)
        return issues_list

    def get_tags_with_attribute(self, attribute, key_class=HedSectionKey.Tags) -> list:
        """ Return tag entries with the given attribute.

        Parameters:
            attribute (str): A tag attribute.  Eg HedKey.ExtensionAllowed
            key_class (HedSectionKey): The HedSectionKey for the section to retrieve from.

        Returns:
            list: A list of all tags with this attribute.

        Notes:
            - The result is cached so will be fast after first call.
        """
        tags = set()
        for schema in self._schemas.values():
            tags.update(schema.get_tags_with_attribute(attribute, key_class))
        return list(tags)

    def get_tag_entry(self, name, key_class=HedSectionKey.Tags, schema_namespace="") -> Union["HedSchemaEntry", None]:
        """ Return the schema entry for this tag, if one exists.

        Parameters:
            name (str): Any form of basic tag(or other section entry) to look up.
                This will not handle extensions or similar.
                If this is a tag, it can have a schema namespace, but it's not required
            key_class (HedSectionKey or str):  The type of entry to return.
            schema_namespace (str): Only used on Tags.  If incorrect, will return None.

        Returns:
            HedSchemaEntry: The schema entry for the given tag.
        """
        specific_schema = self.schema_for_namespace(schema_namespace)
        if not specific_schema:
            return None

        return specific_schema.get_tag_entry(name, key_class, schema_namespace)

    def find_tag_entry(self, tag, schema_namespace="") -> tuple[Union["HedTagEntry", None], Union[str, None], list]:
        """ Find the schema entry for a given source tag.

        Parameters:
            tag (str, HedTag): Any form of tag to look up.  Can have an extension, value, etc.
            schema_namespace (str): The schema namespace of the tag, if any.

        Returns:
            HedTagEntry: The located tag entry for this tag.
            str: The remainder of the tag that isn't part of the base tag.
            list: A list of errors while converting.

        Notes:
            Works left to right (which is mostly relevant for errors).
        """
        specific_schema = self.schema_for_namespace(schema_namespace)
        if not specific_schema:
            validation_issues = ErrorHandler.format_error(ValidationErrors.HED_LIBRARY_UNMATCHED, tag,
                                                          schema_namespace, self.valid_prefixes)
            return None, None, validation_issues

        return specific_schema._find_tag_entry(tag, schema_namespace)
