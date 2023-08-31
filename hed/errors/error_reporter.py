"""
This module is used to report errors found in the validation.

You can scope the formatted errors with calls to push_error_context and pop_error_context.
"""

from functools import wraps
import xml.etree.ElementTree as ET
import copy
from hed.errors.error_types import ErrorContext, ErrorSeverity
from hed.errors.known_error_codes import known_error_codes

error_functions = {}

# Controls if the default issue printing skips adding indentation for this context
no_tab_context = {ErrorContext.HED_STRING, ErrorContext.SCHEMA_ATTRIBUTE}

# Default sort ordering for issues list
default_sort_list = [
    ErrorContext.CUSTOM_TITLE,
    ErrorContext.FILE_NAME,
    ErrorContext.SIDECAR_COLUMN_NAME,
    ErrorContext.SIDECAR_KEY_NAME,
    ErrorContext.ROW,
    ErrorContext.COLUMN,
    ErrorContext.LINE,
    ErrorContext.SCHEMA_SECTION,
    ErrorContext.SCHEMA_TAG,
    ErrorContext.SCHEMA_ATTRIBUTE,
]

# ErrorContext which is expected to be int based.
int_sort_list = [
    ErrorContext.ROW
]


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
            base_message = func(*args, **kwargs)
            error_object = ErrorHandler._create_error_object(actual_code, base_message, severity)
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
                    index_in_tag_end (int): The last index into the tag with a problem - usually len(tag),
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

                base_message = func(org_tag_text, problem_sub_tag, *args, **kwargs)
                error_object = ErrorHandler._create_error_object(actual_code, base_message, severity,
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
                base_message = func(org_tag_text, *args, **kwargs)
                error_object = ErrorHandler._create_error_object(actual_code, base_message, severity,
                                                                 source_tag=tag)

                return error_object

            _register_error_function(error_type, wrapper_func=wrapper)
            return wrapper

    return inner_decorator


# Import after hed_error decorators are defined.
from hed.errors import error_messages
from hed.errors import schema_error_messages

# Intentional to make sure tools don't think the import is unused
error_messages.mark_as_used = True
schema_error_messages.mark_as_used = True


class ErrorHandler:
    def __init__(self, check_for_warnings=True):
        # The current (ordered) dictionary of contexts.
        self.error_context = []
        self._check_for_warnings = check_for_warnings

    def push_error_context(self, context_type, context):
        """ Push a new error context to narrow down error scope.

        Parameters:
            context_type (ErrorContext): A value from ErrorContext representing the type of scope.
            context (str, int, or HedString): The main value for the context_type.

        Notes:
            The context depends on the context_type. For ErrorContext.FILE_NAME this would be the actual filename.

        """
        if context is None:
            if context_type in int_sort_list:
                context = 0
            else:
                context = ""
        self.error_context.append((context_type, context))

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
            actual_error = error_object[0]
            # # Filter out warning errors
            if not self._check_for_warnings and actual_error['severity'] >= ErrorSeverity.WARNING:
                return []
            self._add_context_to_errors(actual_error, self.error_context)
            self._update_error_with_char_pos(actual_error)

        return error_object

    @staticmethod
    def format_error(error_type, *args, actual_error=None, **kwargs):
        """ Format an error based on the parameters, which vary based on what type of error this is.

        Parameters:
            error_type (str): The type of error for this.  Registered with @hed_error or @hed_tag_error.
            args (args): Any remaining non keyword args after those required by the error type.
            actual_error (str or None): Code to actually add to report out.
            kwargs (kwargs): The other keyword args to pass down to the error handling func.

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

    def add_context_and_filter(self, issues):
        """ Filter out warnings if requested, while adding context to issues.

            issues(list):
                list:   A list containing a single dictionary representing a single error.
        """
        if not self._check_for_warnings:
            issues[:] = self.filter_issues_by_severity(issues, ErrorSeverity.ERROR)

        for error_object in issues:
            self._add_context_to_errors(error_object, self.error_context)
            self._update_error_with_char_pos(error_object)

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
            - This can't filter out warnings like the other ones.

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
        for (context_type, context) in error_context_to_add:
            error_object[context_type] = context

        return error_object

    @staticmethod
    def _create_error_object(error_type, base_message, severity, **kwargs):
        error_object = {'code': error_type,
                        'message': base_message,
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

        hed_string = error_object[ErrorContext.HED_STRING]
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

        """
        return f"Unknown error.  Args: {str(args), str(kwargs)}"

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


def sort_issues(issues, reverse=False):
    """Sorts a list of issues by the error context values.

    Parameters:
        issues (list): A list of dictionaries representing the issues to be sorted.
        reverse (bool, optional): If True, sorts the list in descending order. Default is False.

    Returns:
        list: The sorted list of issues."""
    def _get_keys(d):
        result = []
        for key in default_sort_list:
            if key in int_sort_list:
                result.append(d.get(key, -1))
            else:
                result.append(d.get(key, ""))
        return tuple(result)

    issues = sorted(issues, key=_get_keys, reverse=reverse)

    return issues


def check_for_any_errors(issues_list):
    """Returns True if there are any errors with a severity of warning"""
    for issue in issues_list:
        if issue['severity'] < ErrorSeverity.WARNING:
            return True

    return False


def get_printable_issue_string(issues, title=None, severity=None, skip_filename=True, add_link=False):
    """ Return a string with issues list flatted into single string, one per line.

    Parameters:
        issues (list):  Issues to print.
        title (str):  Optional title that will always show up first if present(even if there are no validation issues).
        severity (int):        Return only warnings >= severity.
        skip_filename (bool):  If true, don't add the filename context to the printable string.
        add_link (bool): Add a link at the end of message to the appropriate error if True
    Returns:
        str:   A string containing printable version of the issues or ''.

    """
    if severity is not None:
        issues = ErrorHandler.filter_issues_by_severity(issues, severity)

    output_dict = _build_error_context_dict(issues, skip_filename)
    issue_string = _error_dict_to_string(output_dict, add_link=add_link)

    if title:
        issue_string = title + '\n' + issue_string
    return issue_string


def get_printable_issue_string_html(issues, title=None, severity=None, skip_filename=True):
    """ Return a string with issues list as an HTML tree.

    Parameters:
        issues (list):  Issues to print.
        title (str):  Optional title that will always show up first if present.
        severity (int): Return only warnings >= severity.
        skip_filename (bool): If true, don't add the filename context to the printable string.

    Returns:
        str: An HTML string containing the issues or ''.
    """
    if severity is not None:
        issues = ErrorHandler.filter_issues_by_severity(issues, severity)

    output_dict = _build_error_context_dict(issues, skip_filename)

    root_element = _create_error_tree(output_dict)
    if title:
        title_element = ET.Element("h1")
        title_element.text = title
        root_element.insert(0, title_element)
    return ET.tostring(root_element, encoding='unicode')


def create_doc_link(error_code):
    """If error code is a known code, return a documentation url for it

    Parameters:
        error_code(str): A HED error code

    Returns:
        url(str or None): The URL if it's a valid code
    """
    if error_code in known_error_codes["hed_validation_errors"] \
            or error_code in known_error_codes["schema_validation_errors"]:
        modified_error_code = error_code.replace("_", "-").lower()
        return f"https://hed-specification.readthedocs.io/en/latest/Appendix_B.html#{modified_error_code}"
    return None


def _build_error_context_dict(issues, skip_filename):
    """Builds the context -> error dictionary for an entire list of issues

    Returns:
        dict: A nested dictionary structure with a "children" key at each level for unrelated children.
    """
    output_dict = None
    for single_issue in issues:
        single_issue_context = _get_context_from_issue(single_issue, skip_filename)
        output_dict = _add_single_error_to_dict(single_issue_context, output_dict, single_issue)

    return output_dict


def _add_single_error_to_dict(items, root=None, issue_to_add=None):
    """ Build a nested dictionary out of the context lists

    Parameters:
        items (list): A list of error contexts
        root (dict, optional): An existing nested dictionary structure to update.
        issue_to_add (dict, optional): The issue to add at this level of context

    Returns:
        dict: A nested dictionary structure with a "children" key at each level for unrelated children.
    """
    if root is None:
        root = {"children": []}

    current_dict = root
    for item in items:
        # Navigate to the next level if the item already exists, or create a new level
        next_dict = current_dict.get(item, {"children": []})
        current_dict[item] = next_dict
        current_dict = next_dict

    if issue_to_add:
        current_dict["children"].append(issue_to_add)

    return root


def _error_dict_to_string(print_dict, add_link=True, level=0):
    output = ""
    if print_dict is None:
        return output
    for context, value in print_dict.items():
        if context == "children":
            for child in value:
                single_issue_message = child["message"]
                issue_string = level * "\t" + _get_error_prefix(child)
                issue_string += f"{single_issue_message}\n"
                if add_link:
                    link_url = create_doc_link(child['code'])
                    if link_url:
                        single_issue_message += f"   See... {link_url}"
                output += issue_string
            continue
        output += _format_single_context_string(context[0], context[1], level)
        output += _error_dict_to_string(value, add_link, level + 1)

    return output


def _get_context_from_issue(val_issue, skip_filename=True):
    """ Extract all the context values from the given issue.

    Parameters:
        val_issue (dict): A dictionary a representing a single error.
        skip_filename (bool): If true, don't gather the filename context.

    Returns:
        list: A list of tuples containing the context_type and context for the given issue.

    """
    single_issue_context = []
    for key, value in val_issue.items():
        if skip_filename and key == ErrorContext.FILE_NAME:
            continue
        if key == ErrorContext.HED_STRING:
            value = value.get_original_hed_string()
        if key.startswith("ec_"):
            single_issue_context.append((key, str(value)))

    return single_issue_context


def _get_error_prefix(single_issue):
    """Returns the prefix for the error message based on severity and error code.

    Parameters:
        single_issue(dict): A single issue object

    Returns:
        error_prefix(str):  the prefix to use
    """
    severity = single_issue.get('severity', ErrorSeverity.ERROR)
    error_code = single_issue['code']

    if severity == ErrorSeverity.ERROR:
        error_prefix = f"{error_code}: "
    else:
        error_prefix = f"{error_code}: (Warning) "
    return error_prefix


def _format_single_context_string(context_type, context, tab_count=0):
    """ Return the human-readable form of a single context tuple.

    Parameters:
        context_type (str): The context type of this entry.
        context (str or HedString): The value of this context
        tab_count (int): Number of tabs to name_prefix each line with.

    Returns:
        str: A string containing the context, including tabs.

    """
    tab_string = tab_count * '\t'
    error_types = {
        ErrorContext.FILE_NAME: f"\nErrors in file '{context}'",
        ErrorContext.SIDECAR_COLUMN_NAME: f"Column '{context}':",
        ErrorContext.SIDECAR_KEY_NAME: f"Key: {context}",
        ErrorContext.ROW: f'Issues in row {context}:',
        ErrorContext.COLUMN: f'Issues in column {context}:',
        ErrorContext.CUSTOM_TITLE: context,
        ErrorContext.LINE: f"Line: {context}",
        ErrorContext.HED_STRING: f"hed string: {context}",
        ErrorContext.SCHEMA_SECTION: f"Schema Section: {context}",
        ErrorContext.SCHEMA_TAG: f"Source tag: {context}",
        ErrorContext.SCHEMA_ATTRIBUTE: f"Source Attribute: {context}",
    }
    context_portion = error_types[context_type]
    context_string = f"{tab_string}{context_portion}\n"
    return context_string


def _create_error_tree(error_dict, parent_element=None, add_link=True):
    if parent_element is None:
        parent_element = ET.Element("ul")

    for context, value in error_dict.items():
        if context == "children":
            for child in value:
                child_li = ET.SubElement(parent_element, "li")
                error_prefix = _get_error_prefix(child)
                single_issue_message = child["message"]

                # Create a link for the error prefix if add_link is True
                if add_link:
                    link_url = create_doc_link(child['code'])
                    if link_url:
                        a_element = ET.SubElement(child_li, "a", href=link_url)
                        a_element.text = error_prefix
                        a_element.tail = " " + single_issue_message
                    else:
                        child_li.text = error_prefix + " " + single_issue_message
                else:
                    child_li.text = error_prefix + " " + single_issue_message
            continue

        context_li = ET.SubElement(parent_element, "li")
        context_li.text = _format_single_context_string(context[0], context[1])
        context_ul = ET.SubElement(context_li, "ul")
        _create_error_tree(value, context_ul, add_link)

    return parent_element


def replace_tag_references(list_or_dict):
    """Utility function to remove any references to tags, strings, etc from any type of nested list or dict

       Use this if you want to save out issues to a file.

       If you'd prefer a copy returned, use replace_tag_references(list_or_dict.copy())

    Parameters:
       list_or_dict(list or dict): An arbitrarily nested list/dict structure
    """
    if isinstance(list_or_dict, dict):
        for key, value in list_or_dict.items():
            if isinstance(value, (dict, list)):
                replace_tag_references(value)
            elif isinstance(value, (bool, float, int)):
                list_or_dict[key] = value
            else:
                list_or_dict[key] = str(value)
    elif isinstance(list_or_dict, list):
        for key, value in enumerate(list_or_dict):
            if isinstance(value, (dict, list)):
                replace_tag_references(value)
            elif isinstance(value, (bool, float, int)):
                list_or_dict[key] = value
            else:
                list_or_dict[key] = str(value)
