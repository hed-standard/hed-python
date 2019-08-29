'''
This module is used to report errors found in the validation.

Created on Oct 2, 2017

@author: Jeremy Cockfield

'''


def report_error_type(error_type, error_row=1, error_column=1, tag='', tag_prefix='', previous_tag='',
                      unit_class_units='', opening_bracket_count=0, closing_bracket_count=0):
    """Reports the abc error based on the type of error.

    Parameters
    ----------
    error_type: string
        The type of abc error.
    error_row: int
        The row number that the error occurred on.
    error_column: int
        The column number that the error occurred on.
    tag: string
        The tag that generated the error. The original tag not the formatted one.
    tag_prefix: string
        The tag prefix that generated the error.
    previous_tag: string
        The previous tag that potentially could have generated the error. This is passed in with the tag.
    unit_class_units: string
        The unit class units that are associated with the error.
    opening_bracket_count: int
        The number of opening brackets.
    closing_bracket_count: int
        The number of closing brackets.
    Returns
    -------
    string
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
        'valid': '\tERROR: Invalid tag - \"%s\"\n' % tag

    }
    return error_types.get(error_type, None);
