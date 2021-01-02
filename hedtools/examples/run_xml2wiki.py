"""Example for how to convert from xml format to mediawiki format"""
from shutil import move
from hed.schematools import xml2wiki, constants

if __name__ == '__main__':
    hed_xml_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.1.1.xml'
    local_xml_file = None
    result_dict = xml2wiki.convert_hed_xml_2_wiki(hed_xml_url, local_xml_file)
    xml_location = result_dict[constants.HED_OUTPUT_LOCATION_KEY]
    move(xml_location, "output.mediawiki")
