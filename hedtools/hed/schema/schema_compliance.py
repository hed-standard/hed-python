from hed.errors import error_reporter
from hed.errors.error_types import SchemaWarnings, ErrorContext, SchemaErrors, ErrorSeverity
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_tag import HedTag

ALLOWED_TAG_CHARS = "-"
ALLOWED_DESC_CHARS = "-_:;,./()+ ^"


def check_compliance(hed_schema, also_check_for_warnings=True, name=None,
                     error_handler=None):
    """
        Checks for hed3 compliance of a schema object.

    Parameters
    ----------
    hed_schema : HedSchema
        HedSchema object to check for hed3 compliance
    also_check_for_warnings : bool, default True
        If True, also checks for formatting issues like invalid characters, capitalization, etc.
    name: str
        If present, will use this as the filename for context, rather than using the actual filename
        Useful for temp filenames.
    error_handler : ErrorHandler or None
        Used to report errors.  Uses a default one if none passed in.
    Returns
    -------
    issue_list : [{}]
        A list of all warnings and errors found in the file.
    """
    if not isinstance(hed_schema, HedSchema):
        raise ValueError("To check compliance of a HedGroupSchema, call self.check_compliance on the schema itself.")

    if error_handler is None:
        error_handler = error_reporter.ErrorHandler()
    issues_list = []

    if not name:
        name = hed_schema.filename
    error_handler.push_error_context(ErrorContext.FILE_NAME, name)

    if hed_schema.has_duplicate_tags:
        duplicate_dict = hed_schema.find_duplicate_tags()
        for tag_name, long_org_tags in duplicate_dict.items():
            issues_list += error_handler.format_error_with_context(SchemaErrors.HED_SCHEMA_DUPLICATE_NODE, tag_name,
                                                                   duplicate_tag_list=long_org_tags)

    unknown_attributes = hed_schema.get_all_unknown_attributes()
    if unknown_attributes:
        for attribute_name, source_tags in unknown_attributes.items():
            for tag in source_tags:
                issues_list += error_handler.format_error_with_context(SchemaErrors.HED_SCHEMA_ATTRIBUTE_INVALID,
                                                                       attribute_name,
                                                                       source_tag=tag)

    schema_attribute_validators = {
        'suggestedTag': tag_exists_check,
        'relatedTag': tag_exists_check
    }

    # Check attributes
    for section_key in hed_schema._sections:
        error_handler.push_error_context(ErrorContext.SCHEMA_SECTION, section_key)
        for tag_entry in hed_schema[section_key].values():
            error_handler.push_error_context(ErrorContext.SCHEMA_TAG, tag_entry.long_name)
            for attribute_name in tag_entry.attributes:
                validator = schema_attribute_validators.get(attribute_name)
                if validator:
                    error_handler.push_error_context(ErrorContext.SCHEMA_ATTRIBUTE, attribute_name, False)
                    new_issues = validator(hed_schema, tag_entry.attributes[attribute_name])
                    error_handler.add_context_to_issues(new_issues)
                    issues_list += new_issues
                    error_handler.pop_error_context()
            error_handler.pop_error_context()

        error_handler.pop_error_context()

    if also_check_for_warnings:
        hed_terms = hed_schema.get_all_schema_tags(True)
        for hed_term in hed_terms:
            issues_list += validate_schema_term(hed_term)

        for tag_name, desc in hed_schema.get_desc_iter():
            issues_list += validate_schema_description(tag_name, desc)

    error_handler.pop_error_context()
    return issues_list


def tag_exists_check(hed_schema, possible_tags, force_issues_as_warnings=True):
    """
        Checks if the comma separated list in possible tags are valid HedTags

    Parameters
    ----------
    hed_schema: HedSchema
        The schema to check if the tag exists
    possible_tags: str
        Comma separated list of tags.  Short long or mixed form valid.

    Returns
    -------
    issues_list: [{}]
    """
    issues = []
    split_tags = possible_tags.split(",")
    for org_tag in split_tags:
        tag = HedTag(org_tag)
        issues += tag.convert_to_canonical_forms(hed_schema)

    if force_issues_as_warnings:
        for issue in issues:
            issue['severity'] = ErrorSeverity.WARNING
    return issues


def validate_schema_term(hed_term):
    """
    Takes a single term(ie short tag) and checks capitalization and illegal characters.

    Parameters
    ----------
    hed_term : str
        A single hed term
    Returns
    -------
    issue_list: [{}]
        A list of all formatting issues found in the term
    """
    issues_list = []
    if hed_term == "#":
        return issues_list

    for i, char in enumerate(hed_term):
        if i == 0 and not (char.isdigit() or char.isupper()):
            issues_list += ErrorHandler.format_error(SchemaWarnings.INVALID_CAPITALIZATION,
                                                     hed_term, char_index=i, problem_char=char)
            continue
        if char in ALLOWED_TAG_CHARS:
            continue
        if char.isalnum():
            continue
        issues_list += ErrorHandler.format_error(SchemaWarnings.INVALID_CHARACTERS_IN_TAG,
                                                 hed_term, char_index=i, problem_char=char)
    return issues_list


def validate_schema_description(tag_name, hed_description):
    """
    Takes a single term description and returns a list of warnings and errors in it.

    Parameters
    ----------
    tag_name : str
        A single hed tag - not validated here, just used for error messages
    hed_description: str
        The description string to validate
    Returns
    -------
    issue_list: [{}]
        A list of all formatting issues found in the description
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
