""" Infrastructure for processing HED operations. """

from functools import partial
from hed.schema import HedSchema, HedSchemaGroup
from hed.errors.error_types import ErrorContext, SidecarErrors
from hed.errors import ErrorHandler


# These are the defaults if you pass in nothing.  Most built in routes will have other default values.
default_arguments = {
    'allow_placeholders': False,
    'check_for_definitions': False,
    'expand_defs': False,
    'shrink_defs': False,
    'error_handler': None,
    'check_for_warnings': False,
    'remove_definitions': True
}


def translate_ops(hed_ops, split_ops=False, hed_schema=None, **kwargs):
    """ Return functions to apply to a hed string object.

    Parameters:
        hed_ops (list): A list of func or HedOps or HedSchema to apply to hed strings.
        split_ops (bool): If true, will split the operations into separate lists of tag and string operations.
        hed_schema(HedSchema or None): The schema to use by default in identifying tags
        kwargs (kwargs):  An optional dictionary of name-value pairs representing parameters passed to each HedOps

    Returns:
        list or tuple: A list of functions to apply or a tuple containing separate lists of tag and string ops.

    Notes:
        - The distinction between tag and string ops primarily applies to spreadsheets.
        - Splitting the ops into two lists is mainly used for parsing spreadsheets where any given
            column isn't an entire hed string, but additional detail is needed on which column an
            issue original came from.
        - The currently accepted values of kwargs are:
            - allow_placeholders
            - check_for_definitions
            - expand_defs
            - shrink_defs
            - error_handler
            - check_for_warnings
            - remove_definitions

    """
    if not isinstance(hed_ops, list):
        hed_ops = [hed_ops]

    from hed.models.hed_string import HedString

    settings = default_arguments.copy()
    settings.update(kwargs)

    tag_funcs = []
    string_funcs = []
    for hed_op in hed_ops:
        if hed_op:
            # Handle the special case of a hed schema.
            if isinstance(hed_op, (HedSchema, HedSchemaGroup)):
                tag_funcs.append(partial(HedString.convert_to_canonical_forms, hed_schema=hed_op))
            else:
                try:
                    tag_funcs += hed_op.__get_tag_funcs__(**settings)
                    string_funcs += hed_op.__get_string_funcs__(**settings)
                except AttributeError:
                    string_funcs.append(hed_op)

    # Make sure the first column operation is a convert to forms, if we don't have one.
    if not _func_in_list(HedString.convert_to_canonical_forms, tag_funcs):
        tag_funcs.insert(0, partial(HedString.convert_to_canonical_forms, hed_schema=hed_schema))

    if split_ops:
        return tag_funcs, string_funcs
    return tag_funcs + string_funcs


def apply_ops(hed_strings, hed_ops, **kwargs):
    """ Convenience function to update a list/dict of hed strings

    Parameters:
        hed_strings(str, dict, list): A list/dict/str to update
        hed_ops (list or HedOps or func): A list of func or HedOps or HedSchema to apply to hed strings.
        kwargs (kwargs):  An optional dictionary of name-value pairs representing parameters passed to each HedOps

    Returns:
        tuple:
            hed_strings(str, dict, list): Same type as input
            issues(list): A list of issues found applying the hed_ops
    """
    from hed.models.hed_string import HedString

    if not hed_strings:
        return hed_strings, []
    issues = []
    tag_funcs = translate_ops(hed_ops, **kwargs)
    if isinstance(hed_strings, str):
        hed_string_obj = HedString(hed_strings)
        issues += hed_string_obj.apply_funcs(tag_funcs)
        return str(hed_string_obj), issues
    elif isinstance(hed_strings, dict):
        return_dict = {}
        for key, hed_string in hed_strings.items():
            hed_string_obj = HedString(hed_string)
            issues += hed_string_obj.apply_funcs(tag_funcs)
            return_dict[key] = str(hed_string_obj)
        return return_dict, issues
    elif isinstance(hed_strings, list):
        return_list = []
        for hed_string in hed_strings:
            hed_string_obj = HedString(hed_string)
            issues += hed_string_obj.apply_funcs(tag_funcs)
            return_list.append(str(hed_string_obj))
        return return_list, issues

    raise ValueError("Unaccounted for type in apply_ops")


def hed_string_iter(hed_strings, tag_funcs, error_handler):
    """ Iterate over the given dict of strings, returning HedStrings

        Also gives issues for blank strings

    Parameters:
        hed_strings(dict or str): A hed_string or dict of hed strings
        tag_funcs (list of funcs): The functions to apply before returning
        error_handler (ErrorHandler): The error handler to use for context, uses a default one if none.

    Yields:
        tuple:
            - HedString: The hed string at a given column and key position.
            - str: Indication of the where hed string was loaded from so it can be later set by the user.
            - list: Issues found applying hed_ops. Each issue is a dictionary.

    """
    for hed_string_obj, key_name in _hed_iter_low(hed_strings):
        new_col_issues = []
        error_handler.push_error_context(ErrorContext.SIDECAR_KEY_NAME, key_name)
        if not hed_string_obj:
            new_col_issues += ErrorHandler.format_error(SidecarErrors.BLANK_HED_STRING)
            error_handler.add_context_to_issues(new_col_issues)
            yield hed_string_obj, key_name, new_col_issues
        else:
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj,
                                             increment_depth_after=False)
            if tag_funcs:
                new_col_issues += hed_string_obj.apply_funcs(tag_funcs)

            error_handler.add_context_to_issues(new_col_issues)
            yield hed_string_obj, key_name, new_col_issues
            error_handler.pop_error_context()
        error_handler.pop_error_context()


def _hed_iter_low(hed_strings):
    """ Iterate over the hed string entries.

        Used by hed_string_iter

    Parameters:
        hed_strings(dict or str): A hed_string or dict of hed strings

    Yields:
        tuple:
            - HedString: Individual hed strings for different entries.
            - str: The position to pass back to set this string.

    """
    from hed.models.hed_string import HedString

    if isinstance(hed_strings, dict):
        for key, hed_string in hed_strings.items():
            if isinstance(hed_string, str):
                hed_string = HedString(hed_string)
            else:
                continue
            yield hed_string, key
    elif isinstance(hed_strings, str):
        hed_string = HedString(hed_strings)
        yield hed_string, None


def set_hed_string(new_hed_string, hed_strings, position=None):
    """ Set a hed string for a category key/etc.

    Parameters:
        new_hed_string (str or HedString): The new hed_string to replace the value at position.
        hed_strings(dict or str or HedString): The hed strings we want to update
        position (str, optional): This should only be a value returned from hed_string_iter.

    Returns:
        updated_string (str or dict): The newly updated string/dict.
    Raises:
        TypeError: If the mapping cannot occur.

    """
    from hed.models.hed_string import HedString

    if isinstance(hed_strings, dict):
        if position is None:
            raise TypeError("Error: Trying to set a category HED string with no category")
        if position not in hed_strings:
            raise TypeError("Error: Not allowed to add new categories to a column")
        hed_strings[position] = str(new_hed_string)
    elif isinstance(hed_strings, (str, HedString)):
        if position is not None:
            raise TypeError("Error: Trying to set a value HED string with a category")
        hed_strings = str(new_hed_string)
    else:
        raise TypeError("Error: Trying to set a HED string on a column_type that doesn't support it.")

    return hed_strings


class HedOps:
    """ Base class to support HedOps.

    Notes:
        - HED ops are operations that apply to HedStrings in a sequence.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get_string_funcs__(self, **kwargs):
        """ Return the operations that should be done on the full string at once.

        Parameters:
            kwargs See above.

        Returns:
            list: A list of functions that take a single hed string as a parameter, and return a list of issues.

        """
        return []

    def __get_tag_funcs__(self, **kwargs):
        """ Return the operations that should be done on the individual tags in the string.

        Parameters:
            kwargs: See above.

        Returns:
            list: A list of functions that take a single hed string as a parameter, and return a list of issues.

        """
        return []

    # Todo: possibly add parameter validation
    # def __get_valid_parameters__(self):
    #     return []


def _func_in_list(find_func, func_list):
    for func in func_list:
        if func == find_func:
            return True
        if isinstance(func, partial) and getattr(func, 'func') == find_func:
            return True
    return False
