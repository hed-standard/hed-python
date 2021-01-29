"""Examples of how to validate errors in a json sidecar file independently, and also an example of
        opening a json file and converting each HED tag from short to long."""

from hed.util.column_def_group import ColumnDefGroup
from hed.util.hed_schema import HedSchema
from hed.tools.tag_format import TagFormat

local_hed_xml = "data/HED8.0.0-alpha.1.xml"
hed_schema = HedSchema(local_hed_xml)
json_filename = "data/both_types_events_errors.json"

json_file = ColumnDefGroup(json_filename)
# Print all the errors from the json file
errors = json_file.validate_entries(hed_schema)
print(json_file.get_printable_issue_string(errors))

# Open the json file, convert all tags to long, and save it out
long_tag_formatter = TagFormat(local_hed_xml)
for column_def in json_file:
    for hed_string, position in column_def.hed_string_iter(include_position=True):
        new_hed_string, errors = long_tag_formatter.convert_hed_string_to_long(hed_string)
        column_def.set_hed_string(new_hed_string, position)
        print(f"'{hed_string}' \nconverts to\n '{new_hed_string}'")

# Save off a copy of the input json, modified.
json_file.save_as_json(json_filename + "-long.json")

# Alternate shorter syntax for accessing HED strings in a json file.
for hed_string, position in json_file.hed_string_iter(include_position=True):
    print(hed_string)
    new_hed_string = hed_string + "fake_string_modification"
    json_file.set_hed_string(new_hed_string, position)

# Leave off include_position if you don't need to save the hed strings back to where they came from.
# these now are modified from the above example
for hed_string in json_file.hed_string_iter():
    print(hed_string)
