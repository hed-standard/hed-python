
from urllib.error import URLError, HTTPError
from flask import current_app

from hed.util.file_util import delete_file_if_it_exists
from hed.validator.hed_validator import HedValidator
from hed.schema import hed_schema_file

from hed.web.constants import common_constants, error_constants, file_constants
from hed.web.dictionary import validate_dictionary
from hed.web.spreadsheet import validate_spreadsheet
from hed.web.web_utils import get_hed_path_from_pull_down, get_uploaded_file_path_from_form, get_optional_form_field

app_config = current_app.config


def generate_input_from_events_form(request):
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
    uploaded_events_name, original_events_name = \
        get_uploaded_file_path_from_form(request, common_constants.SPREADSHEET_FILE,
                                         file_constants.SPREADSHEET_FILE_EXTENSIONS)

    uploaded_json_name, original_json_name = \
        get_uploaded_file_path_from_form(request, common_constants.JSON_FILE,
                                         file_constants.DICTIONARY_FILE_EXTENSIONS)

    input_arguments = {
        common_constants.HED_XML_FILE: hed_file_path,
        common_constants.HED_DISPLAY_NAME: hed_display_name,
        common_constants.SPREADSHEET_PATH: uploaded_events_name,
        common_constants.SPREADSHEET_FILE: original_events_name,
        common_constants.JSON_PATH: uploaded_json_name,
        common_constants.JSON_FILE: original_json_name,
        common_constants.WORKSHEET_NAME: get_optional_form_field(request, common_constants.WORKSHEET_NAME,
                                                                 common_constants.STRING),
        common_constants.HAS_COLUMN_NAMES: get_optional_form_field(request,
                                                                   common_constants.HAS_COLUMN_NAMES,
                                                                   common_constants.BOOLEAN),
        common_constants.CHECK_FOR_WARNINGS: get_optional_form_field(request,
                                                                     common_constants.CHECK_FOR_WARNINGS,
                                                                     common_constants.BOOLEAN)
    }
    return input_arguments


def report_events_validation_status(request):
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
        input_arguments = generate_input_from_events_form(request)
        hed_schema = hed_schema_file.load_schema(input_arguments.get(common_constants.HED_XML_FILE, ''))
        download_response = validate_dictionary(input_arguments, hed_schema=hed_schema)
        if download_response:
            return download_response
        hed_validator = HedValidator(hed_schema=hed_schema,
                                     check_for_warnings=input_arguments.get(common_constants.CHECK_FOR_WARNINGS, False))
        download_response = validate_spreadsheet(input_arguments, hed_validator)
        if download_response:
            return download_response
    except HTTPError:
        return error_constants.NO_URL_CONNECTION_ERROR
    except URLError:
        return error_constants.INVALID_URL_ERROR
    except Exception as e:
        return "Unexpected processing error: " + str(e)
    finally:
        delete_file_if_it_exists(input_arguments.get(common_constants.SPREADSHEET_PATH, ''))
        delete_file_if_it_exists(input_arguments.get(common_constants.JSON_PATH, ''))
    return ""
