"""
Utilities to support HED searches based on strings.
"""
from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag


def convert_query(search_query, schema):
    """Converts the given basic search query into a hed_string

    Parameters:
        search_query(str): The basic search query to convert.
        schema(HedSchema): The schema to use to convert tags

    Returns:
        long_query(str): The converted search query, in long form.
    """
    input_tags = HedString.split_hed_string(search_query)
    output_string = ""
    skippable_prefix = ("@", "~")
    skippable_suffix = ("*", )
    for is_hed_tag, (startpos, endpos) in input_tags:
        input_tag = search_query[startpos:endpos]
        add_suffix = ""
        if is_hed_tag:
            if input_tag.startswith(skippable_prefix):
                output_string += input_tag[:1]
                input_tag = input_tag[1:]

            if input_tag.endswith(skippable_suffix):
                add_suffix = input_tag[-1:]
                input_tag = input_tag[:-1]
            output_string += HedTag(input_tag, schema).long_tag
            output_string += add_suffix
        else:
            output_string += input_tag

    return output_string
