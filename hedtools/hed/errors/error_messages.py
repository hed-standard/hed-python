"""
This module contains the actual formatted error messages for each type.

Add new errors here, or any other file imported after error_reporter.py.
"""

from hed.errors.error_reporter import hed_error, hed_tag_error
from hed.errors.error_types import ValidationErrors, ValidationWarnings, SchemaErrors, \
    SidecarErrors, SchemaWarnings, ErrorSeverity, DefinitionErrors


@hed_error(DefinitionErrors.INVALID_DEF_EXTENSION)
def def_error_invalid_def_extension(def_name):
    return f"Term '{def_name}' has an invalid extension.  Definitions can only have one term.", {}


@hed_tag_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT)
def val_error_invalid_unit(tag, unit_class_units):
    units_string = ','.join(sorted(unit_class_units))
    return f'Invalid unit - "{tag}" valid units are "{units_string}"', {
        "unit_class_units": sorted(unit_class_units)
    }


@hed_error(ValidationErrors.EMPTY_TAG)
def val_error_extra_comma(source_string, char_index):
    character = source_string[char_index]
    return f"HED tags cannot be empty.  Extra comma found at: '{character}' at index {char_index}'", {
               'char_index': char_index
           }


@hed_error(ValidationErrors.INVALID_CHARACTER)
def val_error_invalid_char(source_string, char_index):
    character = source_string[char_index]
    return f'Invalid character "{character}" at index {char_index}"', {
               'char_index': char_index
           }


@hed_tag_error(ValidationErrors.INVALID_TAG_CHARACTER, has_sub_tag=True, actual_code=ValidationErrors.INVALID_CHARACTER)
def val_error_invalid_tag_character(tag, problem_tag):
    return f"Invalid character {problem_tag} in {tag}", {}



@hed_error(ValidationErrors.TILDES_NOT_SUPPORTED)
def val_error_tildes_not_supported(source_string, char_index):
    character = source_string[char_index]
    return f"Tildes not supported.  Replace (a ~ b ~ c) with (a, (b, c)).  '{character}' at index {char_index}'", {
               'char_index': char_index
           }


@hed_error(ValidationErrors.COMMA_MISSING)
def val_error_comma_missing(tag):
    return f"Comma missing after - '{tag}'", {}


@hed_tag_error(ValidationErrors.DUPLICATE)
def val_error_duplicate_tag(tag):
    return f'Duplicate tag - "{tag}"', {}


@hed_error(ValidationErrors.PARENTHESES)
def val_error_parentheses(opening_parentheses_count, closing_parentheses_count):
    return f'Number of opening and closing parentheses are unequal. '\
           f'{opening_parentheses_count} opening parentheses. {closing_parentheses_count} '\
           'closing parentheses', {}


@hed_tag_error(ValidationErrors.REQUIRE_CHILD)
def val_error_require_child(tag):
    return f"Descendant tag required - '{tag}'", {}


@hed_error(ValidationErrors.MULTIPLE_UNIQUE)
def val_error_multiple_unique(tag_prefix):
    return f"Multiple unique tags with prefix - '{tag_prefix}'", {}


@hed_tag_error(ValidationErrors.INVALID_EXTENSION)
def val_error_invalid_extension(tag):
    return f'Invalid extension on tag - "{tag}"', {}


@hed_tag_error(ValidationErrors.INVALID_PARENT_NODE, has_sub_tag=True)
def val_error_invalid_parent(tag, problem_tag, expected_parent_tag):
    return f"In '{tag}', '{problem_tag}' appears as '{str(expected_parent_tag)}' and cannot be used " \
           f"as an extension.", {"expected_parent_tag": expected_parent_tag}


@hed_tag_error(ValidationErrors.NO_VALID_TAG_FOUND, has_sub_tag=True)
def val_error_no_valid_tag(tag, problem_tag):
    return f"'{problem_tag}' in {tag} is not a valid base hed tag.", {}


@hed_tag_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, has_sub_tag=True)
def val_error_extra_slashes_spaces(tag, problem_tag):
    return f"Extra slashes or spaces '{problem_tag}' in tag '{tag}'", {}


@hed_tag_error(ValidationErrors.HED_SIDECAR_KEY_MISSING)
def val_error_sidecar_key_missing(tag, category_keys):
    return f"Category key '{tag}' does not exist in column.  Valid keys are: {category_keys}", {}


@hed_tag_error(ValidationErrors.HED_DEFINITION_UNMATCHED)
def val_error_def_unmatched(tag):
    return f"A data-recording’s Def tag cannot be matched to definition.  Tag: '{tag}'", {}


@hed_tag_error(ValidationErrors.HED_DEFINITION_VALUE_MISSING)
def val_error_def_value_missing(tag):
    return f"A definition requires a placeholder value, but was not given one.  Definition: '{tag}'", {}


@hed_tag_error(ValidationErrors.HED_DEFINITION_VALUE_EXTRA)
def val_error_def_value_extra(tag):
    return f"A definition does not take a placeholder value, but was given one.  Definition: '{tag}", {}


@hed_tag_error(ValidationErrors.HED_TOP_LEVEL_TAG)
def val_error_top_level_tag(tag):
    return f"A tag that must be in a top level group was found in another location.  {str(tag)}", {}


@hed_tag_error(ValidationErrors.HED_TAG_GROUP_TAG)
def val_error_tag_group_tag(tag):
    return f"A tag that must be in a group was found in another location.  {str(tag)}", {}


@hed_tag_error(ValidationErrors.HED_MULTIPLE_TOP_TAGS)
def val_error_top_level_tags(tag, multiple_tags):
    tags_as_string = [str(tag) for tag in multiple_tags]
    return f"Multiple top level tags found in a single group.  First one found: {str(tag)}.  Remainder:{str(tags_as_string)}", {}


@hed_error(ValidationWarnings.REQUIRED_PREFIX_MISSING, default_severity=ErrorSeverity.WARNING)
def val_warning_required_prefix_missing(tag_prefix):
    return f"Tag with prefix '{tag_prefix}' is required", {}


@hed_tag_error(ValidationWarnings.CAPITALIZATION, default_severity=ErrorSeverity.WARNING)
def val_warning_capitalization(tag):
    return f"First word not capitalized or camel case - '{tag}'", {}


@hed_tag_error(ValidationWarnings.UNIT_CLASS_DEFAULT_USED, default_severity=ErrorSeverity.WARNING)
def val_warning_default_units_used(tag, default_unit):
    return f"No unit specified. Using '{default_unit}' as the default - '{tag}'", {}


@hed_error(SchemaErrors.DUPLICATE_TERMS)
def schema_error_duplicate_terms(tag, duplicate_tag_list):
    tag_join_delimiter = f"\n\t"
    return f"Term(Short Tag) '{str(tag)}' used {len(duplicate_tag_list)} places in schema as: {tag_join_delimiter}"\
           f"{tag_join_delimiter.join(duplicate_tag_list)}", {}


@hed_error(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, default_severity=ErrorSeverity.WARNING)
def schema_warning_invalid_chars_desc(desc_string, tag_name, problem_char, char_index):
    return f"Invalid character '{problem_char}' in desc for '{tag_name}' at position {char_index}.  '{desc_string}", {}


@hed_error(SchemaWarnings.INVALID_CHARACTERS_IN_TAG, default_severity=ErrorSeverity.WARNING)
def schema_warning_invalid_chars_tag(tag_name, problem_char, char_index):
    return f"Invalid character '{problem_char}' in tag '{tag_name}' at position {char_index}.", {}


@hed_error(SchemaWarnings.INVALID_CAPITALIZATION, default_severity=ErrorSeverity.WARNING)
def schema_warning_invalid_capitalization(tag_name, problem_char, char_index):
    return f"First character must be a capital letter or number.  Found character '{problem_char}' in tag '{tag_name}' at position {char_index}.", {'problem_char': problem_char}


@hed_error(SidecarErrors.BLANK_HED_STRING)
def sidecar_error_blank_hed_string():
    return f"No HED string found for Value or Category column.", {}


@hed_error(SidecarErrors.WRONG_HED_DATA_TYPE)
def sidecar_error_hed_data_type(expected_type, given_type):
    return f"Invalid HED string datatype sidecar. Should be '{expected_type}', but got '{given_type}'", {}


@hed_error(SidecarErrors.INVALID_NUMBER_POUND_SIGNS)
def sidecar_error_invalid_pound_sign_count(pound_sign_count):
    return f"There should be exactly one # character in a sidecar string. Found {pound_sign_count}", {}


@hed_error(SidecarErrors.TOO_MANY_POUND_SIGNS)
def sidecar_error_too_many_pound_signs(pound_sign_count):
    return f"There should be no # characters in a category sidecar string. Found {pound_sign_count}", {}


@hed_error(SidecarErrors.UNKNOWN_COLUMN_TYPE)
def sidecar_error_unknown_column(column_name):
    return f"Could not automatically identify column '{column_name}' type from file. "\
           f"Most likely the column definition in question needs a # sign to replace a number somewhere.", {}


@hed_error(DefinitionErrors.WRONG_NUMBER_DEF_TAGS)
def def_error_wrong_def_tags(def_name, tag_list):
    tag_list_strings = [str(tag) for tag in tag_list]
    return f"Too many def tags found in definition for {def_name}.  Expected 1, also found: {tag_list_strings}", {}


@hed_error(DefinitionErrors.WRONG_NUMBER_GROUP_TAGS)
def def_error_wrong_group_tags(def_name, tag_list):
    tag_list_strings = [str(tag) for tag in tag_list]
    return f"Too many group tags found in definition for {def_name}.  Expected 1, found: {tag_list_strings}", {}


@hed_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS)
def def_error_wrong_placeholder_count(def_name, expected_count, tag_list):
    tag_list_strings = [str(tag) for tag in tag_list]
    return f"Incorrect number placeholder tags found in definition for {def_name}.  Expected {expected_count}, found: {tag_list_strings}", {}


@hed_error(DefinitionErrors.DUPLICATE_DEFINITION)
def def_error_duplicate_definition(def_name):
    return f"Duplicate definition found for '{def_name}'.", {}


@hed_error(DefinitionErrors.TAG_IN_SCHEMA)
def def_error_tag_already_in_schema(def_name):
    return f"Term '{def_name}' already used as term in schema and cannot be re-used as a definition.", {}
