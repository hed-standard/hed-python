# Simplified example code for running xml2_wiki

from shutil import copyfile
from hed.converter import xml2wiki
from hed.converter import constants

hed_xml_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.1.1.xml'
#local_xml_file = "hed_711.mediawiki"
local_xml_file = None
result_dict = xml2wiki.convert_hed_xml_2_wiki(hed_xml_url, "HED7.1.1.xml")
xml_location = result_dict[constants.HED_WIKI_LOCATION_KEY]
copyfile(xml_location, "output.mediawiki")
