'''
This module contains functions that convert a wiki HED schema into a XML HED schema. 

Created on Feb 27, 2017

@author: Jeremy Cockfield 
'''
from hedemailer.hedconversion.parsewiki import hed_wiki_2_xml_tree, get_hed_change_log, prettify
import os
import tempfile
import urllib

HED_WIKI_URL = 'https://raw.githubusercontent.com/wiki/BigEEGConsortium/HED-Schema/HED-Schema.mediawiki'

# Write data from a URL into a file     
def url_to_file(file_url, file_location):
    wiki_url_opener = urllib.URLopener();
    wiki_url_opener.retrieve(file_url, file_location);
    wiki_url_opener.close();

# Downloads the wiki HED schema from github
def download_hed_wiki(wiki_file_location):
    url_to_file(HED_WIKI_URL, wiki_file_location);
    return wiki_file_location;

# Writes a XML element tree object into a XML file 
def write_xml_tree_2_xml_file(xml_tree, xml_file_location):
    xml_file = None;
    try:
        xml_file = open(xml_file_location, 'w');
        xml_string = prettify(xml_tree);
        xml_file.write(xml_string);
    finally:
        if xml_file: 
            xml_file.close();
    return xml_file_location;

# Deletes the file if it exist
def delete_file_if_exist(file_location):
    file_exist = False;
    if os.path.isfile(file_location):
        os.remove(file_location); 
        file_exist = True;   
    return file_exist;

# Converts the HED wiki schema into a XML file.    
def convert_hed_wiki_2_xml():
    hed_info_dictionary = {};
    hed_wiki_file_location = '';
    hed_xml_file_location = '';
    try:
        hed_wiki_file_location = create_hed_wiki_file();
        hed_xml_file_location, hed_xml_tree = create_hed_xml_file(hed_wiki_file_location);
        hed_change_log = get_hed_change_log(hed_wiki_file_location);
        hed_info_dictionary = {"hed_xml_tree":hed_xml_tree,"hed_change_log":hed_change_log,
                               "hed_wiki_file_location":hed_wiki_file_location,
                               "hed_xml_file_location":hed_xml_file_location};
    except:
        delete_file_if_exist(hed_wiki_file_location);
        delete_file_if_exist(hed_xml_file_location);      
    return hed_info_dictionary;

# Creates a HED XML file from a HED wiki schema. 
def create_hed_xml_file(hed_wiki_file_location):
        hed_xml_file = tempfile.NamedTemporaryFile(delete=False);
        hed_xml_file_location = hed_xml_file.name;
        hed_xml_tree = hed_wiki_2_xml_tree(hed_wiki_file_location);
        xml_string = prettify(hed_xml_tree);
        hed_xml_file.write(xml_string);
        hed_xml_file.close();
#         write_xml_tree_2_xml_file(hed_xml_tree, hed_xml_file_location);
        return hed_xml_file_location, hed_xml_tree;

# Creates a HED wiki schema file from the github wiki schemas.  
def create_hed_wiki_file():
        hed_wiki_file = tempfile.NamedTemporaryFile(delete=False);
        hed_wiki_file_location = hed_wiki_file.name;
        download_hed_wiki(hed_wiki_file_location);
        hed_wiki_file.close();
        return hed_wiki_file_location;