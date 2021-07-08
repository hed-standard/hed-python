import os
from hed.models import EventsInput
from hed.validator.event_validator import EventValidator
from hed.schema.hed_schema_file import load_schema
from hed.models import ColumnDefGroup
from hed.errors.error_reporter import get_printable_issue_string

if __name__ == '__main__':
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.1.xml')
    local_hed_file = '../data/HED8.0.0-alpha.1.xml'
    example_data_path = '../data'  # path to example data
    events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events.tsv')

    hed_schema = load_schema(schema_path)
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/bids_events.json")
    json_dictionary = ColumnDefGroup(json_path)
    def_dicts, def_issues = json_dictionary.extract_defs()
    if def_issues:
        print(get_printable_issue_string(def_issues,
                                         title="There should be no errors in the definitions from the sidecars:"))
    event_file = EventsInput(filename=events_path, json_def_files=json_dictionary)

    validator = EventValidator(hed_schema=hed_schema)
    issues = validator.validate_input(event_file)
    issue_str = get_printable_issue_string(issues, f"HED validation errors")
    print(issue_str)

    event_file = EventsInput(filename=events_path, json_def_files=json_dictionary, def_dicts=def_dicts)

    validator = EventValidator(hed_schema=hed_schema)
    issues = validator.validate_input(event_file)
    issue_str = get_printable_issue_string(issues, f"HED validation errors passing definitions")
    print(issue_str)