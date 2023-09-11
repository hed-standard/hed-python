"""
    Abstract base class for HedSchema and HedSchemaGroup, showing the common functionality
"""

from hed.errors import ErrorHandler
from hed.schema.hed_schema_constants import HedSectionKey
from abc import ABC, abstractmethod


class HedSchemaBase(ABC):
    """ Baseclass for schema and schema group.
        Overriding the following functions will allow you to use the schema for validation etc.
    """
    def __init__(self):
        pass

    @abstractmethod
    def get_schema_versions(self):
        """ A list of HED version strings including namespace and library name if any of this schema.

        Returns:
            list: The complete version of this schema including library name and namespace.
        """
        raise NotImplemented("This function must be implemented in the baseclass")

    @abstractmethod
    def get_formatted_version(self):
        """ The HED version string including namespace and library name if any of this schema.

        Returns:
            str: The complete version of this schema including library name and namespace.
        """
        raise NotImplemented("This function must be implemented in the baseclass")

    @abstractmethod
    def schema_for_namespace(self, namespace):
        """ Return the HedSchema for the library namespace.

        Parameters:
            namespace (str): A schema library name namespace.

        Returns:
            HedSchema or None: The specific schema for this library name namespace if exists.
        """
        raise NotImplemented("This function must be implemented in the baseclass")

    @property
    @abstractmethod
    def valid_prefixes(self):
        """ Return a list of all prefixes this group will accept.

        Returns:
            prefixes(list of str):  A list of strings representing valid prefixes for this group.
        """
        raise NotImplemented("This function must be implemented in the baseclass")

    @abstractmethod
    def get_tags_with_attribute(self, attribute, key_class=HedSectionKey.Tags):
        """ Return tag entries with the given attribute.

        Parameters:
            attribute (str): A tag attribute.  Eg HedKey.ExtensionAllowed
            key_class (HedSectionKey): The HedSectionKey for the section to retrieve from.

        Returns:
            list: A list of all tags with this attribute.

        Notes:
            - The result is cached so will be fast after first call.
        """
        raise NotImplemented("This function must be implemented in the baseclass")

    # todo: maybe tweak this API so you don't have to pass in library namespace?
    @abstractmethod
    def get_tag_entry(self, name, key_class=HedSectionKey.Tags, schema_namespace=""):
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
        raise NotImplemented("This function must be implemented in the baseclass")

    @abstractmethod
    def find_tag_entry(self, tag, schema_namespace=""):
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
        raise NotImplemented("This function must be implemented in the baseclass")

    @abstractmethod
    def __eq__(self, other):
        raise NotImplemented("This function must be implemented in the baseclass")

    @abstractmethod
    def check_compliance(self, check_for_warnings=True, name=None, error_handler=None):
        """ Check for HED3 compliance of this schema.

        Parameters:
            check_for_warnings (bool): If True, checks for formatting issues like invalid characters, capitalization.
            name (str): If present, use as the filename for context, rather than using the actual filename.
                        Useful for temp filenames when supporting web services.
            error_handler (ErrorHandler or None): Used to report errors.  Uses a default one if none passed in.

        Returns:
            list: A list of all warnings and errors found in the file. Each issue is a dictionary.
        """
        raise NotImplemented("This function must be implemented in the baseclass")
