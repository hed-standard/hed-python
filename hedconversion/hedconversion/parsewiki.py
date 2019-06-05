'''
This module contains functions for parsing a wiki HED schema. 

Created on Feb 28, 2017

@author: Jeremy Cockfield
'''
from xml.etree.ElementTree import Element, SubElement;
from xml.etree import ElementTree as et;
from hedconversion import parsetag;
from xml.dom import minidom;
import os;

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


def xml_element_2_str(elem):
    """Converts an XML element to an XML string.

    Parameters
    ----------
    elem: Element
        An XML element.

    Returns
    -------
    string
        A XML string representing the XML element.

    """
    rough_string = et.tostring(elem, method='xml');
    reparsed = minidom.parseString(rough_string);
    return reparsed.toprettyxml(indent="   ");


def remove_last_newline_from_string(str):
    """Removes the last newline character from a string.

    Parameters
    ----------
    str: string
        A string.

    Returns
    -------
    string
        The string with last new line character removed.

    """
    return str[:str.rfind('\n')];


def add_tags(wiki_file):
    """Adds the tags to the HED element.

    Parameters
    ----------
    wiki_file: file object.
        A file object that points to the HED wiki file.

    Returns
    -------

    """
    tag_levels = {};
    line = wiki_file.readline();
    while line:
        line = parsetag.remove_nowiki_tag_from_line(line.strip());
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
            parent_tag = tag_levels[level - 1];
            child_tag = parsetag.add_tag_node(parent_tag, line);
            tag_levels[level] = child_tag;
        line = wiki_file.readline();


def add_unit_classes(wiki_file):
    """Adds the unit classes to the HED element.

    Parameters
    ----------
    wiki_file: file object.
        A file object that points to the HED wiki file.

    Returns
    -------

    """
    unit_class_node = SubElement(hed_node, 'unitClasses');
    unit_class = '';
    unit_class_units = [];
    unit_class_attributes = '';
    line = wiki_file.readline();
    while line:
        line = parsetag.remove_nowiki_tag_from_line(line.strip());
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


def hed_wiki_2_xml_tree(wiki_file_path):
    """Converts a HED wiki file into a XML tree.

    Parameters
    ----------
    wiki_file_path: string
        The location of the HED wiki file.

    Returns
    -------
    Element
        A XML element containing the entire HED.
    """
    hed_node.clear();
    if os.path.exists(wiki_file_path):
        with open(wiki_file_path, 'r', encoding='utf-8') as wiki_file:
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
    return hed_node;


def put_change_log_in_list(wiki_file):
    """Puts the change log from a HED wiki file in a list.

    Parameters
    ----------
    wiki_file: file object.
        A file object that points to the HED wiki file.

    Returns
    -------
    list
        A list containing the change log of the HED wiki file.
    """
    change_log = [];
    index = 0;
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
                change_log[index - 1] += '\n' + parsetag.get_change_log_entry(line);
        line = wiki_file.readline();
    return change_log;


def get_hed_change_log(wiki_file_path):
    """Gets the change log from a HED wiki file.

    Parameters
    ----------
    wiki_file_path: string
        The location of the HED wiki file.

    Returns
    -------
    list
        A list containing the change log of the HED wiki file.
    """
    change_log = [];
    if os.path.exists(wiki_file_path):
        with open(wiki_file_path, 'r', encoding='utf-8') as wiki_file:
            line = wiki_file.readline();
            while line:
                line = line.strip();
                if not line:
                    pass
                if line.startswith(CHANGE_LOG_STRING):
                    change_log = put_change_log_in_list(wiki_file);
                    break
                elif line.startswith(SYNTAX_STRING):
                    break
                line = wiki_file.readline();
    return change_log;


def get_wiki_version(version_line):
    """Gets the HED version from the wiki file.

    Parameters
    ----------
    version_line: string
        The line in the wiki file that contains the version.

    Returns
    -------
    string
        The HED version from the wiki file.
    """
    split = version_line.split(':');
    return split[1].strip();
