from functools import partial


def translate_ops(validators, split_tag_and_string_ops=False, **kwargs):
    """
        Takes a list of validators and/or functions and returns a list of functions to apply to a hed string object

    Parameters
    ----------
    validators : [func or validator like] or func or validator like
            A validator or list of validators to apply to the hed strings in the sidecars.
    split_tag_and_string_ops: bool
        If true, will split the operations into tag and string operations
            This is primarily for parsing spreadsheets where any given column isn't an entire hed string,
            but you might want additional detail on which column the issue original came from.
    kwargs : optional list of parameters, passed to each validator
        Currently accepted values: allow_placeholders
                                   check_for_definitions
                                   expand_defs
                                   error_handler
                                   check_for_warnings
    Returns
    -------
    tag_ops, string_ops: ([func], [func]) or [func]
        A list of functions to apply.  Tag vs string primarily applies to spreadsheets.
    """
    if not isinstance(validators, list):
        validators = [validators]

    tag_ops = []
    string_ops = []
    for validator in validators:
        if validator:
            try:
                tag_ops += validator.__get_tag_ops__(**kwargs)
                string_ops += validator.__get_string_ops__(**kwargs)
            except AttributeError:
                string_ops.append(validator)

    # Make sure the first column operation is a convert to forms, if we don't have one.
    from hed.models.hed_string import HedString
    found_convert_form = False
    for func in tag_ops:
        if func == HedString.convert_to_canonical_forms:
            found_convert_form = True
            break
        if isinstance(func, partial) and getattr(func, 'func') == HedString.convert_to_canonical_forms:
            found_convert_form = True
            break

    if not found_convert_form:
        tag_ops.insert(0, partial(HedString.convert_to_canonical_forms, hed_schema=None))

    if split_tag_and_string_ops:
        return tag_ops, string_ops
    return tag_ops + string_ops
