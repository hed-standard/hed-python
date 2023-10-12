from hed.errors.error_types import SchemaErrors, SchemaWarnings, ErrorSeverity, SchemaAttributeErrors
from hed.errors.error_reporter import hed_error


@hed_error(SchemaErrors.SCHEMA_DUPLICATE_NODE)
def schema_error_hed_duplicate_node(tag, duplicate_tag_list, section):
    tag_join_delimiter = "\n\t"
    return f"Duplicate term '{str(tag)}' used {len(duplicate_tag_list)} places in '{section}' section schema as:" + \
           f"{tag_join_delimiter}{tag_join_delimiter.join(duplicate_tag_list)}"


@hed_error(SchemaErrors.SCHEMA_DUPLICATE_FROM_LIBRARY)
def schema_error_hed_duplicate_from_library(tag, duplicate_tag_list, section):
    tag_join_delimiter = "\n\t"
    return f"Duplicate term '{str(tag)}' was found in the library and in the standard schema in '{section}' section schema as:" + \
           f"{tag_join_delimiter}{tag_join_delimiter.join(duplicate_tag_list)}"


@hed_error(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_INVALID)
def schema_error_unknown_attribute(attribute_name, source_tag):
    return f"Attribute '{attribute_name}' used by '{source_tag}' was not defined in the schema, " \
           f"or was used outside of it's defined class."


@hed_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_DESC, default_severity=ErrorSeverity.WARNING,
           actual_code=SchemaWarnings.SCHEMA_CHARACTER_INVALID)
def schema_warning_invalid_chars_desc(desc_string, tag_name, problem_char, char_index):
    return f"Invalid character '{problem_char}' in desc for '{tag_name}' at position {char_index}.  '{desc_string}"


@hed_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_TAG, default_severity=ErrorSeverity.WARNING,
           actual_code=SchemaWarnings.SCHEMA_CHARACTER_INVALID)
def schema_warning_invalid_chars_tag(tag_name, problem_char, char_index):
    return f"Invalid character '{problem_char}' in tag '{tag_name}' at position {char_index}."


@hed_error(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION, default_severity=ErrorSeverity.WARNING)
def schema_warning_SCHEMA_INVALID_CAPITALIZATION(tag_name, problem_char, char_index):
    return "First character must be a capital letter or number.  " + \
           f"Found character '{problem_char}' in tag '{tag_name}' at position {char_index}."


@hed_error(SchemaWarnings.SCHEMA_NON_PLACEHOLDER_HAS_CLASS, default_severity=ErrorSeverity.WARNING,
           actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_warning_non_placeholder_class(tag_name, invalid_attribute_name):
    return "Only placeholder nodes('#') can have a unit class, value class, or takes value." + \
           f"Found {invalid_attribute_name} on {tag_name}"



@hed_error(SchemaAttributeErrors.SCHEMA_DEPRECATED_INVALID, actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_DEPRECATED_INVALID(tag_name, invalid_deprecated_version):
    return f"'{tag_name}' has invalid or unknown value in attribute deprecatedFrom: '{invalid_deprecated_version}'."


@hed_error(SchemaAttributeErrors.SCHEMA_CHILD_OF_DEPRECATED,
           actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_CHILD_OF_DEPRECATED(deprecated_tag, non_deprecated_child):
    return f"Deprecated tag '{deprecated_tag}' has a child that is not deprecated: '{non_deprecated_child}'."


@hed_error(SchemaAttributeErrors.SCHEMA_SUGGESTED_TAG_INVALID, actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_SUGGESTED_TAG_INVALID(suggestedTag, invalidSuggestedTag, attribute_name):
    return f"Tag '{suggestedTag}' has an invalid {attribute_name}: '{invalidSuggestedTag}'."


@hed_error(SchemaAttributeErrors.SCHEMA_UNIT_CLASS_INVALID, actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_UNIT_CLASS_INVALID(tag, unit_class, attribute_name):
    return f"Tag '{tag}' has an invalid {attribute_name}: '{unit_class}'."


@hed_error(SchemaAttributeErrors.SCHEMA_VALUE_CLASS_INVALID, actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_VALUE_CLASS_INVALID(tag, unit_class, attribute_name):
    return f"Tag '{tag}' has an invalid {attribute_name}: '{unit_class}'."


@hed_error(SchemaAttributeErrors.SCHEMA_DEFAULT_UNITS_INVALID, actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_DEFAULT_UNITS_INVALID(tag, bad_unit, valid_units):
    valid_units = ",".join(valid_units)
    return f"Tag '{tag}' has an invalid defaultUnit '{bad_unit}'.  Valid units are: '{valid_units}'."


@hed_error(SchemaAttributeErrors.SCHEMA_CONVERSION_FACTOR_NOT_POSITIVE, actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_CONVERSION_FACTOR_NOT_POSITIVE(tag, conversion_factor):
    return f"Tag '{tag}' has an invalid conversionFactor '{conversion_factor}'.  Conversion factor must be positive."


@hed_error(SchemaAttributeErrors.SCHEMA_ALLOWED_CHARACTERS_INVALID, actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_ALLOWED_CHARACTERS_INVALID(tag, invalid_character):
    return (f"Tag '{tag}' has an invalid allowedCharacter: '{invalid_character}'.  "
            f"Allowed characters are: a single character, "
            f"or one of the following - letters, blank, digits, alphanumeric.")


@hed_error(SchemaAttributeErrors.SCHEMA_IN_LIBRARY_INVALID, actual_code=SchemaAttributeErrors.SCHEMA_ATTRIBUTE_VALUE_INVALID)
def schema_error_SCHEMA_IN_LIBRARY_INVALID(tag, bad_library):
    return (f"Tag '{tag}' has an invalid inLibrary: '{bad_library}'.  ")
