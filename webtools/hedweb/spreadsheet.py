import os
from flask import current_app
from werkzeug.utils import secure_filename
from hed import models
from hed import schema as hedschema
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError
from hed.validator.hed_validator import HedValidator
from hed.util.file_util import get_file_extension

from hedweb.constants import base_constants, file_constants
from hedweb.columns import get_prefix_dict
from hedweb.web_utils import form_has_option, get_hed_schema_from_pull_down, generate_filename


app_config = current_app.config


def get_input_from_form(request):
    """Gets input argument dictionary from the spreadsheet form request.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the spreadsheet form.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying spreadsheet functions
    """
    arguments = {
        base_constants.SCHEMA: get_hed_schema_from_pull_down(request),
        base_constants.SPREADSHEET: None,
        base_constants.SPREADSHEET_TYPE: file_constants.TSV_EXTENSION,
        base_constants.WORKSHEET_NAME: request.form.get(base_constants.WORKSHEET_SELECTED, None),
        base_constants.COMMAND: request.form.get(base_constants.COMMAND_OPTION, ''),
        base_constants.HAS_COLUMN_NAMES: form_has_option(request, base_constants.HAS_COLUMN_NAMES, 'on'),
        base_constants.CHECK_FOR_WARNINGS: form_has_option(request, base_constants.CHECK_FOR_WARNINGS, 'on'),
    }

    tag_columns, prefix_dict = get_prefix_dict(request.form)
    filename = request.files[base_constants.SPREADSHEET_FILE].filename
    file_ext = get_file_extension(filename)
    if file_ext in file_constants.EXCEL_FILE_EXTENSIONS:
        arguments[base_constants.SPREADSHEET_TYPE] = file_constants.EXCEL_EXTENSION
    spreadsheet = models.HedInput(file=request.files[base_constants.SPREADSHEET_FILE],
                                  file_type=arguments[base_constants.SPREADSHEET_TYPE],
                                  worksheet_name=arguments.get(base_constants.WORKSHEET_NAME, None),
                                  tag_columns=tag_columns,
                                  has_column_names=arguments.get(base_constants.HAS_COLUMN_NAMES, None),
                                  column_prefix_dictionary=prefix_dict,
                                  name=filename)
    arguments[base_constants.SPREADSHEET] = spreadsheet
    return arguments


def process(arguments):
    """Perform the requested action for the spreadsheet.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the spreadsheet form.

    Returns
    -------
      dict
        A dictionary of results from spreadsheet processing in standard form.
    """
    hed_schema = arguments.get('schema', None)
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema", "")
    spreadsheet = arguments.get(base_constants.SPREADSHEET, 'None')
    if not spreadsheet or not isinstance(spreadsheet, models.HedInput):
        raise HedFileError('InvalidSpreadsheet', "An spreadsheet was given but could not be processed", "")

    command = arguments.get(base_constants.COMMAND, None)
    check_for_warnings = arguments.get(base_constants.CHECK_FOR_WARNINGS, False)
    if command == base_constants.COMMAND_VALIDATE:
        results = spreadsheet_validate(hed_schema, spreadsheet, check_for_warnings=check_for_warnings)
    elif command == base_constants.COMMAND_TO_SHORT:
        results = spreadsheet_convert(hed_schema, spreadsheet, command, check_for_warnings=check_for_warnings)
    elif command == base_constants.COMMAND_TO_LONG:
        results = spreadsheet_convert(hed_schema, spreadsheet, command, check_for_warnings=check_for_warnings)
    else:
        raise HedFileError('UnknownSpreadsheetProcessingMethod', f"Command {command} is missing or invalid", "")
    return results


def spreadsheet_convert(hed_schema, spreadsheet, command=base_constants.COMMAND_TO_LONG, check_for_warnings=False):
    """Converts a spreadsheet long to short unless unless the command is not COMMAND_TO_LONG then converts to short

    Parameters
    ----------
    hed_schema:HedSchema
        HedSchema object to be used
    spreadsheet: HedInput
        Previously created HedInput object
    command: str
        Name of the command to execute if not COMMAND_TO_LONG
    check_for_warnings: bool
        If True, check for war


    Returns
    -------
    dict
        A downloadable dictionary file or a file containing warnings
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    results = spreadsheet_validate(hed_schema, spreadsheet, check_for_warnings=check_for_warnings)
    if results['data']:
        return results

    display_name = spreadsheet.name
    display_ext = os.path.splitext(secure_filename(display_name))[1]

    if command == base_constants.COMMAND_TO_LONG:
        suffix = '_to_long'
        spreadsheet.convert_to_long(hed_schema)
    else:
        suffix = '_to_short'
        spreadsheet.convert_to_short(hed_schema)

    file_name = generate_filename(display_name, suffix=suffix, extension=display_ext)
    return {base_constants.COMMAND: command, 'data': '',
            base_constants.SPREADSHEET: spreadsheet, 'output_display_name': file_name,
            base_constants.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
            'msg': f'Spreadsheet {display_name} converted_successfully'}


def spreadsheet_validate(hed_schema, spreadsheet, check_for_warnings=False):
    """ Validates the spreadsheet.

    Parameters
    ----------
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    spreadsheet: HedFileInput
        Spreadsheet input object to be validated
    check_for_warnings: bool
        Indicates whether validation should check for warnings as well as errors

    Returns
    -------
    dict
         A dictionary containing results of validation in standard format
    """
    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    validator = HedValidator(hed_schema=hed_schema)
    issues = spreadsheet.validate_file(validator, check_for_warnings=check_for_warnings)
    display_name = spreadsheet.name
    if issues:
        issue_str = get_printable_issue_string(issues, f"Spreadsheet {display_name} validation errors")
        file_name = generate_filename(display_name, suffix='_validation_errors', extension='.txt')
        return {base_constants.COMMAND: base_constants.COMMAND_VALIDATE,
                'data': issue_str, "output_display_name": file_name,
                base_constants.SCHEMA_VERSION: schema_version, "msg_category": "warning",
                'msg': f"Spreadsheet {display_name} had validation errors"}
    else:
        return {base_constants.COMMAND: base_constants.COMMAND_VALIDATE, 'data': '',
                base_constants.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': f'Spreadsheet {display_name} had no validation errors'}
