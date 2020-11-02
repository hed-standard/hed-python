import os
import re
from hed.util.hed_file_input import HedFileInput
from hed.util.hed_string_util import split_hed_string, remove_slashes_and_spaces
from hed.util.schema_node_map import SchemaNodeMap


def validate_single_tag(map_schema, tag):
    # Split off the variable suffix
    if tag.endswith("/XXX"):
        tag = tag[:-len("/XXX")]
    elif tag.endswith("/#"):
        tag = tag[:-len("/#")]
    elif tag.endswith("/YYY"):
        tag = tag[:-len("/YYY")]

    # Sometimes these are entirely on their own.  eg: (hed/tag/string/XXX, YYY)
    if tag == "YYY" or tag == "XXX":
        return True

    if tag not in map_schema.tag_dict:
        return False
    return True


# This assumes there are no square brackets anywhere else in the string except as a comment.
pattern_split_comment = re.compile(r"(.*?)(\[.*?\])")


def split_off_comment(hed_string_with_comment):
    """Splits off the comment in the [] at the end of a string in an upgrade file.
          If no comment is present, returns (original string, "")
    """
    match = pattern_split_comment.match(hed_string_with_comment)
    if not match:
        return hed_string_with_comment, ""

    return match.group(1), match.group(2)


def read_version_map(version_map_filename, left_hed_schema=None, right_hed_schema=None,
                     return_errors=False):
    left_map = right_map = None
    if left_hed_schema:
        left_map = SchemaNodeMap(left_hed_schema, use_full_name_as_key=True)
    if right_hed_schema:
        right_map = SchemaNodeMap(right_hed_schema, use_full_name_as_key=True)
    mapping_dict = {}
    error_list = []

    def add_error(new_error_text, line_number):
        error_list.append(f"Line {line_number:04d}: {new_error_text}")

    with open(version_map_filename, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if len(line) > 5:
                while line.endswith('\n'):
                    line = line[:-1]
                split_segments = line.split('|')
                if len(split_segments) <= 1:
                    add_error(f"Warning: No split operator '|' found in line: {line}", i)
                    continue
                if len(split_segments) > 2:
                    add_error(f"Warning: Too many split operators '|' found in line: {line}", i)
                    continue
                left_tag, right_string = split_segments
                if len(right_string.strip()) < 3:
                    add_error(f"Warning: No right tag version of tag found in line: {line}", i)
                    continue

                # Check for comment if needed
                left_tag = left_tag.lower()
                left_tag = left_tag.strip()
                right_string = right_string.strip()
                right_lower = right_string.lower()
                right_string_no_comment, comment = split_off_comment(right_lower)
                if ("XXX" in right_string_no_comment or "YYY" in right_string_no_comment) and not comment:
                    add_error(f"Warning: XXX or YYY found in a line with no comment: {line}", i)

                # Validate tags if we have a schema
                if left_map is not None:
                    if not validate_single_tag(left_map, left_tag):
                        add_error(f"Warning: Left tag not found in Schema.  {left_tag}", i)
                if right_map is not None:
                    hed_tags = split_hed_string(right_string_no_comment)
                    for is_hed_tag, (startpos, endpos) in hed_tags:
                        if is_hed_tag:
                            hed_tag = right_string_no_comment[startpos:endpos]
                            if not validate_single_tag(right_map, hed_tag):
                                add_error(f"Warning: Right tag not found in Schema.  {hed_tag}  Full line: {right_string}", i)

                mapping_dict[left_tag] = right_string_no_comment, comment

    if return_errors:
        return mapping_dict, error_list
    else:
        for error in error_list:
            print(error)
        return mapping_dict


def find_tag(hed_tag, mapping_dict):
    # Remove leading and trailing slashes
    if hed_tag.startswith('/'):
        hed_tag = hed_tag[1:]
    if hed_tag.endswith('/'):
        hed_tag = hed_tag[:-1]

    tag_lower = hed_tag.lower()
    if tag_lower in mapping_dict:
        remainder = ""
        return mapping_dict[tag_lower], remainder

    found_slash_index = tag_lower.rfind('/')

    while found_slash_index != -1:
        temp_tag = tag_lower[:found_slash_index]
        pound_sign_tag = f"{temp_tag}/#"
        # first see if the variant with /# on the end exists.  If so, use that tag.
        if pound_sign_tag in mapping_dict:
            remainder = hed_tag[found_slash_index:]
            return mapping_dict[pound_sign_tag], remainder

        if temp_tag in mapping_dict:
            remainder = hed_tag[found_slash_index:]
            return mapping_dict[temp_tag], remainder
        found_slash_index = tag_lower.rfind('/', 0, found_slash_index - 1)

    # not in dict at all
    return None, None


def create_out_tag(org_tag, new_tag, remainder):
    """

    Parameters
    ----------
    tag : Full original tag
    new_tag : Full new tag
    remainder : Remainder of old tag.  This is used as the output of # if present.

    Returns
    -------

    """
    original_tag_is_string = ". Original string is "
    if not new_tag:
        new_tag = f"{org_tag} [Missing]"
    elif remainder:
        # It's mostly an error if YYY appears without XXX, so we don't really need to check for it.
        if "XXX" in new_tag or "YYY" in new_tag:
            # Handle default case where XXX tag ends with a ].  This should be all instances involving XXX.
            # Fix this duplicate code
            if new_tag.endswith(']'):
                found_starting_bracket = new_tag.rfind('[')
                if found_starting_bracket != -1:
                    new_tag = f"{new_tag[:-1]}" \
                              f"{original_tag_is_string}{{{org_tag}}}" \
                              f"]"
            else:
                # This is mostly a fallback in case we don't have proper bracketing.
                new_tag = f"{new_tag} [" \
                          f"{original_tag_is_string}{{{org_tag}}}" \
                          f"]"
        else:
            # Direct mapping 1-1 to a # tag.
            if "#" in new_tag:
                # Remove leading slash from remainder
                remainder = remainder[1:]
                new_tag = new_tag.replace("#", remainder)
            else:
                # Handle "normal" extension
                # Fix this duplicate code
                if new_tag.endswith(']'):
                    found_starting_bracket = new_tag.rfind('[')
                    if found_starting_bracket != -1:
                        new_tag = f"{new_tag[:-1]}" \
                                  f"{original_tag_is_string}{{{org_tag}}}" \
                                  f"]"
                else:
                    new_tag = new_tag + remainder

    # Replace brackets with the comment notation.
    tag_bracket_start = '[--- '
    tag_bracket_end = ' ---]'
    # Fix this duplicate code
    if new_tag.endswith(']'):
        found_starting_bracket = new_tag.rfind('[')
        if found_starting_bracket != -1:
            before_bracket = new_tag[:found_starting_bracket]
            after_bracket = new_tag[found_starting_bracket + 1:-1]
            new_tag = f"{before_bracket}" \
                      f"{tag_bracket_start}" \
                      f"{after_bracket}" \
                      f"{tag_bracket_end}"
    return new_tag


def upgrade_file_hed_version(input_file, mapping_filename_or_dict, tag_columns_to_upgrade=None):
    """

    Parameters
    ----------
    input_file : A HedFileInput object
    mapping_filename_or_dict : a dictionary of hed2->hed3 upgrades.  Created by read_version_map above
        It can also be a string pointing to a file that read_version_map can parse.
    tag_columns_to_upgrade : list of column numbers
        If passed in and non empty, ONLY upgrade these column numbers.  You can also filter out
        which columns you want to upgrade via the HedFileInput object.

    Returns
    -------

    """
    mapping_dict = mapping_filename_or_dict
    if isinstance(mapping_filename_or_dict, str):
        mapping_dict = read_version_map(mapping_filename_or_dict)

    for row_number, row_hed_string, column_to_hed_tags_dictionary in input_file:
        for column_number in column_to_hed_tags_dictionary:
            if tag_columns_to_upgrade and column_number not in tag_columns_to_upgrade:
                continue

            old_text = column_to_hed_tags_dictionary[column_number]
            old_cleaned_text = remove_slashes_and_spaces(old_text)
            hed_tags = split_hed_string(old_cleaned_text)
            new_text = ""
            for is_hed_tag, (startpos, endpos) in hed_tags:
                tag = old_cleaned_text[startpos:endpos]
                if is_hed_tag:
                    (new_tag, comment), remainder = find_tag(tag, mapping_dict)
                    if comment:
                        new_tag = new_tag + comment
                    new_tag = create_out_tag(tag, new_tag, remainder)
                    new_text += new_tag
                else:
                    new_text += tag
            input_file.set_cell(row_number, column_number, new_text,
                                include_column_prefix_if_exist=False)

    input_file.save(f"{input_file.filename}_test_hed3_upgrade")


if __name__ == '__main__':
    hed2_xml_file = "tests/data/HED7.1.1.xml"
    hed3_xml_file = "tests/data/reduced_hed3.xml"
    mapping_dict, errors = read_version_map("tests/data/hed2_hed3_conversion.txt",
                                            left_hed_schema=hed2_xml_file, right_hed_schema=hed3_xml_file,
                                            return_errors=True)
    example_data_path = 'tests/data'   # path to example data
    multiple_sheet_xlsx_file = os.path.join(example_data_path, 'ExcelMultipleSheets.xlsx')

    # Comment in prefixed_needed_tag_columns if you want to update those columns as well.
    #prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4],
                              #column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='DAS Events')

    upgrade_file_hed_version(input_file, mapping_dict, tag_columns_to_upgrade=None)
