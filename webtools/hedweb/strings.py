from flask import current_app

from hed import models
from hed import schema as hedschema
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError
from hed.validator.event_validator import EventValidator

from hedweb.constants import common
from hedweb.utils.web_utils import form_has_option, get_hed_schema_from_pull_down

app_config = current_app.config


def get_input_from_string_form(request):
    """Gets input arguments from a request object associated with the string form.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the string form.

    Returns
    -------
    dict
        A dictionary containing input arguments for calling the underlying string processing functions.
    """
    hed_schema = get_hed_schema_from_pull_down(request)
    hed_string = request.form.get(common.STRING_INPUT, None)
    if hed_string:
        string_list = [hed_string]
    else:
        raise HedFileError('EmptyHedString', 'Must enter a HED string', '')
    arguments = {common.COMMAND: request.values.get(common.COMMAND_OPTION, ''),
                 common.SCHEMA: hed_schema,
                 common.STRING_LIST: string_list,
                 common.CHECK_FOR_WARNINGS: form_has_option(request, common.CHECK_FOR_WARNINGS, 'on')}
    return arguments


def string_process(arguments):
    """Perform the requested string processing action

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the string form or string service request.

    Returns
    -------
    dict
        A dictionary with the results in standard format.
    """
    hed_schema = arguments.get('schema', None)
    command = arguments.get(common.COMMAND, None)
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema", "")
    string_list = arguments.get(common.STRING_LIST, None)
    if not string_list:
        raise HedFileError('EmptyHedStringList', "Please provide a list of HED strings to be processed", "")
    if command == common.COMMAND_VALIDATE:
        results = string_validate(hed_schema, string_list)
    elif command == common.COMMAND_TO_SHORT:
        results = string_convert(hed_schema, string_list, command=common.COMMAND_TO_SHORT)
    elif command == common.COMMAND_TO_LONG:
        results = string_convert(hed_schema, string_list)
    else:
        raise HedFileError('UnknownProcessingMethod', 'Select a hedstring processing method', '')
    return results


def string_convert(hed_schema, string_list, command=common.COMMAND_TO_LONG):
    """Converts a list of strings from long to short unless command is not COMMAND_TO_LONG then converts to short

    Parameters
    ----------
    hed_schema: HedSchema
        The HED schema to be used in processing
    string_list: list
        A list of string to be processed
   command: str
        Name of the command to execute if not COMMAND_TO_LONG

    Returns
    -------
    dict
        A dictionary with the results of string processing in standard format.
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    results = string_validate(hed_schema, string_list)
    if results['data']:
        return results
    strings = []
    conversion_errors = []
    for pos, string in enumerate(string_list, start=1):
        hed_string_obj = models.HedString(string)
        if command == common.COMMAND_TO_LONG:
            issues = hed_string_obj.convert_to_long(hed_schema)
        else:
            issues = hed_string_obj.convert_to_short(hed_schema)
        if issues:
            conversion_errors.append(get_printable_issue_string(issues, f"Errors for HED string {pos}:"))
        strings.append(str(hed_string_obj))

    if conversion_errors:
        return {common.COMMAND: command, 'data': conversion_errors, 'additional_info': string_list,
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'warning',
                'msg': 'Some strings had conversion errors, results of conversion in additional_info'}
    else:
        return {common.COMMAND: command, 'data': strings,
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': 'Strings converted successfully'}


def string_validate(hed_schema, string_list):
    """Validates a list of strings and returns a dictionary containing the issues or a no errors message

    Parameters
    ----------
    hed_schema: HedSchema
        The HED schema to be used in processing
    string_list: list
        A list of string to be processed

    Returns
    -------
    dict
        A dictionary with results
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    hed_validator = EventValidator(hed_schema=hed_schema)

    validation_errors = []
    for pos, string in enumerate(string_list, start=1):
        issues = hed_validator.validate_input(string)
        if issues:
            validation_errors.append(get_printable_issue_string(issues, f"Errors for HED string {pos}:"))
    if validation_errors:
        print(common.COMMAND)
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': validation_errors,
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'warning',
                'msg': 'Strings had validation errors'}
    else:
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': '',
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': 'Strings validated successfully...'}
