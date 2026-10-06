"""Classes responsible for basic character validation of a string or tag."""

import datetime

from semantic_version import Version

from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors
from hed.schema.schema_io.schema_util import schema_version_greater_equal
from hed.validator.util.character_sets import CharacterSets, code_point

# The character sets a tag extension may use (specification 3.2.5 says ``name`` characters; hedtools has always
# also admitted the characters below, which appear in extensions of existing datasets).
EXTENSION_SETS = (
    "alphanumeric",
    "hyphen",
    "underscore",
    "forward-slash",
    "period",
    "plus",
    "caret",
    "blank",
    "number-sign",
    "colon",
    "nonascii",
)
# The character sets of the schema path of a tag (the part matched to schema nodes).
TAG_PATH_SETS = ("alphanumeric", "hyphen", "underscore", "forward-slash", "colon", "nonascii")
# The value class used for a value whose placeholder declares no valueClass (decision 2026-09-30, D3).
UNCLASSED_VALUE_SETS = ("value-text",)
# The version from which pre-8.3.0 schemas' ASCII-only rule no longer applies, for the message.
ASCII_ONLY_BEFORE = "8.3.0"
# Message clauses for the string-level checks (specification Appendix B CHARACTER_INVALID b).
COLUMN_BRACES_RULE = "curly braces may appear only in a sidecar column reference"
# The value class whose whole-value rule is a date-time. After the shape regex the date must exist in the
# Gregorian calendar (Kay, 2026-10-02: the BIDS text says so, even though the BIDS validator checks only the
# regex). The leap second ``:60`` the regex admits is not a calendar question and stays allowed.
DATE_TIME_CLASS = "dateTimeClass"


def _standard_version(hed_schema):
    """Return the highest standard schema version a schema or schema group is based on, or None.

    A standard schema contributes its own version; a partnered library its ``withStandard`` version; an
    unpartnered library nothing. None means no standard version is known (an unpartnered library, or no schema).
    """
    if hed_schema is None:
        return None
    versions = []
    for namespace in hed_schema.valid_prefixes:
        schema = hed_schema.schema_for_namespace(namespace)
        if schema.with_standard:
            versions.append(schema.with_standard)
        elif schema.library == "":
            versions.append(schema.version_number)
    if not versions:
        return None
    return max(versions, key=Version)


class CharValidator:
    """Class responsible for basic character level validation of a string or tag."""

    def __init__(self, modern_allowed_char_rules=False):
        """Does basic character validation for HED strings/tags

        Parameters:
            modern_allowed_char_rules(bool): If True, use 8.3 style rules for unicode characters.
        """
        self._validate_characters = modern_allowed_char_rules
        self._sets = CharacterSets.load()

    def check_invalid_character_issues(self, hed_string, allow_placeholders) -> list[dict]:
        """Report characters no HED string may contain.

        Parameters:
            hed_string (str): A HED string.
            allow_placeholders (bool): Allow placeholder and curly brace characters.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - The forbidden characters come from ``character_sets.json`` ``hed_string.forbidden``
              (specification Appendix B CHARACTER_INVALID a): ``[ ] ~ "`` and the control code ranges
              (0-31 and 127-159), whatever the schema version. Curly braces are forbidden where placeholders
              are not allowed (CHARACTER_INVALID b). Schemas before 8.3.0 also reject every non-ASCII character.
        """
        validation_issues = []
        column_braces = self._sets.column_braces
        for index, character in enumerate(hed_string):
            if self._sets.is_forbidden(character):
                validation_issues += self._report_invalid_character_error(
                    hed_string, index, "forbidden", self._sets.describe_forbidden()
                )
            elif character in column_braces and not allow_placeholders:
                validation_issues += self._report_invalid_character_error(
                    hed_string, index, "structural", COLUMN_BRACES_RULE
                )
            elif not self._validate_characters and ord(character) > 127:
                validation_issues += self._report_invalid_character_error(
                    hed_string, index, "ascii", f"schemas before {ASCII_ONLY_BEFORE} allow only ASCII characters"
                )

        return validation_issues

    def check_tag_invalid_chars(self, original_tag, allow_placeholders) -> list[dict]:
        """Report invalid characters in the given tag.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            allow_placeholders (bool): Allow placeholder characters(#) if True.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = self._check_invalid_prefix_issues(original_tag)
        allowed_names = list(TAG_PATH_SETS)
        if allow_placeholders:
            allowed_names.append("number-sign")
        validation_issues += self._check_invalid_chars(
            original_tag.org_base_tag, allowed_names, original_tag, subject="a tag path"
        )
        return validation_issues

    def check_for_invalid_extension_chars(
        self, original_tag, validate_text, error_code=None, index_offset=0
    ) -> list[dict]:
        """Report invalid characters in a tag extension.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            validate_text (str): the text we want to validate, if not the full extension.
            error_code (str): The code to override the error as. Again mostly for def/def-expand tags.
            index_offset (int): Offset into the extension validate_text starts at.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        return self._check_invalid_chars(
            validate_text,
            list(EXTENSION_SETS),
            original_tag,
            starting_index=len(original_tag.org_base_tag) + 1 + index_offset,
            error_code=error_code,
            subject="a tag extension",
        )

    def _check_invalid_chars(
        self, check_string, allowed_names, source_tag, starting_index=0, error_code=None, subject="a tag"
    ):
        """Helper for checking for invalid characters.

        Parameters:
            check_string (str): String to be checked for invalid characters.
            allowed_names (list of str): Names of the character sets allowed in the string.
            source_tag (HedTag): Tag from which the string came from.
            starting_index (int): Starting index of check_string within the tag.
            error_code (str): The code to override the error as. Again mostly for def/def-expand tags.
            subject (str): What is being checked, for the message ("a tag extension").

        Returns:
            list:  List of dictionaries with validation issues.
        """
        validation_issues = []
        allows = f"{subject} allows {self._sets.describe(allowed_names)}"
        for i, character in self._sets.problem_characters(check_string, allowed_names):
            validation_issues += ErrorHandler.format_error(
                ValidationErrors.INVALID_TAG_CHARACTER,
                tag=source_tag,
                index_in_tag=starting_index + i,
                index_in_tag_end=starting_index + i + 1,
                actual_error=error_code,
                char_index=starting_index + i,
                char_set=", ".join(allowed_names),
                code_point=code_point(character),
                allows=allows,
            )
        return validation_issues

    @staticmethod
    def _check_invalid_prefix_issues(original_tag):
        """Check for invalid schema namespace.

        Parameters:
            original_tag (HedTag): Tag to look


        Returns:
            list:  List of dictionaries with validation issues.

        """
        issues = []
        schema_namespace = original_tag.schema_namespace
        if schema_namespace and not schema_namespace[:-1].isalpha():
            issues += ErrorHandler.format_error(
                ValidationErrors.TAG_NAMESPACE_PREFIX_INVALID, tag=original_tag, tag_namespace=schema_namespace
            )
        return issues

    @staticmethod
    def _report_invalid_character_error(hed_string, index, char_set, allows):
        """Report an invalid character.

        Parameters:
            hed_string (str): The HED string that caused the error.
            index (int): The index of the invalid character in the HED string.
            char_set (str): The ``char_set`` issue key: the set or rule the character failed.
            allows (str): What the string may contain instead, for the message.

        Returns:
            list: A singleton list with a dictionary representing the error.

        """
        error_type = ValidationErrors.CHARACTER_INVALID
        character = hed_string[index]
        if character == "~":
            error_type = ValidationErrors.TILDES_UNSUPPORTED
        return ErrorHandler.format_error(
            error_type,
            char_index=index,
            source_string=hed_string,
            char_set=char_set,
            code_point=code_point(character),
            allows=allows,
        )


class CharRexValidator(CharValidator):
    """Character validation of values against the value classes of the loaded schema."""

    def __init__(self, modern_allowed_char_rules=False, hed_schema=None):
        """Does basic character validation for HED strings/tags

        Parameters:
            modern_allowed_char_rules(bool): If True, use 8.3 style rules for Unicode characters.
            hed_schema (HedSchema, HedSchemaGroup or None): The schema being validated against. It decides
                whether a value class's own ``allowedCharacter`` declaration or the specification's per-class
                defaults define its characters (see ``allowed_names``). None trusts the declaration.
        """
        super().__init__(modern_allowed_char_rules)
        self._hed_schema = hed_schema
        self._policies = {}
        self._standard_version, self._declaration_wins = self._policy_for(hed_schema)

    def _policy_for(self, hed_schema):
        """Return ``(standard_version, declaration_wins)`` for a schema, a schema group, or None.

        A single schema answers for itself: a standard schema by its version, a partnered library by its
        ``withStandard`` version, an unpartnered library with no version (so only a class the file has no
        defaults for follows its declaration). A group answers group-wide, with the highest version it holds
        and ``schema_version_greater_equal``; callers that know the owning schema pass that schema instead.
        """
        if hed_schema is None:
            return None, True
        version = _standard_version(hed_schema)
        return version, schema_version_greater_equal(hed_schema, self._sets.declaration_wins_from)

    def _policy(self, hed_schema):
        """Return the cached policy of *hed_schema*, or the policy of the schema this validator was built with."""
        if hed_schema is None or hed_schema is self._hed_schema:
            return self._standard_version, self._declaration_wins
        key = id(hed_schema)
        if key not in self._policies:
            self._policies[key] = self._policy_for(hed_schema)
        return self._policies[key]

    def schema_for_tag(self, tag):
        """Return the schema of the group that owns *tag*, or None when it is unknown.

        Parameters:
            tag (HedTag): A tag whose ``schema_namespace`` names one schema of the group.

        Returns:
            HedSchema or None: The owning schema; None without a schema or for a namespace the group lacks.
        """
        if self._hed_schema is None or tag is None:
            return None
        return self._hed_schema.schema_for_namespace(tag.schema_namespace)

    @property
    def character_sets(self) -> CharacterSets:
        """The shared character-set table."""
        return self._sets

    def allowed_names(self, cname, declared_names=None, hed_schema=None) -> list[str]:
        """Return the character-set names that define the characters of value class *cname*.

        From standard schema 8.5.0, and in libraries partnered with 8.5.0 or later, the schema's own
        ``allowedCharacter`` declaration defines the class (decision D2, 2026-09-30), provided every name is a
        known set, an alias, or a single literal character; an unknown name is a schema compliance error and
        the defaults apply instead. On earlier standard versions the specification's ``value_class_defaults``
        define the five standard classes (D5), because their released declarations are incomplete (nameClass
        omits ``nonascii``; the 8.0.0 to 8.2.0 textClass enumerates characters without the underscore, and the
        file records ``text`` there, as validators have always applied). A class the file has no defaults for (a
        library's own value class) always follows its declaration.

        Parameters:
            cname (str): The value class name.
            declared_names (list of str or None): The ``allowedCharacter`` names the schema declares for it.
            hed_schema (HedSchema or None): The schema that owns the tag being checked. Its standard version
                decides the policy; None uses the schema or group this validator was built with.

        Returns:
            list[str]: The names; empty when nothing constrains the characters.
        """
        standard_version, declaration_wins = self._policy(hed_schema)
        defaults = self._sets.defaults_for(cname, standard_version)
        declared = [name for name in (declared_names or []) if name]
        if declared and (declaration_wins or not defaults):
            if all(self._sets.is_known_name(name) for name in declared):
                return declared
        return defaults

    def get_problem_chars(self, in_str, cname, declared_names=None, hed_schema=None):
        """Return a list of (index, char) pairs for characters in in_str not allowed by the value class cname.

        Parameters:
            in_str (str): The string to check.
            cname (str): The value class name used to look up allowed character classes.
            declared_names (list of str or None): The ``allowedCharacter`` names the schema declares for
                the class, if any. See ``allowed_names`` for when they are used.
            hed_schema (HedSchema or None): The schema that owns the value's tag; see ``allowed_names``.

        Returns:
            list[tuple[int, str]]: Each tuple contains the character index and the offending character.

        """
        return self._sets.problem_characters(in_str, self.allowed_names(cname, declared_names, hed_schema))

    def is_valid_value(self, in_string, cname):
        """Check whether in_string is a valid whole-word value for class cname.

        Parameters:
            in_string (str): The string to validate.
            cname (str): The value class name to look up the word-level regex for.

        Returns:
            True | re.Match | False:
                - ``True`` if no word-level regex is defined for *cname* (class imposes no constraint).
                - A ``re.Match`` object if *in_string* matches the word-level regex (valid value).
                - ``False`` if *in_string* does not match the word-level regex, or is a dateTimeClass value
                  whose date does not exist (invalid value).

        """
        class_regex = self._sets.word_rule(cname)
        if class_regex is None:
            return True
        match = class_regex.match(in_string)
        if not match:
            return False
        if cname == DATE_TIME_CLASS and not self._date_exists(in_string):
            return False
        return match

    def value_failure(self, in_string, cname) -> str:
        """Say why *in_string* fails the whole-value rule of class *cname*, for the VALUE_INVALID message.

        Parameters:
            in_string (str): The value.
            cname (str): The value class name.

        Returns:
            str: The rule the value breaks (the class description, or "an existing Gregorian calendar date;
            2026-02-31 does not exist"); empty when the value passes or the class has no whole-value rule.
        """
        class_regex = self._sets.word_rule(cname)
        if class_regex is None:
            return ""
        if not class_regex.match(in_string):
            return self._sets.word_rule_description(cname)
        if cname == DATE_TIME_CLASS and not self._date_exists(in_string):
            return f"an existing Gregorian calendar date; {in_string[:10]} does not exist"
        return ""

    @staticmethod
    def _date_exists(value) -> bool:
        """Return True when the ``YYYY-MM-DD`` that opens *value* is a real Gregorian date (year 1 or later)."""
        try:
            datetime.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
        except ValueError:
            return False
        return True
