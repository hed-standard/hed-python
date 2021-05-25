import os
import json

from flask import current_app
from hedweb.constants import common
from hedweb.dictionary import dictionary_convert, dictionary_validate
from hedweb.events import events_assemble, events_validate
from hedweb.strings import string_convert, string_validate
from hedweb.web_utils import handle_error

app_config = current_app.config


def services_list():
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
    return {'command': '', 'data': data, 'output_display_name': '',
            'schema_version': '', 'msg_category': 'success',
            'msg': "List of available services and their meanings"}


def services_process(arguments):
    """
    Reports validation status of hed strings associated with EEG events received from EEGLAB plugin HEDTools

    Parameters
    ----------
    arguments dict
        a dictionary of arguments
        Keys include "hed_strings", "check_for_warnings", and "schema_file"

    Returns
    -------
    string
        A serialized JSON string containing information related to the hed strings validation result.
        If the validation fails then a 500 error message is returned.
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
            response["results"] = dictionary_convert(arguments)
        elif service == "dictionary_to_short":
            arguments['command'] = common.COMMAND_TO_SHORT
            response["results"] = dictionary_convert(arguments)
        elif service == "dictionary_validate":
            arguments['command'] = common.COMMAND_VALIDATE
            response["results"] = dictionary_validate(arguments)
        elif service == "events_assemble":
            arguments['command'] = common.COMMAND_ASSEMBLE
            response["results"] = events_assemble(arguments)
        elif service == "events_validate":
            arguments['command'] = common.COMMAND_VALIDATE
            response["results"] = events_validate(arguments)
        elif service == "spreadsheet_validate":
            response["error_type"] = 'HEDServiceNotYetImplemented'
            response["error_msg"] = f"{service} not yet implemented"
        elif service == "string_to_long":
            arguments['command'] = common.COMMAND_TO_LONG
            response["results"] = string_convert(arguments)
        elif service == "string_to_short":
            arguments['command'] = common.COMMAND_TO_SHORT
            response["results"] = string_convert(arguments)
        elif service == "string_validate":
            arguments['command'] = common.COMMAND_VALIDATE
            response["results"] = string_validate(arguments)
        else:
            response["error_type"] = 'HEDServiceNotSupported'
            response["error_msg"] = f"{service} not supported"
    except Exception as ex:
        errors = handle_error(ex)
        response['error_type'] = errors['error_type']
        response['error_msg'] = errors['error_msg']
    return response
