"""
This module is used to report errors found in the validation.

You can scope the formatted errors with calls to push_error_context and pop_error_context.
"""

from hed.util.error_types import ValidationErrors, ValidationWarnings, SchemaErrors, \
    SidecarErrors, SchemaWarnings, ErrorContext, ErrorSeverity, DefinitionErrors


class ErrorHandler:
    def __init__(self):
        # The current (ordered) dictionary of contexts.
        self.error_context = []

    def push_error_context(self, context_type, context, increment_depth_after=True):
        """
        Pushes a new error context to the end of the stack to narrow down error scope.

        Parameters
        ----------
        context_type : ErrorContext
            This should be a value from ErrorContext representing the type of scope.
        context : str or int or HedString
            The main value for the context_type.  eg for ErrorContext.FILE_NAME this would be the actual filename.
        increment_depth_after : bool
            If True, this adds an extra tab to any subsequent errors in the scope.
        Returns
        -------
        """
        self.error_context.append((context_type, context, increment_depth_after))

    def pop_error_context(self):
        """
        Removes the last scope from the error context.

        Returns
        -------
        """
        self.error_context.pop(-1)

    def reset_error_context(self):
        """Reset all error context information to defaults

        This function should not be needed with proper usage."""
        self.error_context = []

    def _add_context_to_errors(self, error_object=None):
        """
        Takes an error object and adds relevant context around it, such as row number, or column name.

        Parameters
        ----------
        error_object : {}
            Generated error containing at least a code and message entry.

        Returns
        -------
        error_object_list: [{}]
            The passed in error with any needed context strings added to the start.
        """
        for (context_type, context, increment_count) in self.error_context:
            error_object[context_type] = (context, increment_count)

        return [error_object]

    def format_val_error(self, error_type, hed_string='', tag='', tag_prefix='', previous_tag='',
                         character='', index=0, unit_class_units='', opening_parentheses_count=0,
                         closing_parentheses_count=0, category_keys=None):
        """Reports the abc error based on the type of error.

        Parameters
        ----------
        error_type: str
            The type of abc error.
        hed_string: str
            The full HED string in which the error occurred
        tag: HedTag or str
            The tag that generated the error.
        tag_prefix: str
            The tag prefix that generated the error.
        previous_tag: str
            The previous tag that potentially could have generated the error. This is passed in with the tag.
        index: int
            The index in the string of where the error occurred.
        character: str
            The character in the string that generated the error.
        unit_class_units: str
            The unit class units that are associated with the error.
        opening_parentheses_count: int
            The number of opening parentheses.
        closing_parentheses_count: int
            The number of closing parentheses.
        category_keys: [str]
            List of valid category keys for the given column
        Returns
        -------
        issue_list: [{}]
            A list containing a single dictionary with the warning type and warning message related to a particular type
            of warning.

        """
        try:
            tag = tag.org_tag
        except AttributeError:
            tag = tag

        error_prefix = "ERROR: "
        error_types = {
            ValidationErrors.PARENTHESES: f'{error_prefix}Number of opening and closing parentheses are unequal. '
                                          f'{opening_parentheses_count} opening parentheses. {closing_parentheses_count} '
                                          'closing parentheses',
            ValidationErrors.INVALID_CHARACTER: f'{error_prefix}Invalid character "{character}" at index {index} of string "{hed_string}"',
            ValidationErrors.TILDES_NOT_SUPPORTED: f'{error_prefix}Tildes not supported.  Replace (a ~ b ~ c) with (a, (b, c)).   "{character}" at index {index} of string "{hed_string}"',
            ValidationErrors.COMMA_MISSING: f'{error_prefix}Comma missing after - "{tag}"',
            ValidationErrors.DUPLICATE: f'{error_prefix}Duplicate tag - "{tag}"',
            ValidationErrors.REQUIRE_CHILD: f'{error_prefix}Descendant tag required - "{tag}"',
            ValidationErrors.MULTIPLE_UNIQUE: f'{error_prefix}Multiple unique tags with prefix - "{tag_prefix}"',
            ValidationErrors.UNIT_CLASS_INVALID_UNIT: f'{error_prefix}Invalid unit - "{tag}" valid units are "{unit_class_units}"',
            ValidationErrors.INVALID_TAG: f'{error_prefix}Invalid tag - "{tag}"',
            ValidationErrors.EMPTY_TAG: f'{error_prefix}HED tags cannot be empty.  Extra comma found at: "{character}" at index {index} of string "{hed_string}"',
            ValidationErrors.EXTRA_SLASHES_OR_SPACES: f"{error_prefix}Extra slashes or spaces '{character}' at index {index} of tag '{tag}'",
            ValidationErrors.HED_SIDECAR_KEY_MISSING: f"{error_prefix}Category key '{tag}' does not exist in column.  Valid keys are: {category_keys}",
            ValidationErrors.HED_DEFINITION_UNMATCHED: f"{error_prefix}A data-recording’s Def tag cannot be matched to definition.  Tag: '{tag}'",
            ValidationErrors.HED_DEFINITION_VALUE_MISSING: f"{error_prefix}A definition requires a placeholder value, but was not given one.  Definition: '{tag}",
            ValidationErrors.HED_DEFINITION_VALUE_EXTRA: f"{error_prefix}A definition does not take a placeholder value, but was given one.  Definition: '{tag}",
        }
        default_error_message = 'ERROR: Unknown error'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type, 'message': error_message, 'severity': ErrorSeverity.ERROR}
        error_object_list = self._add_context_to_errors(error_object)
        return error_object_list

    def format_sidecar_error(self, error_type, column_name="", given_type="", expected_type="", pound_sign_count=0,
                             category_count=0, severity=ErrorSeverity.ERROR):
        """
        Formats a json sidecar error to human readable

        Parameters
        ----------
        error_type : str
            This should be a value from SidecarErrors
        column_name : str
            The column name this error is from
        given_type : str
            A str representing the type of the variable there is an error with
        expected_type : str
            A str representing the expected type of the variable there is an error with
        pound_sign_count : int
            The number of pound signs found in the string.
        category_count : int
            The number of categories found in this column.
        severity: ErrorSeverity
            If this is an error or warning.
        Returns
        -------
        issue_list: [{}]
            A list containing a single dictionary with the warning type and warning message related to a particular type
            of warning.
        """
        error_prefix = "ERROR: "
        error_types = {
            SidecarErrors.BLANK_HED_STRING: f"{error_prefix}No HED string found for Value or Category column.",
            SidecarErrors.WRONG_HED_DATA_TYPE: f"{error_prefix}Invalid HED string datatype sidecar. Should be '{expected_type}', but got '{given_type}'",
            SidecarErrors.INVALID_NUMBER_POUND_SIGNS: f"{error_prefix}There should be exactly one # character in a sidecar string. Found {pound_sign_count}",
            SidecarErrors.TOO_MANY_POUND_SIGNS: f"{error_prefix}There should be no # characters in a category sidecar string. Found {pound_sign_count}",
            SidecarErrors.TOO_FEW_CATEGORIES: f"{error_prefix}A category column should have at least two keys. Found {category_count}",
            SidecarErrors.UNKNOWN_COLUMN_TYPE: f"{error_prefix}Could not automatically identify column '{column_name}' type from file. "
                                              f"Most likely the column definition in question needs a # sign to replace a number somewhere."
        }

        default_error_message = f'{error_prefix}Unknown error {error_type}'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type, 'message': error_message, 'severity': severity}

        error_object_list = self._add_context_to_errors(error_object)
        return error_object_list

    def format_val_warning(self, warning_type, tag='', default_unit='', tag_prefix=''):
        """Reports the abc warning based on the type of warning.

        Parameters
        ----------
        warning_type: string
            The type of abc warning.
        tag: str or HedTag
            The tag that generated the warning.
        default_unit: string
            The default unit class unit associated with the warning.
        tag_prefix: string
            The tag prefix that generated the warning.
        Returns
        -------
        issue_list: [{}]
            A list containing a single dictionary with the warning type and warning message related to a particular type
            of warning.

        """
        try:
            tag = tag.org_tag
        except AttributeError:
            tag = tag

        warning_prefix = "WARNING: "

        warning_types = {
            ValidationWarnings.CAPITALIZATION: f'{warning_prefix}First word not capitalized or camel case - "{tag}"',
            ValidationWarnings.REQUIRED_PREFIX_MISSING: f'{warning_prefix}Tag with prefix "{tag_prefix}" is required',
            ValidationWarnings.UNIT_CLASS_DEFAULT_USED: f'{warning_prefix}No unit specified. Using "{default_unit}" as the default - "{tag}"'
        }
        default_warning_message = 'WARNING: Unknown warning'
        warning_message = warning_types.get(warning_type, default_warning_message)

        warning_object = {'code': warning_type, 'message': warning_message, 'severity': ErrorSeverity.WARNING}
        warning_object_list = self._add_context_to_errors(warning_object)
        return warning_object_list

    def reformat_schema_error(self, error, hed_string, offset):
        """
        Updates a schema error from hed_tag indexing to hed_string indexing.

        Parameters
        ----------
        error : {}
            An error returned from format_schema_error
        hed_string : str
            The full hed_string the error is from.
        offset : int
            The index into hed_string where the reported error hed_tag started
        Returns
        -------
        {}
            The same error with index changed if it was a schema error.
        """
        # Bail early if this isn't a schema error
        if "start_index" not in error:
            return error

        error_type = error["code"]
        error_index = error["start_index"]
        error_index_end = error["end_index"]
        expected_parent_tag = error["expected_parent_tag"]

        reformatted_error = self.format_schema_error(error_type, hed_string, error_index + offset, error_index_end + offset, expected_parent_tag)
        return reformatted_error

    def format_schema_error(self, error_type, hed_tag, error_index=0, error_index_end=None, expected_parent_tag=None,
                            duplicate_tag_list=()):
        """Reports the abc error based on the type of error.

        Parameters
        ----------
        error_type: str
            The type of abc error.
        hed_tag: str
            The hed tag with a problem
        error_index: int
            The index where the error starts
        error_index_end: int
            The index where the error stops
        expected_parent_tag: str
            The expected full path of the tag from the schema.
        duplicate_tag_list: []
            A list of all all possible parents for this tag, if there is more than one.
        Returns
        -------
        issue_list: [{}]
            A list containing a single dictionary with the warning type and warning message related to a particular type
            of warning.

        """
        if error_index_end is None:
            error_index_end = len(hed_tag)

        problem_tag = str(hed_tag)[error_index: error_index_end]

        error_prefix = f"ERROR: "

        tag_join_delimiter = f"\n\t"
        error_types = {
            SchemaErrors.INVALID_PARENT_NODE: f"{error_prefix}'{problem_tag}' appears as '{str(expected_parent_tag)}' and cannot be used "
                                              f"as an extension.  Problem spans hed string indexes: {error_index}, {error_index_end}",
            SchemaErrors.NO_VALID_TAG_FOUND: f"{error_prefix}'{problem_tag}' is not a valid base hed tag.  Problem spans hed string indexes: {error_index}, {error_index_end} ",
            SchemaErrors.EMPTY_TAG_FOUND: f"{error_prefix}Empty tag cannot be converted.",
            SchemaErrors.INVALID_SCHEMA: f"{error_prefix}Source hed schema is invalid as it contains duplicate tags.  "
                                         f"Please fix if you wish to be abe to convert tags.",
            SchemaErrors.DUPLICATE_TERMS: f"{error_prefix}Term(Short Tag) '{str(hed_tag)}' used {len(duplicate_tag_list)} places in schema as: {tag_join_delimiter}"
                                          f"{tag_join_delimiter.join(duplicate_tag_list)}"
        }
        default_error_message = f'{error_prefix}Internal Error'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type,
                        'message': error_message,
                        'source_tag': str(hed_tag),
                        'start_index': error_index,
                        'end_index': error_index_end,
                        'expected_parent_tag': expected_parent_tag,
                        'severity': ErrorSeverity.ERROR}

        error_object_list = self._add_context_to_errors(error_object)
        return error_object_list

    def format_schema_warning(self, error_type, hed_tag, hed_desc=None, error_index=0, problem_char=None):
        """Reports the abc warning based on the type of error.

        Parameters
        ----------
        error_type: str
            The type of abc error.
        hed_tag: str
            The hed tag this error is from
        hed_desc: str
            The description this error is from
        error_index: int
            The position of the character with a problem
        problem_char: char
            The invalid character
        Returns
        -------
        issue_list: [{}]
            A list containing a single dictionary with the warning type and warning message related to a particular type
            of warning.

        """
        problem_tag = hed_tag

        warning_prefix = f"WARNING: "
        error_types = {
            SchemaWarnings.INVALID_CHARACTERS_IN_DESC: f"{warning_prefix}Invalid character '{problem_char}' in desc "
                                                       f"for '{problem_tag}' at position {error_index}.  '{hed_desc}",
            SchemaWarnings.INVALID_CHARACTERS_IN_TAG: f"{warning_prefix}Invalid character '{problem_char}' in tag "
                                                       f"'{problem_tag}' at position {error_index}.",
            SchemaWarnings.INVALID_CAPITALIZATION: f"{warning_prefix}First character just be a capital letter or number.  "
                                                   f"Found character '{problem_char}' in tag "
                                                   f"'{problem_tag}' at position {error_index}.",
        }
        default_warning_message = f'{warning_prefix}Internal Error'
        warning_message = error_types.get(error_type, default_warning_message)

        error_object = {'code': error_type,
                        'message': warning_message,
                        'source_tag': hed_tag,
                        'severity': ErrorSeverity.WARNING}

        error_object_list = self._add_context_to_errors(error_object)
        return error_object_list

    def format_definition_error(self, error_type, def_name, tag_list=None, expected_count=0):
        tag_list_strings = tag_list
        if tag_list:
            tag_list_strings = [str(tag) for tag in tag_list]
        error_prefix = f"ERROR: "
        error_types = {
            DefinitionErrors.WRONG_NUMBER_DEF_TAGS:
                f"{error_prefix}Too many def tags found in definition for {def_name}.  Expected 1, also found: {tag_list_strings}",
            DefinitionErrors.WRONG_NUMBER_GROUP_TAGS:
                f"{error_prefix}Too many group tags found in definition for {def_name}.  Expected 1, found: {tag_list_strings}",
            DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS:
                f"{error_prefix}Incorrect number placeholder tags found in definition for {def_name}.  Expected {expected_count}, found: {tag_list_strings}",
            DefinitionErrors.DUPLICATE_DEFINITION:
                f"{error_prefix}Duplicate definition found for '{def_name}'.",
            DefinitionErrors.TAG_IN_SCHEMA:
                f"{error_prefix}Term '{def_name}' already used as term in schema and cannot be re-used as a definition.",
            DefinitionErrors.INVALID_DEF_EXTENSION:
                f"{error_prefix}Term '{def_name}' has an invalid extension.  Definitions can only have one term."
        }
        default_error_message = f'{error_prefix}Internal Error'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type,
                        'message': error_message,
                        'severity': ErrorSeverity.ERROR}

        error_object_list = self._add_context_to_errors(error_object)
        return error_object_list

    @staticmethod
    def filter_issues_by_severity(issues_list, severity):
        """
        Gathers all issues matching or below a given severity.
            
        Parameters
        ----------
        issues_list : [{}]
            The full issue list
        severity : int
            The level of issue you're interested in

        Returns
        -------
        filtered_issues_list: [{}]
            The list with all other severities removed.
        """
        return [issue for issue in issues_list if issue['severity'] <= severity]


def get_printable_issue_string(validation_issues, title=None, severity=None, skip_filename=True):
    """Return a string with issues list flatted into single string, one per line

    Parameters
    ----------
    validation_issues: []
        Issues to print
    title: str
        Optional title that will always show up first if present(even if there are no validation issues)
    severity: int
        Return only warnings >= severity
    skip_filename: bool
        If true, don't add the filename context to the printable string.
    Returns
    -------
    str
        A str containing printable version of the issues or '[]'.

    """
    last_used_error_context = []

    if severity is not None:
        validation_issues = ErrorHandler.filter_issues_by_severity(validation_issues, severity)

    issue_string = ""
    for single_issue in validation_issues:
        single_issue_context = _get_context_from_issue(single_issue, skip_filename)
        context_string, tab_string = _get_context_string(single_issue_context, last_used_error_context)

        issue_string += context_string
        single_issue_message = tab_string + single_issue['message']
        if "\n" in single_issue_message:
            single_issue_message = single_issue_message.replace("\n", "\n" + tab_string)
        issue_string += f"{single_issue_message}\n"
        last_used_error_context = single_issue_context.copy()

    if issue_string:
        issue_string += "\n"
    if title:
        issue_string = title + '\n' + issue_string
    return issue_string


def _get_context_from_issue(val_issue, skip_filename=True):
    """
    Extract all the context values from the given issue
    Parameters
    ----------
    val_issue : {}
        A dictionary a representing a single error
    skip_filename: bool
        If true, don't gather the filename context.
    Returns
    -------
    context_list: []
        A list of tuples containing the context_type and context for the given issue
    """
    single_issue_context = []
    for key in val_issue:
        if skip_filename and key == ErrorContext.FILE_NAME:
            continue
        if key.startswith("ec_"):
            single_issue_context.append((key, *val_issue[key]))

    return single_issue_context


def _format_single_context_string(context_type, context, tab_count=0):
    """
    Takes a single context tuple and returns the human readable form.

    Parameters
    ----------
    context_type : str
        The context type of this entry
    context : str
        The value of this context
    tab_count : int
        Number of tabs to prefix each line with.

    Returns
    -------
    context_string: str
        A string containing the context, including tabs.
    """
    tab_string = tab_count * '\t'
    if context_type == ErrorContext.HED_STRING:
        context = str(context).replace('\n', ' ')
    error_types = {
        ErrorContext.FILE_NAME: f"\nErrors in file '{context}'",
        ErrorContext.SIDECAR_COLUMN_NAME: f"Column '{context}':",
        ErrorContext.SIDECAR_KEY_NAME: f"Key: {context}",
        ErrorContext.ROW: f'Issues in row {context}:',
        ErrorContext.COLUMN: f'Issues in column {context}:',
        ErrorContext.CUSTOM_TITLE: context,
        ErrorContext.HED_STRING: f"hed string: {context}",
    }
    context_portion = error_types[context_type]
    context_string = f"{tab_string}{context_portion}\n"
    return context_string


def _get_context_string(single_issue_context, last_used_context):
    """
    Converts a single context list into the final human readable output form.

    Parameters
    ----------
    single_issue_context : [()]
        A list of tuples containing the context(context_type, context, increment_tab)
    last_used_context : [()]
        A list of tuples containing the last drawn context, so it can only add the parts that have changed.
        This is always the same format as single_issue_context.

    Returns
    -------
    context_string: str
        The full string of context(potentially multiline) to add before the error
    tab_string: str
        The prefix to add to any message line with this context.
    """
    context_string = ""
    tab_count = 0
    found_difference = False
    for i, context_tuple in enumerate(single_issue_context):
        (context_type, context, increment_tab) = context_tuple
        if len(last_used_context) > i and not found_difference:
            last_drawn = last_used_context[i]
            # Was drawn, and hasn't changed.
            if last_drawn == context_tuple:
                if increment_tab:
                    tab_count += 1
                continue

        context_string += _format_single_context_string(context_type, context, tab_count)
        found_difference = True
        if increment_tab:
            tab_count += 1

    tab_string = '\t' * tab_count
    return context_string, tab_string
