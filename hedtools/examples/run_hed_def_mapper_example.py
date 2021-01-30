"""
Example of outputting a spreadsheet after processing is done(replacing definitions etc)
"""
import os
from hed.util.event_file_input import EventFileInput
from hed.util.hed_schema import HedSchema
from hed.validator.hed_validator import HedValidator
from hed.util.column_def_group import ColumnDefGroup

if __name__ == '__main__':
    local_hed_file = 'data/HED8.0.0-alpha.1.xml'
    example_data_path = 'data'  # path to example data
    hed3_tags_single_sheet = os.path.join(example_data_path, 'hed_tag_def_example.xlsx')

    hed_schema = HedSchema(local_hed_file)
    prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    json_file = "data/both_types_events_def_example.json"
    column_group = ColumnDefGroup(json_file)
    def_dict, def_issues = column_group.extract_defs(hed_schema)
    if def_issues:
        print(HedValidator.get_printable_issue_string(def_issues,
                                                      title="There should be no errors in the definitions from the sidecars:"))
    input_file = EventFileInput(hed3_tags_single_sheet, json_def_files=column_group,
                                tag_columns=[4], column_prefix_dictionary=prefixed_needed_tag_columns,
                                worksheet_name='LKT Events',
                                hed_schema=hed_schema,
                                def_dicts=def_dict)

    validation_issues = input_file.validate_file_sidecars(hed_schema=hed_schema)
    if validation_issues:
        print(HedValidator.get_printable_issue_string(validation_issues,
                                                      title="There should be no errors with the sidecar.  This will likely cause other errors if there are."))
    validator = HedValidator(hed_schema=hed_schema)
    validation_issues = validator.validate_input(input_file)
    print(validator.get_printable_issue_string(validation_issues,
                                               "Normal hed string errors"))

    input_file.save(include_formatting=True, add_suffix="_test_output", output_processed_file=False)
    input_file.save(include_formatting=True, add_suffix="_proc_test_output", output_processed_file=True)
