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
from hed.errors.error_reporter import get_printable_issue_string
from hed.models.sidecar import Sidecar
from hed.models.events_input import EventsInput
from hed.validator.hed_validator import HedValidator
from hed.schema.hed_schema_file import load_schema


if __name__ == '__main__':
    # Setup the files
    local_hed_file = '../data/schema_data/HED8.0.0.xml'
    data_path = '../data/'  # path to example data
    events_file = os.path.join(data_path, 'sub-003_task-FacePerception_run-2_events.tsv')
    json_file = os.path.join(data_path, 'task-FacePerception_events.json')

    # Load the schema for the examples
    hed_schema = load_schema(local_hed_file)

    # Validate sidecar
    validator = HedValidator(hed_schema=hed_schema)
    sidecar = Sidecar(json_file)
    def_issues = sidecar.validate_entries(validator)
    if def_issues:
        print(get_printable_issue_string(def_issues,
                                         title="There should be no errors in the definitions from the sidecars:"))

    # Validate events file with sidecar
    input_file = EventsInput(events_file, sidecars=sidecar)

    # Not recommended that the sidecar be validated separately as part of sidecar validation
    validation_issues = input_file.validate_file_sidecars(validator)
    if validation_issues:
        print(get_printable_issue_string(validation_issues,
                                         title="There should be no errors with this sidecar.  \""
                                         "This will likely cause other errors if there are."))

    # Validate the events file
    validation_issues = input_file.validate_file(validator)
    print(get_printable_issue_string(validation_issues, "There should be no errors with this events file"))
