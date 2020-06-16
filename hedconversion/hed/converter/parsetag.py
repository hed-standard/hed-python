"""
This module contains functions for parsing tags in a wiki HED schema. 

Created on Feb 28, 2017

@author: Jeremy Cockfield
"""

from xml.etree.ElementTree import SubElement
import re

attributes_expression = r'\{.*\}'
description_expression = r'\[.*\]'
extend_here_line = 'extend here'
level_expression = r'\*+'
unit_class_attribute = 'unitClass'
no_wiki_tag = '</?nowiki>'
square_bracket_removal_expression = r'[\[\]]'
tag_name_element = 'name'
invalid_characters_to_strip = ["&#8203"]
tag_name_regexp = r'([<>=#\-a-zA-Z0-9$:()\^µ]+\s*)+'
tag_description_element = 'description'
tag_element = 'node'
true_attribute = 'true'
unit_class_element = 'unitClass'
unit_class_name_element = 'name'
unit_class_units_element = 'units'
unit_class_unit_element = 'unit'
unit_modifier_element = 'unitModifier'
unit_modifier_name_element = 'name'
unit_modifier_description_element = 'description'


def remove_nowiki_tag_from_line(tag_line):
    """Removes the nowiki tag from the  line.

    Parameters
    ----------
    tag_line: string
        A tag line.

    Returns
    -------
    string
        The line with the nowiki tag removed.
    """
    tag_line = re.sub(no_wiki_tag, '', tag_line)
    return tag_line


def get_change_log_entry(change_log_line):
    """Gets the change log entry from the line.

    Parameters
    ----------
    change_log_line: string
        line containing a change log entry.

    Returns
    -------
    string
        The change log entry.
    """
    name = re.compile('[^*]+$')
    match = name.search(change_log_line)
    if match:
        return match.group().strip()
    else:
        return ''


def get_tag_name(tag_line):
    """Gets the tag name from the tag line.

    Parameters
    ----------
    tag_line: string
        A tag line.

    Returns
    -------
    string
        The tag name.
    """
    if tag_line.find(extend_here_line) != -1:
        return ''
    name = re.compile(tag_name_regexp)
    for invalid_chars in invalid_characters_to_strip:
        tag_line = tag_line.replace(invalid_chars, "")
    match = name.search(tag_line)
    if match:
        return match.group().strip()
    else:
        return ''


def get_tag_attributes(tag_line):
    """Gets the tag attributes from a line.

    Parameters
    ----------
    tag_line: string
        A tag line.

    Returns
    -------
    list
        A list containing the tag attributes.
    """
    attributes = re.compile(attributes_expression)
    match = attributes.search(tag_line)
    if match:
        return [x.strip() for x in re.sub('[{}]', '', match.group()).split(',')]
    else:
        return ''


def get_tag_description(tag_line):
    """Gets the tag description from a line.

    Parameters
    ----------
    tag_line: string
        A tag line.

    Returns
    -------
    string
        The tag description.
    """
    description = re.compile(description_expression)
    match = description.search(tag_line)
    if match:
        return re.sub(square_bracket_removal_expression, '', match.group()).strip()
    else:
        return ''


def get_tag_level(tag_line):
    """Gets the tag level from a line in a wiki file.

    Parameters
    ----------
    tag_line: string
        A tag line.

    Returns
    -------
    int
        Gets the tag level. The number of asterisks determine what level the tag is on.
    """
    level = re.compile(level_expression)
    match = level.search(tag_line)
    if match:
        return match.group().count('*')
    else:
        return 1


def add_tag_node(parent_node, tag_line):
    """Adds a tag to its parent.

    Parameters
    ----------
    parent_node: Element
        The parent tag.
    tag_line: string
        A tag line.

    Returns
    -------
    string
        The tag line with the nowiki tag remove.
    """
    tag_node = None
    tag_name = get_tag_name(tag_line)
    if tag_name:
        tag_description = get_tag_description(tag_line)
        tag_attributes = get_tag_attributes(tag_line)
        tag_node = SubElement(parent_node, tag_element)
        name_node = SubElement(tag_node, tag_name_element)
        name_node.text = tag_name
        if tag_description:
            description_node = SubElement(tag_node, tag_description_element)
            description_node.text = tag_description
        if tag_attributes:
            add_tag_node_attributes(tag_node, tag_attributes)
    return tag_node


def add_unit_class_node(parent_node, unit_class, unit_class_units, unit_class_attributes, unit_class_unit_attributes):
    """Adds a unit class to its parent.

    Parameters
    ----------
    parent_node: Element
        The parent of the unit class.
    unit_class: Element
        The unit class.
    unit_class_units: list
        A list of unit class units.
    unit_class_attributes: list
        A list of unit class attributes.
    unit_class_unit_attributes: list
        A list of attributes for a specific unit

    Returns
    -------
    Element
        The unit class element.
    """
    unit_class_node = SubElement(parent_node, unit_class_element)
    name_node = SubElement(unit_class_node, unit_class_name_element)
    name_node.text = unit_class
    units_node = SubElement(unit_class_node, unit_class_units_element)
    for unit, attributes in zip(unit_class_units, unit_class_unit_attributes):
        unit_node = SubElement(units_node, unit_class_unit_element)
        add_tag_node_attributes(unit_node, attributes)
        unit_node.text = unit
    if unit_class_attributes:
        add_tag_node_attributes(unit_class_node, unit_class_attributes)
    return unit_class_node


def add_unit_modifier_node(parent_node, unit_modifier, unit_modifier_attributes, unit_modifier_description):
    """Adds a unit modifier to its parent.

    Parameters
    ----------
    parent_node: Element
        The parent of the unit modifier.
    unit_modifier: Element
        The unit modifier.
    unit_modifier_attributes: list
        A list of unit modifier attributes.
    unit_modifier_description: string
        The unit modifier description.

    Returns
    -------
    Element
        The unit modifier element.
    """
    unit_modifier_node = SubElement(parent_node, unit_modifier_element)
    name_node = SubElement(unit_modifier_node, unit_modifier_name_element)
    name_node.text = unit_modifier
    if unit_modifier_description:
        description_node = SubElement(unit_modifier_node, unit_modifier_description_element)
        description_node.text = unit_modifier_description
    if unit_modifier_attributes:
        add_tag_node_attributes(unit_modifier_node, unit_modifier_attributes)
    return unit_modifier_node


def add_tag_node_attributes(tag_node, tag_attributes):
    """Adds the attributes to a tag.

    Parameters
    ----------
    tag_node: Element
        A tag element.
    tag_attributes: list
        A list containing the tag attributes.

    Returns
    -------

    """
    unitClasses = []
    delimiter = ','
    for attribute in tag_attributes:
        if attribute.startswith(unit_class_attribute):
            split_attribute = attribute.split('=')
            unitClasses.append(split_attribute[1])
        elif attribute.find('=') > -1:
            split_attribute = attribute.split('=')
            tag_node.set(split_attribute[0], split_attribute[1])
        else:
            tag_node.set(attribute, true_attribute)
    if unitClasses:
        tag_node.set(unit_class_attribute, delimiter.join(unitClasses))
