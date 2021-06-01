import os
import pandas as pd
# from hed.schema.hed_schema_file import from_string
from hed import schema


if __name__ == '__main__':
    # schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
    # schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
    BASE_DIRECTORY = 'E:/PythonWebMap'
    HED_CACHE_FOLDER = os.path.join(BASE_DIRECTORY, 'schema_cache')
    schema.set_cache_directory(HED_CACHE_FOLDER)
    schema.cache_all_hed_xml_versions()
    hed_info = {'my_list': schema.get_all_hed_versions()}
    print(hed_info)
