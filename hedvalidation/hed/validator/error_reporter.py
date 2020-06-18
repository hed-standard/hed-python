"""
This module is used to report errors found in the validation.

"""


def report_error_type(error_type, error_row=1, error_column=1, hed_string='', tag='', tag_prefix='', previous_tag='',
                      character='', index=0, unit_class_units='', opening_bracket_count=0, closing_bracket_count=0):
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
    opening_bracket_count: int
        The number of opening brackets.
    closing_bracket_count: int
        The number of closing brackets.
    Returns
    -------
    str
        A error message related to a particular type of error.

    """
    error_types = {
        'bracket': '\tERROR: Number of opening and closing parentheses are unequal. %s opening parentheses. %s '
                   'closing parentheses\n' % (opening_bracket_count, closing_bracket_count),
        'character': '\tERROR: Invalid character \"%s\"\n' % tag,
        'comma': '\tERROR: Comma missing after - \"%s\"\n' % tag,
        'commaValid': '\tERROR: Either \"%s\" contains a comma when it should not or \"%s\" is not a valid tag\n'
                      % (previous_tag, tag),
        'duplicate': '\tERROR: Duplicate tag - \"%s\"\n' % tag,
        'isNumeric': '\tERROR: Invalid numeric tag - \"%s\"\n' % tag,
        'row': 'Issues in row %s:\n' % str(error_row),
        'column': 'Issues in row %s column %s:\n' % (str(error_row), str(error_column)),
        'requireChild': '\tERROR: Descendant tag required - \"%s\"\n' % tag,
        'tilde': '\tERROR: Too many tildes - group \"%s\"\n' % tag,
        'unique': '\tERROR: Multiple unique tags with prefix - \"%s\"\n' % tag_prefix,
        'unitClass': '\tERROR: Invalid unit - \"%s\" valid units are "%s"\n' % (tag, unit_class_units),
        'valid': '\tERROR: Invalid tag - \"%s\"\n' % tag,
        'extraDelimiter': '\tERROR: Extra delimiter \"%s\" at index %s of string \"%s\"'
                          % (character, index, hed_string),
        'invalidCharacter': '\tERROR: ',
    }
    return error_types.get(error_type, None)
