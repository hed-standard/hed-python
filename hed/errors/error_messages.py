"""Format templates for HED schema error messages.

Add new errors here, or any other file imported after error_reporter.py.
"""

from hed.errors.error_reporter import hed_error, hed_tag_error
from hed.errors.error_types import (ValidationErrors, SidecarErrors, ErrorSeverity, DefinitionErrors,
                                    TemporalErrors, ColumnErrors, TagQualityErrors)

def get_tag_list_str(tag_list):
    """ Return a string representation of a list of tags.

    Parameters:
        tag_list (list): A list of tags to convert to a string.

    Returns:
        str: A string representation of the list of tags.
    """
    return "[" + ', '.join([str(tag) for tag in tag_list]) + "]"


@hed_tag_error(ValidationErrors.UNITS_INVALID)
def val_error_invalid_unit(tag, units):
    units_string = ','.join(sorted(units))
    return f'Invalid unit - "{tag}" valid units are "{units_string}"'


@hed_error(ValidationErrors.TAG_EMPTY)
def val_error_extra_comma(source_string, char_index):
    character = source_string[char_index]
    return f"HED tags cannot be empty.  Extra delimiter found: '{character}' at index {char_index}'"


@hed_tag_error(ValidationErrors.HED_GROUP_EMPTY, actual_code=ValidationErrors.TAG_EMPTY)
def val_error_empty_group(tag):
    return f"HED tags cannot be empty.  Extra delimiters found: '{tag}'"


@hed_tag_error(TemporalErrors.TEMPORAL_TAG_NO_TIME, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def val_error_temporal_tag_no_time(tag):
    return f"Cannot have Temporal tags without an 'Onset' column and a time.  Found tag: '{tag}'"


@hed_tag_error(ValidationErrors.TAG_EXTENDED, has_sub_tag=True, default_severity=ErrorSeverity.WARNING)
def val_error_tag_extended(tag, problem_tag):
    return f"Hed tag is extended. '{problem_tag}' in {tag}"


@hed_error(ValidationErrors.CHARACTER_INVALID)
def val_error_invalid_char(source_string, char_index):
    character = source_string[char_index]
    return f'Invalid character "{character}" at index {char_index}"'


@hed_tag_error(ValidationErrors.ELEMENT_DEPRECATED, default_severity=ErrorSeverity.WARNING)
def val_error_element_deprecated(tag):
    return f"Element '{tag}' has been deprecated and an alternative method of tagging should be used"


@hed_tag_error(ValidationErrors.INVALID_TAG_CHARACTER, has_sub_tag=True,
               actual_code=ValidationErrors.CHARACTER_INVALID)
def val_error_invalid_tag_character(tag, problem_tag):
    return f"Invalid character '{problem_tag}' in tag '{tag}'"


@hed_tag_error(ValidationErrors.INVALID_VALUE_CLASS_CHARACTER, has_sub_tag=False,
               actual_code=ValidationErrors.CHARACTER_INVALID)
def val_error_val_error_invalid_value_class_character(tag, problem_tag, value_class):
    return f"Invalid character '{problem_tag}' in tag '{tag}' for value class '{value_class}'"


@hed_tag_error(ValidationErrors.INVALID_VALUE_CLASS_VALUE, has_sub_tag=True,
               actual_code=ValidationErrors.VALUE_INVALID)
def val_error_invalid_value_class_value(tag, problem_tag, value_class):
    return f"'{tag}' has an invalid value portion for value class '{value_class}'"


@hed_error(ValidationErrors.TILDES_UNSUPPORTED)
def val_error_tildes_not_supported(source_string, char_index):
    character = source_string[char_index]
    return f"Tildes not supported.  Replace (a ~ b ~ c) with (a, (b, c)).  '{character}' at index {char_index}'"


@hed_tag_error(ValidationErrors.HED_PLACEHOLDER_OUT_OF_CONTEXT, has_sub_tag=False,
               actual_code=ValidationErrors.PLACEHOLDER_INVALID)
def val_error_hed_placeholder_out_of_context(tag):
    return f"'{tag}' has a '#' placeholder where it is not allowed or where it should have been replaced with a value."


@hed_tag_error(ValidationErrors.CURLY_BRACE_UNSUPPORTED_HERE, has_sub_tag=False,
               actual_code=SidecarErrors.SIDECAR_BRACES_INVALID)
def val_error_curly_brace_unsupported_here(tag, problem_tag):
    return (f"Curly braces are only permitted in sidecars, fully wrapping text in place of a tag.  "
            f"Invalid character '{problem_tag}' in tag '{tag}'")


@hed_error(ValidationErrors.ONSETS_UNORDERED, default_severity=ErrorSeverity.WARNING)
def val_error_onsets_unordered():
    return "Onsets need to be temporally increasing and defined for many downstream tools to work."


@hed_error(ValidationErrors.COMMA_MISSING)
def val_error_comma_missing(tag):
    return f"Comma missing after - '{tag}'"


@hed_tag_error(ValidationErrors.HED_TAG_REPEATED, actual_code=ValidationErrors.TAG_EXPRESSION_REPEATED)
def val_error_duplicate_tag(tag):
    return f'Repeated tag - "{tag}"'


@hed_error(ValidationErrors.HED_TAG_REPEATED_GROUP, actual_code=ValidationErrors.TAG_EXPRESSION_REPEATED)
def val_error_duplicate_group(group):
    return f'Repeated group - "{group}"'


@hed_error(ValidationErrors.HED_RESERVED_TAG_REPEATED, actual_code=ValidationErrors.TAG_GROUP_ERROR)
def val_error_duplicate_reserved_tag(tag, group):
    return f'Repeated reserved tag "{tag}" or multiple reserved tags in group "{group}"'


@hed_error(ValidationErrors.HED_RESERVED_TAG_GROUP_ERROR, actual_code=ValidationErrors.TAG_GROUP_ERROR)
def val_error_group_for_reserved_tag(group, group_count, tag_list):
    return (f'The number of non-def-expand subgroups for group "{group}" is {group_count}, "'
            f'which does not meet reserved tags {get_tag_list_str(tag_list)} requirements."')


@hed_error(ValidationErrors.PARENTHESES_MISMATCH)
def val_error_parentheses(opening_parentheses_count, closing_parentheses_count):
    return f'Number of opening and closing parentheses are unequal. '\
           f'{opening_parentheses_count} opening parentheses. {closing_parentheses_count} '\
           'closing parentheses'


@hed_tag_error(ValidationErrors.TAG_REQUIRES_CHILD)
def val_error_require_child(tag):
    return f"Descendant tag required - '{tag}'"


@hed_error(ValidationErrors.TAG_NOT_UNIQUE)
def val_error_multiple_unique(tag_namespace):
    return f"Multiple unique tags with namespace - '{tag_namespace}'"


@hed_tag_error(ValidationErrors.TAG_NAMESPACE_PREFIX_INVALID)
def val_error_prefix_invalid(tag, tag_namespace):
    return f"Prefixes can only contain alpha characters. - '{tag_namespace}'"


@hed_tag_error(ValidationErrors.TAG_EXTENSION_INVALID)
def val_error_invalid_extension(tag):
    return f'Invalid extension on tag - "{tag}"'


@hed_tag_error(ValidationErrors.INVALID_PARENT_NODE, has_sub_tag=True,
               actual_code=ValidationErrors.TAG_EXTENSION_INVALID)
def val_error_invalid_parent(tag, problem_tag, expected_parent_tag):
    return f"In '{tag}', '{problem_tag}' appears as '{str(expected_parent_tag)}' and cannot be used as an extension."


@hed_tag_error(ValidationErrors.NO_VALID_TAG_FOUND, has_sub_tag=True, actual_code=ValidationErrors.TAG_INVALID)
def val_error_no_valid_tag(tag, problem_tag):
    return f"'{problem_tag}' in {tag} is not a valid base HED tag."


@hed_tag_error(ValidationErrors.VALUE_INVALID)
def val_error_no_value(tag, value_class=''):
    if value_class:
        return f"'{tag}' has an invalid value portion because it is not a valid '{value_class}' value."
    else:
        return f"'{tag}' has an invalid value portion."


@hed_error(ValidationErrors.HED_MISSING_REQUIRED_COLUMN, default_severity=ErrorSeverity.WARNING)
def val_error_missing_column(column_name, column_type):
    return f"Required {column_type} column '{column_name}' not specified or found in file."


@hed_error(ValidationErrors.HED_UNKNOWN_COLUMN, default_severity=ErrorSeverity.WARNING)
def val_error_extra_column(column_name):
    return f"Column named '{column_name}' found in file, but not specified as a tag column " + \
        "or identified in sidecars."


@hed_error(ValidationErrors.SIDECAR_AND_OTHER_COLUMNS)
def val_error_sidecar_with_column(column_names):
    return f"You cannot use a sidecar and tag or prefix columns at the same time. " \
            f"Found {column_names}."


@hed_error(ValidationErrors.DUPLICATE_COLUMN_IN_LIST)
def val_error_duplicate_column(column_number, column_name, list_name):
    if column_name:
        return f"Found column '{column_name}' at index {column_number} twice in {list_name}."
    else:
        return f"Found column number {column_number} twice in {list_name}.  This may indicate a mistake."


@hed_error(ValidationErrors.DUPLICATE_COLUMN_BETWEEN_SOURCES)
def val_error_duplicate_column_between_sources(column_number, column_name, list_names):
    if column_name:
        return f"Found column '{column_name}' at index {column_number} in the following inputs: {list_names}. " \
               f"Each entry must be unique."
    else:
        return f"Found column number {column_number} in the following inputs: {list_names}. " \
               f"Each entry must be unique."


@hed_error(ValidationErrors.HED_BLANK_COLUMN, default_severity=ErrorSeverity.WARNING)
def val_error_hed_blank_column(column_number):
    return f"Column number {column_number} has no column name"


@hed_tag_error(ValidationErrors.HED_LIBRARY_UNMATCHED, actual_code=ValidationErrors.TAG_NAMESPACE_PREFIX_INVALID)
def val_error_unknown_namespace(tag, unknown_prefix, known_prefixes):
    return f"Tag '{tag} has unknown namespace '{unknown_prefix}'.  Valid prefixes: {known_prefixes}"


@hed_tag_error(ValidationErrors.NODE_NAME_EMPTY, has_sub_tag=True, actual_code=ValidationErrors.TAG_INVALID)
def val_error_extra_slashes_spaces(tag, problem_tag):
    return f"Extra slashes or spaces '{problem_tag}' in tag '{tag}'"


@hed_error(ValidationErrors.SIDECAR_KEY_MISSING, default_severity=ErrorSeverity.WARNING)
def val_error_sidecar_key_missing(invalid_keys, category_keys, column_name):
    return f"Category keys {invalid_keys} do not exist in sidecar for column '{column_name}'.  Valid keys are: {category_keys}"


@hed_error(ValidationErrors.TSV_COLUMN_MISSING, actual_code=ValidationErrors.SIDECAR_KEY_MISSING,
           default_severity=ErrorSeverity.WARNING)
def val_error_tsv_column_missing(invalid_keys):
    return f"{invalid_keys} used as column references in sidecar but are not columns in the tabular file"


@hed_tag_error(ValidationErrors.HED_DEF_EXPAND_INVALID, actual_code=ValidationErrors.DEF_EXPAND_INVALID)
def val_error_bad_def_expand(tag, actual_def, found_def):
    return f"A data-recording's Def-expand tag does not match the given definition." \
           f"Tag: '{tag}'.  Actual Def: {actual_def}.  Found Def: {found_def}"


@hed_tag_error(ValidationErrors.HED_DEF_UNMATCHED, actual_code=ValidationErrors.DEF_INVALID)
def val_error_def_unmatched(tag):
    return f"A data-recording's Def tag cannot be matched to definition.  Tag: '{tag}'"


@hed_tag_error(ValidationErrors.HED_DEF_VALUE_MISSING, actual_code=ValidationErrors.DEF_INVALID)
def val_error_def_value_missing(tag):
    return f"A def tag requires a placeholder value, but was not given one.  Definition: '{tag}'"


@hed_tag_error(ValidationErrors.HED_DEF_VALUE_EXTRA, actual_code=ValidationErrors.DEF_INVALID)
def val_error_def_value_extra(tag):
    return f"A def tag does not take a placeholder value, but was given one.  Definition: '{tag}"


@hed_tag_error(ValidationErrors.HED_DEF_EXPAND_UNMATCHED, actual_code=ValidationErrors.DEF_EXPAND_INVALID)
def val_error_def_expand_unmatched(tag):
    return f"A data-recording's Def-expand tag cannot be matched to definition.  Tag: '{tag}'"


@hed_tag_error(ValidationErrors.HED_DEF_EXPAND_VALUE_MISSING, actual_code=ValidationErrors.DEF_EXPAND_INVALID)
def val_error_def_expand_value_missing(tag):
    return f"A Def-expand tag requires a placeholder value, but was not given one.  Definition: '{tag}'"


@hed_tag_error(ValidationErrors.HED_DEF_EXPAND_VALUE_EXTRA, actual_code=ValidationErrors.DEF_EXPAND_INVALID)
def val_error_def_expand_value_extra(tag):
    return f"A Def-expand tag does not take a placeholder value, but was given one.  Definition: '{tag}"


@hed_tag_error(ValidationErrors.HED_TOP_LEVEL_TAG, actual_code=ValidationErrors.TAG_GROUP_ERROR)
def val_error_top_level_tag(tag):
    return f'Tag "{tag}" must be in a top level group but was found in another location.'


@hed_tag_error(ValidationErrors.HED_TAG_GROUP_TAG, actual_code=ValidationErrors.TAG_GROUP_ERROR)
def val_error_tag_group_tag(tag):
    return f'Tag "{tag}" that must be in a group was found in another location.'


@hed_tag_error(ValidationErrors.HED_MULTIPLE_TOP_TAGS, actual_code=ValidationErrors.TAG_GROUP_ERROR)
def val_error_top_level_tags(tag, multiple_tags):
    tags_as_string = [str(tag) for tag in multiple_tags]
    return f"Multiple top level tags found in a single group.  First one found: {str(tag)}. " + \
           f"Remainder:{str(tags_as_string)}"


@hed_tag_error(ValidationErrors.HED_TAGS_NOT_ALLOWED, actual_code=ValidationErrors.TAG_GROUP_ERROR)
def val_error_tags_in_group_with_reserved(tag, group):
    return f'Tag "{tag}" is not allowed with the other tag(s) or Def-expand sub-group in group "{group}"'


@hed_error(ValidationErrors.REQUIRED_TAG_MISSING)
def val_warning_required_prefix_missing(tag_namespace):
    return f"Tag with namespace '{tag_namespace}' is required"


@hed_tag_error(ValidationErrors.STYLE_WARNING, default_severity=ErrorSeverity.WARNING)
def val_warning_capitalization(tag):
    return f"First word not capitalized or camel case - '{tag}'"


@hed_error(SidecarErrors.BLANK_HED_STRING)
def sidecar_error_blank_hed_string():
    return "No HED string found for Value or Category column."


@hed_error(SidecarErrors.WRONG_HED_DATA_TYPE)
def sidecar_error_hed_data_type(expected_type, given_type):
    return f"Invalid HED string datatype sidecar. Should be '{expected_type}', but got '{given_type}'"


@hed_error(SidecarErrors.INVALID_POUND_SIGNS_VALUE, actual_code=ValidationErrors.PLACEHOLDER_INVALID)
def sidecar_error_invalid_pound_sign_count(pound_sign_count):
    return f"There should be exactly one # character in a sidecar string. Found {pound_sign_count}"


@hed_error(SidecarErrors.INVALID_POUND_SIGNS_CATEGORY, actual_code=ValidationErrors.PLACEHOLDER_INVALID)
def sidecar_error_too_many_pound_signs(pound_sign_count):
    return f"There should be no # characters in a category sidecar string. Found {pound_sign_count}"


@hed_error(SidecarErrors.UNKNOWN_COLUMN_TYPE)
def sidecar_error_unknown_column(column_name):
    return f"Could not automatically identify column '{column_name}' type from file. "\
           "Most likely the column definition in question needs a # sign to replace a number somewhere."


@hed_error(SidecarErrors.SIDECAR_HED_USED, actual_code=ValidationErrors.SIDECAR_INVALID)
def sidecar_hed_used():
    return "'HED' is a reserved name and cannot be used as a sidecar except in expected places."


@hed_error(SidecarErrors.SIDECAR_NA_USED, actual_code=ValidationErrors.SIDECAR_INVALID)
def sidecar_na_used(column_name):
    return f"Invalid category key 'n/a' found in column {column_name}."


@hed_tag_error(DefinitionErrors.DEF_TAG_IN_DEFINITION, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_def_tag_in_definition(tag, def_name):
    return f"Invalid tag {tag} found in definition for {def_name}. " \
           f"Def, Def-expand, and Definition tags cannot be in definitions."


@hed_error(DefinitionErrors.NO_DEFINITION_CONTENTS, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_no_group_tags(def_name):
    return f"No group tag found in definition for {def_name}."


@hed_error(DefinitionErrors.WRONG_NUMBER_GROUPS, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_wrong_number_groups(def_name, tag_list):
    return f"Too many group tags found in definition for {def_name}.  Expected 1, found: {get_tag_list_str(tag_list)}"


@hed_error(DefinitionErrors.WRONG_NUMBER_TAGS, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_wrong_number_tags(def_name, tag_list):
    tag_list_strings = [str(tag) for tag in tag_list]
    return f"Too many tags found in definition for {def_name}.  Expected 1, found: {tag_list_strings}"


@hed_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_wrong_placeholder_count(def_name, expected_count, tag_list):
    return f"Incorrect number placeholders or placeholder tags found in definition for {def_name}.  " + \
           f"Expected {expected_count}, found:  {get_tag_list_str(tag_list)}"


@hed_error(DefinitionErrors.DUPLICATE_DEFINITION, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_duplicate_definition(def_name):
    return f"Duplicate definition found for '{def_name}'."


@hed_tag_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_invalid_def_extension(tag, def_name):
    return f"Tag '{str(tag)}' has an invalid placeholder in definition '{def_name}'"


@hed_error(DefinitionErrors.PLACEHOLDER_NO_TAKES_VALUE, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_no_takes_value(def_name, placeholder_tag):
    return f"Definition '{def_name}' has has a placeholder tag {str(placeholder_tag)} that isn't a takes value tag."


@hed_tag_error(DefinitionErrors.BAD_PROP_IN_DEFINITION, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_bad_prop_in_definition(tag, def_name):
    return f"Tag '{str(tag)}' in Definition '{def_name}' has has a the unique or required attribute."


@hed_tag_error(DefinitionErrors.BAD_DEFINITION_LOCATION, actual_code=ValidationErrors.DEFINITION_INVALID)
def def_error_bad_location(tag):
    return f"Tag '{str(tag)}' is found in a location it is not allowed to be."


@hed_tag_error(TemporalErrors.ONSET_DEF_UNMATCHED, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_error_def_unmatched(tag):
    return f"The def tag in an onset/offset tag is unmatched.  Def tag: '{tag}'"


@hed_tag_error(TemporalErrors.OFFSET_BEFORE_ONSET, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_error_offset_before_onset(tag):
    return f"Offset tag '{tag}' does not have a matching onset."


@hed_tag_error(TemporalErrors.ONSET_SAME_DEFS_ONE_ROW, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_error_same_defs_one_row(tag, def_name):
    return f"'{tag}' uses name '{def_name}', which was already used at this onset time."


@hed_tag_error(TemporalErrors.INSET_BEFORE_ONSET, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_error_inset_before_onset(tag):
    return f"Inset tag '{tag}' does not have a matching onset."


@hed_tag_error(TemporalErrors.ONSET_NO_DEF_TAG_FOUND, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_no_def_found(tag):
    return f"'{tag}' tag has no def tag or def-expand group or too many when 1 is required in string."


@hed_tag_error(TemporalErrors.ONSET_TOO_MANY_DEFS, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_too_many_defs(tag, tag_list):
    tag_list_strings = [str(tag) for tag in tag_list]
    return f"Too many def tags found in onset for {tag}.  Expected 1, also found: {tag_list_strings}"


@hed_tag_error(TemporalErrors.ONSET_WRONG_NUMBER_GROUPS, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_too_many_groups(tag, tag_list):
    tag_list_strings = [str(a_tag) for a_tag in tag_list]
    return f"An onset tag should have at most 2 sibling nodes, an offset tag should have 1. " \
           f"Found {len(tag_list_strings)}: {tag_list_strings}"


@hed_tag_error(TemporalErrors.DURATION_WRONG_NUMBER_GROUPS, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_duration_wrong_number_groups(tag, tag_list):
    tag_list_strings = [str(a_tag) for a_tag in tag_list]
    return f"A duration and/or delay tag '{tag}'should have exactly one child group." \
           f"Found {len(tag_list_strings)}: {tag_list_strings}"


@hed_tag_error(TemporalErrors.ONSET_TAG_OUTSIDE_OF_GROUP, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_wrong_type_tag(tag, def_tag):
    return f"Onset def tag '{def_tag}' has an improper sibling tag '{tag}'.  All onset context tags must be " \
           f"in a single group together."


@hed_tag_error(TemporalErrors.ONSET_PLACEHOLDER_WRONG, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_wrong_placeholder(tag, has_placeholder):
    if has_placeholder:
        return f"Onset/offset def tag {tag} expects a placeholder value, but does not have one."
    return f"Onset/offset def tag {tag} should not have a placeholder, but has one."


@hed_tag_error(TemporalErrors.DURATION_HAS_OTHER_TAGS, actual_code=ValidationErrors.TEMPORAL_TAG_ERROR)
def onset_duration_has_other_tags(tag):
    return f"Tag '{tag}' should not be grouped with Duration or Delay.  Context tags should be in a sub-group."


@hed_error(ColumnErrors.INVALID_COLUMN_REF, actual_code=SidecarErrors.SIDECAR_BRACES_INVALID)
def invalid_column_ref(bad_ref):
    return f"The column '{bad_ref}' is unknown or does not have HED annotations.'"


@hed_error(ColumnErrors.SELF_COLUMN_REF, actual_code=SidecarErrors.SIDECAR_BRACES_INVALID)
def self_column_ref(self_ref):
    return f"Column references itself: {self_ref}"


@hed_error(ColumnErrors.NESTED_COLUMN_REF, actual_code=SidecarErrors.SIDECAR_BRACES_INVALID)
def nested_column_ref(column_name, ref_column):
    return f"Column {column_name} has a nested reference to {ref_column}.  " \
           f"Column reference columns cannot contain other column references."


@hed_error(ColumnErrors.MALFORMED_COLUMN_REF, actual_code=SidecarErrors.SIDECAR_BRACES_INVALID)
def malformed_column_ref(column_name, index, symbol):
    return f"Column {column_name} has a malformed column reference.  Improper symbol {symbol} found at index {index}."


@hed_error(TagQualityErrors.MISSING_EVENT_TYPE, default_severity=ErrorSeverity.WARNING,
           actual_code=TagQualityErrors.MISSING_EVENT_TYPE)
def missing_event_type(string, line):
    return f"The HED string '{string}' at line {line} has no Event type."


@hed_error(TagQualityErrors.IMPROPER_EVENT_GROUPS, default_severity=ErrorSeverity.WARNING,
           actual_code=TagQualityErrors.IMPROPER_EVENT_GROUPS)
def improper_event_groups(event_types, string, line):
    return f"The HED string '{string}' at line {line} has multiple events [{event_types}] but is improperly " + \
    f"parenthesized so the other tags cannot be uniquely associated with an event."


@hed_error(TagQualityErrors.MISSING_TASK_ROLE, default_severity=ErrorSeverity.WARNING,
           actual_code=TagQualityErrors.MISSING_TASK_ROLE)
def missing_task_role(event_type, string, line):
    return f"The HED string '{string}' at line {line} with event {event_type} has no Task-event-role type tag."


@hed_error(TagQualityErrors.AMBIGUOUS_TAG_GROUPING, default_severity=ErrorSeverity.WARNING,
           actual_code=TagQualityErrors.AMBIGUOUS_TAG_GROUPING)
def ambiguous_tag_grouping(tag_list, string, line):
    return f"The HED string '{string}' at line {line} has ambiguously grouped tags {get_tag_list_str(tag_list)}and needs parentheses."


@hed_error(TagQualityErrors.MISSING_SENSORY_PRESENTATION, default_severity=ErrorSeverity.WARNING,
           actual_code=TagQualityErrors.MISSING_SENSORY_PRESENTATION)
def missing_sensory_presentation(string, line):
    return f"The HED string '{string}' at line {line} is a Sensory-event but does not have a sensory presentation " + \
    f"modality tag such as Visual-presentation or Auditory-presentation."


@hed_error(TagQualityErrors.MISSING_ACTION_TAG, default_severity=ErrorSeverity.WARNING,
           actual_code=TagQualityErrors.MISSING_ACTION_TAG)
def missing_action_tag(string, line):
    return f"The HED string '{string}' at line {line} is an Agent-action event but does not any Action tags " + \
    f"such as Move or Perform."