"""Example for how to convert from xml format to mediawiki format"""
from shutil import move
from hed.schema import xml2wiki, constants

if __name__ == '__main__':
    hed_xml_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.1.1.xml'
    local_xml_file = None
    xml_location, errors = xml2wiki.convert_hed_xml_2_wiki(hed_xml_url, local_xml_file)
    move(xml_location, "output.mediawiki")
