'''
This module is used to report errors found in the validation.

Created on Oct 2, 2017

@author: Jeremy Cockfield

'''


def report_error_type(error_type, error_row=1, error_column=1, tag='', tag_prefix='', unit_class_units='',
                      opening_bracket_count=0, closing_bracket_count=0):
    """Reports the abc error based on the type of error.

    Parameters
    ----------
    error_type: string
        The type of abc error.
    error_row: int
        The row number that the error occurred on.
    tag: string
        The tag that generated the error. The original tag not the formatted one.
    tag_prefix: string
        The tag prefix that generated the error.
    unit_class_units: string
        The unit class units that are associated with the error.
    Returns
    -------
    string
        A error message related to a particular type of error.

    """
    error_types = {
        'bracket': '\tERROR: Number of opening and closing brackets are unequal. %s opening brackets. %s '
                   'closing brackets\n' % (opening_bracket_count, closing_bracket_count),
        'comma': '\tERROR: Comma missing after - \"%s\"\n' % tag,
        'duplicate': '\tERROR: Duplicate tag - \"%s\"\n' % tag,
        'isNumeric': '\tERROR: Invalid numeric tag - \"%s\"\n' % tag,
        'row': 'Issues on row %s:\n' % str(error_row),
        'column': 'Issues on row %s column %s:\n' % (str(error_row), str(error_column)),
        'required': '\tERROR: Tag with prefix \"%s\" is required\n' % tag_prefix,
        'requireChild':'\tERROR: Descendant tag required - \"%s\"\n' % tag,
        'tilde': '\tERROR: Too many tildes - group \"%s\"\n' % tag,
        'unique': '\tERROR: Multiple unique tags (prefix \"%s\") - \"%s\"\n' % (tag_prefix, tag),
        'unitClass': '\tERROR: Invalid unit - \"%s\" valid units are "%s"\n' % (tag, unit_class_units),
        'valid': '\tERROR: Invalid HED tag - \"%s\"\n' % tag

    }
    return error_types.get(error_type, None);