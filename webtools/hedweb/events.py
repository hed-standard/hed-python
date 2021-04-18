from flask import current_app

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
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_TAGGED_LIST):
        arguments[common.HED_OPTION_TO_SHORT] = True
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
    elif arguments.get(common.HED_OPTION_TO_TAGGED_LIST, None):
        return events_convert(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select an events file processing method", "")


def events_convert(arguments, hed_schema=None):
    """Converts an events file into a tagged event list

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

    return generate_text_response('Not available', category='warning', msg='Spreadsheet conversion not implemented yet')
    #
    # if not hed_schema:
    #     hed_schema = load_schema(arguments.get(common.HED_XML_FILE, ''))
    # error_handler = ErrorHandler()
    # tag_formatter = TagFormat(hed_schema=hed_schema, error_handler=error_handler)
    # issues = []
    # for column_def in json_dictionary:
    #     for hed_string, position in column_def.hed_string_iter(include_position=True):
    #         if short_to_long:
    #             new_hed_string, errors = tag_formatter.convert_hed_string_to_long(hed_string)
    #         else:
    #             new_hed_string, errors = tag_formatter.convert_hed_string_to_short(hed_string)
    #         issues = issues + errors
    #         column_def.set_hed_string(new_hed_string, position)
    # if short_to_long:
    #     suffix = '_to_long'
    # else:
    #     suffix = '_to_short'
    # issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
    # display_name = arguments.get(common.JSON_FILE, '')
    # if issues:
    #     display_name = arguments.get(common.JSON_FILE, '')
    #     issue_str = get_printable_issue_string(issues, f"JSON conversion for {display_name} was unsuccessful")
    #     file_name = generate_filename(display_name, suffix=f"{suffix}_conversion_errors", extension='.txt')
    #     issue_file = save_text_to_upload_folder(issue_str, file_name)
    #     return generate_download_file_response(issue_file, display_name=file_name, category='warning',
    #                                            msg='JSON dictionary had conversion errors')
    # else:
    #     file_name = generate_filename(display_name, suffix=suffix, extension='.json')
    #     file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_name)
    #     json_dictionary.save_as_json(file_path)
    #     return generate_download_file_response(file_path, display_name=file_name, category='success',
    #                                            msg='JSON dictionary was successfully converted')


def events_validate(arguments):
    """Reports the spreadsheet validation status.

    Parameters
    ----------
    arguments: dict
        A dictionary of the values extracted from the form

    Returns
    -------
    Response
         The validation results as a Response object
    """

    hed_schema = load_schema(arguments.get(common.HED_XML_FILE, ''))
    json_sidecar = None
    if arguments.get(common.JSON_PATH, ''):  # If dictionary is provided and it has errors return those errors
        json_sidecar = ColumnDefGroup(arguments.get(common.JSON_PATH, ''))
        issues = json_sidecar.validate_entries(hed_schema)
        if issues:
            issue_str = get_printable_issue_string(issues, f"{common.JSON_FILE} HED validation errors")
            file_name = generate_filename(common.JSON_FILE, suffix='_validation_errors', extension='.txt')
            issue_file = save_text_to_upload_folder(issue_str, file_name)
            return generate_download_file_response(issue_file, display_name=file_name, category='warning',
                                                   msg='JSON dictionary had validation errors')

    input_file = EventFileInput(arguments.get(common.EVENTS_PATH),
                                json_def_files=json_sidecar, hed_schema=hed_schema)
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
