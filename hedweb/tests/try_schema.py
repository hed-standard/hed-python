import os

from hed.schema import hed_schema_file

if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    local_hed_xml = os.path.join(dir_path, 'data/HED8.0.0-alpha.1.xml')
    local_hed_wiki = os.path.join(dir_path, 'data/HED3.mediawiki')

    # Test conversion from xml to mediawiki
    local_hed_schema = hed_schema_file.load_schema(local_hed_xml)
    converted_wiki, errors_wiki = local_hed_schema.save_as_xml()
    print('to here')
