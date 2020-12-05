"""
This module is used to report errors found in the validation.

"""

from hed.util.error_types import ValidationErrors, ValidationWarnings, SchemaErrors, SidecarErrors


def format_val_error(error_type, error_row=1, error_column=1, hed_string='', tag='', tag_prefix='', previous_tag='',
                     character='', index=0, unit_class_units='', file_name='', opening_parentheses_count=0,
                     closing_parentheses_count=0):
    """Reports the abc error based on the type of error.

    Parameters
    ----------
    error_type: str
        The type of abc error.
    error_row: int
        The row number that the error occurred on.
    error_column: int
        The column number that the error occurred on.
    hed_string: str
        The full HED string in which the error occurred
    tag: str
        The tag that generated the error. The original tag not the formatted one.
    tag_prefix: str
        The tag prefix that generated the error.
    previous_tag: str
        The previous tag that potentially could have generated the error. This is passed in with the tag.
    index: int
        The index in the string of where the error occurred.
    character: str
        The character in the string that generated the error.
    unit_class_units: str
        The unit class units that are associated with the error.
    file_name: str
        The invalid file name that cause the error.
    opening_parentheses_count: int
        The number of opening parentheses.
    closing_parentheses_count: int
        The number of closing parentheses.
    Returns
    -------
    list of dict
        A singleton list containing a dictionary with the error type and error message related to a particular type of
        error.

    """

    error_types = {
        ValidationErrors.ROW: 'Issues in row %s:\n' % str(error_row),
        ValidationErrors.COLUMN: 'Issues in row %s column %s:\n' % (str(error_row), str(error_column)),
        ValidationErrors.INVALID_FILENAME: '\tInvalid file name - "%s"\n' % file_name,
        ValidationErrors.PARENTHESES: '\tERROR: Number of opening and closing parentheses are unequal. %s opening parentheses. %s '
                                      'closing parentheses\n' % (opening_parentheses_count, closing_parentheses_count),
        ValidationErrors.INVALID_CHARACTER: '\tERROR: Invalid character "%s" at index %s of string "%s"'
                                            % (character, index, hed_string),
        ValidationErrors.COMMA_MISSING: '\tERROR: Comma missing after - "%s"\n' % tag,
        ValidationErrors.INVALID_COMMA: '\tERROR: Either "%s" contains a comma when it should not or "%s" is not a valid '
                                        'tag\n ' % (previous_tag, tag),
        ValidationErrors.DUPLICATE: '\tERROR: Duplicate tag - "%s"\n' % tag,
        ValidationErrors.REQUIRE_CHILD: '\tERROR: Descendant tag required - "%s"\n' % tag,
        ValidationErrors.EXTRA_TILDE: '\tERROR: Too many tildes - group "%s"\n' % tag,
        ValidationErrors.MULTIPLE_UNIQUE: '\tERROR: Multiple unique tags with prefix - "%s"\n' % tag_prefix,
        ValidationErrors.UNIT_CLASS_INVALID_UNIT: '\tERROR: Invalid unit - "%s" valid units are "%s"\n' % (
        tag, unit_class_units),
        ValidationErrors.INVALID_TAG: '\tERROR: Invalid tag - "%s"\n' % tag,
        ValidationErrors.EXTRA_DELIMITER: '\tERROR: Extra delimiter "%s" at index %s of string "%s"'
                                          % (character, index, hed_string),
    }
    default_error_message = 'ERROR: Unknown error'
    error_message = error_types.get(error_type, default_error_message)

    error_object = {'code': error_type, 'message': error_message}
    return [error_object]


def format_sidecar_error(error_type, filename="", column_name="", given_type="", expected_type="", pound_sign_count=0,
                         category_count=0):
    ERROR_PREFIX = "\tERROR: "
    error_types = {
        SidecarErrors.SIDECAR_FILE_NAME: f"Errors in file '{filename}'",
        SidecarErrors.SIDECAR_COLUMN_NAME: f"Errors in column '{column_name}':",
        SidecarErrors.INVALID_FILENAME: f"ERROR: File does not exist or cannot be opened. '{filename}'",
        SidecarErrors.CANNOT_PARSE_JSON: f"ERROR: Json file cannot be parsed. '{filename}'",
        SidecarErrors.BLANK_HED_STRING: f"{ERROR_PREFIX}No HED string found for Value or Category column.",
        SidecarErrors.WRONG_HED_DATA_TYPE: f"{ERROR_PREFIX}Invalid HED string datatype sidecar. Should be '{expected_type}', but got '{given_type}'",
        SidecarErrors.INVALID_NUMBER_POUND_SIGNS: f"{ERROR_PREFIX}There should be exactly one # character in a sidecar string. Found {pound_sign_count}",
        SidecarErrors.TOO_MANY_POUND_SIGNS: f"{ERROR_PREFIX}There should be no # characters in a category sidecar string. Found {pound_sign_count}",
        SidecarErrors.TOO_FEW_CATEGORIES: f"{ERROR_PREFIX}A category column should have at least two keys. Found {category_count}",
        SidecarErrors.UNKNOWN_COLUMN_TYPE: f"{ERROR_PREFIX}Could not automatically identify column '{column_name}' type from file. "
                                          f"Most likely the column definition in question needs a # sign to replace a number somewhere."
    }

    default_error_message = f'\tERROR: Unknown error {error_type}'
    error_message = error_types.get(error_type, default_error_message)

    error_object = {'code': error_type, 'message': error_message}
    return [error_object]


def format_val_warning(warning_type, tag='', default_unit='', tag_prefix=''):
    """Reports the abc warning based on the type of warning.

    Parameters
    ----------
    warning_type: string
        The type of abc warning.
    tag: string
        The tag that generated the warning. The original tag not the formatted one.
    default_unit: string
        The default unit class unit associated with the warning.
    tag_prefix: string
        The tag prefix that generated the warning.
    Returns
    -------
    list of dict
        A singleton list containing a dictionary with the warning type and warning message related to a particular type
        of warning.

    """
    warning_types = {
        ValidationWarnings.CAPITALIZATION: '\tWARNING: First word not capitalized or camel case - "%s"\n' % tag,
        ValidationWarnings.REQUIRED_PREFIX_MISSING: '\tWARNING: Tag with prefix "%s" is required\n' % tag_prefix,
        ValidationWarnings.UNIT_CLASS_DEFAULT_USED: '\tWARNING: No unit specified. Using "%s" as the default - "%s"\n' % (
        default_unit, tag)
    }
    default_warning_message = 'WARNING: Unknown warning'
    warning_message = warning_types.get(warning_type, default_warning_message)

    warning_object = {'code': warning_type, 'message': warning_message}
    return [warning_object]


SCHEMA_ERROR_PREFIX = "ERROR: "


def format_schema_error(error_type, hed_string, error_index=0, error_index_end=0, expected_parent_tag=None):
    """Reports the abc error based on the type of error.

    Parameters
    ----------
    error_type: str
        The type of abc error.
    Returns
    -------
    list of dict
        A singleton list containing a dictionary with the error type and error message related to a particular type of
        error.

    """
    problem_tag = hed_string[error_index:error_index_end]

    error_types = {
        SchemaErrors.INVALID_PARENT_NODE: f"{SCHEMA_ERROR_PREFIX}'{problem_tag}' appears as '{expected_parent_tag}' and cannot be used "
                                          f"as an extension.  {error_index}, {error_index_end}",
        SchemaErrors.NO_VALID_TAG_FOUND: f"{SCHEMA_ERROR_PREFIX}'{problem_tag}' is not a valid base hed tag.  {error_index}, {error_index_end} ",
        SchemaErrors.EMPTY_TAG_FOUND: f"{SCHEMA_ERROR_PREFIX}'Empty tag cannot be converted.",
        SchemaErrors.INVALID_SCHEMA: f"{SCHEMA_ERROR_PREFIX}'Source hed schema is invalid as it contains duplicate tags.  "
                                     f"Please fix if you wish to be abe to convert tags. {error_index}, {error_index_end}"
    }
    default_error_message = f'{SCHEMA_ERROR_PREFIX}Internal Error'
    error_message = error_types.get(error_type, default_error_message)

    error_object = {'code': error_type, 'message': error_message, 'source_string': hed_string}

    # Debug printing
    # print(f"{hed_string}")
    # print(error_message)

    return [error_object]


def add_row_and_column(error_object, row, col):
    old_error_msg = error_object['message']
    if old_error_msg.startswith(SCHEMA_ERROR_PREFIX):
        old_trimmed_msg = old_error_msg[len(SCHEMA_ERROR_PREFIX):]
        new_error_msg = f"ERROR on {row}, {col}: {old_trimmed_msg}"
        error_object["message"] = new_error_msg
    error_object["row_number"] = row
    error_object["column_number"] = col
