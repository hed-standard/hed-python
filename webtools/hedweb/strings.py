from flask import current_app
from werkzeug import Response

from hed import models
from hed import schema as hedschema
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError
from hed.validator.event_validator import EventValidator

from hedweb.constants import common
from hedweb.utils.web_utils import form_has_option, get_hed_schema_from_pull_down
from hedweb.utils.io_utils import get_hed_schema

app_config = current_app.config


def get_input_from_string_form(request):
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
    hed_schema = get_hed_schema_from_pull_down(request)
    hed_string = request.form[common.STRING_INPUT]
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
    """Perform the requested action on the HED string.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the hedstring form

    Returns
    -------
    Response
        Downloadable response object.
    """
    hed_schema = arguments.get('schema', None)
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema", "")
    string_list = arguments.get(common.STRING_LIST, None)
    if not string_list:
        raise HedFileError('EmptyHedStringList', "Please provide a list of HED strings to be processed", "")
    if common.COMMAND not in arguments:
        raise HedFileError('MissingCommand', 'Command is missing', '')
    if arguments[common.COMMAND] == common.COMMAND_VALIDATE:
        results = string_validate(hed_schema, string_list)
    elif arguments[common.COMMAND] == common.COMMAND_TO_SHORT:
        results = string_convert(hed_schema, string_list)
    elif arguments[common.COMMAND] == common.COMMAND_TO_LONG:
        results = string_convert(hed_schema, string_list, to_short=False)
    else:
        raise HedFileError('UnknownProcessingMethod', 'Select a hedstring processing method', '')
    return results


def string_convert(hed_schema, string_list, to_short=True):
    """Converts a list of strings from short form to long form unless short_to_long is true

    Parameters
    ----------
    hed_schema: HedSchema
        The HED schema to be used in processing
    string_list: list
        A list of string to be processed
    short_to_long: bool
        If true convert from short to long

    Returns
    -------
    dict
        A dictionary with string_results as the key
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    results = string_validate(hed_schema, string_list)
    if results['data']:
        return results
    strings = []
    conversion_errors = []
    for pos, string in enumerate(string_list, start=1):
        hed_string_obj = models.HedString(string)
        if to_short:
            issues = hed_string_obj.convert_to_short(hed_schema)
        else:
            issues = hed_string_obj.convert_to_long(hed_schema)
        if issues:
            conversion_errors.append(get_printable_issue_string(issues, f"Errors for HED string {pos}:"))
        strings.append(str(hed_string_obj))
    if to_short:
        command = common.COMMAND_TO_SHORT
    else:
        command = common.COMMAND_TO_LONG
    if conversion_errors:
        return {'command': command, 'data': conversion_errors, 'additional_info': string_list,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': 'Some strings had conversion errors, results of conversion in additional_info'}
    else:
        return {'command': command, 'data': strings,
                'schema_version': schema_version, 'msg_category': 'success',
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
        return {'command': common.COMMAND_VALIDATE, 'data': validation_errors,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': 'Strings had validation errors'}
    else:
        return {'command': common.COMMAND_VALIDATE, 'data': '',
                'schema_version': schema_version, 'msg_category': 'success',
                'msg': 'Strings validated successfully...'}
