from flask import current_app

from hed.util.error_reporter import get_printable_issue_string
from hed.util.exceptions import HedFileError

from hed.validator.hed_validator import HedValidator
from hedweb.constants import common, file_constants
from hedweb.web_utils import convert_number_str_to_list, form_has_option,\
    generate_filename, get_hed_schema, get_hed_path_from_pull_down, \
    get_spreadsheet, get_uploaded_file_path_from_form, get_optional_form_field, package_results
from hedweb.spreadsheet_utils import get_specific_tag_columns_from_form

app_config = current_app.config


def generate_input_from_spreadsheet_form(request):
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
    hed_file_path, schema_display_name = get_hed_path_from_pull_down(request)
    uploaded_file_name, original_file_name = \
        get_uploaded_file_path_from_form(request, common.SPREADSHEET_FILE, file_constants.SPREADSHEET_FILE_EXTENSIONS)

    arguments = {
        common.SCHEMA_PATH: hed_file_path,
        common.SCHEMA_DISPLAY_NAME: schema_display_name,
        common.SPREADSHEET_PATH: uploaded_file_name,
        common.SPREADSHEET_FILE: original_file_name,
        common.TAG_COLUMNS: convert_number_str_to_list(request.form[common.TAG_COLUMNS]),
        common.COLUMN_PREFIX_DICTIONARY: get_specific_tag_columns_from_form(request),
        common.WORKSHEET_SELECTED: get_optional_form_field(request, common.WORKSHEET_SELECTED, common.STRING),
        common.HAS_COLUMN_NAMES: get_optional_form_field(request, common.HAS_COLUMN_NAMES, common.BOOLEAN)
    }
    if form_has_option(request, common.COMMAND_OPTION, common.COMMAND_VALIDATE):
        arguments[common.COMMAND_VALIDATE] = True
    elif form_has_option(request, common.COMMAND_OPTION, common.COMMAND_TO_SHORT):
        arguments[common.COMMAND_TO_SHORT] = True
    elif form_has_option(request, common.COMMAND_OPTION, common.COMMAND_TO_LONG):
        arguments[common.COMMAND_TO_LONG] = True
    arguments[common.DEFS_EXPAND] = form_has_option(request, common.DEFS_EXPAND, 'on')
    arguments[common.CHECK_FOR_WARNINGS] = form_has_option(request, common.CHECK_FOR_WARNINGS, 'on')
    return arguments


def spreadsheet_process(arguments):
    """Perform the requested action for the spreadsheet.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the dictionary form

    Returns
    -------
      Response
        Downloadable response object.
    """

    if not arguments[common.SPREADSHEET_PATH]:
        raise HedFileError('EmptySpreadsheetFile', "Please upload a spreadsheet to process", "")
    if arguments.get(common.COMMAND_VALIDATE, None):
        results = spreadsheet_validate(arguments)
    elif arguments.get(common.COMMAND_TO_SHORT, None):
        results = spreadsheet_convert(arguments, short_to_long=False)
    elif arguments.get(common.COMMAND_TO_LONG, None):
        results = spreadsheet_convert(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a spreadsheet processing method", "")
    return package_results(results)


def spreadsheet_convert(arguments, short_to_long=True, hed_schema=None):
    """Converts a spreadsheet from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments
    short_to_long: bool
        If True convert the dictionary to long form, otherwise convert to short form
    hed_schema:str or HedSchema
        Version number or path or HedSchema object to be used

    Returns
    -------
    Response
        A downloadable spreadsheet file or a file containing warnings
    """
    if not hed_schema:
        hed_schema = get_hed_schema(arguments)
    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    return {'command': arguments.get('command', ''), 'data': '',
            'schema_version': schema_version, 'msg_category': 'warning',
            'msg': 'This convert command has not yet been implemented for spreadsheets'}


def spreadsheet_validate(arguments, hed_schema=None, spreadsheet=None):
    """ Validates the spreadsheet.

    Parameters
    ----------
    arguments: dictionary
        A dictionary containing the arguments for the validation function.
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    spreadsheet: HedFileInput
        Spreadsheet object
    Returns
    -------
    HedValidator object
        A HedValidator object containing the validation results.
    """
    if not hed_schema:
        hed_schema = get_hed_schema(arguments)
    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    if not spreadsheet:
        spreadsheet = get_spreadsheet(arguments)
    validator = HedValidator(check_for_warnings=arguments[common.CHECK_FOR_WARNINGS], hed_schema=hed_schema)
    issues = validator.validate_input(spreadsheet)
    if issues:
        display_name = arguments.get(common.SPREADSHEET_FILE, None)
        issue_str = get_printable_issue_string(issues, f"{display_name} HED validation errors")

        file_name = generate_filename(display_name, suffix='_validation_errors', extension='.txt')
        return {'command': arguments.get('command', ''), 'data': issue_str, "output_display_name": file_name,
                'schema_version': schema_version, "msg_category": "warning",
                'msg': "Spreadsheet file had validation errors"}
    else:
        return {'command': arguments.get('command', ''), 'data': '',
                'schema_version': schema_version, 'msg_category': 'success',
                'msg': 'Spreadsheet file had no validation errors'}
