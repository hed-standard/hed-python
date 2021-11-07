import re


def split_hed_string(hed_string):
    """Takes a hed string and splits it into delimiters and tags

        Note: This does not validate tags in any form.

    Parameters
    ----------
        hed_string: string
            the hed string to split
    Returns
    -------
    list of tuples.
        each tuple: (is_hed_tag, (start_pos, end_pos))
        is_hed_tag: bool
            This is a (possible) hed tag if true, delimiter if not
        start_pos: int
            index of start of string in hed_string
        end_pos: int
            index of end of string in hed_string
    """
    tag_delimiters = ",()~"
    current_spacing = 0
    inside_d = True
    result_positions = []
    start_pos = None
    last_end_pos = 0
    for i, char in enumerate(hed_string):
        if char == " ":
            current_spacing += 1
            continue

        if char in tag_delimiters:
            if not inside_d:
                inside_d = True
                if start_pos is not None:
                    last_end_pos = i - current_spacing
                    # view_string = hed_string[start_pos: last_end_pos]
                    result_positions.append((True, (start_pos, last_end_pos)))
                    current_spacing = 0
                    start_pos = None
            continue

        # If we have a current delimiter, end it here.
        if inside_d and last_end_pos is not None:
            # view_string = hed_string[last_end_pos: i]
            if last_end_pos != i:
                result_positions.append((False, (last_end_pos, i)))
            last_end_pos = None

        current_spacing = 0
        inside_d = False
        if start_pos is None:
            start_pos = i

    if last_end_pos is not None and len(hed_string) != last_end_pos:
        # view_string = hed_string[last_end_pos: len(hed_string)]
        result_positions.append((False, (last_end_pos, len(hed_string))))
    if start_pos is not None:
        # view_string = hed_string[start_pos: len(hed_string)]
        result_positions.append((True, (start_pos, len(hed_string) - current_spacing)))
        if current_spacing:
            result_positions.append((False, (len(hed_string) - current_spacing, len(hed_string))))

    # debug_result_strings = [hed_string[startpos:endpos] for (is_hed_string, (startpos, endpos)) in result_positions]
    return result_positions


def split_hed_string_return_strings(hed_string):
    """An easier to use variant of split_hed_string if you don't need positions or delimiters."""
    result_positions = split_hed_string(hed_string)
    return [hed_string[startpos:endpos] for (is_hed_tag, (startpos, endpos)) in result_positions if is_hed_tag]


# Regular expression for cleaning up repeated slashes and spaces around slashes.
pattern_doubleslash = re.compile(r"[\s/]*/+[\s/]*")


def remove_slashes_and_spaces(hed_string):
    """This handles removing extra slashes, and spaces around slashes.

        Takes and returns a (hed) string.
        Examples:   '//' -> '/'
                    'Event//Extension' -> 'Event/Extension'
                    'Event  //Extension' -> 'Event/Extension'

    """
    simplified_string = pattern_doubleslash.sub('/', hed_string)
    # Temp - Remove newlines as well
    simplified_string = simplified_string.replace('\n', '')
    return simplified_string
