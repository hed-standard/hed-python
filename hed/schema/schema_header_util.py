
from semantic_version import Version

from hed.schema import hed_schema_constants as constants
from hed.errors.exceptions import HedExceptions, HedFileError
from hed.schema.hed_schema_constants import valid_header_attributes


def validate_library_name(library_name):
    """ Check the validity of the library name.

    Parameters:
        library_name (str): Name of the library.

    Returns:
        Union[bool, str]:  If not False, string indicates the issue.

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
        Union[bool, str]:  If not False, string indicates the issue.

    """
    try:
        Version(version_string)
    except ValueError as e:
        return str(e)
    return False


header_attribute_validators = {
    constants.VERSION_ATTRIBUTE: (validate_version_string, HedExceptions.SCHEMA_VERSION_INVALID),
    constants.LIBRARY_ATTRIBUTE: (validate_library_name, HedExceptions.BAD_HED_LIBRARY_NAME)
}


def validate_present_attributes(attrib_dict, name):
    """ Validate combinations of attributes

        Parameters:
            attrib_dict (dict): Dictionary of attributes to be evaluated.
            name (str):  File name to use in reporting errors.

        Returns:
            list: List of issues. Each issue is a dictionary.

        Raises:
            HedFileError: If withStandard is found in th header, but a library attribute is not specified.

        """
    if constants.WITH_STANDARD_ATTRIBUTE in attrib_dict and constants.LIBRARY_ATTRIBUTE not in attrib_dict:
        raise HedFileError(HedExceptions.BAD_WITH_STANDARD,
                           "withStandard header attribute found, but no library attribute is present",
                           name)


def validate_attributes(attrib_dict, name):
    """ Validate attributes in the dictionary.

    Parameters:
        attrib_dict (dict): Dictionary of attributes to be evaluated.
        name (str):  name to use in reporting errors.

    Returns:
        list: List of issues. Each issue is a dictionary.

    Raises:
        HedFileError: If any of the following issues are found:
        - Invalid library name
        - Version not present
        - Invalid combinations of attributes in header
    """
    validate_present_attributes(attrib_dict, name)

    for attribute_name, attribute_value in attrib_dict.items():
        if attribute_name in header_attribute_validators:
            validator, error_code = header_attribute_validators[attribute_name]
            had_error = validator(attribute_value)
            if had_error:
                raise HedFileError(error_code, had_error, name)
        if attribute_name not in valid_header_attributes:
            raise HedFileError(HedExceptions.SCHEMA_UNKNOWN_HEADER_ATTRIBUTE,
                               f"Unknown attribute {attribute_name} found in header line", filename=name)

    if constants.VERSION_ATTRIBUTE not in attrib_dict:
        raise HedFileError(HedExceptions.SCHEMA_VERSION_INVALID,
                           "No version attribute found in header", filename=name)
