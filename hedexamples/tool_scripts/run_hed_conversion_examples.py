"""
Examples of opening a HED dataset spreadsheet, processing it, then saving it back out as a spreadsheet.
This example is specifically converting tags between short and long form.

Classes Demonstrated:
HedInput - Used to open/modify/save a spreadsheet
HedSchema - Used to convert hed strings between short and long forms
"""
import os
from hed.models.hed_input import HedInput
from hed.models.hed_string import HedString
from hed.schema.hed_schema_file import load_schema

local_hed = '../data/schema_data/HED8.0.0.xml'


def long_to_short_file(input_file, output_filename, hed_schema, error_handler=None):
    error_list = input_file.convert_to_short(hed_schema, error_handler)
    input_file.to_excel(output_filename, )
    return input_file, error_list


def short_to_long_file(input_file, output_filename, hed_schema, error_handler=None):
    error_list = input_file.convert_to_long(hed_schema, error_handler)
    input_file.to_excel(output_filename)
    return input_file, error_list


def long_to_short_string(input_string, hed_schema):
    hed_string_obj = HedString(input_string)
    return hed_string_obj.convert_to_short(hed_schema)


def short_to_long_string(input_string, hed_schema):
    hed_string_obj = HedString(input_string)
    return hed_string_obj.convert_to_long(hed_schema)


if __name__ == '__main__':
    # Convert a spreadsheet to
    data_path = '../data/spreadsheet_data'
    base_name = 'ExcelOneSheet'
    single_sheet = os.path.join(data_path, base_name + '.xlsx')

    loaded_schema = load_schema(local_hed)
    prefixed_needed_tag_columns = {2: 'Property/Informational-property/Label/',
                                   3: 'Property/Informational-property/Description/'}
    loaded_file = HedInput(single_sheet, tag_columns=[4],
                           column_prefix_dictionary=prefixed_needed_tag_columns,
                           worksheet_name='LKT 8HED3')
    filename = os.path.join(data_path, base_name + '_short_form.xlsx')
    long_to_short_file(loaded_file, filename, loaded_schema)

    filename = os.path.join(data_path, base_name + '_long_form.xlsx')
    loaded_file = HedInput(single_sheet, tag_columns=[4],
                           column_prefix_dictionary=prefixed_needed_tag_columns,
                           worksheet_name='LKT 8HED3')
    short_to_long_file(loaded_file, filename, loaded_schema)

    inputs = 'Attribute/Sensory/Visual/Color/CSS-color/White-color/White'
    tag, error = long_to_short_string(inputs, loaded_schema)
    print(f"Converting to short: tag= {tag}, errors=[{error}]")

    inputs = 'Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/White'
    tag, error = long_to_short_string(inputs, loaded_schema)
    print(f"Converting to short: tag= {tag}, errors=[{error}]")

    inputs = 'White'
    tag, error = short_to_long_string(inputs, loaded_schema)
    print(f"Converting to long: tag= {tag}, errors=[{error}]")
