"""
This module is used to create a HedSchema object from an XML file or tree.
"""

from defusedxml.ElementTree import parse
import xml
from hed.util.exceptions import HedFileError, HedExceptions
from hed.schema import hed_schema_constants as constants
from hed.schema.hed_schema_constants import HedKey
from hed.schema.hed_schema import HedSchema


class HedSchemaXMLParser:
    # These should mostly match the HedKey values
    # These are repeated here for clarification primarily
    DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE = HedKey.DefaultUnits
    DEFAULT_UNIT_FOR_OLD_UNIT_CLASS_ATTRIBUTE = HedKey.Default
    UNIT_CLASS_ELEMENT = HedKey.UnitClass
    UNIT_CLASS_UNIT_ELEMENT = 'unit'
    UNIT_CLASS_UNITS_ELEMENT = HedKey.Units
    UNIT_MODIFIER_ELEMENT = 'unitModifier'
    PROLOGUE_ELEMENT = "prologue"
    EPILOGUE_ELEMENT = "epilogue"

    def __init__(self, hed_xml_file_path):
        self._root_element = self._parse_hed_xml_file(hed_xml_file_path)
        # Used to find parent elements of XML nodes during file parsing
        self._parent_map = {c: p for p in self._root_element.iter() for c in p}

        # Required properties
        self.schema_attributes = self._get_schema_attributes()
        self.dictionaries = HedSchema.create_empty_dictionaries()
        self.prologue = self._get_prologue()
        self.epilogue = self._get_epilogue()
        self._populate_dictionaries()

    @staticmethod
    def load_xml(xml_file_path):
        parser = HedSchemaXMLParser(xml_file_path)

        hed_schema = HedSchema()

        hed_schema.filename = xml_file_path
        hed_schema.prologue = parser.prologue
        hed_schema.epilogue = parser.epilogue
        hed_schema.set_dictionaries(parser.dictionaries)
        hed_schema.set_attributes(parser.schema_attributes)

        return hed_schema

    @staticmethod
    def _parse_hed_xml_file(hed_xml_file_path):
        """Parses a XML file and returns the root element.

        Parameters
        ----------
        hed_xml_file_path: str
            The path to a HED XML file.

        Returns
        -------
        RestrictedElement
            The root element of the HED XML file.

        """
        try:
            hed_xml_tree = parse(hed_xml_file_path)
        except xml.etree.ElementTree.ParseError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_XML, e.msg, hed_xml_file_path)
        except FileNotFoundError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, hed_xml_file_path)
        except TypeError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), hed_xml_file_path)

        return hed_xml_tree.getroot()

    def _populate_dictionaries(self):
        """Populates a dictionary of dictionaries that contains all of the tags, tag attributes, unit class units,
           and unit class attributes.

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries that contains all of the tags, tag attributes, unit class units, and unit class
            attributes.

        """
        self._populate_tag_dictionaries()
        self._populate_unit_class_dictionaries()
        self._populate_unit_modifier_dictionaries()

    def _populate_tag_dictionaries(self):
        """Populates a dictionary of dictionaries associated with tags and their attributes.

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries that has been populated with dictionaries associated with tag attributes.

        """
        for dict_key in constants.TAG_ATTRIBUTE_KEYS:
            tags, tag_elements = self._get_tags_by_attribute(dict_key)
            if dict_key in constants.STRING_ATTRIBUTE_DICTIONARY_KEYS:
                tag_dictionary = self._create_tag_to_attribute_dictionary(tags, tag_elements, dict_key)
            else:
                tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
            self.dictionaries[dict_key] = tag_dictionary

        # Finally handle the special cases of all tags, and descriptions
        tags, tag_elements = self._get_all_tags()
        tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
        self.dictionaries[HedKey.Descriptions] = self._get_element_desc(tags, tag_elements)
        self.dictionaries[HedKey.AllTags] = tag_dictionary

    def _populate_unit_class_dictionaries(self):
        """Populates a dictionary of dictionaries associated with all of the unit classes, unit class units, and unit
           class default units.

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries associated with all of the unit classes, unit class units, and unit class
            default units.

        """
        unit_class_elements = self._get_elements_by_name(self.UNIT_CLASS_ELEMENT)
        if len(unit_class_elements) == 0:
            self.has_unit_classes = False
            return
        self.has_unit_classes = True
        self._populate_unit_class_default_unit_dictionary(unit_class_elements)
        self._populate_unit_class_units_dictionary(unit_class_elements)

    def _populate_unit_modifier_dictionaries(self):
        """
        Gets all unit modifier definitions from the

        Returns
        -------

        """
        unit_modifier_elements = self._get_elements_by_name(self.UNIT_MODIFIER_ELEMENT)
        if len(unit_modifier_elements) == 0:
            self.has_unit_modifiers = False
            return
        self.has_unit_modifiers = True
        for unit_modifier_key in constants.UNIT_MODIFIER_DICTIONARY_KEYS:
            self.dictionaries[unit_modifier_key] = {}
        for unit_modifier_element in unit_modifier_elements:
            unit_modifier_name = self._get_element_tag_value(unit_modifier_element)
            unit_modifier_desc = self._get_element_tag_value(unit_modifier_element, "description")
            if unit_modifier_desc:
                self.dictionaries[HedKey.Descriptions][HedKey.SIUnitModifier + unit_modifier_name] = unit_modifier_desc
            for unit_modifier_key in constants.UNIT_MODIFIER_DICTIONARY_KEYS:
                self.dictionaries[unit_modifier_key][unit_modifier_name] = unit_modifier_element.get(unit_modifier_key)

    def _populate_unit_class_units_dictionary(self, unit_class_elements):
        """Populates a dictionary that contains unit class units.

        Parameters
        ----------
        unit_class_elements: list
            A list of unit class elements.

        Returns
        -------
        {}
            A dictionary that contains all the unit class units.

        """
        self.dictionaries[HedKey.Units] = {}
        for unit_class_key in constants.UNIT_CLASS_DICTIONARY_KEYS:
            self.dictionaries[unit_class_key] = {}
        for unit_class_element in unit_class_elements:
            element_name = self._get_element_tag_value(unit_class_element)
            element_desc = self._get_element_tag_value(unit_class_element, "description")
            if element_desc:
                self.dictionaries[HedKey.Descriptions][HedKey.Units + element_name] = element_desc
            element_units = self._get_elements_by_name(self.UNIT_CLASS_UNIT_ELEMENT, unit_class_element)
            if not element_units:
                element_units = self._get_element_tag_value(unit_class_element, self.UNIT_CLASS_UNITS_ELEMENT)
                units = element_units.split(',')
                units_list = list(map(lambda unit: unit.lower(), units))
                self.dictionaries[HedKey.Units][element_name] = units_list
                continue
            element_unit_names = list(map(lambda element: element.text, element_units))
            self.dictionaries[HedKey.Units][element_name] = element_unit_names
            for element_unit in element_units:
                unit_name = element_unit.text
                for unit_class_key in constants.UNIT_CLASS_DICTIONARY_KEYS:
                    self.dictionaries[unit_class_key][unit_name] = element_unit.get(unit_class_key)

    def _populate_unit_class_default_unit_dictionary(self, unit_class_elements):
        """Populates a dictionary that contains unit class default units.

        Parameters
        ----------
        unit_class_elements: list
            A list of unit class elements.

        Returns
        -------
        {}
            A dictionary that contains all the unit class default units.

        """
        self.dictionaries[HedKey.DefaultUnits] = {}
        for unit_class_element in unit_class_elements:
            unit_class_element_name = self._get_element_tag_value(unit_class_element)
            # this is handled in _populate_unit_class_units_dictionary for now.
            # unit_class_desc = self._get_element_tag_value(unit_class_element, "description")
            default_unit = unit_class_element.get(self.DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE)
            if default_unit is None:
                self.dictionaries[HedKey.DefaultUnits][unit_class_element_name] = \
                    unit_class_element.attrib[self.DEFAULT_UNIT_FOR_OLD_UNIT_CLASS_ATTRIBUTE]
            else:
                self.dictionaries[HedKey.DefaultUnits][unit_class_element_name] = default_unit

    @staticmethod
    def _create_tag_to_attribute_dictionary(tag_list, tag_element_list, attribute_name):
        """Populates the dictionaries associated with default unit tags in the attribute dictionary.

        Parameters
        ----------
        tag_list: []
            A list containing tags that have a specific attribute.
        tag_element_list: []
            A list containing tag elements that have a specific attribute.
        attribute_name: str
            The name of the attribute associated with the tags and tag elements.

        Returns
        -------
        {}
            The attribute dictionary that has been populated with dictionaries associated with tags.

        """
        dictionary = {}
        for index, tag in enumerate(tag_list):
            dictionary[tag.lower()] = tag_element_list[index].attrib[attribute_name]
        return dictionary

    @staticmethod
    def _string_list_to_lowercase_dictionary(string_list):
        """Converts a string list into a dictionary. The keys in the dictionary will be the lowercase values of the
           strings in the list.

        Parameters
        ----------
        string_list: list
            A list containing string elements.

        Returns
        -------
        {}
            A dictionary containing the strings in the list.

        """
        lowercase_dictionary = {}
        for string_element in string_list:
            lowercase_dictionary[string_element.lower()] = string_element
        return lowercase_dictionary

    def _get_ancestor_tag_names(self, tag_element):
        """Gets all the ancestor tag names of a tag element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        []
            A list containing all of the ancestor tag names of a given tag.

        """
        ancestor_tags = []
        parent_tag_name = self._get_parent_tag_name(tag_element)
        parent_element = self._parent_map[tag_element]
        while parent_tag_name:
            ancestor_tags.append(parent_tag_name)
            parent_tag_name = self._get_parent_tag_name(parent_element)
            if parent_tag_name:
                parent_element = self._parent_map[parent_element]
        return ancestor_tags

    @staticmethod
    def _get_element_tag_value(element, tag_name='name'):
        """Gets the value of the element's tag.

        Parameters
        ----------
        element: Element
            A element in the HED XML file.
        tag_name: str
            The name of the XML element's tag. The default is 'name'.

        Returns
        -------
        str
            The value of the element's tag. If the element doesn't have the tag then it will return an empty string.

        """
        element = element.find(tag_name)
        if element is not None:
            return element.text
        return ""

    def _get_parent_tag_name(self, tag_element):
        """Gets the name of the tag parent element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        str
            The name of the tag element's parent. If there is no parent tag then an empty string is returned.

        """
        parent_tag_element = self._parent_map[tag_element]
        if parent_tag_element is not None:
            return parent_tag_element.findtext('name')
        else:
            return ''

    def _get_tag_path_from_tag_element(self, tag_element):
        """Gets the tag path from a given tag element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        str
            A tag path which is typically referred to as a tag. The tag and it's ancestor tags will be separated by /'s.

        """
        ancestor_tag_names = self._get_ancestor_tag_names(tag_element)
        ancestor_tag_names.insert(0, self._get_element_tag_value(tag_element))
        ancestor_tag_names.reverse()
        return '/'.join(ancestor_tag_names)

    def _get_schema_attributes(self):
        """
            Gets the schema attributes form the XML root node

        Returns
        -------
        attribute_dict: {str: str}

        """
        return self._root_element.attrib

    def _get_prologue(self):
        prologue_elements = self._get_elements_by_name(self.PROLOGUE_ELEMENT)
        if len(prologue_elements) == 1:
            return prologue_elements[0].text
        return ""

    def _get_epilogue(self):
        epilogue_elements = self._get_elements_by_name(self.EPILOGUE_ELEMENT)
        if len(epilogue_elements) == 1:
            return epilogue_elements[0].text
        return ""

    def _get_tags_by_attribute(self, attribute_name):
        """Gets the tag that have a specific attribute.

        Parameters
        ----------
        attribute_name: str
            The name of the attribute associated with the tags.

        Returns
        -------
        tuple
            A tuple containing tags and tag elements that have a specified attribute.

        """
        tags = []
        tag_elements = self._root_element.findall('.//node[@%s]' % attribute_name)
        for attribute_tag_element in tag_elements:
            tag = self._get_tag_path_from_tag_element(attribute_tag_element)
            tags.append(tag)
        return tags, tag_elements

    def _get_all_tags(self, tag_element_name='node'):
        """Gets the tags that have a specific attribute.

        Parameters
        ----------
        tag_element_name: str
            The XML tag name of the tag elements. The default is 'node'.

        Returns
        -------
        tuple
            A tuple containing all the tags and tag elements in the XML file.

        """
        tags = []
        tag_elements = self._root_element.findall('.//%s' % tag_element_name)
        for tag_element in tag_elements:
            tag = self._get_tag_path_from_tag_element(tag_element)
            tags.append(tag)
        return tags, tag_elements

    def _get_elements_by_name(self, element_name='node', parent_element=None):
        """Gets the elements that have a specific element name.

        Parameters
        ----------
        element_name: str
            The name of the element. The default is 'node'.
        parent_element: RestrictedElement
            The parent element. The default is 'None'. If a parent element is specified then only the children of the
            parent will be returned with the given 'element_name'. If not specified the root element will be the parent.

        Returns
        -------
        []
            A list containing elements that have a specific element name.

        """
        if parent_element is None:
            elements = self._root_element.findall('.//%s' % element_name)
        else:
            elements = parent_element.findall('.//%s' % element_name)
        return elements

    @staticmethod
    def _get_element_desc(tags, tag_elements):
        """
            Create a dictionary of descriptions for the given tags and elements

        Parameters
        ----------
        tags : [str]
            The list of tags to get descriptions for
        tag_elements : [Element]
            The matching list of XML elements to get descriptions from
        Returns
        -------
        desc_dict: {str: str}
            {tag : description} for any tags that have one.
        """
        tags_desc = {}
        for tag, tag_element in zip(tags, tag_elements):
            for child in tag_element:
                if child.tag == "description":
                    tags_desc[tag] = child.text
        return tags_desc
