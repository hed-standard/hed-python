import os
import json
from hedweb.app_factory import AppFactory



def get_service_string(service_info):
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

    return services_string + meanings_string + returns_string + results_string


if __name__ == '__main__':
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    # the_path = os.path.join(dir_path, '../hedweb/static/resources/services.json')
    # with open(the_path) as f:
    #     services_info = json.load(f)
    # s_info = get_service_string(services_info)
    # print(s_info)

    arguments = {'service': 'string_to_long', 'schema_version': '8.0.0-alpha.1',
                 'string_list': ['Red,Blue', 'Green', 'White,Black'],
                 'check_for_warnings': True, 'command': 'command_to_long'}
    app = AppFactory.create_app('config.TestConfig')
    with app.app_context():
        from hedweb.services import services_process
        response = services_process(arguments)
        print(response)