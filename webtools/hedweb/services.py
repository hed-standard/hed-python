import os
import io
import json

from flask import current_app
from hed import models
from hed import schema as hedschema
from hedweb.constants import common
from hedweb.dictionary import dictionary_process
from hedweb.events import events_process
from hedweb.spreadsheet import spreadsheet_process, get_prefix_dict
from hedweb.strings import string_process
from hedweb.web_utils import handle_error

app_config = current_app.config


def get_input_from_service_request(request):
    """Gets a dictionary of input from a service request.

    Parameters
    ----------
    request: Request object
        A Request object containing user data for the service request.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the service request.
    """

    form_data = request.data
    form_string = form_data.decode()
    service_request = json.loads(form_string)
    parameters = service_request.get(common.SERVICE_PARAMETERS, None)
    if not parameters:
        parameters = service_request
    arguments = {common.SERVICE: service_request.get(common.SERVICE, None),
                 common.SCHEMA: None,
                 common.JSON_DICTIONARY: None,
                 common.EVENTS: None,
                 common.SPREADSHEET: None,
                 common.HAS_COLUMN_NAMES: parameters.get(common.HAS_COLUMN_NAMES, False),
                 common.STRING_LIST: parameters.get(common.STRING_LIST, None),
                 common.CHECK_FOR_WARNINGS: parameters.get(common.CHECK_FOR_WARNINGS, True),
                 common.DEFS_EXPAND: parameters.get(common.DEFS_EXPAND, True)}
    if common.JSON_STRING in parameters and parameters[common.JSON_STRING]:
        arguments[common.JSON_DICTIONARY] = models.ColumnDefGroup(file=io.StringIO(parameters[common.JSON_STRING]),
                                                                  name='JSON_Dictionary')
    if common.EVENTS_STRING in parameters and parameters[common.EVENTS_STRING]:
        if arguments[common.JSON_DICTIONARY]:
            def_dicts = arguments[common.JSON_DICTIONARY].extract_defs()
        else:
            def_dicts = None
        arguments[common.EVENTS] = models.EventsInput(filename=io.StringIO(parameters[common.EVENTS_STRING]),
                                                      json_def_files=arguments[common.JSON_DICTIONARY],
                                                      def_dicts=def_dicts, file_type='.tsv', name='Events')
    if common.SPREADSHEET_STRING in parameters and parameters[common.SPREADSHEET_STRING]:
        tag_columns, prefix_dict = get_prefix_dict(parameters)
        arguments[common.SPREADSHEET] = \
            models.HedInput(filename=io.StringIO(parameters[common.SPREADSHEET_STRING]), file_type=".tsv",
                            tag_columns=tag_columns, has_column_names=arguments.get(common.HAS_COLUMN_NAMES, None),
                            column_prefix_dictionary=prefix_dict, name='spreadsheet.tsv')
    if common.SCHEMA_STRING in parameters and parameters[common.SCHEMA_STRING]:
        arguments[common.SCHEMA] = hedschema.from_string(parameters[common.SCHEMA_STRING])
    elif common.SCHEMA_URL in parameters and parameters[common.SCHEMA_URL]:
        schema_url = parameters[common.SCHEMA_URL]
        arguments[common.SCHEMA] = hedschema.load_schema(hed_url_path=schema_url)
    elif common.SCHEMA_VERSION in parameters and parameters[common.SCHEMA_VERSION]:
        hed_file_path = hedschema.get_path_from_hed_version(parameters[common.SCHEMA_VERSION])
        arguments[common.SCHEMA] = hedschema.load_schema(hed_file_path=hed_file_path)
    return arguments


def services_process(arguments):
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

    service = arguments.get('service', '')
    response = {'service': service, 'results': '', 'error_type': '', 'error_msg': ''}
    try:
        if not service:
            response["error_type"] = 'HEDServiceMissing'
            response["error_msg"] = "Must specify a valid service"
        elif service == 'get_services':
            response["results"] = services_list()
        elif service == "dictionary_to_long":
            arguments['command'] = common.COMMAND_TO_LONG
            response["results"] = dictionary_process(arguments)
        elif service == "dictionary_to_short":
            arguments['command'] = common.COMMAND_TO_SHORT
            response["results"] = dictionary_process(arguments)
        elif service == "dictionary_validate":
            arguments['command'] = common.COMMAND_VALIDATE
            response["results"] = dictionary_process(arguments)
        elif service == "events_assemble":
            arguments['command'] = common.COMMAND_ASSEMBLE
            response["results"] = events_process(arguments)
        elif service == "events_validate":
            arguments['command'] = common.COMMAND_VALIDATE
            response["results"] = events_process(arguments)
        elif service == "spreadsheet_to_long":
            arguments['command'] = common.COMMAND_TO_LONG
            results = spreadsheet_process(arguments)
            response["results"] = package_spreadsheet(results)
        elif service == "spreadsheet_to_short":
            arguments['command'] = common.COMMAND_TO_SHORT
            results = spreadsheet_process(arguments)
            response["results"] = package_spreadsheet(results)
        elif service == "spreadsheet_validate":
            arguments['command'] = common.COMMAND_VALIDATE
            response["results"] = spreadsheet_process(arguments)
        elif service == "string_to_long":
            arguments['command'] = common.COMMAND_TO_LONG
            response["results"] = string_process(arguments)
        elif service == "string_to_short":
            arguments['command'] = common.COMMAND_TO_SHORT
            response["results"] = string_process(arguments)
        elif service == "string_validate":
            arguments['command'] = common.COMMAND_VALIDATE
            response["results"] = string_process(arguments)
        else:
            response["error_type"] = 'HEDServiceNotSupported'
            response["error_msg"] = f"{service} not supported"
    except Exception as ex:
        errors = handle_error(ex)
        response['error_type'] = errors['error_type']
        response['error_msg'] = errors['error_msg']
    return response


def package_spreadsheet(results):
    if results['msg_category'] == 'success' and common.SPREADSHEET in results:
        results[common.SPREADSHEET] = results[common.SPREADSHEET].to_csv(filename=None)
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
    services = service_info['services']
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
