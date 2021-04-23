"""Basic easy to use functions showing how to iterate over a given json file and convert all HED tags"""
import os
from hed.util.column_def_group import ColumnDefGroup

raise NotImplementedError("This file needs to be updated to the new hed string system.")


def map_json_file(json_filename, out_filename, mapping_function):
    """
        Run the specified mapping_function on all hed strings in a specified json sidecar

    Parameters
    ----------
    json_filename : str
        Path to input json file
    out_filename : str
        Path to save output file
    mapping_function : (str) -> (str, [])
        The function to map an input string to an output string.
    """
    json_file = ColumnDefGroup(json_filename)
    all_errors = {}
    for column_def in json_file:
        for hed_string, position in column_def.hed_string_iter(include_position=True):
            new_hed_string, errors = mapping_function(hed_string)
            if errors:
                all_errors[column_def.column_name] = errors
            column_def.set_hed_string(new_hed_string, position)

    json_file.save_as_json(out_filename)
    for error_column, errors in all_errors.items():
        print(f"Errors in column definition: {error_column}")
        print(f"Source HED string: {errors[0]['source_tag']}")
        for error in errors:
            print(error["message"])


def convert_json_hed_to_short(json_filename, hed_xml_file):
    formatter = TagFormat(hed_xml_file)
    mapping_function = formatter.convert_hed_string_to_short
    out_filename = os.path.splitext(json_filename)[0] + "_short.json"
    map_json_file(json_filename, out_filename, mapping_function)


def convert_json_hed_to_long(json_filename, hed_xml_file):
    formatter = TagFormat(hed_xml_file)
    mapping_function = formatter.convert_hed_string_to_long
    out_filename = os.path.splitext(json_filename)[0] + "_long.json"
    map_json_file(json_filename, out_filename, mapping_function)
