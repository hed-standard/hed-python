'''
This module contains functions for parsing tags in a wiki HED schema. 

Created on Feb 28, 2017

@author: Jeremy Cockfield
'''

from xml.etree.ElementTree import SubElement;
import re;

# Cleans up the unicode characters in wiki 
def clean_up_tag_line(tag_line):
    tag_line = re.sub('</?nowiki>', '', tag_line);
    return tag_line;

# Gets the change log entry from a line
def get_change_log_entry(tag_line):
    name = re.compile('[^*]+$');
    match = name.search(tag_line);
    if match:
        return match.group().strip();
    else:
        return '';

# Clean this up so that it can be done in one expression (this is a difficult one?) The format of the wiki is inconsistent 
def get_tag_name(tag_line):     
    if tag_line.find('extend here') != -1:
        return '';
    name = re.compile('([<>=#\-a-zA-Z0-9$:()]+\s*)+');
    match = name.search(tag_line);
    if match:
        return match.group().strip();
    else:
        return '';
    
# Gets the tag attributes from a line 
def get_tag_attributes(tag_line):
    attributes = re.compile('\{.*\}');
    match = attributes.search(tag_line);
    if match:
        return [x.strip() for x in re.sub('[{}]', '', match.group()).split(',')];
    else:
        return '';    

# Gets the tag description from a line     
def get_tag_description(tag_line):
    description = re.compile('\[.*\]');
    match = description.search(tag_line);
    if match:
        return re.sub('[\[\]]', '', match.group()).strip();
    else:
        return '';

# Gets the tag level from a line         
def get_tag_level(tag_line):
    level = re.compile('\*+');
    match = level.search(tag_line);
    if match:
        return match.group().count('*');
    else:
        return 1;

# Adds a tag to a element tree node 
def add_tag_node(parent_node, tag_line):
    tag_node = None;
    tag_name = get_tag_name(tag_line);
    if tag_name:
        tag_description = get_tag_description(tag_line);
        tag_attributes = get_tag_attributes(tag_line);
        tag_node = SubElement(parent_node, 'node');
        name_node = SubElement(tag_node, 'name');
        name_node.text = tag_name;
        if tag_description:  
            description_node = SubElement(tag_node, 'description');
            description_node.text = tag_description;
        if tag_attributes:
            add_tag_node_attributes(tag_node, tag_attributes);
    return tag_node

# Adds a unit class to a element tree node     
def add_unit_class_node(parent_node, unit_class, unit_class_units, unit_class_attributes):
    delimiter = ',';
    unit_class_node = SubElement(parent_node, 'unitClass');
    name_node = SubElement(unit_class_node, 'name');
    name_node.text = unit_class;
    units_node = SubElement(unit_class_node, 'units');
    units_node.text = delimiter.join(unit_class_units);
    if unit_class_attributes:
        add_tag_node_attributes(unit_class_node, unit_class_attributes);
    return unit_class_node;

# Adds the attributes to a tag       
def add_tag_node_attributes(tag_node, tag_attributes):
    unitClassStr = 'unitClass';
    unitClasses = [];
    delimiter = ',';
    for attribute in tag_attributes:
        if attribute.startswith(unitClassStr):
            split_attribute = attribute.split('=');
            unitClasses.append(split_attribute[1]);
        elif attribute.find('=') > -1:
            split_attribute = attribute.split('=');
            tag_node.set(split_attribute[0], split_attribute[1]);
        else:
            tag_node.set(attribute, 'true');
    if unitClasses:
        tag_node.set(unitClassStr, delimiter.join(unitClasses));