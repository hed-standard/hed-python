import datetime
import re


DATE_TIME_VALUE_CLASS = 'dateTimeClass'
NUMERIC_VALUE_CLASS = "numericClass"
TEXT_VALUE_CLASS = "textClass"
NAME_VALUE_CLASS = "nameClass"

DIGIT_OR_POUND_EXPRESSION = r'^(-?[\d.]+(?:e-?\d+)?|#)$'


def is_date_time(date_time_string):
    """Checks to see if the specified string is a valid ISO 8601 datetime string.

    Parameters
    ----------
    date_time_string: str
        A datetime string.
    Returns
    -------
    bool
        True if the datetime string is valid. False, if otherwise.

    """
    try:
        date_time_obj = datetime.datetime.fromisoformat(date_time_string)
        return not date_time_obj.tzinfo
    except ValueError:
        return False


def validate_numeric_value_class(numeric_string):
    """Checks to see if the specified string is a valid ISO 8601 datetime string.

    Parameters
    ----------
    numeric_string: str
        A string that should be only a number, with no units at all.
    Returns
    -------
    bool
        True if the numeric string is valid. False, if otherwise.

    """
    if re.search(DIGIT_OR_POUND_EXPRESSION, numeric_string):
        return True

    return False


def validate_text_value_class(text_string):
    """
        Placeholder for eventual text value class validation

    Parameters
    ----------
    text_string :

    Returns
    -------

    """
    return True


def is_clock_face_time(time_string):
    """Checks to see if the specified string is a valid HH:MM time string.

    This is deprecated and has no expected use going forward.
    Parameters
    ----------
    time_string: str
        A time string.
    Returns
    -------
    bool
        True if the time string is valid. False, if otherwise.

    """
    try:
        time_obj = datetime.time.fromisoformat(time_string)
        return not time_obj.tzinfo and not time_obj.microsecond
    except ValueError:
        return False
