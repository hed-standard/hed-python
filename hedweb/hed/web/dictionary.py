import json
import os
import traceback
from urllib.error import URLError, HTTPError
from flask import current_app
from werkzeug.utils import secure_filename

from hed.util.file_util import get_file_extension, delete_file_if_it_exist
from hed.validator.hed_validator import HedValidator
from hed.util.column_def_group import ColumnDefGroup
from hed.util.hed_dictionary import HedDictionary

from hed.web.constants import common_constants, error_constants, file_constants
from hed.web import web_utils
from hed.web import utils

app_config = current_app.config


def generate_arguments_from_validation_form(form_request_object):
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
    hed_file_path, hed_display_name = web_utils.get_hed_path_from_pull_down(form_request_object)
    uploaded_file_name, original_file_name = \
        web_utils.get_uploaded_file_path_from_form(form_request_object, common_constants.DICTIONARY_FILE,
                                                   file_constants.DICTIONARY_FILE_EXTENSIONS)

    input_arguments = {common_constants.HED_XML_FILE: hed_file_path,
                       common_constants.HED_DISPLAY_NAME: hed_display_name,
                       common_constants.DICTIONARY_PATH: uploaded_file_name,
                       common_constants.DICTIONARY_FILE: original_file_name}
    input_arguments[common_constants.CHECK_FOR_WARNINGS] = utils.get_optional_form_field(
        form_request_object, common_constants.CHECK_FOR_WARNINGS, common_constants.BOOLEAN)
    return input_arguments


def generate_dictionary_validation_filename(dictionary_filename):
    """Generates a filename for the attachment that will contain the dictionary validation issues.

    Parameters
    ----------
    dictionary_filename: string
        The name of the dictionary file.

    Returns
    -------
    string
        The name of the attachment other containing the validation issues.
    """

    return common_constants.VALIDATION_OUTPUT_FILE_PREFIX + secure_filename(dictionary_filename).rsplit('.')[
        0] + file_constants.TEXT_EXTENSION


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
        hed_xml_file = web_utils.save_file_to_upload_folder(request.files["hed-xml-file"])
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
        delete_file_if_it_exist(hed_xml_file)

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
        input_arguments = generate_arguments_from_validation_form(form_request_object)
        def_group = validate_dictionary(input_arguments)
        validation_issues = def_group.get_validation_issues()
        if validation_issues:
            issue_file = save_issues_to_upload_folder(input_arguments[common_constants.DICTIONARY_FILE],
                                                      validation_issues)
            download_response = web_utils.generate_download_file_response(issue_file)
            if isinstance(download_response, str):
                return web_utils.handle_http_error(error_constants.NOT_FOUND_ERROR, download_response)
            return download_response
    except HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except Exception as e:
        return "Unexpected processing error: " + str(e)
    finally:
        delete_file_if_it_exist(input_arguments[common_constants.DICTIONARY_PATH])
        # delete_file_if_it_exist(input_arguments[common_constants.HED_XML_FILE])
    return ""


def save_issues_to_upload_folder(dictionary_filename, validation_issues, file_mode='w'):
    """Saves the validation issues found to a other in the upload folder.

    Parameters
    ----------
    dictionary_filename: str
        The name to the dictionary.
    validation_issues: dictionary
        A string containing the validation issues.
    file_mode: str
        Either 'w' to create a new file and write or 'a' to create a new file if necessary and append to end.
    Returns
    -------
    string
        The name of the validation output other.

    """
    validation_issues_filename = generate_dictionary_validation_filename(dictionary_filename)
    validation_issues_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], validation_issues_filename)
    with open(validation_issues_file_path, file_mode, encoding='utf-8') as validation_issues_file:
        for val_issue in validation_issues.values():
            for issue in val_issue:
                validation_issues_file.write(issue['message'] + "\n")
    validation_issues_file.close()
    return validation_issues_file_path


def validate_dictionary(validation_arguments):
    """Validates the dictionary.

    Parameters
    ----------
    validation_arguments: dictionary
        A dictionary containing the arguments for the validation function.

    Returns
    -------
    ColumnDefGroup
        Contains a representation of the JSON dictionary and validation issues.
    """

    json_dictionary = ColumnDefGroup(validation_arguments[common_constants.DICTIONARY_PATH])
    hed_dictionary = HedDictionary(validation_arguments[common_constants.HED_XML_FILE])
    json_dictionary.validate_entries(hed_dictionary)
    return json_dictionary
