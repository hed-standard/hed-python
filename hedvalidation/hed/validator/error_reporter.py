"""
This module is used to report errors found in the validation.

"""


def report_error_type(error_type, error_row=1, error_column=1, hed_string='', tag='', tag_prefix='', previous_tag='',
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
        'row': 'Issues in row %s:\n' % str(error_row),
        'column': 'Issues in row %s column %s:\n' % (str(error_row), str(error_column)),
        'invalidFileName': '\tInvalid file name - "%s"\n' % file_name,
        'parentheses': '\tERROR: Number of opening and closing parentheses are unequal. %s opening parentheses. %s '
                       'closing parentheses\n' % (opening_parentheses_count, closing_parentheses_count),
        'invalidCharacter': '\tERROR: Invalid character "%s" at index %s of string "%s"'
                            % (character, index, hed_string),
        'commaMissing': '\tERROR: Comma missing after - "%s"\n' % tag,
        'extraCommaOrInvalid': '\tERROR: Either "%s" contains a comma when it should not or "%s" is not a valid '
                               'tag\n ' % (previous_tag, tag),
        'duplicateTag': '\tERROR: Duplicate tag - "%s"\n' % tag,
        'childRequired': '\tERROR: Descendant tag required - "%s"\n' % tag,
        'tooManyTildes': '\tERROR: Too many tildes - group "%s"\n' % tag,
        'multipleUniqueTags': '\tERROR: Multiple unique tags with prefix - "%s"\n' % tag_prefix,
        'unitClassInvalidUnit': '\tERROR: Invalid unit - "%s" valid units are "%s"\n' % (tag, unit_class_units),
        'invalidTag': '\tERROR: Invalid tag - "%s"\n' % tag,
        'extraDelimiter': '\tERROR: Extra delimiter "%s" at index %s of string "%s"'
                          % (character, index, hed_string),
    }
    default_error_message = 'ERROR: Unknown error'
    error_message = error_types.get(error_type, default_error_message)

    error_object = {'code': error_type, 'message': error_message}
    return [error_object]
