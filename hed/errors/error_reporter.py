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
    """ Decorator for errors in error handler or inherited classes.

    Parameters:
        error_type (str): A value from error_types or optionally another value.
        default_severity (ErrorSeverity): The default severity for the decorated error.
        actual_code (str): The actual error to report to the outside world.

    """
    if actual_code is None:
        actual_code = error_type

    def inner_decorator(func):
        @wraps(func)
        def wrapper(*args, severity=default_severity, **kwargs):
            """ Wrapper function for error handling non-tag errors.

            Parameters:
                args (args): non keyword args.
                severity (ErrorSeverity): Will override the default error value if passed.
                kwargs (**kwargs): Any keyword args to be passed down to error message function.

            Returns:
                list: A list of dict with the errors.=
            """
            base_message, error_vars = func(*args, **kwargs)
            error_object = ErrorHandler._create_error_object(actual_code, base_message, severity, **error_vars)
            return error_object

        _register_error_function(error_type, wrapper_func=wrapper)
        return wrapper

    return inner_decorator


def hed_tag_error(error_type, default_severity=ErrorSeverity.ERROR, has_sub_tag=False, actual_code=None):
    """  Decorator for errors in error handler or inherited classes.

    Parameters:
        error_type (str): A value from error_types or optionally another value.
        default_severity (ErrorSeverity): The default severity for the decorated error.
        has_sub_tag (bool): If true, this error message also wants a sub_tag passed down.  eg "This" in "This/Is/A/Tag"
        actual_code (str): The actual error to report to the outside world.

    """
    if actual_code is None:
        actual_code = error_type

    def inner_decorator(func):
        if has_sub_tag:
            @wraps(func)
            def wrapper(tag, index_in_tag, index_in_tag_end, *args, severity=default_severity, **kwargs):
                """ Wrapper function for error handling tag errors with sub tags.

                Parameters:
                    tag (HedTag): The hed tag object with the problem,
                    index_in_tag (int): The index into the tag with a problem(usually 0),
                    index_in_tag_end (int): The last index into the tag with a problem(usually len(tag),
                    args (args): Any other non keyword args.
                    severity (ErrorSeverity): Used to include warnings as well as errors.
                    kwargs (**kwargs): Any keyword args to be passed down to error message function.

                Returns:
                    list: A list of dict with the errors.

                """
                try:
                    tag_as_string = tag.tag
                except AttributeError:
                    tag_as_string = str(tag)

                if index_in_tag_end is None:
                    index_in_tag_end = len(tag_as_string)
                problem_sub_tag = tag_as_string[index_in_tag: index_in_tag_end]
                try:
                    org_tag_text = tag.org_tag
                except AttributeError:
                    org_tag_text = str(tag)

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
                """ Wrapper function for error handling tag errors.

                Parameters:
                    tag (HedTag or HedGroup): The hed tag object with the problem.
                    args (non keyword args): Any other non keyword args.
                    severity (ErrorSeverity): For including warnings.
                    kwargs (keyword args): Any keyword args to be passed down to error message function.

                Returns:
                    list: A list of dict with the errors.

                """
                from hed.models.hed_tag import HedTag
                from hed.models.hed_group import HedGroup
                if isinstance(tag, HedTag):
                    org_tag_text = tag.org_tag
                elif isinstance(tag, HedGroup):
                    org_tag_text = tag.get_original_hed_string()
                else:
                    org_tag_text = str(tag)
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

    def push_error_context(self, context_type, context, increment_depth_after=True):
        """ Push a new error context to narrow down error scope.

        Parameters:
            context_type (ErrorContext): A value from ErrorContext representing the type of scope.
            context (str, int, or HedString): The main value for the context_type.
            increment_depth_after (bool): If True, add an extra tab to any subsequent errors in the scope.

        Notes:
            The context depends on the context_type. For ErrorContext.FILE_NAME this would be the actual filename.

        """
        self.error_context.append((context_type, context, increment_depth_after))

    def pop_error_context(self):
        """ Remove the last scope from the error context.

        Notes:
            Modifies the error context of this reporter.

        """

        self.error_context.pop(-1)

    def reset_error_context(self):
        """ Reset all error context information to defaults.

        Notes:
            This function is mainly for testing and should not be needed with proper usage.

        """
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
        """ Format an error based on the parameters, which vary based on what type of error this is.

        Parameters:
            error_type (str): The type of error for this.  Registered with @hed_error or @hed_tag_error.
            args (args): Any remaining non keyword args after those required by the error type.
            actual_error (str or None): Code to actually add to report out.
            kwargs (dict): The other keyword args to pass down to the error handling func.

        Returns:
            list:   A list containing a single dictionary representing a single error.

        Notes:
            The actual error is useful for errors that are shared like invalid character.

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
        """ Convert an issue params list to an issues list.  This means adding the error context primarily.

        Parameters:
            issue_params (list):  A list of dict containing the unformatted issues list.

        Returns:
            list: A list of dict containing unformatted errors.

        """
        formatted_issues = []
        for issue in issue_params:
            formatted_issues += self.format_error(**issue)
        return formatted_issues

    @staticmethod
    def format_error_from_context(error_type, error_context, *args, actual_error=None, **kwargs):
        """ Format an error based on the error type.

        Parameters:
            error_type (str): The type of error.  Registered with @hed_error or @hed_tag_error.
            error_context (list): Contains the error context to use for this error.
            args (args): Any remaining non keyword args.
            actual_error (str or None): Error code to actually add to report out.
            kwargs (kwargs): Keyword parameters to pass down to the error handling func.

        Returns:
            list:  A list containing a single dictionary

        Notes:
            - Generally the error_context is returned from _add_context_to_errors.
            - The actual_error is useful for errors that are shared like invalid character.

        """
        error_func = error_functions.get(error_type)
        if not error_func:
            error_object = ErrorHandler.val_error_unknown(*args, **kwargs)
            error_object['code'] = error_type
            ErrorHandler._add_context_to_errors(error_object, error_context)
            return [error_object]

        error_object = error_func(*args, **kwargs)
        if actual_error:
            error_object['code'] = actual_error

        ErrorHandler._add_context_to_errors(error_object, error_context)
        ErrorHandler._update_error_with_char_pos(error_object)
        return [error_object]

    @staticmethod
    def _add_context_to_errors(error_object, error_context_to_add):
        """ Add relevant context such as row number or column name around an error object.

        Parameters:
            error_object (dict): Generated error containing at least a code and message entry.
            error_context_to_add (list): Source context to use.  If none, the error handler context is used.

        Returns:
            list: A list of dict with needed context strings added at the beginning of the list.

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
        """ Default error handler if no error of this type was registered.

        Parameters:
            args (args):     List of non-keyword parameters (varies).
            kwargs (kwargs): Keyword parameters (varies)

        Returns:
            str: The error message.
            dict: The extra args.

        """
        return f"Unknown error.  Args: {str(args)}", kwargs

    @staticmethod
    def filter_issues_by_severity(issues_list, severity):
        """ Gather all issues matching or below a given severity.

        Parameters:
            issues_list (list): A list of dictionaries containing the full issue list.
            severity (int): The level of issues to keep.

        Returns:
            list: A list of dictionaries containing the issue list after filtering by severity.

        """
        return [issue for issue in issues_list if issue['severity'] <= severity]


def get_exception_issue_string(issues, title=None):
    """ Return a string with issues list flatted into single string, one issue per line.

    Parameters:
        issues (list):  A list of strings containing issues to print.
        title (str or None): An optional title that will always show up first if present.

    Returns:
        str: A str containing printable version of the issues or ''.

    """
    issue_str = ''
    if issues:
        issue_list = []
        for issue in issues:
            this_str = f"{issue['message']}"
            if 'code' in issue:
                this_str = f"{issue['code']}:" + this_str
            if 'line_number' in issue:
                this_str = this_str + f"\n\tLine number {issue['line_number']}: {issue.get('line', '')} "
            issue_list.append(this_str)
        issue_str += '\n' + '\n'.join(issue_list)
    if title:
        issue_str = title + '\n' + issue_str
    return issue_str


def get_printable_issue_string(issues, title=None, severity=None, skip_filename=True):
    """ Return a string with issues list flatted into single string, one per line.

    Parameters:
        issues (list):  Issues to print.
        title (str):  Optional title that will always show up first if present(even if there are no validation issues).
        severity (int):        Return only warnings >= severity.
        skip_filename (bool):  If true, don't add the filename context to the printable string.

    Returns:
        str:   A string containing printable version of the issues or ''.

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
    """ Extract all the context values from the given issue.

    Parameters:
        val_issue (dict): A dictionary a representing a single error.
        skip_filename (bool): If true, don't gather the filename context.

    Returns:
        list: A list of tuples containing the context_type and context for the given issue.

    """
    single_issue_context = []
    for key in val_issue:
        if skip_filename and key == ErrorContext.FILE_NAME:
            continue
        if key.startswith("ec_"):
            single_issue_context.append((key, *val_issue[key]))

    return single_issue_context


def _format_single_context_string(context_type, context, tab_count=0):
    """ Return the human readable form of a single context tuple.

    Parameters:
        context_type (str): The context type of this entry.
        context (str or HedString): The value of this context
        tab_count (int): Number of tabs to name_prefix each line with.

    Returns:
        str: A string containing the context, including tabs.

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
        ErrorContext.SCHEMA_SECTION: f"Schema Section: {context}",
        ErrorContext.SCHEMA_TAG: f"Source tag: {context}",
        ErrorContext.SCHEMA_ATTRIBUTE: f"Source Attribute: {context}",
    }
    context_portion = error_types[context_type]
    context_string = f"{tab_string}{context_portion}\n"
    return context_string


def _get_context_string(single_issue_context, last_used_context):
    """ Convert a single context list into the final human readable output form.

    Parameters:
        single_issue_context (list): A list of tuples containing the context(context_type, context, increment_tab)
        last_used_context (list): A list of tuples containing the last drawn context.

    Returns:
        str: The full string of context(potentially multiline) to add before the error.
        str: The tab string to add to the front of any message line with this context.

    Notes:
        The last used context is always the same format as single_issue_context and used
        so that the error handling can only add the parts that have changed.

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
