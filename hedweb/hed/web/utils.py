import os
import xlrd
import traceback
from flask import Response
from flask import current_app

from hed.util.file_util import get_file_extension, delete_file_if_it_exist
from hed.util import hed_cache
from hed.util.hed_dictionary import HedDictionary

from hed.web.constants import file_constants, spreadsheet_constants
from hed.web.constants import error_constants
from hed.web.constants import common_constants
from hed.web.web_utils import save_hed_to_upload_folder_if_present, file_has_valid_extension, \
    UPLOAD_DIRECTORY_KEY, save_file_to_upload_folder

app_config = current_app.config


def check_if_option_in_form(form_request_object, option_name, target_value):
    """Checks if the given option has a specific value.
       This is used for radio buttons.
    """
    if option_name in form_request_object.values and form_request_object.values[option_name] == target_value:
        return True
    return False


def convert_other_tag_columns_to_list(other_tag_columns):
    """Gets the other tag columns from the validation form.

    Parameters
    ----------
    other_tag_columns: str
        A string containing the other tag columns.

    Returns
    -------
    list
        A list containing the other tag columns.
    """
    if other_tag_columns:
        return list(map(int, other_tag_columns.split(',')))
    return []


def find_all_str_indices_in_list(list_of_strs, str_value):
    """Find the indices of a string value in a list.

    Parameters
    ----------
    list_of_strs: list
        A list containing strings.
    str_value: string
        A string value.

    Returns
    -------
    list
        A list containing all of the indices where a string value occurs in a string list.

    """
    return [index + 1 for index, value in enumerate(list_of_strs) if
            value.lower().replace(' ', '') == str_value.lower().replace(' ', '')]


def find_hed_version_in_file(form_request_object):
    """Finds the version number in a HED XML other.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        A serialized JSON string containing the version number information.

    """
    hed_info = {}
    try:
        if hed_file_present_in_form(form_request_object):
            hed_file = form_request_object.files[common_constants.HED_SCHEMA_FILE]
            hed_file_path = save_hed_to_upload_folder(hed_file)
            hed_info[common_constants.HED_VERSION] = HedDictionary.get_hed_xml_version(hed_file_path)
    except:
        hed_info[error_constants.ERROR_KEY] = traceback.format_exc()
    return hed_info


def find_major_hed_versions():
    """Finds the major HED versions that are kept on the server.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information about the major HED versions.

    """
    hed_info = {}
    try:
        hed_cache.cache_all_hed_xml_versions()
        hed_info[common_constants.HED_MAJOR_VERSIONS] = hed_cache.get_all_hed_versions()
    except:
        hed_info[error_constants.ERROR_KEY] = traceback.format_exc()
    return hed_info


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
        spreadsheet_columns_info = initialize_spreadsheet_columns_info_dictionary()
        if spreadsheet_present_in_form(form_request_object):
            spreadsheet_file = form_request_object.files[common_constants.SPREADSHEET_FILE]
            spreadsheet_file_path = save_spreadsheet_to_upload_folder(spreadsheet_file)
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
        delete_file_if_it_exist(spreadsheet_file_path)
    return spreadsheet_columns_info


def find_str_index_in_list(list_of_strs, str_value):
    """Find the index of a string value in a list.

    Parameters
    ----------
    list_of_strs: list
        A list containing strings.
    str_value: string
        A string value.

    Returns
    -------
    integer
        An positive integer if the string value was found in the list. A -1 is returned if the string value was not
        found.

    """
    try:
        return [s.lower().replace(' ', '') for s in list_of_strs].index(str_value.lower().replace(' ', '')) + 1
    except ValueError:
        return -1


def find_worksheets_info(form_request_object):
    """Finds the info related to the Excel worksheets.

    This information contains the names of the worksheets in a workbook, the names of the columns in the first
    worksheet, and column indices that contain HED tags in the first worksheet.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        A serialized JSON string containing information related to the Excel worksheets.

    """
    workbook_file_path = ''
    worksheets_info = {}
    try:
        worksheets_info = initialize_worksheets_info_dictionary()
        if spreadsheet_present_in_form(form_request_object):
            workbook_file = form_request_object.files[common_constants.SPREADSHEET_FILE]
            workbook_file_path = save_spreadsheet_to_upload_folder(workbook_file)
            if workbook_file_path:
                worksheets_info = populate_worksheets_info_dictionary(worksheets_info, workbook_file_path)
    except:
        worksheets_info[error_constants.ERROR_KEY] = traceback.format_exc()
    finally:
        delete_file_if_it_exist(workbook_file_path)
    return worksheets_info


def generate_download_file_response(download_file_name):
    """Generates a download other response.

    Parameters
    ----------
    download_file_name: string
        The download other name.

    Returns
    -------
    response object
        A response object containing the download other.

    """
    try:
        def generate():
            full_filename = os.path.join(app_config[UPLOAD_DIRECTORY_KEY], download_file_name)
            with open(full_filename, 'r', encoding='utf-8') as download_file:
                for line in download_file:
                    yield line
            delete_file_if_it_exist(full_filename)

        return Response(generate(), mimetype='text/plain charset=utf-8',
                        headers={'Content-Disposition': "attachment filename=%s" % download_file_name})
    except:
        return traceback.format_exc()


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
    file_extension = get_file_extension(file_name_or_path)
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


def get_hed_path_from_form(form_request_object, hed_file_path):
    """Gets the validation function input arguments from a request object associated with the validation form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.
    hed_file_path: string
        The path to the HED XML other.

    Returns
    -------
    string
        The HED XML other path.
    """
    if hed_version_in_form(form_request_object) and \
        (form_request_object.form[common_constants.HED_VERSION] != spreadsheet_constants.OTHER_HED_VERSION_OPTION
         or not hed_file_path):
        return hed_cache.get_path_from_hed_version(form_request_object.form[common_constants.HED_VERSION])
    return hed_file_path


def get_optional_form_field(form_request_object, form_field_name, ftype=''):
    """Gets the specified optional form field if present.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.
    form_field_name: string
        The name of the optional form field.

    Returns
    -------
    boolean or string
        A boolean or string value based on the form field type.

    """
    form_field_value = ''
    if ftype == common_constants.BOOLEAN:
        form_field_value = False
        if form_field_name in form_request_object.form:
            form_field_value = True
    elif ftype == common_constants.STRING:
        if form_field_name in form_request_object.form:
            form_field_value = form_request_object.form[form_field_name]
    return form_field_value


def get_original_spreadsheet_filename(form_request_object):
    """Gets the original name of the spreadsheet.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        The name of the spreadsheet.
    """
    if spreadsheet_present_in_form(form_request_object) and file_has_valid_extension(
            form_request_object.files[common_constants.SPREADSHEET_FILE],
            file_constants.SPREADSHEET_FILE_EXTENSIONS):
        return form_request_object.files[common_constants.SPREADSHEET_FILE].filename
    return ''


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
            specific_tag_column_index = find_str_index_in_list(column_names, alternative_specific_tag_column_name)
            if specific_tag_column_index != -1:
                specific_tag_column_indices[specific_tag_column_name] = specific_tag_column_index
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


def get_uploaded_file_paths_from_forms(form_request_object):
    return ''

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


def hed_present_in_form(validation_form_request_object):
    """Checks to see if a HED XML other is present in a request object from validation form.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if a HED XML other is present in a request object from the validation form.

    """
    return common_constants.HED_SCHEMA_FILE in validation_form_request_object.files


def hed_version_in_form(form_request_object):
    """Checks to see if the hed version is in the validation form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if the hed version is in the validation form. False, if otherwise.
    """
    return common_constants.HED_VERSION in form_request_object.form


def hed_file_present_in_form(validation_form_request_object):
    """Checks to see if a HED XML other is present in a request object from validation form.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if a HED XML other is present in a request object from the validation form.

    """
    return common_constants.HED_XML_FILE in validation_form_request_object.files


def initialize_spreadsheet_columns_info_dictionary():
    """Initializes a dictionary that will hold information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------

    Returns
    -------
    dictionary
        A dictionary that will hold information related to the spreadsheet columns.

    """
    worksheet_columns_info = {common_constants.COLUMN_NAMES: [], common_constants.TAG_COLUMN_INDICES: []}
    return worksheet_columns_info


def initialize_worksheets_info_dictionary():
    """Initializes a dictionary that will hold information related to the Excel worksheets.

    This information contains the names of the worksheets in a workbook, the names of the columns in the first
    worksheet, and column indices that contain HED tags in the first worksheet.

    Parameters
    ----------

    Returns
    -------
    dictionary
        A dictionary that will hold information related to the Excel worksheets.

    """
    worksheets_info = {common_constants.WORKSHEET_NAMES: [], common_constants.COLUMN_NAMES: [],
                       common_constants.TAG_COLUMN_INDICES: []}
    return worksheets_info


def populate_spreadsheet_columns_info_dictionary(spreadsheet_columns_info, spreadsheet_file_path,
                                                 worksheet_name=''):
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
        spreadsheet_columns_info[common_constants.COLUMN_NAMES] = get_worksheet_column_names(
            spreadsheet_file_path,
            worksheet_name)
    else:
        column_delimiter = get_column_delimiter_based_on_file_extension(spreadsheet_file_path)
        spreadsheet_columns_info[common_constants.COLUMN_NAMES] = get_text_file_column_names(
            spreadsheet_file_path,
            column_delimiter)
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


def save_spreadsheet_to_upload_folder(spreadsheet_file_object):
    """Save an spreadsheet other to the upload folder.

    Parameters
    ----------
    spreadsheet_file_object: File object
        A other object that points to a spreadsheet that was first saved in a temporary location.

    Returns
    -------
    string
        The path to the spreadsheet that was saved to the upload folder.

    """
    spreadsheet_file_extension = get_file_extension(spreadsheet_file_object.filename)
    spreadsheet_file_path = save_file_to_upload_folder(spreadsheet_file_object, spreadsheet_file_extension)
    return spreadsheet_file_path


def save_hed_to_upload_folder(hed_file_object):
    """Save an spreadsheet other to the upload folder.

    Parameters
    ----------
    hed_file_object: File object
        A other object that points to a HED XML other that was first saved in a temporary location.

    Returns
    -------
    string
        The path to the HED XML other that was saved to the upload folder.

    """
    hed_file_extension = get_file_extension(hed_file_object.filename)
    hed_file_path = save_file_to_upload_folder(hed_file_object, hed_file_extension)
    return hed_file_path


def spreadsheet_present_in_form(validation_form_request_object):
    """Checks to see if a spreadsheet other is present in a request object from validation form.

    Parameters
    ----------
    validation_form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    boolean
        True if a spreadsheet other is present in a request object from the validation form.

    """
    return common_constants.SPREADSHEET_FILE in validation_form_request_object.files


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
