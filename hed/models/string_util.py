from hed.models.hed_string import HedString


def gather_descriptions(hed_string):
    """Removes any description tags from the string and concatenates them

    Parameters:
        hed_string(HedString): To be modified

    Returns: tuple
        description(str): The concatenated values of all description tags.
 
    Side-effect:
         The input HedString has its Definition tags removed.

    """
    desc_tags = hed_string.find_tags("description", recursive=True, include_groups=0)
    desc_string = " ".join([tag.extension if tag.extension.endswith(".") else tag.extension + "." for tag in desc_tags])

    hed_string.remove(desc_tags)

    return desc_string


def split_base_tags(hed_string, base_tags, remove_group=False):
    """ Splits a HedString object into two separate HedString objects based on the presence of base tags.

    Args:
        hed_string (HedString): The input HedString object to be split.
        base_tags (list of str): A list of strings representing the base tags.
                                 This is matching the base tag NOT all the terms above it.
        remove_group (bool, optional): Flag indicating whether to remove the parent group. Defaults to False.

    Returns:
        tuple: A tuple containing two HedString objects:
            - The first HedString object contains the remaining tags from hed_string.
            - The second HedString object contains the tags from hed_string that match the base_tags.
    """

    base_tags = [tag.lower() for tag in base_tags]
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
    """ Splits a HedString object into two separate HedString objects based on the presence of wildcard tags.

        This does NOT handle def-expand tags currently.

    Args:
        hed_string (HedString): The input HedString object to be split.
        def_names (list of str): A list of def names to search for.  Can optionally include a value.
        remove_group (bool, optional): Flag indicating whether to remove the parent group. Defaults to False.

    Returns:
        tuple: A tuple containing two HedString objects:
            - The first HedString object contains the remaining tags from hed_string.
            - The second HedString object contains the tags from hed_string that match the def_names.
    """
    include_groups = 0
    if remove_group:
        include_groups = 2
    wildcard_tags = [f"def/{def_name}".lower() for def_name in def_names]
    found_things = hed_string.find_wildcard_tags(wildcard_tags, recursive=True, include_groups=include_groups)
    if remove_group:
        found_things = [tag if isinstance(group, HedString) else group for tag, group in found_things]

    if found_things:
        hed_string.remove(found_things)

    return hed_string, HedString("", hed_string._schema, _contents=found_things)
