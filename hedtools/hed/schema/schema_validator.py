from hed import schema
from hed.util import error_reporter
from hed.util.error_types import SchemaErrors, SchemaWarnings, ErrorContext

ALLOWED_TAG_CHARS = "-"
ALLOWED_DESC_CHARS = "-_:;,./()+ ^"


def validate_schema(schema_filename, also_check_for_warnings=True, display_filename=None,
                    error_handler=None):
    """
        Does validation of schema and returns a list of errors and warnings.

    Parameters
    ----------
    schema_filename : str
        filepath to a HED XML/wikimedia file to validate
    also_check_for_warnings : bool, default True
        If True, also checks for formatting issues like invalid characters, capitalization, etc.
    display_filename: str
        If present, will use this as the filename for context, rather than using the actual filename
        Useful for temp filenames.
    error_handler : ErrorHandler or None
        Used to report errors.  Uses a default one if none passed in.
    Returns
    -------
    issue_list : [{}]
        A list of all warnings and errors found in the file.
    """
    if error_handler is None:
        error_handler = error_reporter.ErrorHandler()
    issues_list = []
    hed_schema = schema.load_schema(schema_filename)

    if not display_filename:
        display_filename = schema_filename
    error_handler.push_error_context(ErrorContext.FILE_NAME, display_filename)

    if hed_schema.has_duplicate_tags():
        duplicate_dict = hed_schema.find_duplicate_tags()
        for tag_name, long_org_tags in duplicate_dict.items():
            issues_list += error_handler.format_schema_error(SchemaErrors.DUPLICATE_TERMS, tag_name,
                                                             duplicate_tag_list=long_org_tags)

    if also_check_for_warnings:
        hed_terms = hed_schema.get_all_tags(True)
        for hed_term in hed_terms:
            issues_list += validate_schema_term(hed_term, error_handler=error_handler)

        for tag_name, desc in hed_schema.get_desc_dict().items():
            issues_list += validate_schema_description(tag_name, desc, error_handler=error_handler)

    error_handler.pop_error_context()
    return issues_list


def validate_schema_term(hed_term, error_handler):
    """
    Takes a single term(ie short tag) and checks capitalization and illegal characters.

    Parameters
    ----------
    hed_term : str
        A single hed term
    error_handler : ErrorHandler
        Used to report errors
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
            issues_list += error_handler.format_schema_warning(SchemaWarnings.INVALID_CAPITALIZATION, hed_term,
                                                               error_index=i, problem_char=char)
            continue
        if char in ALLOWED_TAG_CHARS:
            continue
        if char.isalnum():
            continue
        issues_list += error_handler.format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_TAG, hed_term,
                                                           error_index=i, problem_char=char)
    return issues_list


def validate_schema_description(tag_name, hed_description, error_handler):
    """
    Takes a single term description and returns a list of warnings and errors in it.

    Parameters
    ----------
    tag_name : str
        A single hed tag - not validated here, just used for error messages
    hed_description: str
        The description string to validate
    error_handler : ErrorHandler
        Used to report errors
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
        issues_list += error_handler.format_schema_warning(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, tag_name,
                                                           hed_description, i, char)
    return issues_list


def get_printable_issue_string(validation_issues, title=None, severity=None, skip_filename=True):
    """Return a string with issues list flatted into single string, one per line

    Parameters
    ----------
    validation_issues: []
        Issues to print
    title: str
        Optional title that will always show up first if present(even if there are no validation issues)
    severity: int
        Return only warnings >= severity
    skip_filename: bool
        If true, don't add the filename context to the printable string.
    Returns
    -------
    str
        A str containing printable version of the issues or '[]'.

    """
    return error_reporter.ErrorHandler.get_printable_issue_string(validation_issues, title, severity, skip_filename)
