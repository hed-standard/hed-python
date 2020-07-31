"""
Examples of calling the HED validator with files of tags
"""


import os

from hed.validator.hed_input_reader import HedInputReader

if __name__ == '__main__':
    # Set up the file names for the tests
    local_hed_file = '../tests/data/HED.xml'   # path HED v7.1.1 stored locally
    example_data_path = '../tests/data'   # path to example data
    valid_tsv_file = os.path.join(example_data_path, 'ValidTwoColumnHED7_1_1.tsv')
    valid_tsv_file_no_header = os.path.join(example_data_path, 'ValidTwoColumnHED7_1_1NoHeader.tsv')
    valid_tsv_file_separate_cols = os.path.join(example_data_path, 'ValidSeparateColumnTSV.txt')
    unsupported_csv_format = os.path.join(example_data_path, 'UnsupportedFormatCSV.csv')
    multiple_sheet_xlsx_file = os.path.join(example_data_path, 'ExcelMultipleSheets.xlsx')

    # Example 1a: Valid TSV file with default version of HED
    print(valid_tsv_file)
    hed_input_reader = HedInputReader(valid_tsv_file, tag_columns=[2])
    issues = hed_input_reader.get_validation_issues()
    print(hed_input_reader.get_printable_issue_string(
        '[Example 1a] ValidTwoColumnHED7_1_1 is probably okay with default version of HED'))

    # Example 1b: Valid TSV file with specified local version of HED
    print(valid_tsv_file)
    hed_input_reader = HedInputReader(valid_tsv_file, tag_columns=[2], hed_xml_file=local_hed_file)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 1b] ValidTwoColumnHED7_1_1 should have no issues with local version 7.1.1'))

    # Example 1c: Valid TSV file with specified local version of HED and no column headers
    print(valid_tsv_file_no_header)
    hed_input_reader = HedInputReader(valid_tsv_file_no_header, has_column_names=False, tag_columns=[2, 3],
                                      hed_xml_file=local_hed_file)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 1c] ValidTwoColumnHED7_1_1NoHeaders should have no issues with version 7.1.1'))

    # Example 1d: Valid TSV with separate columns for required fields
    print(valid_tsv_file_separate_cols)
    prefixed_needed_tag_columns = {3: 'Description', 4: 'Label', 5: 'Category'}
    hed_input_reader = HedInputReader(valid_tsv_file_separate_cols, tag_columns=[6],
                                      required_tag_columns=prefixed_needed_tag_columns)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 1d] Valid TSV with required tags in separate columns'))

    # Example 2a: CSV files are not supported (Use excel to convert)
    print(unsupported_csv_format)
    prefixed_needed_tag_columns = {3: 'Description', 4: 'Label', 5: 'Category'}
    hed_input_reader = HedInputReader(unsupported_csv_format, tag_columns=[6],
                                      required_tag_columns=prefixed_needed_tag_columns)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 2a] csv is unsupported format, but this call treats file name as HED string'))

    # Example 2b: CSV files are not supported (Use excel to convert) - explicit file specification
    print(unsupported_csv_format)
    prefixed_needed_tag_columns = {3: 'Description', 4: 'Label', 5: 'Category'}
    hed_input_reader = HedInputReader(unsupported_csv_format, is_file=True, tag_columns=[6],
                                      required_tag_columns=prefixed_needed_tag_columns)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 2b] csv is unsupported format, now have right error message'))

    # Example 3a: XLSX file with multiple sheets - first sheet has no issues with 7.1.1
    hed_input_reader = HedInputReader(multiple_sheet_xlsx_file, tag_columns=[4], hed_xml_file=local_hed_file,
                                      required_tag_columns={2: 'Label', 3: 'Description'},
                                      worksheet_name='LKT Events')
    print(hed_input_reader.get_printable_issue_string(
        '[Example 3a] Multiple sheet xlsl has LKT Events sheet with no issues'))

    # Example 3b: Valid XLSX file with multiple sheets - first sheet probably has no issues with default schema
    prefixed_needed_tag_columns = {2: 'Label', 3: 'Description'}
    hed_input_reader = HedInputReader(multiple_sheet_xlsx_file, tag_columns=[4],
                                      required_tag_columns={2: 'Label', 3: 'Description'},
                                      worksheet_name='LKT Events')
    print(hed_input_reader.get_printable_issue_string(
        '[Example 3b] LKT Events sheet probably has with no issues with the default schema'))

    # Example 3c: XLSX file with multiple sheets - assumes first sheet by default
    hed_input_reader = HedInputReader(multiple_sheet_xlsx_file, tag_columns=[4], hed_xml_file=local_hed_file,
                                      required_tag_columns={2: 'Label', 3: 'Description'})
    print(hed_input_reader.get_printable_issue_string(
        '[Example 3c] Multiple sheet xlsl has first sheet with no issues'))

    # Example 3d: XLSX file with multiple sheets - PVT sheet has several issues with 7.1.1
    hed_input_reader = HedInputReader(multiple_sheet_xlsx_file, tag_columns=[4], hed_xml_file=local_hed_file,
                                      required_tag_columns={2: 'Label', 3: 'Description'},
                                      worksheet_name='PVT Events')
    print(hed_input_reader.get_printable_issue_string(
        '[Example 3d] Some PVT worksheet issues that are due to removal of extensionAllowed in places in 7.1.1'))

    # Example 3e: Invalid XLSX sheet with 7.1.1
    hed_input_reader = HedInputReader(multiple_sheet_xlsx_file, tag_columns=[4], hed_xml_file=local_hed_file,
                                      worksheet_name='DAS Events')
    print(hed_input_reader.get_printable_issue_string(
        '[Example 3e] DAS Events worksheet has multiple issues with 7.1.1'))

    # Example 3f: Invalid XLSX sheet with 7.1.1 - also can't duplicate Label and Description in 7.1.1
    hed_input_reader = HedInputReader(multiple_sheet_xlsx_file, tag_columns=[4], hed_xml_file=local_hed_file,
                                      required_tag_columns={2: 'Label', 3: 'Description'},
                                      worksheet_name='DAS Events')
    print(hed_input_reader.get_printable_issue_string(
        '[Example 3f] DAS worse now because of duplicate Label and Description specifications'))
