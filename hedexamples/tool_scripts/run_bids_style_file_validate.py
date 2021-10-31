import os


from hed.models.sidecar import Sidecar
from hed.models.events_input import EventsInput
from hed import HedValidator, load_schema, HedSchemaGroup


def validate_bids_file():
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '../data/schema_data/HED8.0.0.mediawiki')

    hed_schema = load_schema(schema_path)
    hed_schema_lib = load_schema(schema_path, library_prefix="lb")
    schema_group = HedSchemaGroup([hed_schema, hed_schema_lib])
    validator = HedValidator(hed_schema=schema_group)

    events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '../data/bids_data/bids_test_sample.tsv')
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "../data/bids_data/bids_test_sample.json")
    sidecar = Sidecar(json_path)
    input_file = EventsInput(events_path, sidecars=sidecar)
    issues = input_file.validate_file_sidecars(validator)
    issues += input_file.validate_file(validator)
    # If you want to view the expanded version of the file, use this.
    # input_file.to_csv(events_path + "proc_output.tsv", output_processed_file=True)
    breakHere = 3


if __name__ == '__main__':
    validate_bids_file()