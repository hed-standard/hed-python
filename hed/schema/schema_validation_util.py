"""Utilities used in HED validation using a HED schema."""
from semantic_version import Version
from hed.schema import hed_schema_constants as constants
from hed.errors.exceptions import HedExceptions, HedFileError


def validate_library_name(library_name):
    """ Check the validity of the library name.

    Parameters:
        library_name (str): Name of the library.

    Returns:
        bool or str:  If not False, string indicates the issue.

    """
    for i, character in enumerate(library_name):
        if not character.isalpha():
            return f"Non alpha character '{character}' at position {i} in '{library_name}'"
        if character.isupper():
            return f"Non lowercase character '{character}' at position {i} in '{library_name}'"


def validate_version_string(version_string):
    """ Check validity of the version.

    Parameters:
        version_string (str):  A version string.

    Returns:
        bool or str:  If not False, string indicates the issue.

    """
    try:
        Version(version_string)
    except ValueError as e:
        return str(e)
    return False


def is_hed3_version_number(version_string):
    """ Check validity of the version.

    Parameters:
        version_string (str):  A version string.

    Returns:
        bool:  If True the version corresponds to a HED3 schema.

    """
    try:
        version = Version(version_string)
        if version.major >= 8:
            return True
    except ValueError:
        return False
    return False


attribute_validators = {
        constants.VERSION_ATTRIBUTE: (validate_version_string, HedExceptions.HED_SCHEMA_VERSION_INVALID),
        constants.LIBRARY_ATTRIBUTE: (validate_library_name, HedExceptions.BAD_HED_LIBRARY_NAME)
    }


def validate_present_attributes(attrib_dict, filename):
    """ Validate combinations of attributes

        Parameters:
            attrib_dict (dict): Dictionary of attributes to be evaluated.
            filename (str):  File name to use in reporting errors.

        Returns:
            list: List of issues. Each issue is a dictionary.

        :raises  HedFileError:
            - withStandard is found in th header, but a library attribute is not specified
        """
    if constants.WITH_STANDARD_ATTRIBUTE in attrib_dict and constants.LIBRARY_ATTRIBUTE not in attrib_dict:
        raise HedFileError(HedExceptions.BAD_WITH_STANDARD,
                           "withStandard header attribute found, but no library attribute is present",
                           filename)


def validate_attributes(attrib_dict, filename):
    """ Validate attributes in the dictionary.

    Parameters:
        attrib_dict (dict): Dictionary of attributes to be evaluated.
        filename (str):  File name to use in reporting errors.

    Returns:
        list: List of issues. Each issue is a dictionary.

    :raises  HedFileError:
        - Invalid library name
        - Version not present
        - Invalid combinations of attributes in header
    """
    validate_present_attributes(attrib_dict, filename)

    for attribute_name, attribute_value in attrib_dict.items():
        if attribute_name in attribute_validators:
            validator, error_code = attribute_validators[attribute_name]
            had_error = validator(attribute_value)
            if had_error:
                raise HedFileError(error_code, had_error, filename)

    if constants.VERSION_ATTRIBUTE not in attrib_dict:
        raise HedFileError(HedExceptions.HED_SCHEMA_VERSION_INVALID,
                           "No version attribute found in header", filename=filename)


# Might move this to a baseclass version if one is ever made for wiki2schema/xml2schema
def find_rooted_entry(tag_entry, schema, loading_merged):
    """ This semi-validates rooted tags, raising an exception on major errors

    Parameters:
        tag_entry(HedTagEntry): the possibly rooted tag
        schema(HedSchema): The schema being loaded
        loading_merged(bool): If this schema was already merged before loading

    Returns:
        rooted_tag(HedTagEntry or None): The base tag entry from the standard schema
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
                               schema.filename)

        if not isinstance(rooted_tag, str):
            raise HedFileError(HedExceptions.ROOTED_TAG_INVALID,
                               f'Rooted tag \'{tag_entry.short_tag_name}\' is not a string."',
                               schema.filename)

        if tag_entry.parent_name and not loading_merged:
            raise HedFileError(HedExceptions.ROOTED_TAG_INVALID,
                               f'Found rooted tag \'{tag_entry.short_tag_name}\' as a non root node.',
                               schema.filename)

        if not tag_entry.parent_name and loading_merged:
            raise HedFileError(HedExceptions.ROOTED_TAG_INVALID,
                               f'Found rooted tag \'{tag_entry.short_tag_name}\' as a root node in a merged schema.',
                               schema.filename)

        rooted_entry = schema.all_tags.get(rooted_tag)
        if not rooted_entry or rooted_entry.has_attribute(constants.HedKey.InLibrary):
            raise HedFileError(HedExceptions.ROOTED_TAG_DOES_NOT_EXIST,
                               f"Rooted tag '{tag_entry.short_tag_name}' not found in paired standard schema",
                               schema.filename)

        if loading_merged:
            return None

        return rooted_entry
