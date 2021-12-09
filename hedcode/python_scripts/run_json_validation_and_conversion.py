"""
TODO: Update to current schema examples

Example 1: creating a Sidecar from a json sidecar file and validating it

Example 2: how to open a json sidecar, modify it, then save it back out.

Example 3: Iterate over hed strings in a json sidecar.

Classes Demonstrated:
HedSchema - Opens a hed xml schema.  Used by other tools to check tag attributes in the schema.
Sidecar - Contains the data from a single json sidecar, can be validated using a HedSchema.
HedString - Main class for handling a hed string during processing and analysis
"""

from hed.errors.error_reporter import get_printable_issue_string
from hed.models.hed_string import HedString
from hed.models.sidecar import Sidecar
from hed.schema.hed_schema_file import load_schema
from hed.validator.hed_validator import HedValidator

if __name__ == '__main__':
    local_hed_xml = "../data/schema_data/HED8.0.1.xml"
    hed_schema = load_schema(local_hed_xml)
    json_filename = "../data/bids_data/both_types_events_errors.json"

    # Example 1
    sidecar = Sidecar(json_filename)
    validator = HedValidator(hed_schema)
    # Print all the errors from the json file
    errors = sidecar.validate_entries(validator)
    print(get_printable_issue_string(errors))

    # Example 2
    # Open the json file, convert all tags to long, and save it out
    for column_data in sidecar:
        for hed_string, position in column_data.hed_string_iter(include_position=True):
            hed_string_obj = HedString(hed_string)
            errors = hed_string_obj.convert_to_long(hed_schema)
            column_data.set_hed_string(hed_string_obj, position)
            print(f"'{hed_string_obj.get_original_hed_string()}' \nconverts to\n '{str(hed_string_obj)}'")

    # Save off a copy of the input json, modified.
    sidecar.save_as_json(json_filename + "-long.json")

    # Example 3
    # Alternate shorter syntax for accessing HED strings in a json file.
    for hed_string, position in sidecar.hed_string_iter(include_position=True):
        print(hed_string)
        new_hed_string = hed_string + "fake_string_modification"
        sidecar.set_hed_string(new_hed_string, position)

    # Leave off include_position if you don't need to save the hed strings back to where they came from.
    # these now are modified from the above example
    for hed_string in sidecar.hed_string_iter():
        print(hed_string)
