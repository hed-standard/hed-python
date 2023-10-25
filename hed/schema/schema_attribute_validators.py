"""The built-in functions to validate known attributes.

Template for the functions:
attribute_checker_template(hed_schema, tag_entry, attribute_name, possible_values):
    hed_schema (HedSchema): The schema to use for validation
    tag_entry (HedSchemaEntry): The schema entry for this tag.
    attribute_name (str): The name of this attribute
Returns:
    bool
"""

from hed.errors.error_types import SchemaWarnings, ValidationErrors, SchemaAttributeErrors
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_cache import get_hed_versions
from hed.schema.hed_schema_constants import HedKey


def tag_is_placeholder_check(hed_schema, tag_entry, attribute_name):
    """ Check if comma separated list has valid HedTags.

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute

    Returns:
        list: A list of issues. Each issue is a dictionary.

    """
    issues = []
    if not tag_entry.name.endswith("/#"):
        issues += ErrorHandler.format_error(SchemaWarnings.SCHEMA_NON_PLACEHOLDER_HAS_CLASS, tag_entry.name,
                                            attribute_name)

    return issues


# todo: This needs to be refactored, these next several functions are near identical
def tag_exists_check(hed_schema, tag_entry, attribute_name):
    """ Check if the list of possible tags exists in the schema.

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute

    Returns:
        list: A list of issues. Each issue is a dictionary.

    """
    issues = []
    possible_tags = tag_entry.attributes.get(attribute_name, "")
    split_tags = possible_tags.split(",")
    for org_tag in split_tags:
        if org_tag and org_tag not in hed_schema.tags:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_SUGGESTED_TAG_INVALID,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)

    return issues


def unit_class_exists(hed_schema, tag_entry, attribute_name):
    issues = []
    possible_unit_classes = tag_entry.attributes.get(attribute_name, "")
    split_tags = possible_unit_classes.split(",")
    for org_tag in split_tags:
        if org_tag and org_tag not in hed_schema.unit_classes:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_UNIT_CLASS_INVALID,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)

    return issues


def value_class_exists(hed_schema, tag_entry, attribute_name):
    issues = []
    possible_value_classes = tag_entry.attributes.get(attribute_name, "")
    split_tags = possible_value_classes.split(",")
    for org_tag in split_tags:
        if org_tag and org_tag not in hed_schema.value_classes:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_VALUE_CLASS_INVALID,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)

    return issues


def unit_exists(hed_schema, tag_entry, attribute_name):
    issues = []
    default_unit = tag_entry.attributes.get(attribute_name, "")
    if default_unit and default_unit not in tag_entry.derivative_units:
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_DEFAULT_UNITS_INVALID,
                                            tag_entry.name,
                                            default_unit,
                                            tag_entry.units)

    return issues


# This is effectively unused and can never fail - The schema would catch these errors and refuse to load
def tag_exists_base_schema_check(hed_schema, tag_entry, attribute_name):
    """ Check if the single tag is a partnered schema tag

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute

    Returns:
        list: A list of issues. Each issue is a dictionary.
    """
    issues = []
    rooted_tag = tag_entry.attributes.get(attribute_name, "")
    if rooted_tag and rooted_tag not in hed_schema.tags:
        issues += ErrorHandler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                            rooted_tag,
                                            index_in_tag=0,
                                            index_in_tag_end=len(rooted_tag))

    return issues


def tag_is_deprecated_check(hed_schema, tag_entry, attribute_name):
    """ Check if the tag has a valid deprecatedFrom attribute, and that any children have it

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute

    Returns:
        list: A list of issues. Each issue is a dictionary.
    """
    issues = []
    deprecated_version = tag_entry.attributes.get(attribute_name, "")
    library_name = tag_entry.has_attribute(HedKey.InLibrary, return_value=True)
    all_versions = get_hed_versions(library_name=library_name)
    if deprecated_version and deprecated_version not in all_versions:
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_DEPRECATED_INVALID,
                                            tag_entry.name,
                                            deprecated_version)

    for child in tag_entry.children.values():
        if not child.has_attribute(attribute_name):
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_CHILD_OF_DEPRECATED,
                                                tag_entry.name,
                                                child.name)
    return issues


def conversion_factor(hed_schema, tag_entry, attribute_name):
    issues = []
    conversion_factor = tag_entry.attributes.get(attribute_name, "1.0")
    try:
        conversion_factor = float(conversion_factor.replace("^", "e"))
    except (ValueError, AttributeError) as e:
        pass
    if not isinstance(conversion_factor, float) or conversion_factor <= 0.0:
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_CONVERSION_FACTOR_NOT_POSITIVE,
                                            tag_entry.name,
                                            conversion_factor)

    return issues


def allowed_characters_check(hed_schema, tag_entry, attribute_name):
    """ Check allowed character has a valid value

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this attribute.
        attribute_name (str): The name of this attribute

    Returns:
        list: A list of issues. Each issue is a dictionary.

    """
    issues = []
    allowed_strings = {'letters', 'blank', 'digits', 'alphanumeric'}

    char_string = tag_entry.attributes.get(attribute_name, "")
    characters = char_string.split(",")
    for character in characters:
        if character not in allowed_strings and len(character) != 1:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_ALLOWED_CHARACTERS_INVALID,
                                                tag_entry.name,
                                                character)
    return issues


def in_library_check(hed_schema, tag_entry, attribute_name):
    """ Check allowed character has a valid value

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this attribute.
        attribute_name (str): The name of this attribute

    Returns:
        list: A list of issues. Each issue is a dictionary.

    """
    issues = []

    library = tag_entry.attributes.get(attribute_name, "")
    if hed_schema.library != library:
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_IN_LIBRARY_INVALID,
                                            tag_entry.name,
                                            library)
    return issues
