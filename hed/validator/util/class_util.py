"""Utilities to support HED validation."""

import warnings

from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors
from hed.validator.util.char_util import CharRexValidator


class UnitValueValidator:
    """Validates units."""

    def __init__(self, modern_allowed_char_rules=False, value_validators=None):
        """Validates the unit and value classes on a given tag.

        Parameters:
            modern_allowed_char_rules (bool): If True, use the 8.3.0 and later character rules.
            value_validators (dict or None): Deprecated, removed in hedtools 2.0.0. Accepted so
                that existing callers keep working; it has no effect. The per-class validator
                functions it used to override were never reached by validation.

        Notes:
            The per-character sets and the whole-value rules of each value class come from
            ``hed/validator/data/class_regex.json`` through ``CharRexValidator``; there is no
            per-class validator function.
        """

        if value_validators is not None:
            warnings.warn(
                "The value_validators= parameter of UnitValueValidator is deprecated and will be removed in "
                "hedtools 2.0.0; it has no effect. Value class rules come from hed/validator/data/class_regex.json.",
                DeprecationWarning,
                stacklevel=2,
            )
        self._validate_characters = modern_allowed_char_rules
        self._char_validator = CharRexValidator()

    def check_tag_unit_class_units_are_valid(
        self, original_tag, validate_text, report_as=None, error_code=None, allow_placeholders=True
    ) -> list[dict]:
        """Report incorrect unit class or units.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            validate_text (str): The text to validate.
            report_as (HedTag): Report errors as coming from this tag, rather than original_tag.
            error_code (str): Override error codes.
            allow_placeholders (bool): Whether placeholders are allowed (affects value class validation for "#")

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        if not original_tag.is_unit_class_tag():
            return []

        validation_issues = []
        # Check the units first
        stripped_value, units = original_tag.get_stripped_unit_value(validate_text)
        if not stripped_value:
            # stripped_value is None only when invalid units are present
            validation_issues += self._report_bad_units(original_tag, report_as)
            return validation_issues

        # If value is a placeholder (#) and placeholders are allowed, it's valid
        # Invalid units would have been caught above (stripped_value would be None)
        if stripped_value == "#" and allow_placeholders:
            return validation_issues

        # Check the value classes
        # If placeholders are NOT allowed, "#" will fail value class validation (e.g., not a valid number)
        validation_issues += self._check_value_class(original_tag, stripped_value, report_as)

        # Override error code if specified (for def/def-expand tags)
        if error_code and validation_issues and not any(error_code == issue["code"] for issue in validation_issues):
            new_issue = validation_issues[0].copy()
            new_issue["code"] = error_code
            validation_issues += [new_issue]

        return validation_issues

    def check_tag_value_class_valid(self, original_tag, validate_text, report_as=None) -> list[dict]:
        """Report an invalid value portion.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            validate_text (str): The text to validate.
            report_as (HedTag): Report errors as coming from this tag, rather than original_tag.

        Returns:
            list: Validation issues.
        """
        return self._check_value_class(original_tag, validate_text, report_as)

    def _get_problem_indices(self, stripped_value, class_name, start_index=0, class_entry=None):
        declared = None
        if class_entry is not None:
            declared = [name for name in class_entry.attributes.get("allowedCharacter", "").split(",") if name]
        indices = self._char_validator.get_problem_chars(stripped_value, class_name, declared_names=declared)
        if indices:
            indices = [(char, index + start_index) for index, char in indices]
        return indices

    def _check_value_class(self, original_tag, stripped_value, report_as):
        """Return any issues found if this is a value tag,

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            stripped_value (str): value without units
            report_as (HedTag): Report as this tag.

        Returns:
            list:  List of dictionaries of validation issues.

        """

        if not original_tag.is_takes_value_tag():
            return []

        value_classes = original_tag.value_classes
        classes = list(value_classes.keys())
        if not classes:
            return []
        start_index = original_tag.extension.find(stripped_value) + len(original_tag.org_base_tag) + 1

        report_as = report_as if report_as else original_tag
        class_valid = {}
        for class_name in classes:
            class_valid[class_name] = self._char_validator.is_valid_value(stripped_value, class_name)

        char_errors = {}
        for class_name in classes:
            char_errors[class_name] = self._get_problem_indices(
                stripped_value, class_name, start_index=start_index, class_entry=value_classes[class_name]
            )
            if class_valid[class_name] and not char_errors[class_name]:  # We have found a valid class
                return []

        validation_issues = self.report_value_errors(char_errors, class_valid, report_as)
        return validation_issues

    @staticmethod
    def report_value_errors(error_dict, class_valid, report_as):
        """Build validation issues from per-class character error and validity dicts.

        Parameters:
            error_dict (dict): Mapping of class name to list of (char, index) problem tuples.
            class_valid (dict): Mapping of class name to a validity result (``True``, ``re.Match``, or ``False``)
                indicating whether the full value passed word-level format validation for that class.
            report_as (HedTag): The tag object used as context in error reporting.

        Returns:
            list[dict]: Validation issue dictionaries.

        """
        validation_issues = []
        for class_name, errors in error_dict.items():
            if not errors and class_valid[class_name]:
                continue
            elif not class_valid[class_name]:
                validation_issues += ErrorHandler.format_error(
                    ValidationErrors.INVALID_VALUE_CLASS_VALUE,
                    index_in_tag=0,
                    index_in_tag_end=len(report_as.org_tag),
                    value_class=class_name,
                    tag=report_as,
                )
            elif errors:
                validation_issues.extend(UnitValueValidator.report_value_char_errors(class_name, errors, report_as))
        return validation_issues

    @staticmethod
    def report_value_char_errors(class_name, errors, report_as):
        """Build validation issues for specific invalid characters within a value class string.

        Parameters:
            class_name (str): The value class name that detected the errors.
            errors (list[tuple[str, int]]): Character/index pairs of invalid characters.
            report_as (HedTag): The tag object used as context in error reporting.

        Returns:
            list[dict]: Validation issue dictionaries.

        """
        validation_issues = []
        for value in errors:
            if value[0] in "{}":
                validation_issues += ErrorHandler.format_error(
                    ValidationErrors.CURLY_BRACE_UNSUPPORTED_HERE, tag=report_as, problem_tag=value[0]
                )
            else:
                validation_issues += ErrorHandler.format_error(
                    ValidationErrors.INVALID_VALUE_CLASS_CHARACTER,
                    tag=report_as,
                    value_class=class_name,
                    problem_tag=value[0],
                )
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
