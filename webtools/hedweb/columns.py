import pandas
import os
from flask import current_app
import openpyxl
from hed.errors.exceptions import HedFileError

from hedweb.constants import common, file_constants
from hedweb.web_utils import form_has_file, form_has_option, file_extension_is_valid


app_config = current_app.config


def create_column_selections(form_dict):
    """Returns a tag prefix dictionary from a form dictionary.

    Parameters
    ----------
   form_dict: dict
        The dictionary returned from a form that contains a column prefix table
    Returns
    -------
    dict
        A dictionary whose keys are column numbers (starting with 1) and values are tag prefixes to prepend.
    """

    columns_selections = {}
    keys = form_dict.keys()
    for key in keys:
        if not key.startswith('column') or not key.endswith('use'):
            continue
        pieces = key.split('_')
        name_key = 'column_' + pieces[1] + '_name'
        if name_key not in form_dict:
            continue
        name = form_dict[name_key]
        if form_dict.get('column_' + pieces[1] + '_category', None) == 'on':
            columns_selections[name] = True
        else:
            columns_selections[name] = False

    return columns_selections


def create_columns_info(columns_file, has_column_names: True, sheet_name: None):
    header = None
    if has_column_names:
        header = 0

    sheet_names = None
    filename = columns_file.filename
    file_ext = os.path.splitext(filename.lower())[1]
    if file_ext in file_constants.EXCEL_FILE_EXTENSIONS:
        worksheet, sheet_names = get_worksheet(columns_file, sheet_name)
        dataframe = dataframe_from_worksheet(worksheet, has_column_names)
        sheet_name = worksheet.title
    elif file_ext in file_constants.TEXT_FILE_EXTENSIONS:
        dataframe = pandas.read_csv(columns_file, delimiter='\t', header=header)
    else:
        raise HedFileError('BadFileExtension',
                           f'File {filename} extension does not correspond to an Excel or tsv file', '')
    col_dict = get_info_in_columns(dataframe)
    columns_info = {common.COLUMNS_FILE: filename, common.COLUMN_DICTIONARY: col_dict,
                    common.WORKSHEET_SELECTED: sheet_name, common.WORKSHEET_NAMES: sheet_names}
    return columns_info


def dataframe_from_worksheet(worksheet, has_column_names):
    if not has_column_names:
        data_frame = pandas.DataFrame(worksheet.values)
    else:
        data = worksheet.values
        # first row is columns
        cols = next(data)
        data = list(data)
        data_frame = pandas.DataFrame(data, columns=cols)
    return data_frame


def get_columns_request(request):
    if not form_has_file(request, common.COLUMNS_FILE):
        raise HedFileError('MissingFile', 'An uploadable file was not provided', None)
    columns_file = request.files.get(common.COLUMNS_FILE, '')
    has_column_names = form_has_option(request, 'has_column_names', 'on')
    sheet_name = request.form.get(common.WORKSHEET_SELECTED, None)
    return create_columns_info(columns_file, has_column_names, sheet_name)


def get_info_in_columns(dataframe):
    col_info = dict()

    for col_name, col_values in dataframe.iteritems():
        col_info[col_name] = col_values.value_counts(ascending=True).to_dict()
    return col_info


def get_prefix_dict(form_dict):
    """Returns a tag prefix dictionary from a form dictionary.

    Parameters
    ----------
   form_dict: dict
        The dictionary returned from a form that contains a column prefix table
    Returns
    -------
    dict
        A dictionary whose keys are column numbers (starting with 1) and values are tag prefixes to prepend.
    """
    tag_columns = []
    prefix_dict = {}
    keys = form_dict.keys()
    for key in keys:
        if not key.startswith('column') or key.endswith('check'):
            continue
        pieces = key.split('_')
        check = 'column_' + pieces[1] + '_check'
        if form_dict.get(check, None) != 'on':
            continue
        if form_dict[key]:
            prefix_dict[int(pieces[1])] = form_dict[key]
        else:
            tag_columns.append(int(pieces[1]))
    return tag_columns, prefix_dict


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
