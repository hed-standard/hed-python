from flask import current_app
from werkzeug import Response

from hedweb.constants import common, file_constants
from hed.util.column_def_group import ColumnDefGroup
from hed.util.hed_string import HedString
from hed.util.error_reporter import ErrorHandler, get_printable_issue_string
from hed.util.error_types import ErrorSeverity
from hed.util.exceptions import HedFileError
from hedweb.web_utils import form_has_option, generate_filename, \
    generate_response_download_file_from_text, get_hed_schema, get_json_dictionary, \
    generate_text_response, get_hed_path_from_pull_down, get_uploaded_file_path_from_form

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
    hed_file_path, schema_display_name = get_hed_path_from_pull_down(request)
    uploaded_file_name, original_file_name = \
        get_uploaded_file_path_from_form(request, common.JSON_FILE, file_constants.DICTIONARY_FILE_EXTENSIONS)

    arguments = {
        common.SCHEMA_PATH: hed_file_path,
        common.SCHEMA_DISPLAY_NAME: schema_display_name,
        common.JSON_PATH: uploaded_file_name,
        common.JSON_FILE: original_file_name,
    }
    if form_has_option(request, common.COMMAND_OPTION, common.COMMAND_VALIDATE):
        arguments[common.COMMAND] = common.COMMAND_VALIDATE
    elif form_has_option(request, common.COMMAND_OPTION, common.COMMAND_TO_SHORT):
        arguments[common.COMMAND] = common.COMMAND_TO_SHORT
    elif form_has_option(request, common.COMMAND_OPTION, common.COMMAND_TO_LONG):
        arguments[common.COMMAND] = common.COMMAND_TO_LONG
    else:
        arguments[common.COMMAND] = ''
    arguments[common.CHECK_FOR_WARNINGS] = form_has_option(request, common.CHECK_FOR_WARNINGS, 'on')
    return arguments


def dictionary_process(arguments):
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
    if not arguments.get(common.JSON_PATH, 'None'):
        raise HedFileError('EmptyJSONFile', "Please give a JSON file to process", "")
    elif common.COMMAND not in arguments:
        raise HedFileError('MissingCommand', 'Command is missing', '')
    elif arguments[common.COMMAND] == common.COMMAND_VALIDATE:
        results = dictionary_validate(arguments)
    elif arguments[common.COMMAND] == common.COMMAND_TO_SHORT:
        results = dictionary_convert(arguments)
    elif arguments[common.COMMAND] == common.COMMAND_TO_LONG:
        results = dictionary_convert(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', "Select a dictionary processing method", "")
    msg = results.get('msg', '')
    msg_category = results.get('msg_category', 'success')

    if results['data']:
        display_name = results.get('output_display_name', '')
        return generate_response_download_file_from_text(results['data'], display_name=display_name,
                                                         msg_category=msg_category, msg=msg)
    else:
        return generate_text_response("", msg=msg, msg_category=msg_category)


def dictionary_convert(arguments, hed_schema=None, json_dictionary=None):
    """Converts a dictionary from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments
    hed_schema:str or HedSchema
        Version number or path or HedSchema object to be used
    json_dictionary: ColumnDefGroup
        Previously created ColumnDefGroup

    Returns
    -------
    dict
        A downloadable dictionary file or a file containing warnings
    """

    if not hed_schema:
        hed_schema = get_hed_schema(arguments)
    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    if not json_dictionary:
        json_dictionary = get_json_dictionary(arguments)

    results = dictionary_validate(arguments, hed_schema, json_dictionary=json_dictionary)
    if results['data']:
        return results
    if arguments[common.COMMAND] == common.COMMAND_TO_LONG:
        suffix = '_to_long'
    else:
        suffix = '_to_short'
    issues = []
    for column_def in json_dictionary:
        for hed_string, position in column_def.hed_string_iter(include_position=True):
            hed_string_obj = HedString(hed_string)
            if suffix == '_to_long':
                errors = hed_string_obj.convert_to_long(hed_schema)
            else:
                errors = hed_string_obj.convert_to_short(hed_schema)
                column_def.set_hed_string(hed_string_obj, position)
            issues = issues + errors
            column_def.set_hed_string(hed_string_obj, position)

    issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
    json_display_name = arguments.get(common.JSON_FILE, '')

    if issues:
        issue_str = get_printable_issue_string(issues, f"JSON conversion for {json_display_name} was unsuccessful")
        file_name = generate_filename(json_display_name, suffix=f"{suffix}_conversion_errors", extension='.txt')
        return {'command': arguments.get('command', ''), 'data': issue_str, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': 'JSON file had validation errors'}
    else:
        file_name = generate_filename(json_display_name, suffix=suffix, extension='.json')
        data = json_dictionary.get_as_json_string()
        return {'command': arguments.get('command', ''), 'data': data, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'success',
                'msg': 'JSON dictionary was successfully converted'}


def dictionary_validate(arguments, hed_schema=None, json_dictionary=None):
    """ Validates the dictionary and returns the errors and/or a message in a dictionary

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    json_dictionary: ColumnDefGroup
        Dictionary object

    Returns
    -------
    dict
        dictionary of response values.
    """

    if not hed_schema:
        hed_schema = get_hed_schema(arguments)
    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    if not json_dictionary:
        json_dictionary = get_json_dictionary(arguments)
    if not json_dictionary:
        raise HedFileError('EmptyDictionaryFile', "Please upload a dictionary to process", "")

    def_dict, issues = json_dictionary.extract_defs()
    if issues:
        issue_str = get_printable_issue_string(issues,
                                               f"{common.JSON_DISPLAY_NAME} JSON dictionary definition errors")
        file_name = generate_filename(common.JSON_DISPLAY_NAME, suffix='_dictionary_errors', extension='.txt')
        return {'command': arguments.get('command', ''), 'data': issue_str, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': "JSON dictionary had definition errors"}

    issues = json_dictionary.validate_entries(hed_schema)
    if issues:
        display_name = arguments.get(common.JSON_DISPLAY_NAME, '')
        issue_str = get_printable_issue_string(issues, f"HED validation errors for {display_name}")
        file_name = generate_filename(display_name, suffix='validation_errors', extension='.txt')
        return {'command': arguments.get('command', ''), 'data': issue_str, 'output_display_name': file_name,
                'schema_version': schema_version, 'msg_category': 'warning',
                'msg': 'JSON dictionary had validation errors'}
    else:
        return {'command': arguments.get('command', ''), 'data': '',
                'schema_version': schema_version, 'msg_category': 'success',
                'msg': 'JSON file had no validation errors'}
