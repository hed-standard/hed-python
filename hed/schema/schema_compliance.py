""" Utilities for HED schema checking. """

from hed.errors import error_reporter
from hed.errors.error_types import SchemaWarnings, ErrorContext, SchemaErrors, ErrorSeverity, ValidationErrors
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_schema import HedSchema, HedKey

ALLOWED_TAG_CHARS = "-"
ALLOWED_DESC_CHARS = "-_:;,./()+ ^"


def check_compliance(hed_schema, check_for_warnings=True, name=None, error_handler=None):
    """ Check for hed3 compliance of a schema object.

    Parameters:
        hed_schema (HedSchema): HedSchema object to check for hed3 compliance.
        check_for_warnings (bool): If True, check for formatting issues like invalid characters, capitalization, etc.
        name (str): If present, will use as filename for context.
        error_handler (ErrorHandler or None): Used to report errors. Uses a default one if none passed in.

    Returns:
        list: A list of all warnings and errors found in the file. Each issue is a dictionary.

    :raises ValueError:
        - Trying to validate a HedSchemaGroup directly
    """
    if not isinstance(hed_schema, HedSchema):
        raise ValueError("To check compliance of a HedGroupSchema, call self.check_compliance on the schema itself.")

    if error_handler is None:
        error_handler = error_reporter.ErrorHandler()
    issues_list = []

    if not name:
        name = hed_schema.filename
    error_handler.push_error_context(ErrorContext.FILE_NAME, name)

    unknown_attributes = hed_schema.get_unknown_attributes()
    if unknown_attributes:
        for attribute_name, source_tags in unknown_attributes.items():
            for tag in source_tags:
                issues_list += error_handler.format_error_with_context(SchemaErrors.SCHEMA_ATTRIBUTE_INVALID,
                                                                       attribute_name,
                                                                       source_tag=tag)

    schema_attribute_validators = {
        HedKey.SuggestedTag: tag_exists_check,
        HedKey.RelatedTag: tag_exists_check,
        HedKey.UnitClass: tag_is_placeholder_check,
        HedKey.ValueClass: tag_is_placeholder_check,
        HedKey.Rooted: tag_exists_base_schema_check,
    }

    # Check attributes
    for section_key in hed_schema._sections:
        error_handler.push_error_context(ErrorContext.SCHEMA_SECTION, section_key)
        # Check attributes
        for tag_entry in hed_schema[section_key].values():
            error_handler.push_error_context(ErrorContext.SCHEMA_TAG, tag_entry.name)
            for attribute_name in tag_entry.attributes:
                validator = schema_attribute_validators.get(attribute_name)
                if validator:
                    error_handler.push_error_context(ErrorContext.SCHEMA_ATTRIBUTE, attribute_name)
                    new_issues = validator(hed_schema, tag_entry, attribute_name)
                    # if force_issues_as_warnings:
                    for issue in new_issues:
                        issue['severity'] = ErrorSeverity.WARNING
                    error_handler.add_context_and_filter(new_issues)
                    issues_list += new_issues
                    error_handler.pop_error_context()
            error_handler.pop_error_context()

        # Check duplicate names
        for name, duplicate_entries in hed_schema[section_key].duplicate_names.items():
            values = set(entry.has_attribute(HedKey.InLibrary) for entry in duplicate_entries)
            error_code = SchemaErrors.HED_SCHEMA_DUPLICATE_NODE
            if len(values) == 2:
                error_code = SchemaErrors.HED_SCHEMA_DUPLICATE_FROM_LIBRARY
            issues_list += error_handler.format_error_with_context(error_code, name,
                                                                   duplicate_tag_list=[entry.name for entry in duplicate_entries],
                                                                   section=section_key)

        error_handler.pop_error_context()

    if check_for_warnings:
        hed_terms = hed_schema.get_all_schema_tags(True)
        for hed_term in hed_terms:
            issues_list += validate_schema_term(hed_term)

        for tag_name, desc in hed_schema.get_desc_iter():
            issues_list += validate_schema_description(tag_name, desc)

    error_handler.pop_error_context()
    return issues_list

# attribute_checker_template(hed_schema, tag_entry, attribute_name, possible_values):
#     hed_schema (HedSchema): The schema to use for validation
#     tag_entry (HedSchemaEntry): The schema entry for this tag.
#     attribute_name (str): The name of this attribute


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
        if org_tag and org_tag not in hed_schema.all_tags:
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
    if rooted_tag and rooted_tag not in hed_schema.all_tags:
        issues += ErrorHandler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                            rooted_tag,
                                            index_in_tag=0,
                                            index_in_tag_end=len(rooted_tag))

    return issues


def validate_schema_term(hed_term):
    """ Check short tag for capitalization and illegal characters.

    Parameters:
        hed_term (str): A single hed term.

    Returns:
        list: A list of all formatting issues found in the term. Each issue is a dictionary.

    """
    issues_list = []
    # Any # terms will have already been validated as the previous entry.
    if hed_term == "#":
        return issues_list

    for i, char in enumerate(hed_term):
        if i == 0 and not (char.isdigit() or char.isupper()):
            issues_list += ErrorHandler.format_error(SchemaWarnings.INVALID_CAPITALIZATION,
                                                     hed_term, char_index=i, problem_char=char)
            continue
        if char in ALLOWED_TAG_CHARS or char.isalnum():
            continue
        issues_list += ErrorHandler.format_error(SchemaWarnings.INVALID_CHARACTERS_IN_TAG,
                                                 hed_term, char_index=i, problem_char=char)
    return issues_list


def validate_schema_description(tag_name, hed_description):
    """ Check the description of a single schema term.

    Parameters:
        tag_name (str): A single hed tag - not validated here, just used for error messages.
        hed_description (str): The description string to validate.

    Returns:
        list: A list of all formatting issues found in the description.

    """
    issues_list = []
    # Blank description is fine
    if not hed_description:
        return issues_list
    for i, char in enumerate(hed_description):
        if char.isalnum():
            continue
        if char in ALLOWED_DESC_CHARS:
            continue
        issues_list += ErrorHandler.format_error(SchemaWarnings.INVALID_CHARACTERS_IN_DESC,
                                                 hed_description, tag_name, char_index=i, problem_char=char)
    return issues_list
