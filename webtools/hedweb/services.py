import os
import io
import json

from flask import current_app
from hed import models
from hed import schema as hedschema
from hedweb.constants import common
from hedweb import events, spreadsheet, sidecar, strings, schema


app_config = current_app.config


def get_input_from_request(request):
    """Gets a dictionary of input from a service request.

    Parameters
    ----------
    request: Request object
        A Request object containing user data for the service request.

    Returns
    -------
    dict
        A dictionary containing input arguments for calling the service request.
    """

    form_data = request.data
    form_string = form_data.decode()
    service_request = json.loads(form_string)
    parameters = service_request.get(common.SERVICE_PARAMETERS, None)
    if not parameters:
        parameters = service_request
    arguments = {
                 common.COMMAND_TARGET: service_request.get(common.COMMAND_TARGET, None),
                 common.COMMAND: service_request.get(common.COMMAND, None),
                 common.SCHEMA: get_input_schema(parameters),
                 common.JSON_SIDECAR: None,
                 common.EVENTS: None,
                 common.SPREADSHEET: None,
                 common.HAS_COLUMN_NAMES: parameters.get(common.HAS_COLUMN_NAMES, False),
                 common.STRING_LIST: parameters.get(common.STRING_LIST, None),
                 common.CHECK_WARNINGS_VALIDATE: parameters.get(common.CHECK_WARNINGS_VALIDATE, True),
                 common.DEFS_EXPAND: parameters.get(common.DEFS_EXPAND, True)}
    arguments.update(get_input_objects(parameters))
    return arguments


def get_input_objects(params):
    args = {}
    if common.JSON_STRING in params and params[common.JSON_STRING]:
        args[common.JSON_SIDECAR] = models.Sidecar(file=io.StringIO(params[common.JSON_STRING]), name='JSON_Sidecar')
    if common.EVENTS_STRING in params and params[common.EVENTS_STRING]:
        args[common.EVENTS] = models.EventsInput(file=io.StringIO(params[common.EVENTS_STRING]),
                                                 sidecars=args[common.JSON_SIDECAR], name='Events')
    if common.SPREADSHEET_STRING in params and params[common.SPREADSHEET_STRING]:
        tag_columns, prefix_dict = spreadsheet.get_prefix_dict(params)
        args[common.SPREADSHEET] = models.HedInput(file=io.StringIO(params[common.SPREADSHEET_STRING]),
                                                   file_type=".tsv", tag_columns=tag_columns,
                                                   has_column_names=args.get(common.HAS_COLUMN_NAMES, None),
                                                   column_prefix_dictionary=prefix_dict, name='spreadsheet.tsv')
    return args


def get_input_schema(parameters):
    if common.SCHEMA_STRING in parameters and parameters[common.SCHEMA_STRING]:
        schema = hedschema.from_string(parameters[common.SCHEMA_STRING])
    elif common.SCHEMA_URL in parameters and parameters[common.SCHEMA_URL]:
        schema_url = parameters[common.SCHEMA_URL]
        schema = hedschema.load_schema(hed_url_path=schema_url)
    elif common.SCHEMA_VERSION in parameters and parameters[common.SCHEMA_VERSION]:
        hed_file_path = hedschema.get_path_from_hed_version(parameters[common.SCHEMA_VERSION])
        schema = hedschema.load_schema(hed_file_path=hed_file_path)
    return schema


def process(arguments):
    """
    Calls the desired service processing function and returns results

    Parameters
    ----------
    arguments: dict
        a dictionary of arguments for the processing

    Returns
    -------
    dist
        A dictionary of results in standard response format to be jsonified.
    """

    command = arguments[common.COMMAND]
    target = arguments[common.COMMAND_TARGET]
    response = {common.COMMAND: command, common.COMMAND_TARGET: target,
                'results': '', 'error_type': '', 'error_msg': ''}

    if not command:
        response["error_type"] = 'HEDServiceMissing'
        response["error_msg"] = "Must specify a valid service"
    elif command == 'get_services':
        response["results"] = services_list()
    elif target == "events":
        response["results"] = events.process(arguments)
    elif target == "sidecar":
        response["results"] = sidecar.process(arguments)
    elif target == "spreadsheet":
        results = spreadsheet.process(arguments)
        response["results"] = package_spreadsheet(results)
    elif target == "strings":
        response["results"] = strings.process(arguments)
    else:
        response["error_type"] = 'HEDServiceNotSupported'
        response["error_msg"] = f"{command} for {target} not supported"
    return response


def package_spreadsheet(results):
    if results['msg_category'] == 'success' and common.SPREADSHEET in results:
        results[common.SPREADSHEET] = results[common.SPREADSHEET].to_csv(file=None)
    elif common.SPREADSHEET in results:
        del results[common.SPREADSHEET]
    return results


def services_list():
    """
     Returns a formatted string describing services using the resources/services.json file

     Returns
     -------
     str
         A formatted string listing available services.
     """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    the_path = os.path.join(dir_path, './static/resources/services.json')
    with open(the_path) as f:
        service_info = json.load(f)
    commands = service_info['command']
    command_targets = service_info['command_target']
    meanings = service_info['meanings']
    returns = service_info['returns']
    results = service_info['results']
    services_string = '\nServices:\n'
    for service, info in services.items():
        description = info['Description']
        parm_string = json.dumps(info['Parameters'])
        next_string = f'{service}: {description}\n\tParameters: {parm_string}\n'
        services_string += next_string

    meanings_string = '\nMeanings:\n'
    for string, meaning in meanings.items():
        meanings_string += f'\t{string}: {meaning}\n'

    returns_string = '\nReturn values:\n'
    for return_val, meaning in returns.items():
        returns_string += f'\t{return_val}: {meaning}\n'

    results_string = '\nresults field meanings:\n'
    for result_val, meaning in results.items():
        results_string += f'\t{result_val}: {meaning}\n'
    data = services_string + meanings_string + returns_string + results_string
    return {common.COMMAND: '', 'data': data, 'output_display_name': '',
            common.SCHEMA_VERSION: '', 'msg_category': 'success',
            'msg': "List of available services and their meanings"}
