from flask import current_app

from hed.util.column_def_group import ColumnDefGroup
from hed.util.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_file import load_schema
from hed.web.constants import common, file_constants
from hed.web.web_utils import generate_filename, generate_download_file_response, \
    generate_text_response, get_hed_path_from_pull_down, \
    get_uploaded_file_path_from_form, save_text_to_upload_folder, get_optional_form_field

app_config = current_app.config


def generate_input_from_dictionary_form(request):
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
    uploaded_file_name, original_file_name = get_uploaded_file_path_from_form(request, common.JSON_FILE,
                                                                              file_constants.DICTIONARY_FILE_EXTENSIONS)

    input_arguments = {
        common.HED_XML_FILE: hed_file_path,
        common.HED_DISPLAY_NAME: hed_display_name,
        common.JSON_PATH: uploaded_file_name,
        common.JSON_FILE: original_file_name,
        common.CHECK_FOR_WARNINGS: get_optional_form_field(request, common.CHECK_FOR_WARNINGS, common.BOOLEAN)
    }
    return input_arguments


def dictionary_validate(input_arguments, hed_schema=None):
    """Validates the dictionary and returns a response or a printable string depending on return_response value

    Parameters
    ----------
    input_arguments: dict
        Dictionary containing standard input form arguments
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used

    Returns
    -------
    Response
        Response object containing the results of the dictionary validation.
    """

    json_dictionary = ColumnDefGroup(input_arguments.get(common.JSON_PATH, ''))
    if not hed_schema:
        hed_schema = load_schema(input_arguments.get(common.HED_XML_FILE, ''))
    issues = json_dictionary.validate_entries(hed_schema)
    if issues:
        display_name = input_arguments.get(common.JSON_FILE, '')
        issue_str = get_printable_issue_string(issues, f"HED validation errors for {display_name}")
        file_name = generate_filename(display_name, suffix='validation_errors', extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                               msg='JSON dictionary had validation errors')
    else:
        return generate_text_response("", msg='JSON dictionary had no validation errors')
