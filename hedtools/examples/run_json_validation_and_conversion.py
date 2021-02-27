"""
Example 1: creating a ColumnDefGroup from a json sidecar file and validating it

Example 2: how to open a json sidecar, modify it, then save it back out.

Example 3: Iterate over hed strings in a json sidecar.

Classes Demonstrated:
HedSchema - Opens a hed xml schema.  Used by other tools to check tag attributes in the schema.
TagFormat - Used to convert between short and long tags
ColumnDefGroup - Contains the data from a single json sidecar, can be validated using a HedSchema.
"""
import hed
from hed.util.column_def_group import ColumnDefGroup
from hed import schema
from hed.tools.tag_format import TagFormat

local_hed_xml = "data/HED8.0.0-alpha.1.xml"
hed_schema = schema.load_schema(local_hed_xml)
json_filename = "data/both_types_events_errors.json"

# Example 1
json_file = ColumnDefGroup(json_filename)
# Print all the errors from the json file
errors = json_file.validate_entries(hed_schema)
print(hed.get_printable_issue_string(errors))

# Example 2
# Open the json file, convert all tags to long, and save it out
long_tag_formatter = TagFormat(local_hed_xml)
for column_def in json_file:
    for hed_string, position in column_def.hed_string_iter(include_position=True):
        new_hed_string, errors = long_tag_formatter.convert_hed_string_to_long(hed_string)
        column_def.set_hed_string(new_hed_string, position)
        print(f"'{hed_string}' \nconverts to\n '{new_hed_string}'")

# Save off a copy of the input json, modified.
json_file.save_as_json(json_filename + "-long.json")

# Example 3
# Alternate shorter syntax for accessing HED strings in a json file.
for hed_string, position in json_file.hed_string_iter(include_position=True):
    print(hed_string)
    new_hed_string = hed_string + "fake_string_modification"
    json_file.set_hed_string(new_hed_string, position)

# Leave off include_position if you don't need to save the hed strings back to where they came from.
# these now are modified from the above example
for hed_string in json_file.hed_string_iter():
    print(hed_string)
