from semantic_version import Version
from hed.schema import hed_schema_constants as constants
from hed.errors.exceptions import HedExceptions, HedFileError


def _validate_library_name(library_name):
    if library_name.isalpha():
        return True

    for i, character in enumerate(library_name):
        if not character.isalpha():
            return f"Non alpha character '{character}' at position {i} in '{library_name}'"


def _validate_version_string(version_string):
    try:
        Version(version_string)
    except ValueError as e:
        return str(e)

    return True


def is_hed3_version_number(version_string):
    try:
        version = Version(version_string)
        if version.major >= 8:
            return True
    except ValueError:
        return False

    return False


attribute_validators = {
        "version": (_validate_version_string, HedExceptions.BAD_HED_SEMANTIC_VERSION),
        "library": (_validate_library_name, HedExceptions.BAD_HED_LIBRARY_NAME)
    }


def validate_attributes(attrib_dict, filename):
    for attribute_name, attribute_value in attrib_dict.items():
        if attribute_name in attribute_validators:
            validator, error_code = attribute_validators[attribute_name]
            result = validator(attribute_value)
            if result is not True:
                raise HedFileError(error_code, result, filename)

    if constants.VERSION_ATTRIBUTE not in attrib_dict:
        raise HedFileError(HedExceptions.BAD_HED_SEMANTIC_VERSION, "No version attribute found in header",
                           filename=filename)

