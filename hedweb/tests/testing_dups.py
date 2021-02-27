import json
import os.path


if __name__ == '__main__':
    # hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
    # result_dict = duplicate_nodes.check_for_duplicate_tags(hed_file)
    # output_location = result_dict[constants.HED_OUTPUT_LOCATION_KEY]
    # move(output_location, "duplicate_tags_in_HEDXML.txt")
    # hed_file_path = ''
    # delete_file_if_it_exists(hed_file_path)
    # hed_file_path = None
    # delete_file_if_it_exists(hed_file_path)
    # url = urlparse('')
    # print(url)
    # x = bytearray("abcd", 'utf-8')
    # y = x.decode()
    # print(y)
    #
    dir_path = os.path.dirname(os.path.realpath(__file__))
    the_path = os.path.join(dir_path, 'static/resources/services.json')
    RESOURCE_PATH = './static/resources/services.json'
    with open(the_path) as f:
        service_info = json.load(f)

    print(service_info)

