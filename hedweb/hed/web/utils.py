import xlrd
import traceback

from flask import current_app

from hed.util.file_util import get_file_extension, delete_file_if_it_exists

from hed.web.constants import common_constants, error_constants, spreadsheet_constants
from hed.web.web_utils import save_file_to_upload_folder, find_all_str_indices_in_list

app_config = current_app.config


def find_spreadsheet_columns_info(form_request_object):
    """Finds the info associated with the spreadsheet columns.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    dictionary
        A dictionary populated with information related to the spreadsheet columns.
    """
    spreadsheet_file_path = ''
    spreadsheet_columns_info = []
    try:
        spreadsheet_columns_info = {common_constants.COLUMN_NAMES: [], common_constants.TAG_COLUMN_INDICES: []}
        if common_constants.SPREADSHEET_FILE in form_request_object.files:
            spreadsheet_file = form_request_object.files[common_constants.SPREADSHEET_FILE]
            spreadsheet_file_path = save_file_to_upload_folder(spreadsheet_file)
            if spreadsheet_file_path and worksheet_name_present_in_form(form_request_object):
                worksheet_name = form_request_object.form[common_constants.WORKSHEET_NAME]
                spreadsheet_columns_info = populate_spreadsheet_columns_info_dictionary(spreadsheet_columns_info,
                                                                                        spreadsheet_file_path,
                                                                                        worksheet_name)
            else:
                spreadsheet_columns_info = populate_spreadsheet_columns_info_dictionary(spreadsheet_columns_info,
                                                                                        spreadsheet_file_path)
    except:
        spreadsheet_columns_info[error_constants.ERROR_KEY] = traceback.format_exc()
    finally:
        delete_file_if_it_exists(spreadsheet_file_path)
    return spreadsheet_columns_info


def get_column_delimiter_based_on_file_extension(file_name_or_path):
    """Gets the spreadsheet column delimiter based on the other extension.

    Parameters
    ----------
    file_name_or_path: string
        A other name or path.

    Returns
    -------
    string
        The spreadsheet column delimiter based on the other extension.

    """
    column_delimiter = ''
    file_extension = get_file_extension(file_name_or_path).lower()
    if file_extension in spreadsheet_constants.SPREADSHEET_FILE_EXTENSION_TO_DELIMITER_DICTIONARY:
        column_delimiter = spreadsheet_constants.SPREADSHEET_FILE_EXTENSION_TO_DELIMITER_DICTIONARY.get(file_extension)
    return column_delimiter


def get_excel_worksheet_names(workbook_file_path):
    """Gets the worksheet names in an Excel workbook.

    Parameters
    ----------
    workbook_file_path: string
        The full path to an Excel workbook other.

    Returns
    -------
    list
        A list containing the worksheet names in an Excel workbook.

    """
    opened_workbook_file = xlrd.open_workbook(workbook_file_path)
    worksheet_names = opened_workbook_file.sheet_names()
    return worksheet_names


def get_optional_form_field(form_request_object, form_field_name, type=''):
    """Gets the specified optional form field if present.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.
    form_field_name: string
        The name of the optional form field.
    type: str
        Name of expected type: 'boolean' or 'string'

    Returns
    -------
    boolean or string
        A boolean or string value based on the form field type.

    """
    form_field_value = ''
    if type == common_constants.BOOLEAN:
        form_field_value = False
        if form_field_name in form_request_object.form:
            form_field_value = True
    elif type == common_constants.STRING:
        if form_field_name in form_request_object.form:
            form_field_value = form_request_object.form[form_field_name]
    return form_field_value


def get_specific_tag_columns_from_form(form_request_object):
    """Gets the specific tag columns from the validation form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    dictionary
        A dictionary containing the required tag columns. The keys will be the column numbers and the values will be
        the name of the column.
    """
    column_prefix_dictionary = {}
    for tag_column_name in spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES:
        form_tag_column_name = tag_column_name.lower() + common_constants.COLUMN_POSTFIX
        if form_tag_column_name in form_request_object.form:
            tag_column_name_index = form_request_object.form[form_tag_column_name].strip()
            if tag_column_name_index:
                tag_column_name_index = int(tag_column_name_index)

                # todo: Remove these giant kludges at some point
                if tag_column_name == "Long":
                    tag_column_name = "Long Name"
                tag_column_name = "Event/" + tag_column_name + "/"
                # End giant kludges

                column_prefix_dictionary[tag_column_name_index] = tag_column_name
    return column_prefix_dictionary


def get_spreadsheet_other_tag_column_indices(column_names):
    """Gets the other tag column indices in a spreadsheet. The indices found will be one-based.

    Parameters
    ----------
    column_names: list
        A list containing the column names in a spreadsheet.

    Returns
    -------
    list
        A list containing the tag column indices found in a spreadsheet.

    """
    tag_column_indices = []
    for tag_column_name in spreadsheet_constants.OTHER_TAG_COLUMN_NAMES:
        found_indices = find_all_str_indices_in_list(column_names, tag_column_name)
        if found_indices:
            tag_column_indices.extend(found_indices)
    return tag_column_indices


def get_spreadsheet_specific_tag_column_indices(column_names):
    """Gets the required tag column indices in a spreadsheet. The indices found will be one-based.

    Parameters
    ----------
    column_names: list
        A list containing the column names in a spreadsheet.

    Returns
    -------
    dictionary
        A dictionary containing the required tag column indices found in a spreadsheet.

    """
    specific_tag_column_indices = {}
    specific_tag_column_names = spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES_DICTIONARY.keys()
    for specific_tag_column_name in specific_tag_column_names:
        alternative_specific_tag_column_names = spreadsheet_constants.SPECIFIC_TAG_COLUMN_NAMES_DICTIONARY[
            specific_tag_column_name]
        for alternative_specific_tag_column_name in alternative_specific_tag_column_names:
            indices = find_all_str_indices_in_list(column_names, alternative_specific_tag_column_name)
            if indices:
                specific_tag_column_indices[specific_tag_column_name] = indices[0]
    return specific_tag_column_indices


def get_text_file_column_names(text_file_path, column_delimiter):
    """Gets the text spreadsheet column names.

    Parameters
    ----------
    text_file_path: string
        The path to a text other.
    column_delimiter: string
        The spreadsheet column delimiter.

    Returns
    -------
    string
        The spreadsheet column delimiter based on the other extension.

    """
    with open(text_file_path, 'r', encoding='utf-8') as opened_text_file:
        first_line = opened_text_file.readline()
        text_file_columns = first_line.split(column_delimiter)
    return text_file_columns


def get_worksheet_column_names(workbook_file_path, worksheet_name):
    """Get the worksheet columns in a Excel workbook.

    Parameters
    ----------
    workbook_file_path : string
        The full path to an Excel workbook other.
    worksheet_name : string
        The name of an Excel worksheet.

    Returns
    -------
    list
        A list containing the worksheet columns in an Excel workbook.

    """
    opened_workbook_file = xlrd.open_workbook(workbook_file_path)
    opened_worksheet = opened_workbook_file.sheet_by_name(worksheet_name)
    worksheet_column_names = [opened_worksheet.cell(0, col_index).value for col_index in range(opened_worksheet.ncols)]
    return worksheet_column_names


def populate_spreadsheet_columns_info_dictionary(spreadsheet_columns_info, spreadsheet_file_path, worksheet_name=''):
    """Populate dictionary with information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------
    spreadsheet_columns_info: dictionary
        A dictionary that contains information related to the spreadsheet column.
    spreadsheet_file_path: string
        The full path to a spreadsheet other.
    worksheet_name: string
        The name of an Excel worksheet.

    Returns
    -------
    dictionary
        A dictionary populated with information related to the spreadsheet columns.

    """
    if worksheet_name:
        spreadsheet_columns_info[common_constants.COLUMN_NAMES] = \
            get_worksheet_column_names(spreadsheet_file_path, worksheet_name)
    else:
        column_delimiter = get_column_delimiter_based_on_file_extension(spreadsheet_file_path)
        spreadsheet_columns_info[common_constants.COLUMN_NAMES] = \
            get_text_file_column_names(spreadsheet_file_path, column_delimiter)
    spreadsheet_columns_info[common_constants.TAG_COLUMN_INDICES] = \
        get_spreadsheet_other_tag_column_indices(spreadsheet_columns_info[common_constants.COLUMN_NAMES])
    spreadsheet_columns_info[common_constants.REQUIRED_TAG_COLUMN_INDICES] = \
        get_spreadsheet_specific_tag_column_indices(spreadsheet_columns_info[common_constants.COLUMN_NAMES])
    return spreadsheet_columns_info


def populate_worksheets_info_dictionary(worksheets_info, spreadsheet_file_path):
    """Populate dictionary with information related to the Excel worksheets.

    This information contains the names of the worksheets in a workbook, the names of the columns in the first
    worksheet, and column indices that contain HED tags in the first worksheet.

    Parameters
    ----------
    worksheets_info: dictionary
        A dictionary that contains information related to the Excel worksheets.
    spreadsheet_file_path: string
        The full path to an Excel workbook other.

    Returns
    -------
    dictionary
        A dictionary populated with information related to the Excel worksheets.

    """
    worksheets_info[common_constants.WORKSHEET_NAMES] = get_excel_worksheet_names(spreadsheet_file_path)
    worksheets_info[common_constants.COLUMN_NAMES] = \
        get_worksheet_column_names(spreadsheet_file_path, worksheets_info[common_constants.WORKSHEET_NAMES][0])
    worksheets_info[common_constants.TAG_COLUMN_INDICES] = get_spreadsheet_other_tag_column_indices(
        worksheets_info[common_constants.COLUMN_NAMES])
    worksheets_info[common_constants.REQUIRED_TAG_COLUMN_INDICES] = \
        get_spreadsheet_specific_tag_column_indices(worksheets_info[common_constants.COLUMN_NAMES])
    return worksheets_info


def worksheet_name_present_in_form(validation_form_request_object):
    """Checks to see if a worksheet name is present in a request object from the validation form.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if a worksheet name is present in a request object from the validation form.

    """
    return common_constants.WORKSHEET_NAME in validation_form_request_object.form
