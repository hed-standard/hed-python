"""
This module is used to report warnings found in the validation.

"""


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
        The tag prefix that generated the warning.
    Returns
    -------
    list of dict
        A singleton list containing a dictionary with the warning type and warning message related to a particular type
        of warning.

    """
    warning_types = {
        'capitalization': '\tWARNING: First word not capitalized or camel case - "%s"\n' % tag,
        'requiredPrefixMissing': '\tWARNING: Tag with prefix "%s" is required\n' % tag_prefix,
        'unitClassDefaultUsed': '\tWARNING: No unit specified. Using "%s" as the default - "%s"\n' % (default_unit, tag)
    }
    default_warning_message = 'WARNING: Unknown warning'
    warning_message = warning_types.get(warning_type, default_warning_message)

    warning_object = {'code': warning_type, 'message': warning_message}
    return [warning_object]
