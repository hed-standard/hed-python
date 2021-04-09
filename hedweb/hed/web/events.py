from flask import current_app

from hed.schema.hed_schema_file import load_schema
from hed.util.column_def_group import ColumnDefGroup
from hed.util.error_reporter import get_printable_issue_string
from hed.util.event_file_input import EventFileInput
from hed.validator.hed_validator import HedValidator
from hed.web.constants import common, file_constants

from hed.web.web_utils import generate_download_file_response, generate_filename, generate_text_response, \
    get_hed_path_from_pull_down, get_uploaded_file_path_from_form, get_optional_form_field, save_text_to_upload_folder
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
    uploaded_events_path, original_events_name = \
        get_uploaded_file_path_from_form(request, common.EVENTS_FILE, file_constants.TEXT_FILE_EXTENSIONS)
    uploaded_json_name, original_json_name = \
        get_uploaded_file_path_from_form(request, common.JSON_FILE, file_constants.DICTIONARY_FILE_EXTENSIONS)

    input_arguments = {
        common.HED_XML_FILE: hed_file_path,
        common.HED_DISPLAY_NAME: hed_display_name,
        common.EVENTS_PATH: uploaded_events_path,
        common.EVENTS_FILE: original_events_name,
        common.JSON_PATH: uploaded_json_name,
        common.JSON_FILE: original_json_name,
        common.HAS_COLUMN_NAMES: get_optional_form_field(request, common.HAS_COLUMN_NAMES, common.BOOLEAN),
        common.CHECK_FOR_WARNINGS: get_optional_form_field(request, common.CHECK_FOR_WARNINGS, common.BOOLEAN)
    }
    return input_arguments


def events_validate(input_arguments):
    """Reports the spreadsheet validation status.

    Parameters
    ----------
    input_arguments: dict
        A dictionary of the values extracted from the form

    Returns
    -------
    Response
         The validation results as a Response object
    """

    hed_schema = load_schema(input_arguments.get(common.HED_XML_FILE, ''))
    json_sidecar = None
    if input_arguments.get(common.JSON_PATH, ''):  # If dictionary is provided and it has errors return those errors
        json_sidecar = ColumnDefGroup(input_arguments.get(common.JSON_PATH, ''))
        issues = json_sidecar.validate_entries(hed_schema)
        if issues:
            issue_str = get_printable_issue_string(issues, f"{common.JSON_FILE} HED validation errors")
            file_name = generate_filename(common.JSON_FILE, suffix='_validation_errors', extension='.txt')
            issue_file = save_text_to_upload_folder(issue_str, file_name)
            return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                                   msg='JSON dictionary had validation errors')

    input_file = EventFileInput(input_arguments.get(common.EVENTS_PATH),
                                json_def_files=json_sidecar, hed_schema=hed_schema)
    validator = HedValidator(hed_schema=hed_schema,
                             check_for_warnings=input_arguments.get(common.CHECK_FOR_WARNINGS, False))
    issues = validator.validate_input(input_file)
    if issues:
        display_name = input_arguments.get(common.EVENTS_FILE, None)
        issue_str = get_printable_issue_string(issues, f"{display_name} HED validation errors")

        file_name = generate_filename(display_name, suffix='_validation_errors', extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                               msg='Events file had validation errors')
    else:
        return generate_text_response("", msg='Events file had no validation errors')
