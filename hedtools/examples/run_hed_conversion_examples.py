"""
Examples of opening a HED dataset spreadsheet, processing it, then saving it back out as a spreadsheet.
This example is specifically converting tags between short and long form.

Classes Demonstrated:
HedInput - Used to open/modify/save a spreadsheet
HedSchema - Used to convert hed strings between short and long forms
"""
import os

from hed.models.hed_input import HedInput
from hed.schema.hed_schema_file import load_schema
from hed.models.hed_string import HedString

local_hed_file_no_dupe = 'data/HED8.0.0-alpha.1.xml'


def long_to_short_file(input_file, output_filename, hed_schema, source_for_formatting=None,
                       source_for_formatting_sheet=None, error_handler=None):
    error_list = input_file.convert_to_short(hed_schema, error_handler)
    input_file.to_excel(output_filename, source_for_formatting=source_for_formatting,
                        source_for_formatting_sheet=source_for_formatting_sheet)
    return input_file, error_list


def short_to_long_file(input_file, output_filename, hed_schema, source_for_formatting=None,
                       source_for_formatting_sheet=None, error_handler=None):
    error_list = input_file.convert_to_long(hed_schema, error_handler)
    input_file.to_excel(output_filename, source_for_formatting=source_for_formatting,
                        source_for_formatting_sheet=source_for_formatting_sheet)
    return input_file, error_list


def long_to_short_string(input_string, hed_schema):
    hed_string_obj = HedString(input_string)
    return hed_string_obj.convert_to_short(hed_schema)


def short_to_long_string(input_string, hed_schema):
    hed_string_obj = HedString(input_string)
    return hed_string_obj.convert_to_long(hed_schema)


if __name__ == '__main__':
    example_data_path = 'data'
    hed3_tags_single_sheet = os.path.join(example_data_path, 'hed3_tags_single_sheet.xlsx')

    loaded_schema = load_schema(local_hed_file_no_dupe)
    prefixed_needed_tag_columns = {2: 'Attribute/Informational/Label/', 3: 'Attribute/Informational/Description/'}
    loaded_file = HedInput(hed3_tags_single_sheet, tag_columns=[4],
                           column_prefix_dictionary=prefixed_needed_tag_columns,
                           worksheet_name='LKT Events')
    output_filename = hed3_tags_single_sheet + "_short_form.xlsx"
    long_to_short_file(loaded_file, output_filename, loaded_schema, source_for_formatting=hed3_tags_single_sheet,
                       source_for_formatting_sheet="LKT Events")

    output_filename = hed3_tags_single_sheet + "_long_form.xlsx"
    loaded_file = HedInput(hed3_tags_single_sheet, tag_columns=[4],
                           column_prefix_dictionary=prefixed_needed_tag_columns,
                           worksheet_name='LKT Events')
    short_to_long_file(loaded_file, output_filename, loaded_schema, source_for_formatting=hed3_tags_single_sheet,
                       source_for_formatting_sheet="LKT Events")

    inputs = 'Attribute/Sensory/Visual/Color/CSS-color/White-color/White'
    tag, error = long_to_short_string(inputs, loaded_schema)
    print(f"Tag= {tag}, errors=[{error}]")

    inputs = 'Attribute/Visual/Color/CSS-color/White-color/White'
    tag, error = long_to_short_string(inputs, loaded_schema)
    print(f"Tag= {tag}, errors=[{error}]")

    inputs = 'White'
    tag, error = short_to_long_string(inputs, loaded_schema)
    print(f"Tag= {tag}, errors=[{error}]")
