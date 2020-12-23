"""
Examples of outputting a spreadsheet after processing is done(removing definitions etc)
"""
import os
from hed.util.event_file_input import EventFileInput
from hed.util.hed_dictionary import HedDictionary


if __name__ == '__main__':
    local_hed_file = 'examples/data/HED8.0.0-alpha.1.xml'
    example_data_path = 'examples/data'   # path to example data
    hed3_tags_single_sheet = os.path.join(example_data_path, 'hed_tag_def_example.xlsx')

    hed_dict = HedDictionary(local_hed_file)
    prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    input_file = EventFileInput(hed3_tags_single_sheet, json_def_files="examples/data/both_types_events_def_example.json",
                                tag_columns=[4], column_prefix_dictionary=prefixed_needed_tag_columns,
                                worksheet_name='LKT Events',
                                hed_dictionary=hed_dict)

    input_file.save(f"{input_file.filename}_test_output", include_formatting=True, output_processed_file=False)
    input_file.save(f"{input_file.filename}_proc_test_output", include_formatting=True, output_processed_file=True)


