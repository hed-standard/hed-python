"""Infrastructure for processing lists of HED operations."""
from functools import partial
from hed.schema import HedSchema, HedSchemaGroup


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


def translate_ops(hed_ops, split_tag_and_string_ops=False, **kwargs):
    """
        Takes a list of hed_ops and/or functions and returns a list of functions to apply to a hed string object

    Parameters
    ----------
    hed_ops : [func or HedOps or HedSchema] or func or HedOps or HedSchema
            A list of HedOps of funcs to apply to the hed strings in the sidecars.
    split_tag_and_string_ops: bool
        If true, will split the operations into tag and string operations
            This is primarily for parsing spreadsheets where any given column isn't an entire hed string,
            but you might want additional detail on which column the issue original came from.
    kwargs : optional list of parameters, passed to each HedOps
        Currently accepted values: allow_placeholders
                                   check_for_definitions
                                   expand_defs
                                   shrink_defs
                                   error_handler
                                   check_for_warnings
                                   remove_definitions
    Returns
    -------
    tag_funcs, string_funcs: ([func], [func]) or [func]
        A list of functions to apply.  Tag vs string primarily applies to spreadsheets.
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
        tag_funcs.insert(0, partial(HedString.convert_to_canonical_forms, hed_schema=None))

    if split_tag_and_string_ops:
        return tag_funcs, string_funcs
    return tag_funcs + string_funcs


class HedOps:
    """
        Baseclass to support HedOps.  These are operations that apply to HedStrings in a sequence.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get_string_funcs__(self, **kwargs):
        """
            Returns the operations that should be done on the full string at once.

        Parameters
        ----------
        kwargs: See above.

        Returns
        -------
        string_funcs: []
            A list of functions that take a single hed string as a parameter, and return a list of issues.
        """
        return []

    def __get_tag_funcs__(self, **kwargs):
        """
            Returns the operations that should be done on the individual tags in the string.

        Parameters
        ----------
        kwargs: See above.

        Returns
        -------
        tag_funcs: []
            A list of functions that take a single hed string as a parameter, and return a list of issues.
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
