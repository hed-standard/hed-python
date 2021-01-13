import os
import os.path
from urllib.parse import urlparse
from shutil import move
from hed.schema import duplicate_nodes
from hed.schema import constants
from hed.util.file_util import delete_file_if_it_exist, url_to_file, get_file_extension, write_text_iter_to_file

if __name__ == '__main__':
    # hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
    # result_dict = duplicate_nodes.check_for_duplicate_tags(hed_file)
    # output_location = result_dict[constants.HED_OUTPUT_LOCATION_KEY]
    # move(output_location, "duplicate_tags_in_HEDXML.txt")
    hed_file_path = ''
    delete_file_if_it_exist(hed_file_path)
    hed_file_path = None
    delete_file_if_it_exist(hed_file_path)
    url = urlparse('')
    print(url)