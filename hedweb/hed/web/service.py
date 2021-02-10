import json
import traceback
from urllib.error import URLError, HTTPError
from flask import current_app

from hed.util.file_util import get_file_extension, delete_file_if_it_exists
from hed.validator.hed_validator import HedValidator
from hed.util.hed_file_input import HedFileInput

from hed.web.constants import common_constants, error_constants, file_constants
from hed.web.web_utils import convert_number_str_to_list, generate_filename, get_printable_issue_string, \
    generate_download_file_response, get_hed_path_from_pull_down, get_uploaded_file_path_from_form, \
    handle_http_error, save_file_to_upload_folder, save_text_to_upload_folder
from hed.web import utils

app_config = current_app.config


def generate_arguments_from_form(request):
    """Gets the input arguments from a request object associated with a service.

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

    input_arguments = { }
    #     common_constants.HED_VERSION:  form_data = request.form,
    #     common_constants.HED_DISPLAY_NAME: hed_display_name,
    #
    #
    #     common_constants.CHECK_FOR_WARNINGS:
    #         utils.get_optional_form_field(request, common_constants.CHECK_FOR_WARNINGS,
    #                                       common_constants.BOOLEAN)
    # }
    return input_arguments


def report_service_status(request):
    """
    Reports validation status of hed strings associated with EEG events received from EEGLAB plugin HEDTools

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
