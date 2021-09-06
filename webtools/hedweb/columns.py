import pandas
from flask import current_app
import openpyxl
from hed.errors.exceptions import HedFileError

from hedweb.constants import common, file_constants
from hedweb.web_utils import form_has_file, form_has_option, file_extension_is_valid


app_config = current_app.config


def get_columns_info(request):
    if ~form_has_file(request, common.COLUMNS_FILE):
        raise HedFileError('MissingFile', 'An uploadable file was not provided', None)
    columns_file = request.files.get(common.COLUMNS_FILE, '')
    has_column_names = form_has_option(request, 'has_column_names', 'on')
    sheet_names = None
    filename = request.files[common.COLUMNS_FILE].filename
    sheet_name = request.form.get(common.WORKSHEET_SELECTED, None)

    if file_extension_is_valid(filename, file_constants.EXCEL_FILE_EXTENSIONS):
        worksheet, sheet_names = get_worksheet(columns_file, sheet_name)
        dataframe = dataframe_from_worksheet(worksheet, has_column_names)
    elif file_extension_is_valid(filename, file_constants.TEXT_FILE_EXTENSIONS):
        dataframe = pandas.read_csv(columns_file, delimiter='\t', header=has_column_names)
    else:
        raise HedFileError('BadFileExtension',
                           f'File {filename} extension does not correspond to an Excel or tsv file', '')
    col_dict = get_info_in_columns(dataframe)
    columns_info = {common.COLUMNS_FILE: filename, common.COLUMN_NAMES: col_dict,
                    common.WORKSHEET_SELECTED: sheet_name, common.WORKSHEET_NAMES: sheet_names}
    return columns_info


def get_info_in_columns(dataframe):
    col_info = dict()

    for col_name, col_vals in dataframe.iteritems():
        col_info[col_name] = col_vals.value_counts(ascending=True)
    return col_info


def dataframe_from_worksheet(worksheet, has_column_names):
    if ~has_column_names:
        data_frame = pandas.DataFrame(worksheet.values)
    else:
        data = worksheet.values
        # first row is columns
        cols = next(data)
        data = list(data)
        data_frame = pandas.DataFrame(data, columns=cols)
    return data_frame


def get_worksheet(excel_file, sheet_name):
    wb = openpyxl.load_workbook(excel_file, read_only=True)
    sheet_names = wb.sheetnames
    if not sheet_names:
        raise HedFileError('BadExcelFile', 'Excel files must have worksheets', None)
    if sheet_name and sheet_name not in sheet_names:
        raise HedFileError('BadWorksheetName', f'Worksheet {sheet_name} not in Excel file', '')
    if sheet_name:
        worksheet = wb[sheet_name]
    else:
        worksheet = wb.worksheets[0]
    return worksheet, sheet_names
