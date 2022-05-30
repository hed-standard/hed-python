"""Utilities used in HED validation using a HED schema."""
from semantic_version import Version
from hed.schema import hed_schema_constants as constants
from hed.errors.exceptions import HedExceptions, HedFileError


def _validate_library_name(library_name):
    """ Check the validity of the library name.

    Args:
        library_name (str): Name of the library.

    Returns:
        bool or str:  If not True, string indicates the issue.

    """
    if library_name.isalpha():
        return True

    for i, character in enumerate(library_name):
        if not character.isalpha():
            return f"Non alpha character '{character}' at position {i} in '{library_name}'"


def _validate_version_string(version_string):
    """ Check validity of the version.

    Args:
        version_string (str):  A version string.

    Returns:
        bool or str:  If not True, string indicates the issue.

    """
    try:
        Version(version_string)
    except ValueError as e:
        return str(e)
    return True


def is_hed3_version_number(version_string):
    """ Check validity of the version.

    Args:
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
        "version": (_validate_version_string, HedExceptions.HED_SCHEMA_VERSION_INVALID),
        "library": (_validate_library_name, HedExceptions.BAD_HED_LIBRARY_NAME)
    }


def validate_attributes(attrib_dict, filename):
    """ Validate attributes in the dictionary.

    Args:
        attrib_dict (dict): Dictionary of attributes to be evaluated.
        filename (str):  File name to use in reporting errors.

    Returns:
        list: List of issues. Each issue is a dictionary.

    Raises:
        HedFileError: if invalid or version not found in the dictionary.

    """
    for attribute_name, attribute_value in attrib_dict.items():
        if attribute_name in attribute_validators:
            validator, error_code = attribute_validators[attribute_name]
            result = validator(attribute_value)
            if result is not True:
                raise HedFileError(error_code, result, filename)

    if constants.VERSION_ATTRIBUTE not in attrib_dict:
        raise HedFileError(HedExceptions.HED_SCHEMA_VERSION_INVALID,
                           "No version attribute found in header", filename=filename)
