"""Legacy validation for terms and descriptions prior to 8.3.0."""
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import SchemaWarnings


ALLOWED_TAG_CHARS = "-"
ALLOWED_DESC_CHARS = "-_:;,./()+ ^"


def validate_schema_tag(hed_entry):
    """ Check short tag for capitalization and illegal characters.

    Parameters:
        hed_entry (HedTagEntry): A single HED term.

    Returns:
        list: A list of all formatting issues found in the term. Each issue is a dictionary.

    """
    issues_list = []
    hed_term = hed_entry.short_tag_name
    # Any # terms will have already been validated as the previous entry.
    if hed_term == "#":
        return issues_list

    for i, char in enumerate(hed_term):
        if i == 0 and not (char.isdigit() or char.isupper()):
            issues_list += ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION,
                                                     hed_term, char_index=i, problem_char=char)
            continue
        if char in ALLOWED_TAG_CHARS or char.isalnum():
            continue
        issues_list += ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_TAG,
                                                 hed_term, char_index=i, problem_char=char)
    return issues_list


def validate_schema_description(hed_entry):
    """ Check the description of a single schema entry.

    Parameters:
        hed_entry (HedSchemaEntry): A single schema entry

    Returns:
        list: A list of all formatting issues found in the description.

    """
    issues_list = []
    # Blank description is fine
    if not hed_entry.description:
        return issues_list
    for i, char in enumerate(hed_entry.description):
        if char.isalnum():
            continue
        if char in ALLOWED_DESC_CHARS:
            continue
        issues_list += ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_DESC,
                                                 hed_entry.description, hed_entry.name, char_index=i, problem_char=char)
    return issues_list


def verify_no_brackets(hed_entry):
    """ Extremely basic check to block curly braces

    Parameters:
        hed_entry (HedSchemaEntry): A single schema entry

    Returns:
        list: A list of issues for invalid characters found in the name
    """
    hed_term = hed_entry.name
    issues_list = []
    indexes = _get_disallowed_character_indexes(hed_term)
    for char, index in indexes:
        issues_list += ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_TAG,
                                                 hed_term, char_index=index, problem_char=char)
    return issues_list


def _get_disallowed_character_indexes(validation_string, index_adj=0, disallowed_chars="{}"):
    indexes = [(char, index + index_adj) for index, char in enumerate(validation_string) if char in disallowed_chars]
    return indexes
