from flask import current_app
import json
from werkzeug.utils import secure_filename
import pandas as pd

from hed import models
from hed import schema as hedschema
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError
from hed.validator.hed_validator import HedValidator
from hedweb.constants import base_constants
from hedweb.columns import create_column_selections
from hed.tools import get_columns_info
from hed.tools import SidecarMap
from hedweb.web_utils import form_has_option, get_hed_schema_from_pull_down, generate_filename

app_config = current_app.config


def get_input_from_events_form(request):
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

    arguments = {base_constants.SCHEMA: get_hed_schema_from_pull_down(request), base_constants.EVENTS: None,
                 base_constants.COMMAND: request.form.get(base_constants.COMMAND_OPTION, ''),
                 base_constants.CHECK_FOR_WARNINGS: form_has_option(request, base_constants.CHECK_FOR_WARNINGS, 'on'),
                 base_constants.DEFS_EXPAND: form_has_option(request, base_constants.DEFS_EXPAND, 'on'),
                 base_constants.COLUMNS_SELECTED: create_column_selections(request.form)
                 }

    json_sidecar = None
    if base_constants.JSON_FILE in request.files:
        f = request.files[base_constants.JSON_FILE]
        json_sidecar = models.Sidecar(file=f, name=secure_filename(f.filename))
    arguments[base_constants.JSON_SIDECAR] = json_sidecar
    if base_constants.EVENTS_FILE in request.files:
        f = request.files[base_constants.EVENTS_FILE]
        arguments[base_constants.EVENTS] = \
            models.EventsInput(file=f, sidecars=json_sidecar, name=secure_filename(f.filename))
    return arguments


def process(arguments):
    """Perform the requested action for the events file and its sidecar

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the event form

    Returns
    -------
      dict
        A dictionary with the results.
    """
    hed_schema = arguments.get('schema', None)
    command = arguments.get(base_constants.COMMAND, None)
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema for event processing", "")
    events = arguments.get(base_constants.EVENTS, None)
    sidecar = arguments.get(base_constants.JSON_SIDECAR, None)
    if not events or not isinstance(events, models.EventsInput):
        raise HedFileError('InvalidEventsFile', "An events file was given but could not be processed", "")

    if command == base_constants.COMMAND_VALIDATE:
        results = validate(hed_schema, events, sidecar, arguments.get(base_constants.CHECK_FOR_WARNINGS, False))
    elif command == base_constants.COMMAND_ASSEMBLE:
        results = assemble(hed_schema, events, arguments.get(base_constants.DEFS_EXPAND, False),
                           arguments.get(base_constants.CHECK_FOR_WARNINGS, False))
    elif command == base_constants.COMMAND_EXTRACT:
        results = extract(events, arguments.get(base_constants.COLUMNS_SELECTED, None))
    else:
        raise HedFileError('UnknownEventsProcessingMethod', f'Command {command} is missing or invalid', '')
    return results


def assemble(hed_schema, events, defs_expand=True, check_for_warnings=False):
    """Creates a two-column event file with first column Onset and second column HED tags.

    Parameters
    ----------
    hed_schema: HedSchema
        A HED schema
    events: model.EventsInput
        An events input object
    defs_expand: bool
        True if definitions should be expanded during assembly
    check_for_warnings: bool
        True if warnings should be checked for
    Returns
    -------
    dict
        A dictionary pointing to assembled string or errors
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    results = validate(hed_schema, events)
    if results['data']:
        return results

    hed_tags = []
    onsets = []
    for row_number, row_dict in events.iter_dataframe(return_row_dict=True, expand_defs=defs_expand):
        hed_tags.append(str(row_dict.get("HED", "")))
        onsets.append(row_dict.get("onset", "n/a"))
    data = {'onset': onsets, 'HED': hed_tags}
    df = pd.DataFrame(data)
    csv_string = df.to_csv(None, sep='\t', index=False, header=True)
    display_name = events.name
    file_name = generate_filename(display_name, suffix='_expanded', extension='.tsv')
    return {base_constants.COMMAND: base_constants.COMMAND_ASSEMBLE,
            'data': csv_string, 'output_display_name': file_name,
            'schema_version': schema_version, 'msg_category': 'success', 'msg': 'Events file successfully expanded'}


def extract(events, columns_selected):
    """Extracts a JSON sidecar template from a BIDS-style events file.

    Parameters
    ----------
    events: EventInput
        An events input object
    columns_selected: dict
        dictionary of columns selected

    Returns
    -------
    dict
        A dictionary pointing to extracted JSON file.
    """

    columns_info = get_columns_info(events.dataframe)
    sr = SidecarMap()
    hed_dict, issues = sr.get_sidecar_dict(columns_info, columns_selected)
    display_name = events.name
    if issues:
        issue_str = get_printable_issue_string(issues, f"{display_name} HED validation errors")
        file_name = generate_filename(display_name, suffix='_errors', extension='.txt')
        return {base_constants.COMMAND: base_constants.COMMAND_VALIDATE,
                'data': issue_str, "output_display_name": file_name, "msg_category": "warning",
                'msg': f"Events file {display_name} had extraction errors"}
    else:
        file_name = generate_filename(display_name, suffix='_extracted', extension='.json')
        return {base_constants.COMMAND: base_constants.COMMAND_EXTRACT, 'data': json.dumps(hed_dict, indent=4),
                'output_display_name': file_name, 'msg_category': 'success',
                'msg': 'Events extraction to JSON complete'}


def validate(hed_schema, events, sidecar=None, check_for_warnings=False):
    """Validates and events input object and returns the results.

    Parameters
    ----------
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    events: EventsInput
        Events input object to be validated
    sidecar: Sidecar
        Representation of a BIDS JSON sidecar object
    check_for_warnings: bool
        If true, validation should include warnings

    Returns
    -------
    dict
         A dictionary containing results of validation in standard format
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    display_name = events.name
    validator = HedValidator(hed_schema=hed_schema)
    issue_str = ''
    if sidecar:
        issues = sidecar.validate_entries(validator, check_for_warnings=check_for_warnings)
        if issues:
            issue_str = issue_str + get_printable_issue_string(issues, title="Sidecar definition errors:")
    issues = events.validate_file(validator, check_for_warnings=check_for_warnings )
    if issues:
        issue_str = issue_str + get_printable_issue_string(issues, title="Event file errors:")

    if issue_str:
        file_name = generate_filename(display_name, suffix='_validation_errors', extension='.txt')
        return {base_constants.COMMAND: base_constants.COMMAND_VALIDATE,
                'data': issue_str, "output_display_name": file_name,
                base_constants.SCHEMA_VERSION: schema_version, "msg_category": "warning",
                'msg': f"Events file {display_name} had validation errors"}
    else:
        return {base_constants.COMMAND: base_constants.COMMAND_VALIDATE, 'data': '',
                base_constants.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': f"Events file {display_name} had no validation errors"}
