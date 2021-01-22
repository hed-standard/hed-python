import json
import traceback
from urllib.error import URLError, HTTPError
from flask import current_app
from werkzeug.utils import secure_filename

from hed.util.file_util import get_file_extension, delete_file_if_it_exists
from hed.validator.hed_validator import HedValidator
from hed.util.hed_file_input import HedFileInput

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
        web_utils.get_uploaded_file_path_from_form(form_request_object, common_constants.SPREADSHEET_FILE,
                                                   file_constants.SPREADSHEET_FILE_EXTENSIONS)

    validation_input_arguments = {common_constants.HED_XML_FILE: hed_file_path,
                                  common_constants.HED_DISPLAY_NAME: hed_display_name,
                                  common_constants.SPREADSHEET_PATH: uploaded_file_name,
                                  common_constants.SPREADSHEET_FILE: original_file_name}
    validation_input_arguments[common_constants.TAG_COLUMNS] = \
        web_utils.convert_number_str_to_list(form_request_object.form[common_constants.TAG_COLUMNS])
    validation_input_arguments[common_constants.COLUMN_PREFIX_DICTIONARY] = \
        utils.get_specific_tag_columns_from_form(form_request_object)
    validation_input_arguments[common_constants.WORKSHEET_NAME] = \
        utils.get_optional_form_field(form_request_object, common_constants.WORKSHEET_NAME,
                                      common_constants.STRING)
    validation_input_arguments[common_constants.HAS_COLUMN_NAMES] = utils.get_optional_form_field(
        form_request_object, common_constants.HAS_COLUMN_NAMES, common_constants.BOOLEAN)
    validation_input_arguments[common_constants.CHECK_FOR_WARNINGS] = utils.get_optional_form_field(
        form_request_object, common_constants.CHECK_FOR_WARNINGS, common_constants.BOOLEAN)
    return validation_input_arguments


def report_eeg_events_validation_status(request):
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
        delete_file_if_it_exists(hed_xml_file)

    return validation_status


def report_spreadsheet_validation_status(form_request_object):
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
        hed_validator = validate_spreadsheet(input_arguments)
        validation_issues = hed_validator.get_validation_issues()
        if validation_issues:
            issues_filename = web_utils.generate_issues_filename(common_constants.VALIDATION_OUTPUT_FILE_PREFIX,
                                                                 input_arguments[common_constants.SPREADSHEET_FILE],
                                                                 input_arguments[common_constants.WORKSHEET_NAME])
            issue_file = web_utils.save_issues_to_upload_folder(validation_issues, issues_filename)
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
        delete_file_if_it_exists(input_arguments.get(common_constants.SPREADSHEET_PATH, ''))
    return ""


def validate_spreadsheet(validation_arguments):
    """Validates the spreadsheet.

    Parameters
    ----------
    validation_arguments: dictionary
        A dictionary containing the arguments for the validation function.

    Returns
    -------
    HedValidator object
        A HedValidator object containing the validation results.
    """

    file_input_object = HedFileInput(validation_arguments[common_constants.SPREADSHEET_PATH],
                                     worksheet_name=validation_arguments[common_constants.WORKSHEET_NAME],
                                     tag_columns=validation_arguments[common_constants.TAG_COLUMNS],
                                     has_column_names=validation_arguments[common_constants.HAS_COLUMN_NAMES],
                                     column_prefix_dictionary=validation_arguments[
                                         common_constants.COLUMN_PREFIX_DICTIONARY])

    return HedValidator(file_input_object,
                        check_for_warnings=validation_arguments[common_constants.CHECK_FOR_WARNINGS],
                        hed_xml_file=validation_arguments[common_constants.HED_XML_FILE])
