"""Basic example of the file input/column mapper API usage."""

from hed.util.column_def_group import ColumnDefGroup
from hed.util.hed_dictionary import HedDictionary
from hed.util.event_file_input import EventFileInput

local_hed_xml = "examples/data/HED7.1.1.xml"
hed_dictionary = HedDictionary(local_hed_xml)
json_filename = "examples/data/both_types_events_errors.json"
json_file = ColumnDefGroup(json_filename)
for column_def in json_file:
    for hed_string, position in column_def.hed_string_iter(include_position=True):
        new_hed_string = hed_string + "extra"
        column_def.set_hed_string(new_hed_string, position)
        print(hed_string)

# Save off a copy of the input json, modified.
json_file.save_as_json(json_filename + "-extra.json")

# Print all the errors from the json file
errors = json_file.validate_entries(hed_dictionary)
for error in errors.values():
    for sub_error in error:
        print(sub_error["message"])

# Alt syntax for accessing strings
for hed_string, position in json_file.hed_string_iter(include_position=True):
    new_hed_string = hed_string + "extra2"
    json_file.set_hed_string(new_hed_string, position)
    print(hed_string)

for hed_string in json_file.hed_string_iter():
    print(hed_string)

event_file = EventFileInput("examples/data/basic_events_test.tsv",
                            json_def_files="examples/data/both_types_events.json", attribute_columns=["onset"],
                            hed_dictionary=hed_dictionary)

for row in event_file:
    print(row)