from flask import current_app
import json
from werkzeug.utils import secure_filename
import pandas as pd

from hed import models
from hed import schema as hedschema
from hed.errors.error_reporter import get_printable_issue_string
from hed.errors.exceptions import HedFileError
from hed.validator.event_validator import EventValidator
from hedweb.constants import common
from hedweb.columns import create_column_selections, get_info_in_columns
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
    arguments = {common.SCHEMA: get_hed_schema_from_pull_down(request), common.EVENTS: None,
                 common.COMMAND: request.form.get(common.COMMAND_OPTION, ''),
                 common.CHECK_FOR_WARNINGS_ASSEMBLE: form_has_option(request, common.CHECK_FOR_WARNINGS_ASSEMBLE, 'on'),
                 common.CHECK_FOR_WARNINGS_VALIDATE: form_has_option(request, common.CHECK_FOR_WARNINGS_VALIDATE, 'on'),
                 common.DEFS_EXPAND: form_has_option(request, common.DEFS_EXPAND, 'on'),
                 common.COLUMNS_SELECTED: create_column_selections(request.form)
                 }

    json_sidecar = None
    if common.JSON_FILE in request.files:
        f = request.files[common.JSON_FILE]
        json_sidecar = models.Sidecar(file=f, name=secure_filename(f.filename))
    if common.EVENTS_FILE in request.files:
        f = request.files[common.EVENTS_FILE]
        arguments[common.EVENTS] = models.EventsInput(file=f, sidecars=json_sidecar, name=secure_filename(f.filename))
    return arguments


def events_process(arguments):
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
    command = arguments.get(common.COMMAND, None)
    if not hed_schema or not isinstance(hed_schema, hedschema.hed_schema.HedSchema):
        raise HedFileError('BadHedSchema', "Please provide a valid HedSchema for event processing", "")
    events = arguments.get(common.EVENTS, 'None')
    if not events or not isinstance(events, models.EventsInput):
        raise HedFileError('InvalidEventsFile', "An events file was given but could not be processed", "")

    if command == common.COMMAND_VALIDATE:
        results = events_validate(hed_schema, events)
    elif command == common.COMMAND_ASSEMBLE:
        results = events_assemble(hed_schema, events, arguments.get(common.DEFS_EXPAND, True))
    elif command == common.COMMAND_EXTRACT:
        results = events_extract(hed_schema, events, arguments.get(common.COLUMNS_SELECTED, None))
    else:
        raise HedFileError('UnknownEventsProcessingMethod', f'Command {command} is missing or invalid', '')
    return results


def events_assemble(hed_schema, events, defs_expand=True):
    """Converts an events file from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    hed_schema: HedSchema
        A HED schema
    events: model.EventsInput
        An events input object
    defs_expand: bool
        True if definitions should be expanded during assembly

    Returns
    -------
    dict
        A dictionary pointing to assembled string or errors
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    results = events_validate(hed_schema, events)
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
    return {common.COMMAND: common.COMMAND_ASSEMBLE, 'data': csv_string, 'output_display_name': file_name,
            'schema_version': schema_version, 'msg_category': 'success', 'msg': 'Events file successfully expanded'}


def events_extract(hed_schema, events, columns_selected):
    """Extracts a JSON sidecar template from a BIDS-style events file.

    Parameters
    ----------
    hed_schema: HedSchema
        A HEDSchema object
    events: EventInput
        An events input object
    columns_selected: dict
        dictionary of columns selected

    Returns
    -------
    dict
        A dictionary pointing to extracted JSON file.
    """
    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    columns_info = get_info_in_columns(events.dataframe)
    hed_dict = {}
    for key in columns_selected:
        if key not in columns_info:
            raise HedFileError("INVALID_COLUMN_NAME", f"{key} is not a valid column name in the events file", "")
        key_description = f"Description for {key}"
        if columns_selected[key]:
            levels = {}
            hed = {}
            for val_key in columns_info[key].keys():
                levels[val_key] = f"Level for {val_key}"
                hed[val_key] = f"Description/Tags for {val_key}"
            hed_dict[key] = {"Description": key_description, "Levels": levels, "HED": hed}
        else:
            hed_dict[key] = {"Description": key_description, "HED": "Label/#"}
    display_name = events.name
    file_name = generate_filename(display_name, suffix='_extracted', extension='.json')
    return {common.COMMAND: common.COMMAND_EXTRACT, 'data': json.dumps(hed_dict, indent=4),
            'output_display_name': file_name, 'schema_version': schema_version,
            'msg_category': 'success', 'msg': 'Events extraction to JSON complete'}


def events_validate(hed_schema, events):
    """Validates and events input object and returns the results.

    Parameters
    ----------
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used
    events: EventsInput
        Events input object to be validated

    Returns
    -------
    dict
         A dictionary containing results of validation in standard format
    """

    schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
    display_name = events.name
    issues = events.validate_file_sidecars(hed_schema)
    if not issues:
        validator = EventValidator(hed_schema=hed_schema)
        issues = validator.validate_file(events)
    if issues:
        issue_str = get_printable_issue_string(issues, f"{display_name} HED validation errors")
        file_name = generate_filename(display_name, suffix='_validation_errors', extension='.txt')
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': issue_str, "output_display_name": file_name,
                common.SCHEMA_VERSION: schema_version, "msg_category": "warning",
                'msg': f"Events file {display_name} had validation errors"}
    else:
        return {common.COMMAND: common.COMMAND_VALIDATE, 'data': '',
                common.SCHEMA_VERSION: schema_version, 'msg_category': 'success',
                'msg': f"Events file {display_name} had no validation errors"}
