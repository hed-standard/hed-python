
from urllib.error import URLError, HTTPError
from flask import current_app

from hed.util.file_util import delete_file_if_it_exists
from hed.validator.hed_validator import HedValidator
from hed.util.event_file_input import EventFileInput
from hed.util.column_def_group import ColumnDefGroup
from hed.util.hed_schema import HedSchema

from hed.web.constants import common_constants, error_constants, file_constants
from hed.web.web_utils import generate_issues_filename, generate_download_file_response, \
    get_hed_path_from_pull_down, get_uploaded_file_path_from_form, handle_http_error, \
    save_issues_to_upload_folder
from hed.web.utils import get_optional_form_field

app_config = current_app.config


def generate_arguments_from_events_form(form_request_object):
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
    uploaded_events_name, original_events_name = \
        get_uploaded_file_path_from_form(form_request_object, common_constants.SPREADSHEET_FILE,
                                         file_constants.SPREADSHEET_FILE_EXTENSIONS)

    uploaded_json_name, original_json_name = \
        get_uploaded_file_path_from_form(form_request_object, common_constants.JSON_FILE,
                                         file_constants.DICTIONARY_FILE_EXTENSIONS)

    input_arguments = {common_constants.HED_XML_FILE: hed_file_path,
                       common_constants.HED_DISPLAY_NAME: hed_display_name,
                       common_constants.SPREADSHEET_PATH: uploaded_events_name,
                       common_constants.SPREADSHEET_FILE: original_events_name,
                       common_constants.JSON_PATH: uploaded_json_name,
                       common_constants.JSON_FILE: original_json_name}
    input_arguments[common_constants.WORKSHEET_NAME] = \
        get_optional_form_field(form_request_object, common_constants.WORKSHEET_NAME, common_constants.STRING)
    input_arguments[common_constants.HAS_COLUMN_NAMES] = \
        get_optional_form_field(form_request_object, common_constants.HAS_COLUMN_NAMES, common_constants.BOOLEAN)
    input_arguments[common_constants.CHECK_FOR_WARNINGS] = \
        get_optional_form_field(form_request_object, common_constants.CHECK_FOR_WARNINGS, common_constants.BOOLEAN)
    return input_arguments


def report_events_validation_status(form_request_object):
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
        input_arguments = generate_arguments_from_events_form(form_request_object)
        validation_issues = validate_events(input_arguments)
        if validation_issues:
            issues_filename = \
                generate_issues_filename(input_arguments.get(common_constants.SPREADSHEET_FILE, ''),
                                         common_constants.VALIDATION_OUTPUT_FILE_PREFIX,
                                         input_arguments.get(common_constants.WORKSHEET_NAME, ''))

            issue_file = save_issues_to_upload_folder(validation_issues, issues_filename)
            download_response = generate_download_file_response(issue_file)
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
        delete_file_if_it_exists(input_arguments.get(common_constants.SPREADSHEET_PATH, ''))
    return ""


def validate_events(validation_arguments):
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

    schema = HedSchema(validation_arguments.get(common_constants.HED_XML_FILE, ''))
    worksheet = validation_arguments.get(common_constants.WORKSHEET_NAME, '')
    spreadsheet = validation_arguments.get(common_constants.SPREADSHEET_PATH, '')
    json = validation_arguments.get(common_constants.JSON_PATH, '')
    issue_list = []
    if json:
        json_def = ColumnDefGroup(json)
        display_name = validation_arguments.get(common_constants.JSON_FILE, '')
        json_issues = json_def.validate_entries(hed_schema=schema, display_filename=display_name)
        if json_issues:
            issue_list = issue_list + json_issues
    else:
        json_def = None
    if spreadsheet:
        input_object = EventFileInput(spreadsheet, worksheet_name=worksheet, json_def_files=json_def, hed_schema=schema)
        validator = HedValidator(input_object, hed_schema=schema,
                                 check_for_warnings=validation_arguments.get(common_constants.CHECK_FOR_WARNINGS, False))
        spreadsheet_issues = validator.get_validation_issues()
        if spreadsheet_issues:
            issue_list = issue_list + spreadsheet_issues
    return issue_list
