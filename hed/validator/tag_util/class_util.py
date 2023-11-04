""" Utilities to support HED validation. """
import datetime
import re


from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors


class UnitValueValidator:
    DATE_TIME_VALUE_CLASS = 'dateTimeClass'
    NUMERIC_VALUE_CLASS = "numericClass"
    TEXT_VALUE_CLASS = "textClass"
    NAME_VALUE_CLASS = "nameClass"

    DIGIT_OR_POUND_EXPRESSION = r'^(-?[\d.]+(?:e-?\d+)?|#)$'

    def __init__(self, value_validators=None):
        """ Validates the unit and value classes on a given tag.

        Parameters:
            value_validators(dict or None): Override or add value class validators

        """
        self._value_validators = self._get_default_value_class_validators()
        if value_validators and isinstance(value_validators, dict):
            self._value_validators.update(value_validators)

    def _get_default_value_class_validators(self):
        validator_dict = {
            self.DATE_TIME_VALUE_CLASS: is_date_time,
            self.NUMERIC_VALUE_CLASS: validate_numeric_value_class,
            self.TEXT_VALUE_CLASS: validate_text_value_class,
            self.NAME_VALUE_CLASS: validate_text_value_class
        }

        return validator_dict

    def check_tag_unit_class_units_are_valid(self, original_tag, report_as=None, error_code=None):
        """ Report incorrect unit class or units.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            report_as (HedTag): Report errors as coming from this tag, rather than original_tag.
            error_code (str): Override error codes
        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        if original_tag.is_unit_class_tag():
            stripped_value, unit = original_tag.get_stripped_unit_value()
            if not unit:
                # Todo: in theory this should separately validate the number and the units, for units
                # that are prefixes like $.  Right now those are marked as unit invalid AND value_invalid.
                bad_units = " " in original_tag.extension

                if bad_units:
                    stripped_value = stripped_value.split(" ")[0]

                validation_issues += self._check_value_class(original_tag, stripped_value, report_as, error_code)
                validation_issues += self._check_units(original_tag, bad_units, report_as)

                # We don't want to give this overall error twice
                if error_code and not any(error_code == issue['code'] for issue in validation_issues):
                    new_issue = validation_issues[0].copy()
                    new_issue['code'] = error_code
                    validation_issues += [new_issue]

        return validation_issues

    def check_tag_value_class_valid(self, original_tag, report_as=None, error_code=None):
        """ Report an invalid value portion.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            report_as (HedTag): Report errors as coming from this tag, rather than original_tag.
            error_code (str): Override error codes
        Returns:
            list: Validation issues.
        """
        return self._check_value_class(original_tag, original_tag.extension, report_as, error_code)

    def _check_value_class(self, original_tag, stripped_value, report_as, error_code=None):
        """Returns any issues found if this is a value tag"""
        validation_issues = []
        if original_tag.is_takes_value_tag() and \
                not self._validate_value_class_portion(original_tag, stripped_value):
            report_as = report_as if report_as else original_tag
            validation_issues += ErrorHandler.format_error(ValidationErrors.VALUE_INVALID, report_as)
            if error_code:
                validation_issues += ErrorHandler.format_error(ValidationErrors.VALUE_INVALID,
                                                               report_as, actual_error=error_code)
        return validation_issues

    @staticmethod
    def _check_units(original_tag, bad_units, report_as):
        """Returns an issue noting this is either bad units, or missing units"""
        report_as = report_as if report_as else original_tag
        if bad_units:
            tag_unit_class_units = original_tag.get_tag_unit_class_units()
            validation_issue = ErrorHandler.format_error(ValidationErrors.UNITS_INVALID,
                                                         tag=report_as, units=tag_unit_class_units)
        else:
            default_unit = original_tag.default_unit
            validation_issue = ErrorHandler.format_error(ValidationErrors.UNITS_MISSING,
                                                         tag=report_as, default_unit=default_unit)
        return validation_issue

    def _validate_value_class_portion(self, original_tag, portion_to_validate):
        if portion_to_validate is None:
            return False

        value_class_types = original_tag.value_classes
        return self.validate_value_class_type(portion_to_validate, value_class_types)

    def validate_value_class_type(self, unit_or_value_portion, valid_types):
        """ Report invalid unit or valid class values.

        Parameters:
            unit_or_value_portion (str): The value portion to validate.
            valid_types (list): The names of value class or unit class types (e.g. dateTime or dateTimeClass).

        Returns:
            type_valid (bool): True if this is one of the valid_types validators.

        """
        for unit_class_type in valid_types:
            valid_func = self._value_validators.get(unit_class_type)
            if valid_func:
                if valid_func(unit_or_value_portion):
                    return True
        return False


def is_date_time(date_time_string):
    """Check if the specified string is a valid datetime.

    Parameters:
        date_time_string (str): A datetime string.

    Returns:
        bool: True if the datetime string is valid. False, if otherwise.

    Notes:
        - ISO 8601 datetime string.

    """
    try:
        date_time_obj = datetime.datetime.fromisoformat(date_time_string)
        return not date_time_obj.tzinfo
    except ValueError:
        return False


def validate_numeric_value_class(numeric_string):
    """ Checks to see if valid numeric value.

    Parameters:
        numeric_string (str): A string that should be only a number with no units.

    Returns:
        bool: True if the numeric string is valid. False, if otherwise.

    """
    if re.search(UnitValueValidator.DIGIT_OR_POUND_EXPRESSION, numeric_string):
        return True

    return False


def validate_text_value_class(text_string):
    """ Placeholder for eventual text value class validation

    Parameters:
        text_string (str): Text class.

    Returns:
        bool: True

    """
    return True


def is_clock_face_time(time_string):
    """ Check if a valid HH:MM time string.

    Parameters:
        time_string (str): A time string.

    Returns:
        bool: True if the time string is valid. False, if otherwise.

    Notes:
        - This is deprecated and has no expected use going forward.

    """
    try:
        time_obj = datetime.time.fromisoformat(time_string)
        return not time_obj.tzinfo and not time_obj.microsecond
    except ValueError:
        return False
