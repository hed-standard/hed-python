"""The built-in functions to validate known attributes.

Template for the functions:

- ``attribute_checker_template(hed_schema, tag_entry, attribute_name)``:
  - ``hed_schema (HedSchema)``: The schema to use for validation.
  - ``tag_entry (HedSchemaEntry)``: The schema entry for this tag.
  - ``attribute_name (str)``: The name of this attribute.

Returns:
    - ``issues (list)``: A list of issues found validating this attribute
    """

from hed.errors.error_types import SchemaWarnings, ValidationErrors, SchemaAttributeErrors
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_cache import get_hed_versions
from hed.schema.hed_schema_constants import HedKey, character_types, HedSectionKey
from hed.schema.schema_validation_util import schema_version_for_library
from semantic_version import Version


def tag_is_placeholder_check(hed_schema, tag_entry, attribute_name):
    """Check if comma separated list has valid HedTags."""
    issues = []
    if not tag_entry.name.endswith("/#"):
        issues += ErrorHandler.format_error(SchemaWarnings.SCHEMA_NON_PLACEHOLDER_HAS_CLASS, tag_entry.name,
                                            attribute_name)

    return issues


def attribute_is_deprecated(hed_schema, tag_entry, attribute_name):
    """ Check if the attribute is deprecated.  does not check value."""
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


# todo: This needs to be refactored, these next several functions are near identical
def tag_exists_check(hed_schema, tag_entry, attribute_name):
    """Check if the list of possible tags exists in the schema."""
    issues = []
    possible_tags = tag_entry.attributes.get(attribute_name, "")
    split_tags = possible_tags.split(",")
    for org_tag in split_tags:
        org_entry = hed_schema.tags.get(org_tag)
        if org_tag and not org_entry:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_SUGGESTED_TAG_INVALID,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)
        elif (org_entry and org_entry.has_attribute(HedKey.DeprecatedFrom)
              and not tag_entry.has_attribute(HedKey.DeprecatedFrom)):
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_DEPRECATED,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)

    return issues


def unit_class_exists(hed_schema, tag_entry, attribute_name):
    """Check if comma separated list is valid unit classes."""
    issues = []
    possible_unit_classes = tag_entry.attributes.get(attribute_name, "")
    split_tags = possible_unit_classes.split(",")
    for org_tag in split_tags:
        unit_class_entry = hed_schema.unit_classes.get(org_tag)
        if org_tag and not unit_class_entry:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_UNIT_CLASS_INVALID,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)
        elif (unit_class_entry and unit_class_entry.has_attribute(HedKey.DeprecatedFrom)
              and not tag_entry.has_attribute(HedKey.DeprecatedFrom)):
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_DEPRECATED,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)

    return issues


def value_class_exists(hed_schema, tag_entry, attribute_name):
    """Check if comma separated list is valid value classes."""
    issues = []
    possible_value_classes = tag_entry.attributes.get(attribute_name, "")
    split_tags = possible_value_classes.split(",")

    for org_tag in split_tags:
        value_class_entry = hed_schema.value_classes.get(org_tag)
        if org_tag and not value_class_entry:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_VALUE_CLASS_INVALID,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)
        elif (value_class_entry and value_class_entry.has_attribute(HedKey.DeprecatedFrom)
              and not tag_entry.has_attribute(HedKey.DeprecatedFrom)):
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_DEPRECATED,
                                                tag_entry.name,
                                                org_tag,
                                                attribute_name)

    return issues


def unit_exists(hed_schema, tag_entry, attribute_name):
    """Check the given unit is valid, and not deprecated."""
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
def tag_exists_base_schema_check(hed_schema, tag_entry, attribute_name):
    """Check if the single tag is a partnered schema tag"""
    issues = []
    rooted_tag = tag_entry.attributes.get(attribute_name, "")
    if rooted_tag and rooted_tag not in hed_schema.tags:
        issues += ErrorHandler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                            rooted_tag,
                                            index_in_tag=0,
                                            index_in_tag_end=len(rooted_tag))

    return issues


def tag_is_deprecated_check(hed_schema, tag_entry, attribute_name):
    """ Check if the element has a valid deprecatedFrom attribute, and that any children have it"""
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


def conversion_factor(hed_schema, tag_entry, attribute_name):
    """Check if the conversion_factor on is valid"""
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


def allowed_characters_check(hed_schema, tag_entry, attribute_name):
    """ Check allowed character has a valid value"""
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


def in_library_check(hed_schema, tag_entry, attribute_name):
    """Check if the library attribute is a valid schema name"""
    issues = []

    library = tag_entry.attributes.get(attribute_name, "")
    if library not in hed_schema.library.split(","):
        issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_IN_LIBRARY_INVALID,
                                            tag_entry.name,
                                            library)
    return issues
