"""The built-in functions to validate known attributes.

Template for the functions:

All attribute validation functions should follow this signature:
  ``attribute_checker_template(hed_schema, tag_entry, attribute_name)``

Parameters:
  - ``hed_schema (HedSchema)``: The schema to use for validation.
  - ``tag_entry (HedSchemaEntry)``: The schema entry for this tag.
  - ``attribute_name (str)``: The name of this attribute.

Return value:
  ``list[dict]``: A list of issues found validating this attribute.

"""

from hed.errors.error_types import SchemaWarnings, ValidationErrors, SchemaAttributeErrors, SchemaErrors
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_cache import get_hed_versions
from hed.schema.hed_schema_constants import HedKey, character_types, HedSectionKey
from hed.schema.schema_validation_util import schema_version_for_library
from semantic_version import Version


def tag_is_placeholder_check(hed_schema, tag_entry, attribute_name) -> list:
    """Check if comma separated list has valid HedTags.

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []
    if not tag_entry.name.endswith("/#"):
        issues += ErrorHandler.format_error(SchemaWarnings.SCHEMA_NON_PLACEHOLDER_HAS_CLASS, tag_entry.name,
                                            attribute_name)

    if tag_entry.parent:
        other_entries = [child for child in tag_entry.parent.children.values() if child is not tag_entry]
        if len(other_entries) > 0:
            issues += ErrorHandler.format_error(SchemaErrors.SCHEMA_INVALID_SIBLING, tag_entry.name,
                                                other_entries)

    if tag_entry.children:
        issues += ErrorHandler.format_error(SchemaErrors.SCHEMA_INVALID_CHILD, tag_entry.name,
                                            tag_entry.children)

    return issues


def attribute_is_deprecated(hed_schema, tag_entry, attribute_name) -> list:
    """ Check if the attribute is deprecated.  does not check value.

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []
    # Attributes has to check properties
    section_key = HedSectionKey.Attributes
    if tag_entry.section_key == HedSectionKey.Attributes:
        section_key = HedSectionKey.Properties

    attribute_entry = hed_schema.get_tag_entry(attribute_name, section_key)
    if (attribute_entry and attribute_entry.has_attribute(HedKey.DeprecatedFrom)
            and not tag_entry.has_attribute(HedKey.DeprecatedFrom)):
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_DEPRECATED,
                                            tag_entry.name,
                                            attribute_entry.name,
                                            attribute_name)

    return issues


def item_exists_check(hed_schema, tag_entry, attribute_name, section_key) -> list:
    """Check if the list of possible items exists in the schema and are not deprecated.

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute
        section_key (HedSectionKey): The section this item should be in.
                                   This is generally passed via functools.partial

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []
    item_values = tag_entry.attributes.get(attribute_name, "")
    split_items = item_values.split(",")

    for item in split_items:
        if not item:
            continue
        # todo: make a dict if any more added
        if section_key == HedSectionKey.Tags:
            item_entry = hed_schema.tags.get(item)
        elif section_key == HedSectionKey.UnitClasses:
            item_entry = hed_schema.unit_classes.get(item)
        elif section_key == HedSectionKey.ValueClasses:
            item_entry = hed_schema.value_classes.get(item)
        else:
            raise ValueError(f"Invalid item type: {section_key}")

        if not item_entry:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_GENERIC_ATTRIBUTE_VALUE_INVALID,
                                                tag_entry.name,
                                                item,
                                                attribute_name)
        elif item_entry.has_attribute(HedKey.DeprecatedFrom) and not tag_entry.has_attribute(HedKey.DeprecatedFrom):
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_DEPRECATED,
                                                tag_entry.name,
                                                item,
                                                attribute_name)

    return issues


def unit_exists(hed_schema, tag_entry, attribute_name) -> list:
    """Check the given unit is valid, and not deprecated.

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []
    unit = tag_entry.attributes.get(attribute_name, "")
    unit_entry = tag_entry.get_derivative_unit_entry(unit)
    if unit and not unit_entry:
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_DEFAULT_UNITS_INVALID,
                                            tag_entry.name,
                                            unit,
                                            tag_entry.units)
    elif (unit_entry and unit_entry.has_attribute(HedKey.DeprecatedFrom)
          and not tag_entry.has_attribute(HedKey.DeprecatedFrom)):
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_DEFAULT_UNITS_DEPRECATED,
                                            tag_entry.name,
                                            unit_entry.name)

    return issues


# This is effectively unused and can never fail - The schema would catch these errors and refuse to load
def tag_exists_base_schema_check(hed_schema, tag_entry, attribute_name) -> list:
    """Check if the single tag is a partnered schema tag

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []
    rooted_tag = tag_entry.attributes.get(attribute_name, "")
    if rooted_tag and rooted_tag not in hed_schema.tags:
        issues += ErrorHandler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                            rooted_tag,
                                            index_in_tag=0,
                                            index_in_tag_end=len(rooted_tag))

    return issues


def tag_is_deprecated_check(hed_schema, tag_entry, attribute_name) -> list:
    """ Check if the element has a valid deprecatedFrom attribute, and that any children have it

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []
    deprecated_version = tag_entry.attributes.get(attribute_name, "")
    library_name = tag_entry.has_attribute(HedKey.InLibrary, return_value=True)
    if not library_name and not hed_schema.with_standard:
        library_name = hed_schema.library
    all_versions = get_hed_versions(library_name=library_name)
    if deprecated_version:
        library_version = schema_version_for_library(hed_schema, library_name)
        # The version must exist, and be lower or equal to our current version
        if (deprecated_version not in all_versions or
                (library_version and Version(library_version) <= Version(deprecated_version))):
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_DEPRECATED_INVALID,
                                                tag_entry.name,
                                                deprecated_version)

    if hasattr(tag_entry, "children"):
        # Fix up this error message if we ever actually issue it for units
        for child in tag_entry.children.values():
            if not child.has_attribute(attribute_name):
                issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_CHILD_OF_DEPRECATED,
                                                    tag_entry.name,
                                                    child.name)
    return issues


def conversion_factor(hed_schema, tag_entry, attribute_name) -> list:
    """Check if the conversion_factor on is valid

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []
    cf = tag_entry.attributes.get(attribute_name, "1.0")
    try:
        cf = float(cf.replace("^", "e"))
    except (ValueError, AttributeError):
        pass
    if not isinstance(cf, float) or cf <= 0.0:
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_CONVERSION_FACTOR_NOT_POSITIVE,
                                            tag_entry.name,
                                            cf)

    return issues


def allowed_characters_check(hed_schema, tag_entry, attribute_name) -> list:
    """ Check allowed character has a valid value

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []
    allowed_strings = character_types

    char_string = tag_entry.attributes.get(attribute_name, "")
    characters = char_string.split(",")
    for character in characters:
        if character not in allowed_strings and len(character) != 1:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_ALLOWED_CHARACTERS_INVALID,
                                                tag_entry.name,
                                                character)
    return issues


def in_library_check(hed_schema, tag_entry, attribute_name) -> list:
    """Check if the library attribute is a valid schema name

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []

    library = tag_entry.attributes.get(attribute_name, "")
    if library not in hed_schema.library.split(","):
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_IN_LIBRARY_INVALID,
                                            tag_entry.name,
                                            library)
    return issues


def is_numeric_value(hed_schema, tag_entry, attribute_name) -> list:
    """Check if the attribute is a valid numeric(float) value

    Parameters:
        hed_schema (HedSchema): The schema to use for validation
        tag_entry (HedSchemaEntry): The schema entry for this tag.
        attribute_name (str): The name of this attribute.

    Returns:
        list[dict]: A list of issues from validating this attribute.
    """
    issues = []

    float_str = tag_entry.attributes.get(attribute_name, "")

    try:
        float(float_str)
    except ValueError:
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_NUMERIC_INVALID,
                                            tag_entry.name,
                                            float_str,
                                            attribute_name)
    return issues
