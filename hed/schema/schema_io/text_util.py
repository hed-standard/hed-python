"""Functions for parsing text from dataframes/text formats"""

import re

# Might need separate version again for wiki
header_attr_expression = "([^ ,]+?)=\"(.*?)\""
attr_re = re.compile(header_attr_expression)


def _parse_header_attributes_line(version_line):
    matches = {}
    unmatched = []
    last_end = 0

    for match in attr_re.finditer(version_line):
        start, end = match.span()

        # If there's unmatched content between the last match and the current one.
        if start > last_end:
            unmatched.append(version_line[last_end:start])

        matches[match.group(1)] = match.group(2)
        last_end = end

    # If there's unmatched content after the last match
    if last_end < len(version_line):
        unmatched.append(version_line[last_end:])

    unmatched = [m.strip() for m in unmatched if m.strip()]
    return matches, unmatched


def _validate_attribute_string(attribute_string):
    """Raises ValueError on bad input"""
    pattern = r'^[A-Za-z]+(=.+)?$'
    match = re.fullmatch(pattern, attribute_string)
    if match:
        return match.group()
    raise ValueError(f'Malformed attribute {attribute_string}.  Valid formatting is: attribute, or attribute="value"')


def parse_attribute_string(attr_string):
    """ Parse attributes for a single element into a dict.

    Parameters:
        attr_string(str): Formatted attributes (a=b, c=d, etc.)

    Returns:
        attributes(dict): The located attributes.  Can be empty.

    Raises:
        ValueError: Very malformed input.
    """
    if attr_string:
        attributes_split = [x.strip() for x in attr_string.split(',')]

        final_attributes = {}
        for attribute in attributes_split:
            # Raises error on very invalid
            _validate_attribute_string(attribute)
            split_attribute = attribute.split("=")
            if len(split_attribute) == 1:
                final_attributes[split_attribute[0]] = True
            else:
                if split_attribute[0] in final_attributes:
                    final_attributes[split_attribute[0]] += "," + split_attribute[1]
                else:
                    final_attributes[split_attribute[0]] = split_attribute[1]
        return final_attributes
    elif attr_string == "":
        return {}
