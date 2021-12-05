import os

from hed.errors.error_reporter import get_printable_issue_string
from hed.models.sidecar import Sidecar
from hed.models.events_input import EventsInput
from hed.validator.hed_validator import HedValidator
from hed.schema.hed_schema_file import load_schema
from hed.schema.hed_schema_group import HedSchemaGroup


def validate_bids_file():
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '../data/schema_data/HED8.0.0.mediawiki')

    hed_schema = load_schema(schema_path)
    hed_schema_lib = load_schema(schema_path, library_prefix="lb")
    schema_group = HedSchemaGroup([hed_schema, hed_schema_lib])
    validator = HedValidator(hed_schema=schema_group)

    events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '../data/wakeman_henson_data/sub-002_task-FacePerception_run-1_events.tsv')
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "../data/wakeman_henson_data/task-FacePerception_events.json")
    sidecar = Sidecar(json_path)
    input_file = EventsInput(events_path, sidecars=sidecar)
    issues = input_file.validate_file_sidecars(validator, check_for_warnings=False)
    issues += input_file.validate_file(validator, check_for_warnings=False)
    # If you want to view the expanded version of the file, use this.
    # input_file.to_csv(events_path + "proc_output.tsv", output_processed_file=True)
    return issues


if __name__ == '__main__':

    validation_issues = validate_bids_file()
    if validation_issues:
        issues_str = get_printable_issue_string(validation_issues, "validation errors for bids file:")
        print(issues_str)
