""" Utilities to support HED validation. """
import datetime
import re

from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors
from hed.validator.util.char_util import CharRexValidator


class UnitValueValidator:
    """ Validates units. """
    DATE_TIME_VALUE_CLASS = 'dateTimeClass'
    NUMERIC_VALUE_CLASS = "numericClass"
    TEXT_VALUE_CLASS = "textClass"
    NAME_VALUE_CLASS = "nameClass"

    DIGIT_OR_POUND_EXPRESSION = r'^(-?[\d.]+(?:e-?\d+)?|#)$'

    def __init__(self, modern_allowed_char_rules=False, value_validators=None):
        """ Validates the unit and value classes on a given tag.

        Parameters:
            value_validators(dict or None): Override or add value class validators

        """

        self._validate_characters = modern_allowed_char_rules
        self._value_validators = self._get_default_value_class_validators()
        self._char_validator = CharRexValidator()
        if value_validators and isinstance(value_validators, dict):
            self._value_validators.update(value_validators)

    def _get_default_value_class_validators(self):
        """ Return a dictionary of value class validator functions.

        Returns:
            dict:  Dictionary of value class validator functions.

        """
        validator_dict = {
            self.DATE_TIME_VALUE_CLASS: is_date_time_value_class,
            self.NUMERIC_VALUE_CLASS: is_numeric_value_class,
            self.TEXT_VALUE_CLASS: is_text_value_class,
            self.NAME_VALUE_CLASS: is_name_value_class
        }

        return validator_dict

    def check_tag_unit_class_units_are_valid(self, original_tag, validate_text, report_as=None, error_code=None) -> list[dict]:
        """ Report incorrect unit class or units.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            validate_text (str): The text to validate.
            report_as (HedTag): Report errors as coming from this tag, rather than original_tag.
            error_code (str): Override error codes.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        if original_tag.is_unit_class_tag():

            # Check the units first
            stripped_value, units = original_tag.get_stripped_unit_value(validate_text)
            if not stripped_value:
                validation_issues += self._report_bad_units(original_tag, report_as)
                return validation_issues

            # Check the value classes
            validation_issues += self._check_value_class(original_tag, stripped_value, report_as)
            if validation_issues:
                return validation_issues

            # We don't want to give this overall error twice
            if error_code and validation_issues and not any(error_code == issue['code'] for issue in validation_issues):
                new_issue = validation_issues[0].copy()
                new_issue['code'] = error_code
                validation_issues += [new_issue]

        return validation_issues

    def check_tag_value_class_valid(self, original_tag, validate_text, report_as=None) -> list[dict]:
        """ Report an invalid value portion.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            validate_text (str): The text to validate.
            report_as (HedTag): Report errors as coming from this tag, rather than original_tag.

        Returns:
            list: Validation issues.
        """
        return self._check_value_class(original_tag, validate_text, report_as)

    def _get_problem_indices(self, stripped_value, class_name, start_index=0):
        indices = self._char_validator.get_problem_chars(stripped_value, class_name)
        if indices:
            indices = [(char, index + start_index) for index, char in indices]
        return indices
        # value_classes = original_tag.value_classes.values()
        # allowed_characters = schema_validation_util.get_allowed_characters(original_tag.value_classes.values())

    def _check_value_class(self, original_tag, stripped_value, report_as):
        """ Return any issues found if this is a value tag,

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            stripped_value (str): value without units
            report_as (HedTag): Report as this tag.

        Returns:
            list:  List of dictionaries of validation issues.

        """

        if not original_tag.is_takes_value_tag():
            return []

        classes = list(original_tag.value_classes.keys())
        if not classes:
            return []
        start_index = original_tag.extension.find(stripped_value) + len(original_tag.org_base_tag) + 1

        report_as = report_as if report_as else original_tag
        class_valid = {}
        for class_name in classes:
            class_valid[class_name] = self._char_validator.is_valid_value(stripped_value, class_name)

        char_errors = {}
        for class_name in classes:
            char_errors[class_name] = self._get_problem_indices(stripped_value, class_name, start_index=start_index)
            if class_valid[class_name] and not char_errors[class_name]:  # We have found a valid class
                return []

        validation_issues = self.report_value_errors(char_errors, class_valid, report_as)
        return validation_issues

    @staticmethod
    def report_value_errors(error_dict, class_valid, report_as):
        validation_issues = []
        for class_name, errors in error_dict.items():
            if not errors and class_valid[class_name]:
                continue
            elif not class_valid[class_name]:
                validation_issues += ErrorHandler.format_error(ValidationErrors.INVALID_VALUE_CLASS_VALUE,
                                                               index_in_tag=0, index_in_tag_end=len(report_as.org_tag),
                                                               value_class=class_name, tag=report_as)
            elif errors:
                validation_issues.extend(UnitValueValidator.report_value_char_errors(class_name, errors, report_as))
        return validation_issues

    @staticmethod
    def report_value_char_errors(class_name, errors, report_as):
        validation_issues = []
        for value in errors:
            if value[0] in "{}":
                validation_issues += ErrorHandler.format_error(ValidationErrors.CURLY_BRACE_UNSUPPORTED_HERE,
                                                               tag=report_as, problem_tag=value[0])
            else:
                validation_issues += ErrorHandler.format_error(ValidationErrors.INVALID_VALUE_CLASS_CHARACTER,
                                                               tag=report_as, value_class=class_name,
                                                               problem_tag=value[0])
        return validation_issues

    @staticmethod
    def _report_bad_units(original_tag, report_as):
        """Returns an issue noting this is bad units

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            report_as (HedTag): Report as this tag.

        Returns:
            list:  List of dictionaries of validation issues.

        """
        report_as = report_as if report_as else original_tag
        tag_unit_class_units = original_tag.get_tag_unit_class_units()
        return ErrorHandler.format_error(ValidationErrors.UNITS_INVALID, tag=report_as, units=tag_unit_class_units)

    def _validate_value_class_portion(self, original_tag, portion_to_validate):
        if portion_to_validate is None:
            return False

        value_class_types = original_tag.value_classes
        return self.validate_value_class_type(portion_to_validate, value_class_types)

    def validate_value_class_type(self, unit_or_value_portion, valid_types) -> bool:
        """ Report invalid unit or valid class values.

        Parameters:
            unit_or_value_portion (str): The value portion to validate.
            valid_types (list): The names of value class or unit class types (e.g. dateTime or dateTimeClass).

        Returns:
            bool: True if this is one of the valid_types validators.

        """
        has_valid_func = False
        for unit_class_type in valid_types:
            valid_func = self._value_validators.get(unit_class_type)
            if valid_func:
                has_valid_func = True
                if valid_func(unit_or_value_portion):
                    return True
        return not has_valid_func


def find_invalid_positions(s, pattern):
    # List to store positions of invalid characters
    invalid_positions = []

    # Iterate over the string, check each character
    for i, char in enumerate(s):
        if not re.match(pattern, char):
            # If the character does not match, record its position and value
            invalid_positions.append((i, char))

    return invalid_positions


def is_date_time_value_class(date_time_string) -> bool:
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


def is_name_value_class(name_str) -> bool:
    pattern = r'^[\w\-\u0080-\uFFFF]+$'
    if re.fullmatch(pattern, name_str):
        return True
    else:
        return False


def is_numeric_value_class(numeric_string) -> bool:
    """ Check to see if valid numeric value.

    Parameters:
        numeric_string (str): A string that should be only a number with no units.

    Returns:
        bool: True if the numeric string is valid. False, if otherwise.

    """
    if re.search(UnitValueValidator.DIGIT_OR_POUND_EXPRESSION, numeric_string):
        return True

    return False


def is_text_value_class(text_string) -> bool:
    """ Placeholder for eventual text value class validation.

    Parameters:
        text_string (str): Text class.

    Returns:
        bool: True

    """
    return True


def is_clock_face_time(time_string) -> bool:
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
