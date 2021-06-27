from flask import current_app
from werkzeug.utils import secure_filename

from hed import models
from hed import schema as hedschema
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError
from hedweb.constants import common, file_constants
from hedweb.utils.web_utils import form_has_option, get_hed_schema_from_pull_down
from hedweb.utils.io_utils import generate_filename

app_config = current_app.config


def get_input_from_dictionary_form(request):
    """Gets the dictionary processing input arguments from a request object.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the dictionary processing form.

    Returns
    -------
    dict
        A dictionary containing input arguments for calling the underlying dictionary processing functions.
    """
    arguments = {
        common.SCHEMA: None,
        common.JSON_DICTIONARY: None,
        common.COMMAND: request.values.get(common.COMMAND_OPTION, None),
        common.CHECK_FOR_WARNINGS: form_has_option(request, common.CHECK_FOR_WARNINGS, 'on')
    }
    arguments[common.SCHEMA] = get_hed_schema_from_pull_down(request)
    if common.JSON_FILE in request.files:
        f = request.files[common.JSON_FILE]
        arguments[common.JSON_DICTIONARY] = \
            models.ColumnDefGroup(json_string=f.read(file_constants.BYTE_LIMIT).decode('ascii'),
                                  display_name=secure_filename(f.filename))
    return arguments


def dictionary_process(arguments):
    """Perform the requested action for the dictionary.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the dictionary form

    Returns
    -------
      dict
        A dictionary of results.
    """
    hed_schema = arguments.get(common.SCHEMA, None)
    command = arguments.get(common.COMMAND, None)
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema", "")
    json_dictionary = arguments.get(common.JSON_DICTIONARY, 'None')
    if not json_dictionary or not isinstance(json_dictionary, models.ColumnDefGroup):
        raise HedFileError('InvalidJSONFile', "Please give a valid JSON file to process", "")

    if arguments[common.COMMAND] == common.COMMAND_VALIDATE:
        results = dictionary_validate(hed_schema, json_dictionary)
    elif arguments[common.COMMAND] == common.COMMAND_TO_SHORT:
        results = dictionary_convert(hed_schema, json_dictionary, command=common.COMMAND_TO_SHORT)
    elif arguments[common.COMMAND] == common.COMMAND_TO_LONG:
        results = dictionary_convert(hed_schema, json_dictionary)
    else:
        raise HedFileError('UnknownDictionaryProcessingMethod', f'Command {command} is missing or invalid', '')
    return results


def dictionary_convert(hed_schema, json_dictionary, command=common.COMMAND_TO_LONG):
    """Converts a dictionary from long to short unless unless the command is not COMMAND_TO_LONG then converts to short

    Parameters
    ----------
    hed_schema:HedSchema
        HedSchema object to be used
    json_dictionary: ColumnDefGroup
        Previously created ColumnDefGroup
    command: str
        Name of the command to execute if not COMMAND_TO_LONG

    Returns
    -------
    dict
        A downloadable dictionary file or a file containing warnings
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    results = dictionary_validate(hed_schema, json_dictionary)
    if results['data']:
        return results
    if command == common.COMMAND_TO_LONG:
        suffix = '_to_long'
    else:
        suffix = '_to_short'
    issues = []
    for column_def in json_dictionary:
        for hed_string, position in column_def.hed_string_iter(include_position=True):
            hed_string_obj = models.HedString(hed_string)
            if command == common.COMMAND_TO_LONG:
                errors = hed_string_obj.convert_to_long(hed_schema)
            else:
                errors = hed_string_obj.convert_to_short(hed_schema)
                column_def.set_hed_string(hed_string_obj, position)
            issues = issues + errors
            column_def.set_hed_string(hed_string_obj, position)

    # issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
    display_name = json_dictionary.display_name
    if issues:
        issue_str = get_printable_issue_string(issues, f"JSON conversion for {display_name} was unsuccessful")
        file_name = generate_filename(display_name, suffix=f"{suffix}_conversion_errors", extension='.txt')
        return {common.COMMAND: command, 'data': issue_str, 'output_display_name': file_name,
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'warning',
                'msg': f'JSON file {display_name} had validation errors'}
    else:
        file_name = generate_filename(display_name, suffix=suffix, extension='.json')
        data = json_dictionary.get_as_json_string()
        return {common.COMMAND: command, 'data': data, 'output_display_name': file_name,
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': f'JSON dictionary {display_name} was successfully converted'}


def dictionary_validate(hed_schema, json_dictionary):
    """ Validates the dictionary and returns the errors and/or a message in a dictionary

    Parameters
    ----------
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    json_dictionary: ColumnDefGroup
        Dictionary object

    Returns
    -------
    dict
        dictionary of response values.
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    if not json_dictionary or not isinstance(json_dictionary, models.ColumnDefGroup):
        raise HedFileError('BadDictionaryFile', "Please provide a dictionary to process", "")
    display_name = json_dictionary.display_name
    def_dict, issues = json_dictionary.extract_defs()
    if issues:
        issue_str = get_printable_issue_string(issues, f"JSON dictionary {display_name} definition errors")
        file_name = generate_filename(display_name, suffix='_dictionary_errors', extension='.txt')
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': issue_str, 'output_display_name': file_name,
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'warning',
                'msg': f"JSON dictionary {display_name} had definition errors"}

    issues = json_dictionary.validate_entries(hed_schema)
    if issues:
        issue_str = get_printable_issue_string(issues, f"JSON dictionary {display_name } validation errors")
        file_name = generate_filename(display_name, suffix='validation_errors', extension='.txt')
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': issue_str, 'output_display_name': file_name,
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'warning',
                'msg': f'JSON dictionary {display_name} had validation errors'}
    else:
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': '',
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': f'JSON file {display_name} had no validation errors'}
