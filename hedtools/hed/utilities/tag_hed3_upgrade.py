import os
from hed.validator.hed_file_input import HedFileInput
from hed.utilities.format_util import split_hed_string, remove_slashes_and_spaces


def read_in_hed3_upgrade_file(upgrade_filename):
    mapping_dict = {}
    with open(upgrade_filename, 'r', encoding='utf-8') as f:
        for line in f:
            if len(line) > 5:
                while line.endswith('\n'):
                    line = line[:-1]
                split_segments = line.split('|')
                if len(split_segments) == 1:
                    print(f"No split operator '|' found in line: {line}")
                    continue
                if len(split_segments) > 2:
                    print(f"Too many split operators '|' found in line: {line}")
                    continue
                key, value = split_segments
                if len(value.strip()) < 3:
                    print(f"No hed3 version of tag found in line: {line}")
                    continue
                clean_key = key.lower()
                clean_key = clean_key.strip()
                value = value.strip()
                mapping_dict[clean_key] = value

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

    print(hed_tag)
    while found_slash_index != -1:
        temp_tag = tag_lower[:found_slash_index]
        print(temp_tag)
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
    if not new_tag:
        new_tag = f"{org_tag} [Missing]"
    elif remainder:
        if "XXX" in new_tag:
            # Handle "special case" where XXX tag ends with a ].  This should be all instances involving XXX.
            if new_tag.endswith(']'):
                found_starting_bracket = new_tag.rfind('[')
                if found_starting_bracket != -1:
                    new_tag = f"{new_tag[:-1]}" \
                              f"- Original tag is {{{org_tag}}}" \
                              f"]"
            else:
                # This is mostly a fallback in case we don't have proper bracketing.
                new_tag = f"{new_tag} [" \
                             f"- Original tag is {{{org_tag}}}" \
                             f"]"
        else:
            if "#" in new_tag:
                # Remove leading slash from remainder
                remainder = remainder[1:]
                new_tag = new_tag.replace("#", remainder)
            else:
                new_tag = new_tag + remainder

    # Replace brackets with the comment notation.
    tag_bracket_start = '[--- '
    tag_bracket_end = ' ---]'
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

def upgrade_file_to_hed3(input_file, mapping_dict, tag_columns_to_upgrade=None):
    """

    Parameters
    ----------
    input_file : A HedFileInput object
    mapping_dict : a dictionary of hed2->hed3 upgrades.  Created by read_in_hed3_upgrade_file above
    tag_columns_to_upgrade : list of column numbers
        If passed in and non empty, ONLY upgrade these column numbers.  You can also filter out
        which columns you want to upgrade via the HedFileInput object.

    Returns
    -------

    """
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
                    new_tag, remainder = find_tag(tag, mapping_dict)
                    new_tag = create_out_tag(tag, new_tag, remainder)
                    new_text += new_tag
                else:
                    new_text += tag
            input_file.set_cell(row_number, column_number, new_text,
                                include_column_prefix_if_exist=False)

    input_file.save(f"{input_file.filename}_test_hed3_upgrade")


if __name__ == '__main__':
    mapping_dict = read_in_hed3_upgrade_file("tests/data/hed2_hed3_conversion.txt")

    example_data_path = 'tests/data'   # path to example data
    multiple_sheet_xlsx_file = os.path.join(example_data_path, 'ExcelMultipleSheets.xlsx')

    # Comment in prefixed_needed_tag_columns if you want to update those columns as well.
    #prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4],
                              #column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='DAS Events')
    upgrade_file_to_hed3(input_file, mapping_dict, tag_columns_to_upgrade=None)
