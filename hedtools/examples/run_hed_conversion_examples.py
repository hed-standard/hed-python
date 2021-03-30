"""
Examples of opening a HED dataset spreadsheet, processing it, then saving it back out as a spreadsheet.
This example is specifically converting tags between short and long form.

Classes Demonstrated:
HedFileInput - Used to open/modify/save a spreadsheet
TagFormat - Used to convert between short and long tags
"""
import os

from hed.util.hed_file_input import HedFileInput
from hed.tools.tag_format import TagFormat

local_hed_file_no_dupe = 'data/HED8.0.0-alpha.1.xml'


def long_to_short_file(input_file):
    tag_formatter = TagFormat(local_hed_file_no_dupe)
    converted_file, errors = tag_formatter.convert_file_to_short_tags(input_file)
    converted_file.save(include_formatting=True, add_suffix="_test_long_to_short")


def long_to_short_string(input_string):
    tag_formatter = TagFormat(local_hed_file_no_dupe)
    converted_string, errors = tag_formatter.convert_hed_string_to_short(input_string)
    return converted_string, errors


def short_to_long_file(input_file):
    tag_formatter = TagFormat(local_hed_file_no_dupe)
    converted_file, errors = tag_formatter.convert_file_to_long_tags(input_file)
    converted_file.save(include_formatting=True, add_suffix="_test_short_to_long")


def short_to_long_string(input_string):
    tag_formatter = TagFormat(local_hed_file_no_dupe)
    converted_string, errors = tag_formatter.convert_hed_string_to_long(input_string)
    return converted_string, errors


if __name__ == '__main__':
    example_data_path = 'data'
    hed3_tags_single_sheet = os.path.join(example_data_path, 'hed3_tags_single_sheet.xlsx')

    prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    inputs = HedFileInput(hed3_tags_single_sheet, tag_columns=[4],
                          column_prefix_dictionary=prefixed_needed_tag_columns,
                          worksheet_name='LKT Events')
    long_to_short_file(inputs)

    inputs = HedFileInput(hed3_tags_single_sheet, tag_columns=[4],
                          column_prefix_dictionary=prefixed_needed_tag_columns,
                          worksheet_name='LKT Events')
    short_to_long_file(inputs)

    inputs = 'Attribute/Sensory/Visual/Color/CSS-color/White-color/White'
    tag, error = long_to_short_string(inputs)
    print(f"Tag= {tag}, errors=[{error}]")

    inputs =  'Attribute/Visual/Color/CSS-color/White-color/White'
    tag, error = long_to_short_string(inputs)
    print(f"Tag= {tag}, errors=[{error}]")

    inputs =  'White'
    tag, error = short_to_long_string(inputs)
    print(f"Tag= {tag}, errors=[{error}]")
