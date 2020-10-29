"""
Examples of calling the HED validator with files of tags
"""


import os

from hed.util.hed_file_input import HedFileInput
from hed.tools.tag_format import TagFormat

local_hed_file = 'data/reduced_no_dupe.xml'  # path HED v7.1.1 stored locally

def resave_file(input_file):
    for row_number, row_hed_string, column_to_hed_tags_dictionary in input_file:
        for column_number in column_to_hed_tags_dictionary:
            old_text = column_to_hed_tags_dictionary[column_number]
            new_text = old_text
            input_file.set_cell(row_number, column_number, new_text)

    input_file.save(f"{input_file.filename}_test_output")


def long_to_short_file(input_file):
    tag_formatter = TagFormat(local_hed_file)
    for row_number, row_hed_string, column_to_hed_tags_dictionary in input_file:
        for column_number in column_to_hed_tags_dictionary:
            old_text = column_to_hed_tags_dictionary[column_number]
            new_text, _ = tag_formatter.convert_hed_string_to_short(old_text)
            input_file.set_cell(row_number, column_number, new_text,
                                include_column_prefix_if_exist=False)

    input_file.save(f"{input_file.filename}_test_long_to_short")

def short_to_long_file(input_file):
    tag_formatter = TagFormat(local_hed_file)
    for row_number, row_hed_string, column_to_hed_tags_dictionary in input_file:
        for column_number in column_to_hed_tags_dictionary:
            old_text = column_to_hed_tags_dictionary[column_number]
            new_text, _ = tag_formatter.convert_hed_string_to_long(old_text)
            input_file.set_cell(row_number, column_number, new_text,
                                include_column_prefix_if_exist=False)

    input_file.save(f"{input_file.filename}_test_short_to_long")

if __name__ == '__main__':
    # Set up the file names for the tests
    local_hed_file = 'data/HED7.1.1.xml'   # path HED v7.1.1 stored locally
    example_data_path = 'data'   # path to example data
    valid_tsv_file = os.path.join(example_data_path, 'ValidTwoColumnHED7_1_1.tsv')
    valid_tsv_file_no_header = os.path.join(example_data_path, 'ValidTwoColumnHED7_1_1NoHeader.tsv')
    valid_tsv_file_separate_cols = os.path.join(example_data_path, 'ValidSeparateColumnTSV.txt')
    unsupported_csv_format = os.path.join(example_data_path, 'UnsupportedFormatCSV.csv')
    multiple_sheet_xlsx_file = os.path.join(example_data_path, 'ExcelMultipleSheets.xlsx')
    hed3_tags_single_sheet = os.path.join(example_data_path, 'hed3_tags_single_sheet.xlsx')

    # Example 1a: Valid TSV file with default version of HED
    print(valid_tsv_file)
    input_file = HedFileInput(valid_tsv_file, tag_columns=[2])
    resave_file(input_file)

    # Example 1b: Valid TSV file with specified local version of HED
    print(valid_tsv_file)
    input_file = HedFileInput(valid_tsv_file, tag_columns=[2])
    resave_file(input_file)

    # Example 1c: Valid TSV file with specified local version of HED and no column headers
    print(valid_tsv_file_no_header)
    input_file = HedFileInput(valid_tsv_file_no_header, has_column_names=False, tag_columns=[2, 3])
    resave_file(input_file)

    # Example 1d: Valid TSV with separate columns for required fields
    print(valid_tsv_file_separate_cols)
    prefixed_needed_tag_columns = {3: 'Event/Description/', 4: 'Event/Label/', 5: 'Event/Category/'}
    input_file = HedFileInput(valid_tsv_file_separate_cols, tag_columns=[6],
                                      column_prefix_dictionary=prefixed_needed_tag_columns)
    resave_file(input_file)

    # Example 2a: CSV files are not supported (Use excel to convert)
    # print(unsupported_csv_format)
    # prefixed_needed_tag_columns = {3: 'Event/Description/', 4: 'Event/Label/', 5: 'Event/Category/'}
    # input_file = HedFileInput(unsupported_csv_format, tag_columns=[6],
    #                                   column_prefix_dictionary=prefixed_needed_tag_columns)
    # short_to_long_file(input_file)
    #
    # # Example 2b: CSV files are not supported (Use excel to convert) - explicit file specification
    # print(unsupported_csv_format)
    # prefixed_needed_tag_columns = {3: 'Event/Description/', 4: 'Event/Label/', 5: 'Event/Category/'}
    # input_file = HedFileInput(unsupported_csv_format, tag_columns=[6],
    #                           column_prefix_dictionary=prefixed_needed_tag_columns)
    # short_to_long_file(input_file)

    prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    # Example 3a: XLSX file with multiple sheets - first sheet has no issues with 7.1.1
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')
    resave_file(input_file)

    # Example 3b: Valid XLSX file with multiple sheets - first sheet probably has no issues with default schema
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')
    resave_file(input_file)

    # Example 3c: XLSX file with multiple sheets - assumes first sheet by default
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns)
    resave_file(input_file)

    # Example 3d: XLSX file with multiple sheets - PVT sheet has several issues with 7.1.1
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4],
                                      column_prefix_dictionary=prefixed_needed_tag_columns,
                                      worksheet_name='PVT Events')
    resave_file(input_file)

    # Example 3e: Invalid XLSX sheet with 7.1.1
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4], worksheet_name='DAS Events')
    resave_file(input_file)

    # Example 3f: Invalid XLSX sheet with 7.1.1 - also can't duplicate Label and Description in 7.1.1
    input_file = HedFileInput(multiple_sheet_xlsx_file, tag_columns=[4],
                                      column_prefix_dictionary=prefixed_needed_tag_columns,
                                      worksheet_name='DAS Events')
    resave_file(input_file)

    prefixed_needed_tag_columns = {2: 'Event/Label/', 3: 'Event/Description/'}
    # Example 3a: XLSX file with multiple sheets - first sheet has no issues with 7.1.1
    input_file = HedFileInput(hed3_tags_single_sheet, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')
    long_to_short_file(input_file)

    input_file = HedFileInput(hed3_tags_single_sheet, tag_columns=[4],
                              column_prefix_dictionary=prefixed_needed_tag_columns,
                              worksheet_name='LKT Events')
    short_to_long_file(input_file)