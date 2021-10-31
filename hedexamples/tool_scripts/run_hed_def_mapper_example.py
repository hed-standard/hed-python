"""
Examples of creating an EventsInput to open a spreadsheet, process it, then save it back out.

Classes Demonstrated:
HedSchema - Opens a hed xml schema.  Used by other tools to check tag attributes in the schema.
HedValidator - Validates a given input string or file
EventsInput - Used to open/modify/save a bids style spreadsheet, with json sidecars and definitions.
HedFileError - Exception thrown when a file cannot be opened.(parsing error, file not found error, etc)
Sidecar - Contains the data from a single json sidecar, can be validated using a HedSchema.
"""
import os
from hed import EventsInput, get_printable_issue_string, load_schema, HedValidator, Sidecar


if __name__ == '__main__':
    local_hed_file = '../data/schema_data/HED8.0.0-alpha.1.xml'
    example_data_path = '../data'  # path to example data
    hed3_tags_single_sheet = os.path.join(example_data_path, 'hed_tag_def_example.tsv')
    hed_schema = load_schema(local_hed_file)
    prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    json_file = "../data/bids_data/both_types_events_def_example.json"
    validator = HedValidator(hed_schema=hed_schema)
    sidecar = Sidecar(json_file)
    def_issues = sidecar.validate_entries(validator)
    # def_issues = sidecar.validate_entries(hed_schema=hed_schema)
    if def_issues:
        print(get_printable_issue_string(def_issues,
                                         title="There should be no errors in the definitions from the sidecars:"))
    input_file = EventsInput(hed3_tags_single_sheet, sidecars=sidecar)

    validation_issues = input_file.validate_file_sidecars(validator)
    if validation_issues:
        print(get_printable_issue_string(validation_issues,
                                         title="There should be no errors with the sidecar.  \""
                                         "This will likely cause other errors if there are."))
    validation_issues = input_file.validate_file(validator)
    print(get_printable_issue_string(validation_issues, "Normal hed string errors"))

    output_filename = hed3_tags_single_sheet + "_test_output.xlsx"
    input_file.to_excel(output_filename, output_processed_file=False)
    output_filename = hed3_tags_single_sheet + "_proc_test_output.xlsx"
    input_file.to_excel(output_filename, output_processed_file=True)
    breakHEre = 3
