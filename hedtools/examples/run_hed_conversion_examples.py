"""
Examples of opening a HED dataset spreadsheet and resaving the entire thing with tags converted to short or long.
"""
import os

from hed.util.hed_file_input import HedFileInput
from hed.tools.tag_format import TagFormat

local_hed_file_no_dupe = 'data/HED8.0.0-alpha.1.xml'


def long_to_short_file(input_file):
    tag_formatter = TagFormat(local_hed_file_no_dupe)
    converted_file, errors = tag_formatter.convert_file_to_short_tags(input_file)
    converted_file.save(include_formatting=True, add_suffix="_test_long_to_short")


def short_to_long_file(input_file):
    tag_formatter = TagFormat(local_hed_file_no_dupe)
    converted_file, errors = tag_formatter.convert_file_to_long_tags(input_file)
    converted_file.save(include_formatting=True, add_suffix="_test_short_to_long")

if __name__ == '__main__':
    example_data_path = 'data'
    hed3_tags_single_sheet = os.path.join(example_data_path, 'hed3_tags_single_sheet.xlsx')

    prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    input_file = HedFileInput(hed3_tags_single_sheet, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')
    long_to_short_file(input_file)

    input_file = HedFileInput(hed3_tags_single_sheet, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')
    short_to_long_file(input_file)