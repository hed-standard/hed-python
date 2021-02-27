from urllib.error import URLError, HTTPError
from flask import current_app

from hed.schema import HedSchema, load_schema
from hed.util.error_reporter import get_printable_issue_string
from hed.util.file_util import delete_file_if_it_exists
from hed.util.column_def_group import ColumnDefGroup
from hed.web.constants import common_constants, error_constants, file_constants
from hed.web.web_utils import generate_filename, generate_download_file_response, \
    handle_http_error, get_hed_path_from_pull_down, \
    get_uploaded_file_path_from_form, save_text_to_upload_folder, get_optional_form_field

app_config = current_app.config


def generate_arguments_from_dictionary_form(request):
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
    uploaded_file_name, original_file_name = get_uploaded_file_path_from_form(request, common_constants.JSON_FILE,
                                                                              file_constants.DICTIONARY_FILE_EXTENSIONS)

    input_arguments = {common_constants.HED_XML_FILE: hed_file_path,
                       common_constants.HED_DISPLAY_NAME: hed_display_name,
                       common_constants.JSON_PATH: uploaded_file_name,
                       common_constants.JSON_FILE: original_file_name,
                       common_constants.CHECK_FOR_WARNINGS: get_optional_form_field(request,
                                                                                    common_constants.CHECK_FOR_WARNINGS,
                                                                                    common_constants.BOOLEAN)
                       }

    return input_arguments


def report_dictionary_validation_status(request):
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
        input_arguments = generate_arguments_from_dictionary_form(request)
        return validate_dictionary(input_arguments)
    except HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except Exception as e:
        return "Unexpected processing error: " + str(e)
    finally:
        delete_file_if_it_exists(input_arguments.get(common_constants.JSON_PATH, ''))


def validate_dictionary(input_arguments, hed_schema=None, return_response=True):
    """Validates the dictionary and returns a response or a printable string depending on return_response value

    Parameters
    ----------
    input_arguments: dict
        Dictionary containing standard input form arguments
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    return_response: bool
        If true, return a Response. If false return a printable issue string

    Returns
    -------
    Response or str
        Either a Response or a printable issue string
    """

    json_dictionary = ColumnDefGroup(input_arguments.get(common_constants.JSON_PATH, ''))
    if not hed_schema:
        hed_schema = load_schema(input_arguments.get(common_constants.HED_XML_FILE, ''))
    issues = json_dictionary.validate_entries(hed_schema)
    if issues:
        display_name = input_arguments.get(common_constants.JSON_FILE, '')
        issue_str = get_printable_issue_string(issues, f"HED validation errors for {display_name}")
        if not return_response:
            return issue_str
        file_name = generate_filename(display_name, suffix='validation_errors', extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        download_response = generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                                            msg='JSON dictionary had validation errors')
        if isinstance(download_response, str):
            return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
        return download_response
    return ""
