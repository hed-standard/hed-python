"""
Examples of opening a HED dataset spreadsheet, processing it, then saving it back out as a spreadsheet.
This example is specifically converting tags between short and long form.

Classes Demonstrated:
HedFileInput - Used to open/modify/save a spreadsheet
HedSchema - Used to convert hed strings between short and long forms
"""
import os

from hed.util.hed_file_input import HedFileInput
from hed.schema.hed_schema_file import load_schema

local_hed_file_no_dupe = 'data/HED8.0.0-alpha.1.xml'


def long_to_short_file(input_file, hed_schema, error_handler=None):
    error_list = input_file.convert_to_short(hed_schema, error_handler)
    input_file.save(include_formatting=True, add_suffix="_test_long_to_short")
    return input_file, error_list


def short_to_long_file(input_file, hed_schema, error_handler=None):
    error_list = input_file.convert_to_long(hed_schema, error_handler)
    input_file.save(include_formatting=True, add_suffix="_test_short_to_long")
    return input_file, error_list


if __name__ == '__main__':
    example_data_path = 'data'
    hed3_tags_single_sheet = os.path.join(example_data_path, 'hed3_tags_single_sheet.xlsx')

    loaded_schema = load_schema(local_hed_file_no_dupe)
    prefixed_needed_tag_columns = {2: 'Attribute/Informational/Label/', 3: 'Attribute/Informational/Description/'}
    loaded_file = HedFileInput(hed3_tags_single_sheet, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')
    long_to_short_file(loaded_file, loaded_schema)

    loaded_file = HedFileInput(hed3_tags_single_sheet, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')
    short_to_long_file(loaded_file, loaded_schema)