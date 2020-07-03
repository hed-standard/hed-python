# Simplified example code for running wiki2xml

from shutil import copyfile
from hed.converter import wiki2xml
from hed.converter import constants

if __name__ == '__main__':
    # local_hed_file = "hed_711.mediawiki"
    local_hed_file = None
    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/HED-schema.mediawiki'
    result_dict = wiki2xml.convert_hed_wiki_2_xml(hed_wiki_url, local_wiki_file=local_hed_file)
    xml_location = result_dict[constants.HED_XML_LOCATION_KEY]
    copyfile(xml_location, "output.xml")
