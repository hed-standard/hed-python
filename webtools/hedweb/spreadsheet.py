from flask import current_app

from hed import models
from hed import schema as hedschema
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError
from hed.validator.event_validator import EventValidator

from hedweb.constants import common, file_constants
from hedweb.utils.web_utils import form_has_option, get_hed_schema_from_pull_down, get_uploaded_file_path_from_form
from hedweb.utils.io_utils import generate_filename, get_prefix_dict

app_config = current_app.config


def get_input_from_spreadsheet_form(request):
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
    arguments = {
        common.SCHEMA: get_hed_schema_from_pull_down(request),
        common.SPREADSHEET: None,
        common.COMMAND: request.values.get(common.COMMAND_OPTION, ''),
        common.HAS_COLUMN_NAMES: form_has_option(request, common.HAS_COLUMN_NAMES, 'on'),
        common.CHECK_FOR_WARNINGS: form_has_option(request, common.CHECK_FOR_WARNINGS, 'on'),
    }

    uploaded_file_name, original_file_name = \
        get_uploaded_file_path_from_form(request, common.SPREADSHEET_FILE, file_constants.SPREADSHEET_FILE_EXTENSIONS)
    tag_columns, prefix_dict = get_prefix_dict(request.form)
    spreadsheet = models.HedInput(uploaded_file_name,
                                  worksheet_name=arguments.get(common.WORKSHEET_SELECTED, None),
                                  tag_columns=tag_columns,
                                  has_column_names=arguments.get(common.HAS_COLUMN_NAMES, None),
                                  column_prefix_dictionary=prefix_dict,
                                  display_name=original_file_name)
    arguments[common.SPREADSHEET] = spreadsheet
    # arguments = { \
    #     common.SCHEMA: get_hed_schema_from_pull_down(request),
    #     common.SPREADSHEET: None,
    #     common.COMMAND = request.values.get(common.COMMAND_OPTION, ''),
    #     common.TAG_COLUMNS: convert_number_str_to_list(request.form[common.TAG_COLUMNS]),
    #     common.COLUMN_PREFIX_DICTIONARY: get_specific_tag_columns_from_form(request),
    #     common.WORKSHEET_SELECTED: get_optional_form_field(request, common.WORKSHEET_SELECTED, common.STRING),
    #     common.HAS_COLUMN_NAMES: get_optional_form_field(request, common.HAS_COLUMN_NAMES, common.BOOLEAN),
    #     common.CHECK_FOR_WARNINGS: form_has_option(request, common.CHECK_FOR_WARNINGS, 'on'),
    #     common.DEFS_EXPAND: form_has_option(request, common.DEFS_EXPAND, 'on')
    # }

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
    hed_schema = arguments.get('schema', None)
    command = arguments.get(common.COMMAND, None)
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema", "")
    spreadsheet = arguments.get(common.SPREADSHEET, 'None')
    if not spreadsheet or not isinstance(spreadsheet, models.HedInput):
        raise HedFileError('InvalidSpreadsheet', "An spreadsheet was given but could not be processed", "")

    if command == common.COMMAND_VALIDATE:
        results = spreadsheet_validate(hed_schema, spreadsheet)
    elif command == common.COMMAND_TO_SHORT:
        results = spreadsheet_convert(hed_schema, spreadsheet, command=common.COMMAND_TO_SHORT)
    elif command == common.COMMAND_TO_LONG:
        results = spreadsheet_convert(hed_schema, spreadsheet)
    else:
        raise HedFileError('UnknownSpreadsheetProcessingMethod', f"Command {command} is missing or invalid", "")
    return results


def spreadsheet_convert(hed_schema, spreadsheet, command=common.COMMAND_TO_LONG):
    """Converts a spreadsheet long to short unless unless the command is not COMMAND_TO_LONG then converts to short

    Parameters
    ----------
    hed_schema:HedSchema
        HedSchema object to be used
    spreadsheet: HedInput
        Previously created HedInput object
    command: str
        Name of the command to execute if not COMMAND_TO_LONG

    Returns
    -------
    dict
        A downloadable dictionary file or a file containing warnings
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    return {common.COMMAND: common.COMMAND_TO_LONG, 'data': '',
            common.SCHEMA_VERSION: schema_version, 'msg_category': 'warning',
            'msg': 'This convert command has not yet been implemented for spreadsheets'}


def spreadsheet_validate(hed_schema, spreadsheet):
    """ Validates the spreadsheet.

    Parameters
    ----------
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    spreadsheet: HedFileInput
        Spreadsheet input object to be validated

    Returns
    -------
    dict
         A dictionary containing results of validation in standard form
    """
    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    validator = EventValidator(hed_schema=hed_schema)
    issues = validator.validate_input(spreadsheet)
    display_name = spreadsheet.get_display_name()
    if issues:
        issue_str = get_printable_issue_string(issues, f"Spreadsheet {display_name} validation errors")
        file_name = generate_filename(display_name, suffix='_validation_errors', extension='.txt')
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': issue_str, "output_display_name": file_name,
                common.SCHEMA_VERSION: schema_version, "msg_category": "warning",
                'msg': f"Spreadsheet {display_name} had validation errors"}
    else:
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': '',
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': f'Spreadsheet {display_name} had no validation errors'}
