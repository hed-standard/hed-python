"""Example for how to convert from xml format to mediawiki format"""
from shutil import move
from hed.schema import xml2wiki

if __name__ == '__main__':
    hed_xml_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.1.1.xml'
    local_xml_file = None
    mediawiki_location, errors = xml2wiki.convert_hed_xml_2_wiki(hed_xml_url, local_xml_file,
                                                                 display_filename="HED7.1.1.xml")
    for issue in errors:
        print(issue['message'])
    if mediawiki_location:
        move(mediawiki_location, "HED7.1.1.mediawiki")
