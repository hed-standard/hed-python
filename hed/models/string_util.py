""" Utilities for manipulating HedString objects. """
import re
from hed.models.hed_string import HedString


def gather_descriptions(hed_string):
    """Remove any description tags from the HedString and concatenates them.

    Parameters:
        hed_string(HedString): To be modified.

    Returns:
        str: The concatenated values of all description tags.

    Side effect:
         The input HedString has its description tags removed.

    """
    desc_tags = hed_string.find_tags({"description"}, recursive=True, include_groups=0)
    desc_string = " ".join([tag.extension if tag.extension.endswith(".") else tag.extension + "." for tag in desc_tags])

    hed_string.remove(desc_tags)

    return desc_string


def split_base_tags(hed_string, base_tags, remove_group=False):
    """ Split a HedString object into two separate HedString objects based on the presence of base tags.

    Parameters:
        hed_string (HedString): The input HedString object to be split.
        base_tags (list of str): A list of strings representing the base tags.
                                 This is matching the base tag NOT all the terms above it.
        remove_group (bool, optional): Flag indicating whether to remove the parent group. Defaults to False.

    Returns:
        tuple[HedString, HedString]:
            - HedString: The HedString with the base_tags removed.
            - HedString: The HedString containing only the base_tags.
    """

    base_tags = [tag.casefold() for tag in base_tags]
    include_groups = 0
    if remove_group:
        include_groups = 2
    found_things = hed_string.find_tags(base_tags, recursive=True, include_groups=include_groups)
    if remove_group:
        found_things = [tag if isinstance(group, HedString) else group for tag, group in found_things]

    if found_things:
        hed_string.remove(found_things)

    return hed_string, HedString("", hed_string._schema, _contents=found_things)


def split_def_tags(hed_string, def_names, remove_group=False):
    """ Split a HedString object into two separate HedString objects based on the presence of def tags

        This does NOT handle def-expand tags currently.

    Parameters:
        hed_string (HedString): The input HedString object to be split.
        def_names (list of str): A list of def names to search for.  Can optionally include a value.
        remove_group (bool, optional): Flag indicating whether to remove the parent group. Defaults to False.

    Returns:
        tuple[HedString, HedString]:
            - The HedString with the remaining tags from hed_string.
            - The HedString with the tags from hed_string that match the def_names.
    """
    include_groups = 0
    if remove_group:
        include_groups = 2
    wildcard_tags = [f"def/{def_name}".casefold() for def_name in def_names]
    found_things = hed_string.find_wildcard_tags(wildcard_tags, recursive=True, include_groups=include_groups)
    if remove_group:
        found_things = [tag if isinstance(group, HedString) else group for tag, group in found_things]

    if found_things:
        hed_string.remove(found_things)

    return hed_string, HedString("", hed_string._schema, _contents=found_things)


def cleanup_empties(string_in: str) -> str:
    leading_comma_regex = re.compile(r'^\s*,+')
    trailing_comma_regex = re.compile(r',\s*$')
    inner_comma_regex = re.compile(r',\s*,+')
    empty_parens_regex = re.compile(r'\(\s*\)')
    redundant_parens_regex = re.compile(r'\(\s*([,\s]*)\s*\)')
    trailing_inner_comma_regex = re.compile(r'[\s,]+\)')

    result = string_in
    previous_result = None

    while result != previous_result:
        previous_result = result

        # Step 1: Remove empty parentheses
        result = empty_parens_regex.sub('', result)

        # Step 2: Remove redundant parentheses containing only commas/spaces
        def replace_redundant_parens(match):
            group1 = match.group(1)
            if re.fullmatch(r'[,\s()]*', group1):
                return ''
            return f"({group1.strip().lstrip(',').rstrip(',')})"

        result = redundant_parens_regex.sub(replace_redundant_parens, result)

        # Step 3: Remove leading and trailing commas
        result = leading_comma_regex.sub('', result)
        result = trailing_comma_regex.sub('', result)

        # Step 4: Collapse multiple commas inside
        result = inner_comma_regex.sub(',', result)

        # Step 5: Remove trailing commas inside parentheses
        result = trailing_inner_comma_regex.sub(')', result)

    result = re.sub(r'\(\s*,+', '(', result)

    return result.strip()
