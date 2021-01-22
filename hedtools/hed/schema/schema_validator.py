from hed.util.hed_schema import HedSchema
from hed.util.error_reporter import format_schema_error, format_schema_warning, push_error_context, pop_error_context
from hed.util.error_types import SchemaErrors, SchemaWarnings, ErrorContext
from hed.util.exceptions import HedFileError

ALLOWED_TAG_CHARS = "-"
ALLOWED_DESC_CHARS = "-_:;,./()+ ^"


def validate_schema(hed_xml_file, also_check_for_warnings=True, display_filename=None):
    """
        Does validation of schema and returns a list of errors and warnings.

    Parameters
    ----------
    hed_xml_file : str
        filepath to a HED XML file to validate
    also_check_for_warnings : bool, default True
        If True, also checks for formatting issues like invalid characters, capitalization, etc.
    display_filename: str
        If present, it will display errors as coming from this filename instead of the actual source.
        Useful for temporary files and similar.
    Returns
    -------
    issue_list : [{}]
        A list of all warnings and errors found in the file.
    """
    issues_list = []
    try:
        hed_dict = HedSchema(hed_xml_file, display_filename=display_filename)
    except HedFileError as e:
        return e.format_error_message()

    if not display_filename:
        display_filename = hed_xml_file

    push_error_context(ErrorContext.FILE_NAME, display_filename)
    if hed_dict.has_duplicate_tags():
        duplicate_dict = hed_dict.find_duplicate_tags()
        for tag_name, long_org_tags in duplicate_dict.items():
            issues_list += format_schema_error(SchemaErrors.DUPLICATE_TERMS, tag_name, duplicate_tag_list=long_org_tags)

    if also_check_for_warnings:
        hed_terms = hed_dict.get_all_terms()
        for hed_term in hed_terms:
            issues_list += validate_schema_term(hed_term)

        tag_descs = hed_dict.get_all_descriptions()
        for tag_name, desc in tag_descs.items():
            issues_list += validate_schema_description(tag_name, desc)

    pop_error_context()
    return issues_list


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
            issues_list += format_schema_warning(SchemaWarnings.INVALID_CAPITALIZATION, hed_term,
                                                 error_index=i, problem_char=char)
            continue
        if char in ALLOWED_TAG_CHARS:
            continue
        if char.isalnum():
            continue
        issues_list += format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_TAG, hed_term,
                                             error_index=i, problem_char=char)
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
        issues_list += format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, tag_name, hed_description, i, char)
    return issues_list