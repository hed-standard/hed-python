"""
This module is used to report errors found in the validation.

You can scope the formatted errors with calls to push_error_context and pop_error_context.
"""

from functools import wraps
import copy
from hed.errors.error_types import ErrorContext, ErrorSeverity

error_functions = {}


def _register_error_function(error_type, wrapper_func):
    if error_type in error_functions:
        raise KeyError(f"{error_type} defined more than once.")

    error_functions[error_type] = wrapper_func


def hed_error(error_type, default_severity=ErrorSeverity.ERROR, actual_code=None):
    """
    Decorator for errors in error handler or inherited classes.

    Parameters
    ----------
    error_type : str
        This should be a value from error_types, but doesn't strictly have to be.
    default_severity: ErrorSeverity
        The default severity for the decorated error
    actual_code: str
        The actual error to report to the outside world
    """
    if actual_code is None:
        actual_code = error_type

    def inner_decorator(func):
        @wraps(func)
        def wrapper(*args, severity=default_severity, **kwargs):
            """
            Wrapper function for error handling non-tag errors

           Parameters
           ----------
           args:
               Any other non keyword args
           severity: ErrorSeverity, Optional
               Will override the default error value if passed.(If you want to turn a warning into an error)
           kwargs:
               Any keyword args to be passed down to error message function
           Returns
           -------
           error_list: [{}]
           """
            base_message, error_vars = func(*args, **kwargs)
            error_object = ErrorHandler._create_error_object(actual_code, base_message, severity, **error_vars)
            return error_object

        _register_error_function(error_type, wrapper_func=wrapper)
        return wrapper

    return inner_decorator


def hed_tag_error(error_type, default_severity=ErrorSeverity.ERROR, has_sub_tag=False, actual_code=None):
    """
    Decorator for errors in error handler or inherited classes.

    Parameters
    ----------
    error_type : str
        This should be a value from error_types, but doesn't strictly have to be.
    default_severity: ErrorSeverity
        The default severity for the decorated error
    has_sub_tag : bool
        Determines if this error message also wants a sub_tag passed down.  eg "This" in "This/Is/A/Tag"
    actual_code: str
        The actual error to report to the outside world
    """
    if actual_code is None:
        actual_code = error_type

    def inner_decorator(func):
        if has_sub_tag:
            @wraps(func)
            def wrapper(tag, index_in_tag, index_in_tag_end, *args, severity=default_severity,
                        **kwargs):
                """
                Wrapper function for error handling tag errors with sub tags.

                Parameters
                ----------
                tag: HedTag
                    The hed tag object with the problem
                index_in_tag: int,
                    The index into the tag with a problem(usually 0)
                index_in_tag_end: int
                    the last index into the tag with a problem(usually len(tag)
                args:
                    Any other non keyword args
                severity: ErrorSeverity, Optional
                    Will override the default error value if passed.(If you want to turn a warning into an error)
                kwargs:
                    Any keyword args to be passed down to error message function
                Returns
                -------
                error_list: [{}]
                """
                try:
                    tag_as_string = tag.tag
                except AttributeError:
                    tag_as_string = "PlaceholderYouShouldNotSee2"

                if index_in_tag_end is None:
                    index_in_tag_end = len(tag_as_string)
                problem_sub_tag = tag_as_string[index_in_tag: index_in_tag_end]
                try:
                    org_tag_text = tag.org_tag
                except AttributeError:
                    org_tag_text = "PlaceholderYouShouldNotSee"

                base_message, error_vars = func(org_tag_text, problem_sub_tag, *args, **kwargs)
                error_object = ErrorHandler._create_error_object(actual_code, base_message, severity, **error_vars,
                                                                 index_in_tag=index_in_tag,
                                                                 index_in_tag_end=index_in_tag_end, source_tag=tag)

                return error_object

            _register_error_function(error_type, wrapper_func=wrapper)
            return wrapper
        else:
            @wraps(func)
            def wrapper(tag, *args, severity=default_severity, **kwargs):
                """
                Wrapper function for error handling tag errors

                Parameters
                ----------
                tag: HedTag or HedGroup
                    The hed tag object with the problem
                args:
                    Any other non keyword args
                severity: ErrorSeverity, Optional
                    Will override the default error value if passed.(If you want to turn a warning into an error)
                kwargs:
                    Any keyword args to be passed down to error message function
                Returns
                -------
                error_list: [{}]
                """
                from hed.schema.hed_tag import HedTag
                from hed.models.hed_group import HedGroup
                if isinstance(tag, HedTag):
                    org_tag_text = tag.org_tag
                elif isinstance(tag, HedGroup):
                    org_tag_text = tag.get_original_hed_string()
                else:
                    org_tag_text = "PlaceholderYouShouldNotSee"
                base_message, error_vars = func(org_tag_text, *args, **kwargs)
                error_object = ErrorHandler._create_error_object(actual_code, base_message, severity, **error_vars,
                                                                 source_tag=tag)

                return error_object

            _register_error_function(error_type, wrapper_func=wrapper)
            return wrapper

    return inner_decorator


# Import after hed_error decorators are defined.
from hed.errors import error_messages
# Intentional to make sure tools don't think the import is unused
error_messages.mark_as_used = True


class ErrorHandler:
    def __init__(self):
        # The current (ordered) dictionary of contexts.
        self.error_context = []
        # The list of validation issues found
        self.issue_list = []

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

    def get_error_context_copy(self):
        return copy.copy(self.error_context)

    def format_error_with_context(self, *args, **kwargs):
        error_object = ErrorHandler.format_error(*args, **kwargs)
        if self is not None:
            self._add_context_to_errors(error_object[0], self.error_context)
            self._update_error_with_char_pos(error_object[0])

        return error_object

    @staticmethod
    def format_error(error_type, *args, actual_error=None, **kwargs):
        """
            The parameters vary based on what type of error this is.

        Parameters
        ----------
        error_type : str
            The type of error for this.  Registered with @hed_error or @hed_tag_error.
        args: args
            Any remaining non keyword args.
        actual_error: str or None
            The code to actually add to report out.  Useful for errors that are shared like invalid character.
        kwargs :
            The other parameters to pass down to the error handling func.
        Returns
        -------
        error: [{}]
            A single error
        """
        error_func = error_functions.get(error_type)
        if not error_func:
            error_object = ErrorHandler.val_error_unknown(*args, **kwargs)
            error_object['code'] = error_type
            return [error_object]

        error_object = error_func(*args, **kwargs)
        if actual_error:
            error_object['code'] = actual_error

        return [error_object]

    def add_context_to_issues(self, issues):
        for error_object in issues:
            self._add_context_to_errors(error_object, self.error_context)
            self._update_error_with_char_pos(error_object)

    def format_error_list(self, issue_params):
        """
            Convert an issue params list to an issues list.  This means adding the error context primarily.

        Parameters
        ----------
        issue_params : [{}]
            The unformatted issues list
        Returns
        -------
        issues_list: [{}]
        """
        formatted_issues = []
        for issue in issue_params:
            formatted_issues += self.format_error(**issue)
        return formatted_issues

    @staticmethod
    def format_error_from_context(error_type, error_context, *args, actual_error=None, **kwargs):
        """
            The parameters vary based on what type of error this is.

        Parameters
        ----------
        error_type : str
            The type of error for this.  Registered with @hed_error or @hed_tag_error.
        error_context: []
            A list containing the error context to use for this error.  Generally returned from _add_context_to_errors
        args: args
            Any remaining non keyword args.
        actual_error: str or None
            The code to actually add to report out.  Useful for errors that are shared like invalid character.
        kwargs :
            The other parameters to pass down to the error handling func.
        Returns
        -------
        error: [{}]
            A single error
        """
        error_func = error_functions.get(error_type)
        if not error_func:
            error_object_list = ErrorHandler.val_error_unknown(*args, **kwargs)
            error_object_list[0]['code'] = error_type
            ErrorHandler._add_context_to_errors(error_object_list[0], error_context)
            return error_object_list

        error_object_list = error_func(*args, **kwargs)
        if actual_error:
            error_object_list[0]['code'] = actual_error

        ErrorHandler._add_context_to_errors(error_object_list[0], error_context)
        ErrorHandler._update_error_with_char_pos(error_object_list[0])
        return error_object_list

    @staticmethod
    def _add_context_to_errors(error_object, error_context_to_add):
        """
        Takes an error object and adds relevant context around it, such as row number, or column name.

        Parameters
        ----------
        error_object : {}
            Generated error containing at least a code and message entry.
        error_context_to_add: []
            Source context to use.  If none, gets it from the error handler directly at this time.
        Returns
        -------
        error_object_list: [{}]
            The passed in error with any needed context strings added to the start.
        """
        if error_object is None:
            error_object = {}
        for (context_type, context, increment_count) in error_context_to_add:
            error_object[context_type] = (context, increment_count)

        return error_object

    @staticmethod
    def _create_error_object(error_type, base_message, severity, **kwargs):
        if severity == ErrorSeverity.ERROR:
            error_prefix = "ERROR: "
        else:
            error_prefix = "WARNING: "
        error_message = error_prefix + base_message
        error_object = {'code': error_type,
                        'message': error_message,
                        'severity': severity
                        }

        for key, value in kwargs.items():
            error_object.setdefault(key, value)

        return error_object

    @staticmethod
    def _get_tag_span_to_error_object(error_object):
        if ErrorContext.HED_STRING not in error_object:
            return None, None

        if 'char_index' in error_object:
            char_index = error_object['char_index']
            char_index_end = error_object.get('char_index_end', char_index + 1)
            return char_index, char_index_end
        elif 'source_tag' in error_object:
            source_tag = error_object['source_tag']
            if isinstance(source_tag, int):
                return None, None
        else:
            return None, None

        hed_string = error_object[ErrorContext.HED_STRING][0]
        span = hed_string._get_org_span(source_tag)
        return span

    @staticmethod
    def _update_error_with_char_pos(error_object):
        # This part is optional as you can always generate these as needed.
        start, end = ErrorHandler._get_tag_span_to_error_object(error_object)
        if start is not None and end is not None:
            source_tag = error_object.get('source_tag', None)
            # Todo: Move this functionality somewhere more centralized.
            # If the tag has been modified from the original, don't try to use sub indexing.
            if source_tag and source_tag._tag:
                new_start, new_end = start, end
            else:
                new_start = start + error_object.get('index_in_tag', 0)
                index_in_tag_end = end
                if 'index_in_tag_end' in error_object:
                    index_in_tag_end = start + error_object['index_in_tag_end']
                new_end = index_in_tag_end
            error_object['char_index'], error_object['char_index_end'] = new_start, new_end
            error_object['message'] += f"  Problem spans string indexes: {new_start}, {new_end}"

    @hed_error("Unknown")
    def val_error_unknown(*args, **kwargs):
        """
        Default error handler if no error of this type was registered.

        Parameters
        ----------
        args : varies
        kwargs : varies

        Returns
        -------
        error_message, extra_error_args: str, dict
        """
        return f"Unknown error.  Args: {str(args)}", kwargs

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


def get_exception_issue_string(issues, title=None):
    """Return a string with issues list flatted into single string, one per line

    Parameters
    ----------
    issues: []
        Issues to print
    title: str
        Optional title that will always show up first if present(even if there are no validation issues)
    Returns
    -------
    str
        A str containing printable version of the issues or ''.
    """

    issue_str = ''
    if issues:
        translated_messages = [f"ERROR: {issue[1]}.\n    Source Line: {issue[0]}" for issue in issues]
        issue_str += '\n' + '\n'.join(translated_messages)
    if title:
        issue_str = title + '\n' + issue_str
    return issue_str


def get_printable_issue_string(issues, title=None, severity=None, skip_filename=True):
    """Return a string with issues list flatted into single string, one per line

    Parameters
    ----------
    issues: []
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
        A str containing printable version of the issues or ''.

    """
    last_used_error_context = []

    if severity is not None:
        issues = ErrorHandler.filter_issues_by_severity(issues, severity)

    issue_string = ""
    for single_issue in issues:
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


def check_for_any_errors(issues_list):
    for issue in issues_list:
        if issue['severity'] < ErrorSeverity.WARNING:
            return True

    return False



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
        context = context.get_original_hed_string()
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
