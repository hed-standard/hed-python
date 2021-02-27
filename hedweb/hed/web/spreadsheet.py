from urllib.error import URLError, HTTPError
from flask import current_app

from hed.util.error_reporter import get_printable_issue_string
from hed.util.file_util import delete_file_if_it_exists
from hed.validator.hed_validator import HedValidator
from hed.util.hed_file_input import HedFileInput

import hed.web.web_utils
from hed.web.constants import common_constants, error_constants, file_constants
from hed.web.web_utils import convert_number_str_to_list, generate_filename, \
    generate_download_file_response, get_hed_path_from_pull_down, get_uploaded_file_path_from_form, \
    handle_http_error, save_text_to_upload_folder
from hed.web import spreadsheet_utils

app_config = current_app.config


def generate_input_from_validation_form(request):
    """Gets the validation function input arguments from a request object associated with the validation form.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying validation function.
    """
    hed_file_path, hed_display_name = get_hed_path_from_pull_down(request)
    uploaded_file_name, original_file_name = \
        get_uploaded_file_path_from_form(request, common_constants.SPREADSHEET_FILE,
                                         file_constants.SPREADSHEET_FILE_EXTENSIONS)

    input_arguments = {
        common_constants.HED_XML_FILE: hed_file_path,
        common_constants.HED_DISPLAY_NAME: hed_display_name,
        common_constants.SPREADSHEET_PATH: uploaded_file_name,
        common_constants.SPREADSHEET_FILE: original_file_name,
        common_constants.TAG_COLUMNS: convert_number_str_to_list(request.form[common_constants.TAG_COLUMNS]),
        common_constants.COLUMN_PREFIX_DICTIONARY: spreadsheet_utils.get_specific_tag_columns_from_form(request),
        common_constants.WORKSHEET_NAME: hed.web.web_utils.get_optional_form_field(request,
                                                                                   common_constants.WORKSHEET_NAME,
                                                                                   common_constants.STRING),
        common_constants.HAS_COLUMN_NAMES:
            hed.web.web_utils.get_optional_form_field(request, common_constants.HAS_COLUMN_NAMES,
                                                      common_constants.BOOLEAN),
        common_constants.CHECK_FOR_WARNINGS:
            hed.web.web_utils.get_optional_form_field(request, common_constants.CHECK_FOR_WARNINGS,
                                                      common_constants.BOOLEAN)
    }
    return input_arguments


def report_spreadsheet_validation_status(request):
    """Reports the spreadsheet validation status.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """
    input_arguments = []
    try:
        input_arguments = generate_input_from_validation_form(request)
        return validate_spreadsheet(input_arguments)
    except HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except Exception as e:
        return "Unexpected processing error: " + str(e)
    finally:
        delete_file_if_it_exists(input_arguments.get(common_constants.SPREADSHEET_PATH, ''))


def validate_spreadsheet(input_arguments, hed_validator=None, return_response=True):
    """Validates the spreadsheet.

    Parameters
    ----------
    input_arguments: dictionary
        A dictionary containing the arguments for the validation function.
    hed_validator: HedValidator
        Validator passed if previously created in another phase
    return_response: bool
        If true returns a response object, otherwise directly returns a printable issue string
    Returns
    -------
    HedValidator object
        A HedValidator object containing the validation results.
    """

    file_input = HedFileInput(input_arguments.get(common_constants.SPREADSHEET_PATH, None),
                              worksheet_name=input_arguments.get(common_constants.WORKSHEET_NAME, None),
                              tag_columns=input_arguments.get(common_constants.TAG_COLUMNS, None),
                              has_column_names=input_arguments.get(common_constants.HAS_COLUMN_NAMES, None),
                              column_prefix_dictionary=input_arguments.get(common_constants.COLUMN_PREFIX_DICTIONARY,
                                                                           None))
    if not hed_validator:
        hed_validator = HedValidator(hed_xml_file=input_arguments.get(common_constants.HED_XML_FILE, ''),
                                     check_for_warnings=input_arguments.get(common_constants.CHECK_FOR_WARNINGS, False))

    issues = hed_validator.validate_input(file_input)

    if issues:
        display_name = input_arguments.get(common_constants.SPREADSHEET_FILE, None)
        worksheet_name = input_arguments.get(common_constants.WORKSHEET_NAME, None)
        title_string = display_name
        suffix = 'validation_errors'
        if worksheet_name:
            title_string = display_name + ' [worksheet ' + worksheet_name + ']'
            suffix = '_worksheet_' + worksheet_name + '_' + suffix
        issue_str = get_printable_issue_string(issues, f"{title_string} HED validation errors")
        if not return_response:
            return issue_str
        file_name = generate_filename(display_name, suffix=suffix, extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        download_response = generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                                            msg='Spreadsheet had validation errors')
        if isinstance(download_response, str):
            return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
        return download_response
    return ""
