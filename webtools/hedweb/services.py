import os
import io
import json
from flask import current_app
from hed import models
from hed import schema as hedschema
from hedweb.constants import base_constants
from hedweb import events, spreadsheet, sidecar, strings


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
    arguments = get_service_info(service_request)
    arguments[base_constants.SCHEMA] = get_input_schema(service_request)
    get_input_objects(arguments, service_request)
    return arguments


def get_input_objects(arguments, params):
    if base_constants.JSON_STRING in params and params[base_constants.JSON_STRING]:
        arguments[base_constants.JSON_SIDECAR] = \
            models.Sidecar(file=io.StringIO(params[base_constants.JSON_STRING]), name='JSON_Sidecar')
    if base_constants.EVENTS_STRING in params and params[base_constants.EVENTS_STRING]:
        arguments[base_constants.EVENTS] = \
            models.EventsInput(file=io.StringIO(params[base_constants.EVENTS_STRING]),
                               sidecars=arguments[base_constants.JSON_SIDECAR], name='Events')
    if base_constants.SPREADSHEET_STRING in params and params[base_constants.SPREADSHEET_STRING]:
        tag_columns, prefix_dict = spreadsheet.get_prefix_dict(params)
        arguments[base_constants.SPREADSHEET] = \
            models.HedInput(file=io.StringIO(params[base_constants.SPREADSHEET_STRING]), file_type=".tsv",
                            tag_columns=tag_columns,
                            has_column_names=arguments.get(base_constants.HAS_COLUMN_NAMES, None),
                            column_prefix_dictionary=prefix_dict, name='spreadsheet.tsv')
    if base_constants.STRING_LIST in params and params[base_constants.STRING_LIST]:
        s_list = []
        for s in params[base_constants.STRING_LIST]:
            s_list.append(models.HedString(s))
        arguments[base_constants.STRING_LIST] = s_list


def get_service_info(parameters):
    service = parameters.get(base_constants.SERVICE, '')
    command = service
    command_target = ''
    pieces = service.split('_', 1)
    if command != "get_services" and len(pieces) == 2:
        command = pieces[1]
        command_target = pieces[0]
    has_column_names = parameters.get(base_constants.HAS_COLUMN_NAMES, '') == 'on'
    defs_expand = parameters.get(base_constants.DEFS_EXPAND, '') == 'on'
    check_for_warnings = parameters.get(base_constants.CHECK_FOR_WARNINGS, '') == 'on'

    return {base_constants.SERVICE: service,
            base_constants.COMMAND: command,
            base_constants.COMMAND_TARGET: command_target,
            base_constants.HAS_COLUMN_NAMES: has_column_names,
            base_constants.CHECK_FOR_WARNINGS: check_for_warnings,
            base_constants.DEFS_EXPAND: defs_expand
            # base_constants.TAG_COLUMNS: tag_columns,
            # base_constants.COLUMN_PREFIX_DICTIONARY: prefix_dict
            }


def get_input_schema(parameters):

    if base_constants.SCHEMA_STRING in parameters and parameters[base_constants.SCHEMA_STRING]:
        the_schema = hedschema.from_string(parameters[base_constants.SCHEMA_STRING])
    elif base_constants.SCHEMA_URL in parameters and parameters[base_constants.SCHEMA_URL]:
        schema_url = parameters[base_constants.SCHEMA_URL]
        the_schema = hedschema.load_schema(hed_url_path=schema_url)
    elif base_constants.SCHEMA_VERSION in parameters and parameters[base_constants.SCHEMA_VERSION]:
        hed_file_path = hedschema.get_path_from_hed_version(parameters[base_constants.SCHEMA_VERSION])
        the_schema = hedschema.load_schema(hed_file_path=hed_file_path)
    else:
        the_schema = []
    return the_schema


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

    command = arguments.get(base_constants.COMMAND, '')
    target = arguments.get(base_constants.COMMAND_TARGET, '')
    response = {base_constants.SERVICE: arguments.get(base_constants.SERVICE, ''),
                base_constants.COMMAND: command, base_constants.COMMAND_TARGET: target,
                'results': '', 'error_type': '', 'error_msg': ''}

    if not arguments.get(base_constants.SERVICE, ''):
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
    if results['msg_category'] == 'success' and base_constants.SPREADSHEET in results:
        results[base_constants.SPREADSHEET] = results[base_constants.SPREADSHEET].to_csv(file=None)
    elif base_constants.SPREADSHEET in results:
        del results[base_constants.SPREADSHEET]
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
    services = service_info['services']
    meanings = service_info['parameter_meanings']
    returns = service_info['returns']
    results = service_info['results']
    services_string = '\nServices:\n'
    for service, info in services.items():
        description = info['Description']
        parm_string = json.dumps(info['Parameters'])
        next_string = f'{service}: {description}\n\tParameters: {parm_string}\n'
        services_string += next_string

    meanings_string = '\nParameter meanings:\n'
    for string, meaning in meanings.items():
        meanings_string += f'\t{string}: {meaning}\n'

    returns_string = '\nReturn values:\n'
    for return_val, meaning in returns.items():
        returns_string += f'\t{return_val}: {meaning}\n'

    results_string = '\nResults field meanings:\n'
    for result_val, meaning in results.items():
        results_string += f'\t{result_val}: {meaning}\n'
    data = services_string + meanings_string + returns_string + results_string
    return {base_constants.COMMAND: '', 'data': data, 'output_display_name': '',
            base_constants.SCHEMA_VERSION: '', 'msg_category': 'success',
            'msg': "List of available services and their meanings"}
