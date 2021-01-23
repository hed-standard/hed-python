"""
This module is used to report errors found in the validation.

You can scope the formatted errors with calls to push_error_context and pop_error_context.
"""

from hed.util.error_types import ValidationErrors, ValidationWarnings, SchemaErrors, \
    SidecarErrors, SchemaWarnings, ErrorContext


class ErrorHandler:
    def __init__(self):
        # Number of tabs to insert at the start of each line.  Incremented when you push a new error_context.
        self.current_tab_depth = 0
        # A list of strings containing the current error context scope such as row or column number.
        # Starts from index 0 being the largest(eg file usually) scope.
        self.error_context_stack = []
        # A copy of the last error_context_stack used to actually format an error.
        # This is used to allow us to only display the context once, regardless of how many errors there are.
        self.last_used_error_context = []

    def push_error_context(self, context_type, context, increment_depth_after=True, column_context=None):
        """
        Pushes a new error context to the end of the stack to narrow down error scope.

        Parameters
        ----------
        context_type : str
            This should be a value from ErrorContext representing the type of scope.
        context : str or int
            The main value for the context_type.  eg for ErrorContext.FILE_NAME this would be the actual filename.
        increment_depth_after : bool
            If True, this adds an extra tab to any subsequent errors in the scope.
        column_context : str or int
            This is only used by ErrorContext.COLUMN, where context is the row and column_context is the column number.
        Returns
        -------
        """
        default_tabbing = "\t" * self.current_tab_depth

        error_types = {
            ErrorContext.FILE_NAME: f"\nErrors in file '{context}'",
            ErrorContext.SIDECAR_COLUMN_NAME: f"Column '{context}':",
            ErrorContext.SIDECAR_CUE_NAME: f"Cue: {context}",
            ErrorContext.SIDECAR_HED_STRING: f"hed_string: {context}",
            ErrorContext.ROW: f'Issues in row {context}:',
            ErrorContext.COLUMN: f'Issues in row {context} column {column_context}:'
        }

        default_context = 'ERROR: Unknown error context'
        context_message = error_types.get(context_type, default_context)

        self.error_context_stack.append(f"{default_tabbing}{context_message}")
        if increment_depth_after:
            self.current_tab_depth += 1


    def pop_error_context(self, decrement_depth_after=True):
        """
        Removes the last scope from the error context.

        Parameters
        ----------
        decrement_depth_after : bool
            This should always match the value passed to push_error_context.

        Returns
        -------
        """
        if decrement_depth_after:
            self.current_tab_depth -= 1
        self.error_context_stack.pop()


    def reset_error_context(self):
        """Reset all error context information to defaults

        This function should not be needed with proper usage."""
        self.current_tab_depth = 0
        self.error_context_stack = []
        self.last_used_error_context = []


    def _add_context_to_errors(self, error_object):
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
        # The context has not changed, no need to add new context text
        if self.last_used_error_context == self.error_context_stack:
            return [error_object]

        error_context = []
        for i, context in enumerate(self.error_context_stack):
            if len(self.last_used_error_context) > i:
                last_drawn = self.last_used_error_context[i]
                # Was drawn, and hasn't changed.
                if last_drawn == context:
                    continue

            context_object = {'code': 'context', 'message': context}
            error_context.append(context_object)

        self.last_used_error_context = self.error_context_stack.copy()

        return error_context + [error_object]


    def format_val_error(self, error_type, hed_string='', tag='', tag_prefix='', previous_tag='',
                         character='', index=0, unit_class_units='', file_name='', opening_parentheses_count=0,
                         closing_parentheses_count=0):
        """Reports the abc error based on the type of error.

        Parameters
        ----------
        error_type: str
            The type of abc error.
        hed_string: str
            The full HED string in which the error occurred
        tag: str
            The tag that generated the error. The original tag not the formatted one.
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
        file_name: str
            The invalid file name that cause the error.
        opening_parentheses_count: int
            The number of opening parentheses.
        closing_parentheses_count: int
            The number of closing parentheses.
        Returns
        -------
        issue_list: [{}]
            A list containing a single dictionary with the warning type and warning message related to a particular type
            of warning.

        """
        default_tabbing = "\t" * self.current_tab_depth
        error_prefix = default_tabbing + "ERROR: "
        error_types = {
            ValidationErrors.INVALID_FILENAME: f'Invalid file name - "{file_name}"',
            ValidationErrors.PARENTHESES: f'{error_prefix}Number of opening and closing parentheses are unequal. '
                                          f'{opening_parentheses_count} opening parentheses. {closing_parentheses_count} '
                                          'closing parentheses',
            ValidationErrors.INVALID_CHARACTER: f'{error_prefix}Invalid character "{character}" at index {index} of string "{hed_string}"',
            ValidationErrors.COMMA_MISSING: f'{error_prefix}Comma missing after - "{tag}"',
            ValidationErrors.INVALID_COMMA: f'{error_prefix}Either "{previous_tag}" contains a comma when it should not or "{tag}" is not a valid '
                                            'tag ',
            ValidationErrors.DUPLICATE: f'{error_prefix}Duplicate tag - "{tag}"',
            ValidationErrors.REQUIRE_CHILD: f'{error_prefix}Descendant tag required - "{tag}"',
            ValidationErrors.EXTRA_TILDE: f'{error_prefix}Too many tildes - group "{tag}"',
            ValidationErrors.MULTIPLE_UNIQUE: f'{error_prefix}Multiple unique tags with prefix - "{tag_prefix}"',
            ValidationErrors.UNIT_CLASS_INVALID_UNIT: f'{error_prefix}Invalid unit - "{tag}" valid units are "{unit_class_units}"',
            ValidationErrors.INVALID_TAG: f'{error_prefix}Invalid tag - "{tag}"',
            ValidationErrors.EXTRA_DELIMITER: f'{error_prefix}Extra delimiter "{character}" at index {index} of string "{hed_string}"',
        }
        default_error_message = 'ERROR: Unknown error'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type, 'message': error_message}
        error_object_list = self._add_context_to_errors(error_object)
        return error_object_list


    def format_sidecar_error(self, error_type, filename="", column_name="", given_type="", expected_type="", pound_sign_count=0,
                             category_count=0):
        """
        Formats a json sidecar error to human readable

        Parameters
        ----------
        error_type : str
            This should be a value from SidecarErrors
        filename : str
            The filename this error is from
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

        Returns
        -------
        issue_list: [{}]
            A list containing a single dictionary with the warning type and warning message related to a particular type
            of warning.
        """
        default_tabbing = "\t" * self.current_tab_depth
        error_prefix = default_tabbing + "ERROR: "
        error_types = {
            SidecarErrors.BLANK_HED_STRING: f"{error_prefix}No HED string found for Value or Category column.",
            SidecarErrors.WRONG_HED_DATA_TYPE: f"{error_prefix}Invalid HED string datatype sidecar. Should be '{expected_type}', but got '{given_type}'",
            SidecarErrors.INVALID_NUMBER_POUND_SIGNS: f"{error_prefix}There should be exactly one # character in a sidecar string. Found {pound_sign_count}",
            SidecarErrors.TOO_MANY_POUND_SIGNS: f"{error_prefix}There should be no # characters in a category sidecar string. Found {pound_sign_count}",
            SidecarErrors.TOO_FEW_CATEGORIES: f"{error_prefix}A category column should have at least two cues. Found {category_count}",
            SidecarErrors.UNKNOWN_COLUMN_TYPE: f"{error_prefix}Could not automatically identify column '{column_name}' type from file. "
                                              f"Most likely the column definition in question needs a # sign to replace a number somewhere."
        }

        default_error_message = f'{error_prefix}Unknown error {error_type}'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type, 'message': error_message}

        error_object_list = self._add_context_to_errors(error_object)
        return error_object_list


    def format_val_warning(self, warning_type, tag='', default_unit='', tag_prefix=''):
        """Reports the abc warning based on the type of warning.

        Parameters
        ----------
        warning_type: string
            The type of abc warning.
        tag: string
            The tag that generated the warning. The original tag not the formatted one.
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
        default_tabbing = "\t" * self.current_tab_depth
        warning_prefix = default_tabbing + "WARNING: "

        warning_types = {
            ValidationWarnings.CAPITALIZATION: f'{warning_prefix}First word not capitalized or camel case - "{tag}"',
            ValidationWarnings.REQUIRED_PREFIX_MISSING: f'{warning_prefix}Tag with prefix "{tag_prefix}" is required',
            ValidationWarnings.UNIT_CLASS_DEFAULT_USED: f'{warning_prefix}No unit specified. Using "{default_unit}" as the default - "{tag}"'
        }
        default_warning_message = 'WARNING: Unknown warning'
        warning_message = warning_types.get(warning_type, default_warning_message)

        warning_object = {'code': warning_type, 'message': warning_message}
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

        problem_tag = hed_tag[error_index: error_index_end]

        default_tabbing = "\t" * self.current_tab_depth
        error_prefix = f"{default_tabbing}ERROR: "

        tag_join_delimiter = f"\n\t{default_tabbing}"
        error_types = {
            SchemaErrors.INVALID_PARENT_NODE: f"{error_prefix}'{problem_tag}' appears as '{expected_parent_tag}' and cannot be used "
                                              f"as an extension.  {error_index}, {error_index_end}",
            SchemaErrors.NO_VALID_TAG_FOUND: f"{error_prefix}'{problem_tag}' is not a valid base hed tag.  {error_index}, {error_index_end} ",
            SchemaErrors.EMPTY_TAG_FOUND: f"{error_prefix}Empty tag cannot be converted.",
            SchemaErrors.INVALID_SCHEMA: f"{error_prefix}Source hed schema is invalid as it contains duplicate tags.  "
                                         f"Please fix if you wish to be abe to convert tags. {error_index}, {error_index_end}",
            SchemaErrors.DUPLICATE_TERMS: f"{error_prefix}Term(Short Tag) '{hed_tag}' used {len(duplicate_tag_list)} places in schema as: {tag_join_delimiter}"
                                          f"{tag_join_delimiter.join(duplicate_tag_list)}"
        }
        default_error_message = f'{error_prefix}Internal Error'
        error_message = error_types.get(error_type, default_error_message)

        error_object = {'code': error_type,
                        'message': error_message,
                        'source_tag': hed_tag,
                        'start_index': error_index,
                        'end_index': error_index_end,
                        'expected_parent_tag': expected_parent_tag}

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

        default_tabbing = "\t" * self.current_tab_depth
        warning_prefix = f"{default_tabbing}WARNING: "
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
                        'source_tag': hed_tag}

        error_object_list = self._add_context_to_errors(error_object)
        return error_object_list

default_handler = ErrorHandler()
