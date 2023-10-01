""" Utilities for HED schema checking. """

from hed.errors.error_types import ErrorContext, SchemaErrors, ErrorSeverity, SchemaAttributeErrors, SchemaWarnings
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_schema import HedSchema, HedKey
from hed.schema import schema_attribute_validators
from hed.schema.schema_validation_util import validate_schema_term, validate_schema_description


def check_compliance(hed_schema, check_for_warnings=True, name=None, error_handler=None):
    """ Check for hed3 compliance of a schema object.

    Parameters:
        hed_schema (HedSchema): HedSchema object to check for hed3 compliance.
        check_for_warnings (bool): If True, check for formatting issues like invalid characters, capitalization, etc.
        name (str): If present, will use as filename for context.
        error_handler (ErrorHandler or None): Used to report errors. Uses a default one if none passed in.

    Returns:
        list: A list of all warnings and errors found in the file. Each issue is a dictionary.

    :raises ValueError:
        - Trying to validate a HedSchemaGroup directly
    """
    if not isinstance(hed_schema, HedSchema):
        raise ValueError("To check compliance of a HedGroupSchema, call self.check_compliance on the schema itself.")

    error_handler = error_handler if error_handler else ErrorHandler(check_for_warnings)
    validator = SchemaValidator(hed_schema, check_for_warnings, error_handler)
    issues_list = []

    if not name:
        name = hed_schema.filename
    error_handler.push_error_context(ErrorContext.FILE_NAME, name)

    issues_list += validator.check_unknown_attributes()
    issues_list += validator.check_attributes()
    issues_list += validator.check_duplicate_names()
    issues_list += validator.check_invalid_chars()

    error_handler.pop_error_context()
    return issues_list


class SchemaValidator:
    """Validator class to wrap some code.  In general, just call check_compliance."""
    attribute_validators = {
        HedKey.SuggestedTag: [schema_attribute_validators.tag_exists_check],
        HedKey.RelatedTag: [schema_attribute_validators.tag_exists_check],
        HedKey.UnitClass: [schema_attribute_validators.tag_is_placeholder_check,
                           schema_attribute_validators.unit_class_exists],
        HedKey.ValueClass: [schema_attribute_validators.tag_is_placeholder_check,
                            schema_attribute_validators.value_class_exists],
        # Rooted tag is implicitly verified on loading
        # HedKey.Rooted: [schema_attribute_validators.tag_exists_base_schema_check],
        HedKey.DeprecatedFrom: [schema_attribute_validators.tag_is_deprecated_check],
        HedKey.TakesValue: [schema_attribute_validators.tag_is_placeholder_check],
        HedKey.DefaultUnits: [schema_attribute_validators.unit_exists],
        HedKey.ConversionFactor: [schema_attribute_validators.conversion_factor],
        HedKey.AllowedCharacter: [schema_attribute_validators.allowed_characters_check],
        HedKey.InLibrary: [schema_attribute_validators.in_library_check]
    }

    def __init__(self, hed_schema, check_for_warnings=True, error_handler=None):
        self.hed_schema = hed_schema
        self._check_for_warnings = check_for_warnings
        self.error_handler = error_handler

    def check_unknown_attributes(self):
        """Returns issues for any unknown attributes in any section"""
        unknown_attributes = self.hed_schema.get_unknown_attributes()
        issues_list = []
        if unknown_attributes:
            for attribute_name, source_tags in unknown_attributes.items():
                for tag in source_tags:
                    issues_list += self.error_handler.format_error_with_context(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_INVALID,
                                                                                attribute_name,
                                                                                source_tag=tag)
        return issues_list

    def check_attributes(self):
        """Returns issues from validating known attributes in all sections"""
        issues_list = []
        for section_key in self.hed_schema._sections:
            self.error_handler.push_error_context(ErrorContext.SCHEMA_SECTION, section_key)
            for tag_entry in self.hed_schema[section_key].values():
                self.error_handler.push_error_context(ErrorContext.SCHEMA_TAG, tag_entry.name)
                for attribute_name in tag_entry.attributes:
                    validators = self.attribute_validators.get(attribute_name, [])
                    for validator in validators:
                        self.error_handler.push_error_context(ErrorContext.SCHEMA_ATTRIBUTE, attribute_name)
                        new_issues = validator(self.hed_schema, tag_entry, attribute_name)
                        for issue in new_issues:
                            issue['severity'] = ErrorSeverity.WARNING
                        self.error_handler.add_context_and_filter(new_issues)
                        issues_list += new_issues
                        self.error_handler.pop_error_context()
                self.error_handler.pop_error_context()
            self.error_handler.pop_error_context()
        return issues_list

    def check_duplicate_names(self):
        """Return issues for any duplicate names in all sections."""
        issues_list = []
        for section_key in self.hed_schema._sections:
            for name, duplicate_entries in self.hed_schema[section_key].duplicate_names.items():
                values = set(entry.has_attribute(HedKey.InLibrary) for entry in duplicate_entries)
                error_code = SchemaErrors.SCHEMA_DUPLICATE_NODE
                if len(values) == 2:
                    error_code = SchemaErrors.SCHEMA_DUPLICATE_FROM_LIBRARY
                issues_list += self.error_handler.format_error_with_context(error_code, name,
                                                                            duplicate_tag_list=[entry.name for entry in
                                                                                                duplicate_entries],
                                                                            section=section_key)
        return issues_list

    def check_invalid_chars(self):
        """Returns issues for bad chars in terms or descriptions."""
        issues_list = []
        if self._check_for_warnings:
            hed_terms = self.hed_schema.get_all_schema_tags(True)
            for hed_term in hed_terms:
                issues_list += validate_schema_term(hed_term)

            for tag_name, desc in self.hed_schema.get_desc_iter():
                issues_list += validate_schema_description(tag_name, desc)
        return issues_list
