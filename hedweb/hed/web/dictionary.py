import os
from flask import current_app

from hed.util.column_def_group import ColumnDefGroup
from hed.util.error_reporter import ErrorHandler, get_printable_issue_string
from hed.util.error_types import ErrorSeverity
from hed.util.exceptions import HedFileError
from hed.schema.hed_schema_file import load_schema
from hed.tools.tag_format import TagFormat
from hed.web.constants import common, file_constants
from hed.web.web_utils import form_has_option, generate_filename, generate_download_file_response, \
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
    uploaded_file_name, original_file_name = \
        get_uploaded_file_path_from_form(request, common.JSON_FILE, file_constants.DICTIONARY_FILE_EXTENSIONS)

    input_arguments = {
        common.HED_XML_FILE: hed_file_path,
        common.HED_DISPLAY_NAME: hed_display_name,
        common.JSON_PATH: uploaded_file_name,
        common.JSON_FILE: original_file_name,
    }
    if form_has_option(request, common.HED_OPTION, common.HED_OPTION_VALIDATE):
        input_arguments[common.HED_OPTION_VALIDATE] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_SHORT):
        input_arguments[common.HED_OPTION_TO_SHORT] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_LONG):
        input_arguments[common.HED_OPTION_TO_LONG] = True

    return input_arguments


def dictionary_process(input_arguments):
    """Perform the requested action for the dictionary.

    Parameters
    ----------
    input_arguments: dict
        A dictionary with the input arguments from the dictionary form

    Returns
    -------
      Response
        Downloadable response object.
    """

    if not input_arguments[common.JSON_PATH]:
        raise HedFileError('EmptyDictionaryFile', "Please upload a dictionary to process", "")
    if input_arguments.get(common.HED_OPTION_VALIDATE, None):
        return dictionary_validate(input_arguments)
    elif input_arguments.get(common.HED_OPTION_TO_SHORT, None):
        return dictionary_convert(input_arguments, short_to_long=False)
    elif input_arguments.get(common.HED_OPTION_TO_LONG, None):
        return dictionary_convert(input_arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a dictionary processing method", "")


def dictionary_convert(input_arguments, short_to_long=True,  hed_schema=None):
    """Converts a hedstring from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    input_arguments: dict
        Dictionary containing standard input form arguments
    short_to_long: bool
        If True convert the dictionary to long form, otherwise convert to short form
    hed_schema:str or HedSchema
        Version number or path or HedSchema object to be used

    Returns
    -------
    Response
        A downloadable dictionary file
    """

    json_dictionary = ColumnDefGroup(input_arguments.get(common.JSON_PATH, ''))

    if not hed_schema:
        hed_schema = load_schema(input_arguments.get(common.HED_XML_FILE, ''))
    error_handler = ErrorHandler()
    tag_formatter = TagFormat(hed_schema=hed_schema, error_handler=error_handler)
    issues = []
    for column_def in json_dictionary:
        for hed_string, position in column_def.hed_string_iter(include_position=True):
            if short_to_long:
                new_hed_string, errors = tag_formatter.convert_hed_string_to_long(hed_string)
            else:
                new_hed_string, errors = tag_formatter.convert_hed_string_to_short(hed_string)
            issues = issues + errors
            column_def.set_hed_string(new_hed_string, position)
    if short_to_long:
        suffix = '_to_long'
    else:
        suffix = '_to_short'
    issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
    display_name = input_arguments.get(common.JSON_FILE, '')
    if issues:
        display_name = input_arguments.get(common.JSON_FILE, '')
        issue_str = get_printable_issue_string(issues, f"JSON conversion for {display_name} was unsuccessful")
        file_name = generate_filename(display_name, suffix=f"{suffix}_conversion_errors", extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                               msg='JSON dictionary had conversion errors')
    else:
        file_name = generate_filename(display_name, suffix=suffix, extension='.json')
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_name)
        json_dictionary.save_as_json(file_path)
        return generate_download_file_response(file_path, display_name=file_name, category='success',
                                               msg='JSON dictionary was successfully converted')


def dictionary_validate(input_arguments, hed_schema=None):
    """ Validates the dictionary and returns a response or a printable string depending on return_response value

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
