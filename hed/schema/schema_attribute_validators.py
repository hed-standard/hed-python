"""The built-in functions to validate known attributes.

Template for the functions:
attribute_checker_template(hed_schema, tag_entry, attribute_name, possible_values):
    hed_schema (HedSchema): The schema to use for validation
    tag_entry (HedSchemaEntry): The schema entry for this tag.
    attribute_name (str): The name of this attribute
Returns:
    bool
"""

from hed.errors.error_types import SchemaWarnings, ValidationErrors
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_schema import HedSchema


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
        issues += ErrorHandler.format_error(SchemaWarnings.NON_PLACEHOLDER_HAS_CLASS, tag_entry.name,
                                            attribute_name)

    return issues


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
            issues += ErrorHandler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                                org_tag,
                                                index_in_tag=0,
                                                index_in_tag_end=len(org_tag))

    return issues


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