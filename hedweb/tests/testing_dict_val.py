
from hed.util.column_def_group import ColumnDefGroup
from hed.util.hed_schema import HedSchema

if __name__ == '__main__':
    local_hed_xml = "data/HED8.0.0-alpha.1.xml"
    hed_dictionary = HedSchema(local_hed_xml)
    json_filename = "data/task_pennies_events.json"

    json_file = ColumnDefGroup(json_filename)
    # Print all the errors from the json file
    errors = json_file.validate_entries(hed_dictionary)
    for error in errors:
        x = error
        print(error["message"])