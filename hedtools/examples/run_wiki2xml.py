"""Example for how to convert from mediawiki format to xml format"""
from shutil import move
from hed.schematools import wiki2xml, constants

if __name__ == '__main__':
    local_hed_file = None
    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/HED-schema.mediawiki'
    result_dict = wiki2xml.convert_hed_wiki_2_xml(hed_wiki_url, local_wiki_file=local_hed_file)
    xml_location = result_dict[constants.HED_OUTPUT_LOCATION_KEY]
    move(xml_location, "output.xml")