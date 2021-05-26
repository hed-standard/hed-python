"""
This module is used to create a HedSchema object from an XML file or tree.
"""

from defusedxml import ElementTree
import xml
from hed.util.exceptions import HedFileError, HedExceptions
from hed.schema.hed_schema_constants import HedKey
from hed.schema.hed_schema import HedSchema
from hed.schema import xml_constants


class HedSchemaXMLParser:
    def __init__(self, hed_xml_file_path, schema_as_string=None):
        self._root_element = self._parse_hed_xml(hed_xml_file_path, schema_as_string)
        # Used to find parent elements of XML nodes during file parsing
        self._parent_map = {c: p for p in self._root_element.iter() for c in p}

        self._legacy_style_xml = False
        self._schema = HedSchema()
        self._schema.filename = hed_xml_file_path
        self._schema.header_attributes = self._get_header_attributes()

        self._populate_attribute_dictionaries()

        self._schema.prologue = self._get_prologue()
        self._schema.epilogue = self._get_epilogue()
        self._populate_dictionaries()
        self._schema.finalize_dictionaries()

    @staticmethod
    def load_xml(xml_file_path=None, schema_as_string=None):
        parser = HedSchemaXMLParser(xml_file_path, schema_as_string)
        return parser._schema

    @staticmethod
    def _parse_hed_xml(hed_xml_file_path, schema_as_string=None):
        """Parses a XML file and returns the root element.

        Parameters
        ----------
        hed_xml_file_path: str
            The path to a HED XML file.
        schema_as_string: str
            Alternate input, a full schema XML file as a string.
        Returns
        -------
        RestrictedElement
            The root element of the HED XML file.

        """
        if schema_as_string and hed_xml_file_path:
            raise HedFileError(HedExceptions.BAD_PARAMETERS, "Invalid parameters to schema creation.",
                               hed_xml_file_path)

        try:
            if hed_xml_file_path:
                hed_xml_tree = ElementTree.parse(hed_xml_file_path)
                root = hed_xml_tree.getroot()
            else:
                root = ElementTree.fromstring(schema_as_string)
        except xml.etree.ElementTree.ParseError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_XML, e.msg, hed_xml_file_path)
        except FileNotFoundError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, hed_xml_file_path)
        except TypeError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), hed_xml_file_path)

        return root

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

    def _populate_attribute_dictionaries(self):
        """Populates a dictionary of dictionaries associated with attributes and their properties

        If this section is not found, default HED2 attributes will be added from hed_2g_attributes.py

        Parameters
        ----------

        Returns
        -------
        """
        section_name = xml_constants.get_section_name(HedKey.Attributes)
        attribute_section = self._get_elements_by_name(section_name)
        if not attribute_section:
            self._schema.add_hed2_attributes()
            self._legacy_style_xml = True
            return
        attribute_section = attribute_section[0]

        def_element_name = xml_constants.get_element_name(HedKey.Attributes)
        attribute_elements = self._get_elements_by_name(def_element_name, attribute_section)
        for element in attribute_elements:
            attribute_name = self._get_element_tag_value(element)
            self._schema._add_attribute_name_to_dict(attribute_name)
            self._parse_node(element, HedKey.Attributes)

    def _populate_tag_dictionaries(self):
        """Populates a dictionary of dictionaries associated with tags and their attributes.

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries that has been populated with dictionaries associated with tag attributes.

        """
        tag_elements = self._get_elements_by_name("node")
        for tag_element in tag_elements:
            tag = self._get_tag_path_from_tag_element(tag_element)
            if self._legacy_style_xml:
                self._parse_node_old(tag_element, HedKey.AllTags, tag)
            else:
                self._parse_node(tag_element, HedKey.AllTags, tag)

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
        section_name = xml_constants.get_section_name(HedKey.Units, self._legacy_style_xml)
        units_section_nodes = self._get_elements_by_name(section_name)
        if len(units_section_nodes) == 0:
            return
        units_section = units_section_nodes[0]

        def_element_name = xml_constants.get_element_name(HedKey.Units, self._legacy_style_xml)
        unit_class_elements = self._get_elements_by_name(def_element_name, units_section)

        if self._legacy_style_xml:
            for unit_class_element in unit_class_elements:
                self._parse_node_old(unit_class_element, HedKey.Units, skip_adding_name=True)
                element_name = self._get_element_tag_value(unit_class_element)
                self._schema._add_unit_class_unit(element_name, None)
                element_units = self._get_elements_by_name(xml_constants.UNIT_CLASS_UNIT_ELEMENT, unit_class_element)
                if not element_units:
                    # Support super legacy format where units were just comma separated on a single line.
                    element_units = self._get_element_tag_value(unit_class_element,
                                                                xml_constants.UNIT_CLASS_UNITS_ELEMENT)
                    if element_units:
                        units = element_units.split(',')
                        units_list = [unit.lower() for unit in units]
                        for unit in units_list:
                            self._schema._add_unit_class_unit(element_name, unit)
                        continue
                    element_units = []

                element_unit_names = [element.text for element in element_units]
                for unit in element_unit_names:
                    self._schema._add_unit_class_unit(element_name, unit)
                for element in element_units:
                    self._parse_node_old(element, HedKey.Units, element_name=element.text,
                                         skip_adding_name=True)
        else:
            for unit_class_element in unit_class_elements:
                self._parse_node(unit_class_element, HedKey.Units, skip_adding_name=True)
                element_name = self._get_element_tag_value(unit_class_element)
                element_units = self._get_elements_by_name(xml_constants.UNIT_CLASS_UNIT_ELEMENT, unit_class_element)
                element_unit_names = [self._get_element_tag_value(element) for element in element_units]
                self._schema._add_unit_class_unit(element_name, None)
                for unit in element_unit_names:
                    self._schema._add_unit_class_unit(element_name, unit)
                for element in element_units:
                    self._parse_node(element, HedKey.Units, skip_adding_name=True)

    def _populate_unit_modifier_dictionaries(self):
        """
        Gets all unit modifier definitions from the

        Returns
        -------

        """
        section_name = xml_constants.get_section_name(HedKey.UnitModifiers, self._legacy_style_xml)
        unit_modifier_section_nodes = self._get_elements_by_name(section_name)
        if len(unit_modifier_section_nodes) == 0:
            return
        unit_modifier_section = unit_modifier_section_nodes[0]
        def_element_name = xml_constants.get_element_name(HedKey.UnitModifiers, self._legacy_style_xml)
        node_elements = self._get_elements_by_name(def_element_name, unit_modifier_section)
        for node_element in node_elements:
            if self._legacy_style_xml:
                self._parse_node_old(node_element, key_class=HedKey.UnitModifiers)
            else:
                self._parse_node(node_element, key_class=HedKey.UnitModifiers)

    def _get_header_attributes(self):
        """
            Gets the schema attributes form the XML root node

        Returns
        -------
        attribute_dict: {str: str}

        """
        return self._root_element.attrib

    def _get_prologue(self):
        prologue_elements = self._get_elements_by_name(xml_constants.PROLOGUE_ELEMENT)
        if len(prologue_elements) == 1:
            return prologue_elements[0].text
        return ""

    def _get_epilogue(self):
        epilogue_elements = self._get_elements_by_name(xml_constants.EPILOGUE_ELEMENT)
        if len(epilogue_elements) == 1:
            return epilogue_elements[0].text
        return ""

    def _parse_node_old(self, node_element, key_class, element_name=None, skip_adding_name=False):
        if element_name:
            node_name = element_name
        else:
            node_name = self._get_element_tag_value(node_element)

        node_desc = self._get_element_tag_value(node_element, xml_constants.DESCRIPTION_ELEMENT)
        if not skip_adding_name:
            self._schema._add_tag_to_dict(node_name, key_class, node_name)
        self._schema._add_description_to_dict(node_name, node_desc, key_class)

        for attribute_name in node_element.attrib:
            new_value = node_element.get(attribute_name)
            if new_value and attribute_name == xml_constants.DEFAULT_UNIT_FOR_OLD_UNIT_CLASS_ATTRIBUTE:
                attribute_name = xml_constants.DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE
            self._schema._add_attribute_to_dict(node_name, attribute_name, new_value, key_class)

    def _parse_node(self, node_element, key_class, element_name=None, skip_adding_name=False):
        if element_name:
            node_name = element_name
        else:
            node_name = self._get_element_tag_value(node_element)
        attribute_desc = self._get_element_tag_value(node_element, xml_constants.DESCRIPTION_ELEMENT)
        if not skip_adding_name:
            self._schema._add_tag_to_dict(node_name, key_class)
        self._schema._add_description_to_dict(node_name, attribute_desc, key_class=key_class)

        for attribute_element in node_element:
            if attribute_element.tag != xml_constants.ATTRIBUTE_PROPERTY_ELEMENTS[key_class]:
                continue
            attribute_name = self._get_element_tag_value(attribute_element)
            attribute_value_elements = self._get_elements_by_name("value", attribute_element)
            attribute_value = ",".join(element.text for element in attribute_value_elements)
            if not attribute_value:
                attribute_value = True
            self._schema._add_attribute_to_dict(node_name, attribute_name, attribute_value, key_class)

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
    def _get_element_tag_value(element, tag_name=xml_constants.NAME_ELEMENT):
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
            return parent_tag_element.findtext(xml_constants.NAME_ELEMENT)
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
