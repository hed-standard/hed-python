import json
import os
import traceback
from urllib.error import URLError, HTTPError
from flask import current_app

from hed.util.file_util import get_file_extension, delete_file_if_it_exists, write_strings_to_file
from hed.validator.hed_validator import HedValidator
from hed.util.column_def_group import ColumnDefGroup
from hed.util.hed_schema import HedSchema

from hed.web.constants import common_constants, error_constants, file_constants
from hed.web.web_utils import generate_filename, generate_download_file_response, \
    handle_http_error, get_hed_path_from_pull_down, get_printable_issue_string, \
    get_uploaded_file_path_from_form, save_file_to_upload_folder, save_text_to_upload_folder
from hed.web.utils import get_optional_form_field

app_config = current_app.config


def generate_arguments_from_dictionary_form(form_request_object):
    """Gets the validation function input arguments from a request object associated with the validation form.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying validation function.
    """
    hed_file_path, hed_display_name = get_hed_path_from_pull_down(form_request_object)
    uploaded_file_name, original_file_name = \
        get_uploaded_file_path_from_form(form_request_object, common_constants.JSON_FILE,
                                         file_constants.DICTIONARY_FILE_EXTENSIONS)

    input_arguments = {common_constants.HED_XML_FILE: hed_file_path,
                       common_constants.HED_DISPLAY_NAME: hed_display_name,
                       common_constants.JSON_PATH: uploaded_file_name,
                       common_constants.JSON_FILE: original_file_name}
    input_arguments[common_constants.CHECK_FOR_WARNINGS] = get_optional_form_field(
        form_request_object, common_constants.CHECK_FOR_WARNINGS, common_constants.BOOLEAN)
    return input_arguments


def report_eeg_events_validation_status(request):
    """Reports validation status of hed strings associated with EEG events
       received from EEGLAB plugin HEDTools

    Parameters
    ----------
    request: Request object
        A Request object containing user data submitted by HEDTools.
        Keys include "hed_strings", "check_for_warnings", and "hed_xml_file"

    Returns
    -------
    string
        A serialized JSON string containing information related to the hed strings validation result.
        If the validation fails then a 500 error message is returned.
    """
    validation_status = {}

    # Parse uploaded data
    form_data = request.form
    check_for_warnings = form_data["check_for_warnings"] == '1' if "check_for_warnings" in form_data else False
    # if hed_xml_file was submitted, it's accessed by request.files, otherwise empty
    if "hed-xml-file" in request.files and get_file_extension(request.files["hed-xml-file"].filename) == "xml":
        hed_xml_file = save_file_to_upload_folder(request.files["hed-xml-file"])
    else:
        hed_xml_file = ''

    try:
        # parse hed_strings from json
        hed_strings = json.loads(form_data["hed-strings"])
        # hed_strings is a list of HED strings associated with events in EEG.event (order preserved)
        hed_input_reader = HedValidator(hed_strings, check_for_warnings=check_for_warnings, hed_xml_file=hed_xml_file)
        # issues is a list of lists. Element list is empty if no error,
        # else is a list of dictionaries, each dictionary contains an error-message key-value pair
        issues = hed_input_reader.get_validation_issues()

        # Prepare response
        validation_status["issues"] = issues
    except:
        validation_status[error_constants.ERROR_KEY] = traceback.format_exc()
    finally:
        delete_file_if_it_exists(hed_xml_file)

    return validation_status


def report_dictionary_validation_status(form_request_object):
    """Reports the spreadsheet validation status.

    Parameters
    ----------
    form_request_object: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """
    input_arguments = []
    try:
        input_arguments = generate_arguments_from_dictionary_form(form_request_object)
        issues = validate_dictionary(input_arguments)
        if issues:
            display_name = input_arguments.get(common_constants.JSON_FILE, '')
            issue_str = get_printable_issue_string(issues, display_name, 'HED validation errors for ')
            file_name = generate_filename(display_name, suffix='validation_errors', extension='.txt')
            issue_file = save_text_to_upload_folder(issue_str, file_name)
            download_response = generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                                                msg='JSON dictionary had validation errors')
            if isinstance(download_response, str):
                return handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
            return download_response
    except HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except Exception as e:
        return "Unexpected processing error: " + str(e)
    finally:
        delete_file_if_it_exists(input_arguments.get(common_constants.JSON_PATH, ''))
    return ""


def validate_dictionary(input_arguments, hed_schema=None):
    """Validates the dictionary and returns a

    Parameters
    ----------
    input_arguments: dict
        Dictionary containing standard input form arguments
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    display_name: str
        Display filename for showing in messages

    Returns
    -------
    str
        Text blob containing the issues or empty if none.
    """

    json_dictionary = ColumnDefGroup(input_arguments.get(common_constants.JSON_PATH, ''))
    if not hed_schema:
        hed_schema = HedSchema(input_arguments.get(common_constants.HED_XML_FILE, ''))
    return json_dictionary.validate_entries(hed_schema)
