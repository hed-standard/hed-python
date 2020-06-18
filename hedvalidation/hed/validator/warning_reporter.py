'''
This module is used to report warnings found in the validation.

'''


def report_warning_type(warning_type, tag='', default_unit='', tag_prefix=''):
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
        The tag prefix that generated the error.
    Returns
    -------
    string
        A warning message related to a particular type of warning.

    """
    warning_types = {
        'cap': '\tWARNING: First word not capitalized or camel case - "%s"\n' % tag,
        'required': '\tWARNING: Tag with prefix \"%s\" is required\n' % tag_prefix,
        'unitClass': '\tWARNING: No unit specified. Using "%s" as the default - "%s"\n' % (default_unit, tag)
    }
    return warning_types.get(warning_type, None)