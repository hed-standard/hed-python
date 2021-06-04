
def split_hed_string(hed_string):
    """
    Takes a hed string and splits it into delimiters and tags

    Note: This does not validate tags or delimiters in any form.

    Parameters
    ----------
        hed_string: string
            the hed string to split
    Returns
    -------
    [tuple]
        each tuple: (is_hed_tag, (start_pos, end_pos))
        is_hed_tag: bool
            This is a (possible) hed tag if true, delimiter if not
        start_pos: int
            index of start of string in hed_string
        end_pos: int
            index of end of string in hed_string
    """
    tag_delimiters = ",()"
    current_spacing = 0
    found_symbol = True
    result_positions = []
    tag_start_pos = None
    last_end_pos = 0
    for i, char in enumerate(hed_string):
        if char == " ":
            current_spacing += 1
            continue

        if char in tag_delimiters:
            if found_symbol:
                # view_string = hed_string[last_end_pos: i]
                if last_end_pos != i:
                    result_positions.append((False, (last_end_pos, i)))
                last_end_pos = i
            elif not found_symbol:
                found_symbol = True
                last_end_pos = i - current_spacing
                # view_string = hed_string[tag_start_pos: last_end_pos]
                result_positions.append((True, (tag_start_pos, last_end_pos)))
                current_spacing = 0
                tag_start_pos = None
            continue

        # If we have a current delimiter, end it here.
        if found_symbol and last_end_pos is not None:
            # view_string = hed_string[last_end_pos: i]
            if last_end_pos != i:
                result_positions.append((False, (last_end_pos, i)))
            last_end_pos = None

        found_symbol = False
        current_spacing = 0
        if tag_start_pos is None:
            tag_start_pos = i

    if last_end_pos is not None and len(hed_string) != last_end_pos:
        # view_string = hed_string[last_end_pos: len(hed_string)]
        result_positions.append((False, (last_end_pos, len(hed_string))))
    if tag_start_pos is not None:
        # view_string = hed_string[tag_start_pos: len(hed_string)]
        result_positions.append((True, (tag_start_pos, len(hed_string) - current_spacing)))
        if current_spacing:
            result_positions.append((False, (len(hed_string) - current_spacing, len(hed_string))))

    return result_positions


def split_hed_string_return_tags(hed_string):
    """
    An easier to use variant of split_hed_string if you're only interested in tags

    Parameters
    ----------
    hed_string : str
        A hed string to split into tags
    Returns
    -------
    hed_tags: [HedTag]
        The string split apart into hed tags with all delimiters removed
    """
    from hed.models.hed_tag import HedTag
    result_positions = split_hed_string(hed_string)
    return [HedTag(hed_string, span) for (is_hed_tag, span) in
            result_positions if is_hed_tag]
