'''
This module is used to report warnings found in the validation.

Created on Oct 2, 2017

@author: Jeremy Cockfield

'''


def report_warning_type(warning_type, tag='', default_unit=''):
    """Reports the abc warning based on the type of warning.

    Parameters
    ----------
    warning_type: string
        The type of abc warning.
    tag: string
        The tag that generated the warning. The original tag not the formatted one.
    default_unit: string
        The default unit class unit associated with the warning.
    Returns
    -------
    string
        A warning message related to a particular type of warning.

    """
    warning_types = {
        'cap': '\tWARNING: First word not capitalized or camel case - "%s"\n' % tag,
        'unitClass': '\tWARNING: No unit specified. Using "%s" as the default - "%s"' % (default_unit, tag)
    }
    return warning_types.get(warning_type, None);