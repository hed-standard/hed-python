from flask import current_app
from werkzeug import Response
import pandas as pd

from hed.schema.hed_schema_file import load_schema
from hed.util.column_def_group import ColumnDefGroup
from hed.util.error_reporter import get_printable_issue_string
from hed.util.event_file_input import EventFileInput
from hed.util.exceptions import HedFileError
from hed.validator.hed_validator import HedValidator
from hedweb.constants import common, file_constants

from hedweb.web_utils import form_has_option, generate_download_file_response,\
    generate_filename, generate_text_response, \
    get_hed_path_from_pull_down, get_uploaded_file_path_from_form, save_text_to_upload_folder
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

    arguments = {
        common.HED_XML_FILE: hed_file_path,
        common.HED_DISPLAY_NAME: hed_display_name,
        common.EVENTS_PATH: uploaded_events_path,
        common.EVENTS_FILE: original_events_name,
        common.JSON_PATH: uploaded_json_name,
        common.JSON_FILE: original_json_name,
    }
    if form_has_option(request, common.HED_OPTION, common.HED_OPTION_VALIDATE):
        arguments[common.HED_OPTION_VALIDATE] = True
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_ASSEMBLE):
        arguments[common.HED_OPTION_ASSEMBLE] = True
    return arguments


def events_process(arguments):
    """Perform the requested action for the dictionary.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the dictionary form

    Returns
    -------
      Response
        Downloadable response object.
    """

    if not arguments[common.EVENTS_PATH]:
        raise HedFileError('EmptyEventsFile', "Please upload an events file to process", "")
    if arguments.get(common.HED_OPTION_VALIDATE, None):
        return events_validate(arguments)
    elif arguments.get(common.HED_OPTION_ASSEMBLE, None):
        return events_assemble(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select an events file processing method", "")


def events_assemble(arguments, hed_schema=None):
    """Converts an events file from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments
    hed_schema:str or HedSchema
        Version number or path or HedSchema object to be used

    Returns
    -------
    Response
        A downloadable spreadsheet file or a file containing warnings
    """

    if not hed_schema:
        hed_schema = load_schema(arguments.get(common.HED_XML_FILE, ''))

    results = events_validate(arguments, hed_schema)
    if results.data:
        return results

    if arguments.get(common.JSON_PATH, ''):  # If dictionary is provided and it has errors return those errors
        json_sidecar = ColumnDefGroup(arguments.get(common.JSON_PATH, ''))
        def_dict = json_sidecar.extract_defs(hed_schema)
    else:
        json_sidecar = None
        def_dict = None
    event_file = EventFileInput(arguments.get(common.EVENTS_PATH),
                                json_def_files=json_sidecar, hed_schema=hed_schema, def_dicts=def_dict)
    hed_tags = []
    onsets = []
    for row_number, row_dict in event_file.parse_dataframe(return_row_dict=True):
        hed_tags.append(row_dict.get("HED", "").hed_string)
        onsets.append(row_dict.get("onset", "n/a"))
    data = {'onset': onsets, 'HED': hed_tags}
    df = pd.DataFrame(data)
    file_name = generate_filename(common.EVENTS_FILE, suffix='_expanded', extension='.tsv')
    df.to_csv(file_name, '\t', index=False, header=True)
    return generate_download_file_response(file_name, display_name=file_name, category='success',
                                           msg='Events file successfully expanded')


def events_validate(arguments, hed_schema=None):
    """Reports the spreadsheet validation status.

    Parameters
    ----------
    arguments: dict
        A dictionary of the values extracted from the form
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used

    Returns
    -------
    Response
         The validation results as a Response object
    """
    if not hed_schema:
        hed_schema = load_schema(arguments.get(common.HED_XML_FILE, ''))
    json_sidecar = None
    def_dict = None
    if arguments.get(common.JSON_PATH, ''):  # If dictionary is provided and it has errors return those errors
        json_sidecar = ColumnDefGroup(arguments.get(common.JSON_PATH, ''))
        def_dict, issues = json_sidecar.extract_defs(hed_schema)
        if issues:
            issue_str = get_printable_issue_string(issues, f"{common.JSON_FILE} HED dictionary errors")
            file_name = generate_filename(common.JSON_FILE, suffix='_dictionary_errors', extension='.txt')
            issue_file = save_text_to_upload_folder(issue_str, file_name)
            return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                                   msg='JSON sidecar had dictionary errors')
        issues = json_sidecar.validate_entries(hed_schema)
        if issues:
            issue_str = get_printable_issue_string(issues, f"{common.JSON_FILE} HED validation errors")
            file_name = generate_filename(common.JSON_FILE, suffix='_validation_errors', extension='.txt')
            issue_file = save_text_to_upload_folder(issue_str, file_name)
            return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                                   msg='JSON dictionary had validation errors')

    input_file = EventFileInput(arguments.get(common.EVENTS_PATH),
                                json_def_files=json_sidecar, hed_schema=hed_schema, def_dicts=def_dict)
    validator = HedValidator(hed_schema=hed_schema)
    issues = validator.validate_input(input_file)
    if issues:
        display_name = arguments.get(common.EVENTS_FILE, None)
        issue_str = get_printable_issue_string(issues, f"{display_name} HED validation errors")

        file_name = generate_filename(display_name, suffix='_validation_errors', extension='.txt')
        issue_file = save_text_to_upload_folder(issue_str, file_name)
        return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                               msg='Events file had validation errors')
    else:
        return generate_text_response("", msg='Events file had no validation errors')
