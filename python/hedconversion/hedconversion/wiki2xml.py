'''
This module contains functions that convert a wiki HED schema into a XML HED schema. 

Created on Feb 27, 2017

@author: Jeremy Cockfield 
'''
from hedemailer import utils;
from hedconversion import parsewiki;
import tempfile;

HED_WIKI_URL = 'https://raw.githubusercontent.com/wiki/BigEEGConsortium/HED-Schema/HED-Schema.mediawiki'


# Downloads the wiki HED schema from github
def download_hed_wiki(wiki_file_location):
    utils.url_to_file(HED_WIKI_URL, wiki_file_location);
    return wiki_file_location;


# Writes a XML element tree object into a XML file
def write_xml_tree_2_xml_file(xml_tree, xml_file_location):
    with open(xml_file_location, 'w') as xml_file:
        xml_string = parsewiki.prettify(xml_tree);
        xml_file.write(xml_string);


# Converts the HED wiki schema into a XML file.
def convert_hed_wiki_2_xml():
    hed_wiki_file_location = create_hed_wiki_file();
    hed_xml_file_location, hed_xml_tree = create_hed_xml_file(hed_wiki_file_location);
    hed_change_log = parsewiki.get_hed_change_log(hed_wiki_file_location);
    hed_info_dictionary = {"hed_xml_tree": hed_xml_tree, "hed_change_log": hed_change_log,
                           "hed_wiki_file_location": hed_wiki_file_location,
                           "hed_xml_file_location": hed_xml_file_location};
    return hed_info_dictionary;


# Creates a HED XML file from a HED wiki schema.
def create_hed_xml_file(hed_wiki_file_location):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as hed_xml_file:
        hed_xml_file_location = hed_xml_file.name;
        hed_xml_tree = parsewiki.hed_wiki_2_xml_tree(hed_wiki_file_location);
        xml_string = parsewiki.prettify(hed_xml_tree);
        hed_xml_file.write(xml_string);
        return hed_xml_file_location, hed_xml_tree;


# Creates a HED wiki schema file from the github wiki schemas.
def create_hed_wiki_file():
    with tempfile.NamedTemporaryFile(delete=False) as hed_wiki_file:
        hed_wiki_file_location = hed_wiki_file.name;
        download_hed_wiki(hed_wiki_file_location);
        return hed_wiki_file_location;
