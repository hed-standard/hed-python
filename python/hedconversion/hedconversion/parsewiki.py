'''
This module contains functions for parsing a wiki HED schema. 

Created on Feb 28, 2017

@author: Jeremy Cockfield
'''
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree as et
import parsetag
from xml.dom import minidom
import codecs
import os

ATTRIBUTE_DEFINITION_STRING = '\'\'\'Attribute Definitions:'
CHANGE_LOG_STRING = 'Changelog'
SYNTAX_STRING = '\'\'\'Syntax'
ROOT_TAG = '\'\'\''
HED_NODE_NAME = 'HED'
HED_VERSION_STRING = 'HED version:'
START_STRING = '!# start hed' 
UNIT_CLASS_STRING = '\'\'\'Unit classes'
END_STRING = '!# end hed'
hed_node = Element('HED')  

# Prints an element tree 
def prettify(elem):
    rough_string = et.tostring(elem, encoding='utf-8', method='xml');
    reparsed = minidom.parseString(rough_string);
    prettified_string = reparsed.toprettyxml(indent="   ", encoding='utf-8');
    return prettified_string[:prettified_string.rfind('\n')];

# Removes the last line from a string 
def remove_last_line_from_string(s):
    return s[:s.rfind('\n')];

# Adds the tags to an element tree containing the HED 
def add_tags(wiki_file):
    tag_levels = {};
    line = wiki_file.readline();
    while line:
        line = parsetag.clean_up_tag_line(line.strip());
        if not line:
            pass
        elif line.startswith(UNIT_CLASS_STRING):
            add_unit_classes(wiki_file);
            break
        elif line.startswith(ROOT_TAG):
            root_tag = parsetag.add_tag_node(hed_node, line);
            tag_levels[0] = root_tag;
        else:
            level = parsetag.get_tag_level(line);
            parent_tag = tag_levels[level-1];
            child_tag = parsetag.add_tag_node(parent_tag, line);
            tag_levels[level] = child_tag;
        line = wiki_file.readline();
    return

# Adds the unit classes to an element tree containing the HED 
def add_unit_classes(wiki_file):
    unit_class_node = SubElement(hed_node, 'unitClasses');
    unit_class = '';
    unit_class_units = [];
    unit_class_attributes = '';
    line = wiki_file.readline();
    while line:
        line =  parsetag.clean_up_tag_line(line.strip());
        if not line:
            pass
        elif line.startswith(END_STRING):          
            break
        else:
            level = parsetag.get_tag_level(line);   
            if level == 1:
                if unit_class_units:      
                    parsetag.add_unit_class_node(unit_class_node, unit_class, unit_class_units, unit_class_attributes);     
                unit_class = parsetag.get_tag_name(line);
                unit_class_attributes = parsetag.get_tag_attributes(line);            
                unit_class_units = [];
            else:
                unit_class_unit = parsetag.get_tag_name(line);
                unit_class_units.append(unit_class_unit);
        line = wiki_file.readline();
    parsetag.add_unit_class_node(unit_class_node, unit_class, unit_class_units, unit_class_attributes);

# Converts a HED wiki file into a element tree         
def hed_wiki_2_xml_tree(wiki_file_location):
    hed_node.clear();
    wiki_file = None;
    if os.path.exists(wiki_file_location):
        try:
            wiki_file = codecs.open(wiki_file_location, 'r', 'utf-8');
            line = wiki_file.readline();
            while line:
                line = line.strip();
                if not line:
                    pass
                if line.startswith(HED_VERSION_STRING):
                    version_number = get_wiki_version(line);
                    hed_node.set('version', version_number);
                elif line.startswith(START_STRING):
                    add_tags(wiki_file);
                    break
                line = wiki_file.readline();
        finally:
            if wiki_file:
                wiki_file.close();
    return hed_node

# Stores the wiki change log in a list 
def change_log_2_list(wiki_file):
    change_log = [];
    index = 0;
    try:
        line = wiki_file.readline();
        while line:
            line = line.strip();
            if not line:
                pass
            elif line.startswith(SYNTAX_STRING):
                break
            else:
                level = parsetag.get_tag_level(line);   
                if level == 1:
                    change_log.append(parsetag.get_change_log_entry(line));
                    index += 1;
                else: 
                    change_log[index-1] += '\n' + parsetag.get_change_log_entry(line);                    
            line = wiki_file.readline();
    finally:
        wiki_file.close();
    return change_log;

# Gets the change log from a wiki HED file 
def get_hed_change_log(wiki_file_location):
    wiki_file = None;
    change_log = [];
    if os.path.exists(wiki_file_location):
        try:
            wiki_file = codecs.open(wiki_file_location, 'r', 'utf-8');
            line = wiki_file.readline();
            while line:
                line = line.strip();
                if not line:
                    pass
                if line.startswith(CHANGE_LOG_STRING):
                    change_log = change_log_2_list(wiki_file);
                    break
                elif line.startswith(SYNTAX_STRING):
                    break
                line = wiki_file.readline();
        finally:
            if wiki_file:
                wiki_file.close();
    return change_log;

# Gets the HED wiki version 
def get_wiki_version(version_line):
    split = version_line.split(':');
    return split[1].strip();