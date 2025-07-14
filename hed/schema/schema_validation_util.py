"""Utilities used in HED validation/loading using a HED schema."""
from typing import Union

from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import SchemaWarnings
from hed.schema import hed_schema_constants as constants
from hed.schema.hed_schema_constants import character_types
from hed.schema.hed_schema import HedSchema


def validate_schema_tag_new(hed_entry) -> list[dict]:
    """ Check tag entry for capitalization and illegal characters.

    Parameters:
        hed_entry (HedTagEntry): A single tag entry

    Returns:
        list[dict]: A list of all formatting issues found in the term. Each issue is a dictionary.
    """
    issues_list = []
    hed_term = hed_entry.short_tag_name
    # Any # terms will have already been validated as the previous entry.
    if hed_term == "#":
        return issues_list

    if hed_term and hed_term[0] and not (hed_term[0].isdigit() or hed_term[0].isupper()):
        issues_list += ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION,
                                                 hed_term, char_index=0, problem_char=hed_term[0])
    issues_list += validate_schema_term_new(hed_entry, hed_term)
    return issues_list


def validate_schema_term_new(hed_entry, hed_term=None) -> list[dict]:
    """ Check the term for invalid character issues

    Parameters:
        hed_entry (HedSchemaEntry): A single schema entry
        hed_term (str or None): Use instead of hed_entry.name if present.

    Returns:
        list[dict]: A list of all formatting issues found in the term. Each issue is a dictionary.
    """
    if not hed_term:
        hed_term = hed_entry.name
    issues_list = []
    # todo: potentially optimize this someday, as most values are the same
    character_set = get_allowed_characters_by_name(["name"] +
                                                   hed_entry.attributes.get("allowedCharacter", "").split(","))
    indexes = get_problem_indexes(hed_term, character_set)
    for char, index in indexes:
        issues_list += ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_TAG,
                                                 hed_term, char_index=index, problem_char=char)
    return issues_list


def validate_schema_description_new(hed_entry) -> list[dict]:
    """ Check the description of the entry for invalid character issues

    Parameters:
        hed_entry (HedSchemaEntry): A single schema entry

    Returns:
        list[dict]: A list issues pertaining to all invalid characters found in description. Each issue is a dictionary.
    """
    if not hed_entry.description:
        return []
    issues_list = []
    character_set = get_allowed_characters_by_name(["text", "comma"])
    indexes = get_problem_indexes(hed_entry.description, character_set)
    # Kludge, just get short name here if we have it for error reporting
    name = hed_entry.name
    if hasattr(hed_entry, "short_tag_name"):
        name = hed_entry.short_tag_name
    for char, index in indexes:

        issues_list += ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_DESC,
                                                 hed_entry.description, name, problem_char=char, char_index=index)
    return issues_list


def schema_version_for_library(hed_schema, library_name) -> Union[str, None]:
    """ Given the library name and HED schema object, return the version

    Parameters:
        hed_schema (HedSchema): the schema object
        library_name (str or None): The library name you're interested in.  "" for the standard schema.

    Returns:
        Union[str, None]: The version number of the given library name.  Returns None if unknown library_name.
    """
    if library_name is None:
        library_name = ""
    names = hed_schema.library.split(",")
    versions = hed_schema.version_number.split(",")
    for name, version in zip(names, versions):
        if name == library_name:
            return version

    # Return the partnered schema version
    if library_name == "" and hed_schema.with_standard:
        return hed_schema.with_standard
    return None


def get_allowed_characters(value_classes) -> set[str]:
    """Returns the allowed characters in a given container of value classes

    Parameters:
        value_classes (list of HedSchemaEntry): A list of schema entries that should have the allowedCharacter attribute

    Returns:
        set[str]: The set of all characters from the given classes
    """
    # This could be pre-computed
    character_set_names = []

    for value_class in value_classes:
        allowed_types = value_class.attributes.get(constants.HedKey.AllowedCharacter, "").split(",")
        character_set_names.extend(allowed_types)

    character_set = get_allowed_characters_by_name(character_set_names)
    # for now, just always allow these special cases(it's validated extensively elsewhere)
    character_set.update("#/")
    return character_set


def get_allowed_characters_by_name(character_set_names) -> set[str]:
    """Returns the allowed characters from a list of character set names

    Note: "nonascii" is a special case "character" that can be included as well

    Parameters:
        character_set_names (list of str): A list of character sets to allow.  See hed_schema_constants.character_types

    Returns:
        set[str]: The set of all characters from the names
    """
    character_set = set()
    for name in character_set_names:
        if name in character_types and name != "nonascii":
            character_set.update(character_types[name])
        else:
            character_set.add(name)
    return character_set


def get_problem_indexes(validation_string, character_set, index_adj=0) -> list[tuple[str, int]]:
    """Finds indexes with values not in character set

    Parameters:
        validation_string (str): The string to check characters in.
        character_set (set): The list of valid characters (or the value "nonascii" as a set entry).
        index_adj (int): The value to adjust the reported indices by, if this isn't the start of a string.

    Returns:
        list[tuple[str, int]]: The list of problematic characters and their indices.
    """
    if not character_set:
        return []

    indexes = [(char, index + index_adj) for index, char in enumerate(validation_string) if char not in character_set]
    if "nonascii" in character_set:
        indexes = [(char, index) for char, index in indexes if not ord(char) > 127]

    return indexes
