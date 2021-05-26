import os
import pandas as pd
from hed.util.event_file_input import EventFileInput
from hed.schema.hed_schema_file import load_schema
from hed.util.column_def_group import ColumnDefGroup
from hed.util.error_reporter import get_printable_issue_string

if __name__ == '__main__':
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
    local_hed_file = 'data/HED8.0.0-alpha.1.xml'
    example_data_path = 'data'  # path to example data
    events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/bids_events.tsv')

    hed_schema = load_schema(schema_path)
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/bids_events.json")
    column_group = ColumnDefGroup(json_path)
    def_dict, def_issues = column_group.extract_defs()
    if def_issues:
        print(get_printable_issue_string(def_issues,
                                         title="There should be no errors in the definitions from the sidecars:"))
    #event_file = EventFileInput(events_path, json_def_files=column_group, def_dicts=def_dict)
    event_file = EventFileInput(filename=events_path, json_def_files=column_group)
    # for row_number, columns_to_row_dict in event_file:
    hed_tags = []
    onsets = []
    for row_number, row_dict in event_file.iter_dataframe(return_row_dict=True):
        assembled_row_hed_string = row_dict.get("HED", "")
        onset = row_dict.get("onset", "n/a")
        hed_tags.append(str(row_dict.get("HED", "")))
        onsets.append(row_dict.get("onset", "n/a"))
    data = {'onset': onsets, 'HED': hed_tags}

    df = pd.DataFrame(data)
    final_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/myTemp.tsv')
    df.to_csv(final_filename, '\t', index=False, header=True)
