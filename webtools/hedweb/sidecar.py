import io
import json
from flask import current_app
from werkzeug.utils import secure_filename

from hed import models
from hed import schema as hedschema
from hed.validator.hed_validator import HedValidator
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError
from hedweb.constants import base_constants, file_constants
from hed.tools import SidecarMap
from hedweb.web_utils import form_has_option, get_hed_schema_from_pull_down, generate_filename

app_config = current_app.config


def get_input_from_form(request):
    """Gets the sidecar processing input arguments from a request object.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the sidecar processing form.

    Returns
    -------
    dict
        A dictionary containing input arguments for calling the underlying sidecar processing functions.
    """

    arguments = {base_constants.SCHEMA: get_hed_schema_from_pull_down(request), base_constants.JSON_SIDECAR: None,
                 base_constants.COMMAND: request.form.get(base_constants.COMMAND_OPTION, None),
                 base_constants.CHECK_FOR_WARNINGS:
                     form_has_option(request, base_constants.CHECK_FOR_WARNINGS, 'on')}
    if base_constants.JSON_FILE in request.files:
        f = request.files[base_constants.JSON_FILE]
        fb = io.StringIO(f.read(file_constants.BYTE_LIMIT).decode('ascii'))
        arguments[base_constants.JSON_SIDECAR] = models.Sidecar(file=fb, name=secure_filename(f.filename))
    return arguments


def process(arguments):
    """Perform the requested action for the sidecar.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the sidecar form

    Returns
    -------
      dict
        A dictionary of results.
    """
    hed_schema = arguments.get(base_constants.SCHEMA, None)
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema", "")
    json_sidecar = arguments.get(base_constants.JSON_SIDECAR, 'None')
    if not json_sidecar or not isinstance(json_sidecar, models.Sidecar):
        raise HedFileError('InvalidJSONFile', "Please give a valid JSON file to process", "")
    command = arguments.get(base_constants.COMMAND, None)
    check_for_warnings = arguments.get(base_constants.CHECK_FOR_WARNINGS, False)
    if command == base_constants.COMMAND_VALIDATE:
        results = sidecar_validate(hed_schema, json_sidecar, check_for_warnings=check_for_warnings)
    elif command == base_constants.COMMAND_TO_SHORT:
        results = sidecar_convert(hed_schema, json_sidecar, command=command, check_for_warnings=check_for_warnings)
    elif command == base_constants.COMMAND_TO_LONG:
        results = sidecar_convert(hed_schema, json_sidecar, check_for_warnings=check_for_warnings)
    else:
        raise HedFileError('UnknownProcessingMethod', f'Command {command} is missing or invalid', '')
    return results


def sidecar_convert(hed_schema, json_sidecar, command=base_constants.COMMAND_TO_SHORT, check_for_warnings=False):
    """Converts a sidecar from long to short or short to long

    Parameters
    ----------
    hed_schema:HedSchema
        HedSchema object to be used
    json_sidecar: Sidecar
        Previously created Sidecar
    command: str
        Name of the command to execute (default to short if unrecognized)
    check_for_warnings: bool
        Indicates whether validation should check for warnings as well as errors

    Returns
    -------
    dict
        A downloadable dictionary file or a file containing warnings
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    results = sidecar_validate(hed_schema, json_sidecar, check_for_warnings=check_for_warnings)
    if results['data']:
        return results
    if command == base_constants.COMMAND_TO_LONG:
        suffix = '_to_long'
    else:
        suffix = '_to_short'
    issues = []
    for column_def in json_sidecar:
        for hed_string, position in column_def.hed_string_iter(include_position=True):
            hed_string_obj = models.HedString(hed_string)
            if command == base_constants.COMMAND_TO_LONG:
                converted_string, errors = hed_string_obj.convert_to_long(hed_schema)
            else:
                converted_string, errors = hed_string_obj.convert_to_short(hed_schema)
            issues = issues + errors
            column_def.set_hed_string(converted_string, position)

    # issues = ErrorHandler.filter_issues_by_severity(issues, ErrorSeverity.ERROR)
    display_name = json_sidecar.name
    if issues:
        issue_str = get_printable_issue_string(issues, f"JSON conversion for {display_name} was unsuccessful")
        file_name = generate_filename(display_name, suffix=f"{suffix}_conversion_errors", extension='.txt')
        return {base_constants.COMMAND: command, 'data': issue_str, 'output_display_name': file_name,
                base_constants.SCHEMA_VERSION: schema_version, 'msg_category': 'warning',
                'msg': f'JSON file {display_name} had validation errors'}
    else:
        file_name = generate_filename(display_name, suffix=suffix, extension='.json')
        data = json_sidecar.get_as_json_string()
        return {base_constants.COMMAND: command, 'data': data, 'output_display_name': file_name,
                base_constants.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': f'JSON sidecar {display_name} was successfully converted'}


def sidecar_flatten(json_sidecar):
    """Converts a sidecar from long to short unless unless the command is not COMMAND_TO_LONG then converts to short

    Parameters
    ----------
    json_sidecar: Sidecar
        Previously created Sidecar

    Returns
    -------
    dict
        A downloadable dictionary file or a file containing warnings
    """

    json_string = json_sidecar.get_as_json_string()
    sidecar = json.loads(json_string)
    sr = SidecarMap()
    df = sr.flatten(sidecar)
    data = df.to_csv(None, sep='\t', index=False, header=True)
    display_name = json_sidecar.name
    file_name = generate_filename(display_name, suffix='flattened', extension='.tsv')
    return {base_constants.COMMAND: base_constants.COMMAND_FLATTEN, 'data': data, 'output_display_name': file_name,
            'msg_category': 'success', 'msg': f'JSON sidecar {display_name} was successfully flattened'}


def sidecar_validate(hed_schema, json_sidecar, check_for_warnings=False):
    """ Validates the sidecar and returns the errors and/or a message in a dictionary

    Parameters
    ----------
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    json_sidecar: Sidecar
        Dictionary object
    check_for_warnings: bool
        Indicates whether validation should check for warnings as well as errors

    Returns
    -------
    dict
        dictionary of response values.
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    display_name = json_sidecar.name
    validator = HedValidator(hed_schema)
    issues = json_sidecar.validate_entries(validator, check_for_warnings=check_for_warnings)
    if issues:
        issue_str = get_printable_issue_string(issues, f"JSON dictionary {display_name } validation errors")
        file_name = generate_filename(display_name, suffix='validation_errors', extension='.txt')
        return {base_constants.COMMAND: base_constants.COMMAND_VALIDATE,
                'data': issue_str, 'output_display_name': file_name,
                base_constants.SCHEMA_VERSION: schema_version, 'msg_category': 'warning',
                'msg': f'JSON sidecar {display_name} had validation errors'}
    else:
        return {base_constants.COMMAND: base_constants.COMMAND_VALIDATE, 'data': '',
                base_constants.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': f'JSON file {display_name} had no validation errors'}
