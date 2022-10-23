"""
This module is used to create a HedSchema object from an XML file or tree.
"""

from defusedxml import ElementTree
import xml
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema import HedSchema
from hed.schema.schema_io import xml_constants


class HedSchemaXMLParser:
    def __init__(self, hed_xml_file_path, schema_as_string=None):
        self._root_element = self._parse_hed_xml(hed_xml_file_path, schema_as_string)
        # Used to find parent elements of XML nodes during file parsing
        self._parent_map = {c: p for p in self._root_element.iter() for c in p}

        self._schema = HedSchema()
        self._schema.filename = hed_xml_file_path
        self._schema.header_attributes = self._get_header_attributes()

        self._populate_property_dictionaries()
        self._populate_attribute_dictionaries()
        self._populate_value_class_dictionaries()

        self._schema.prologue = self._get_prologue()
        self._schema.epilogue = self._get_epilogue()
        self._populate_unit_modifier_dictionaries()
        self._populate_unit_class_dictionaries()
        self._populate_tag_dictionaries()
        self._schema.finalize_dictionaries()

    @staticmethod
    def load_xml(xml_file_path=None, schema_as_string=None):
        parser = HedSchemaXMLParser(xml_file_path, schema_as_string)
        return parser._schema

    @staticmethod
    def _parse_hed_xml(hed_xml_file_path, schema_as_string=None):
        """Parses an XML file and returns the root element.

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

    def _populate_property_dictionaries(self):
        """Populates a dictionary of dictionaries associated with properties

        Parameters
        ----------

        Returns
        -------
        """
        section_name = xml_constants.SECTION_NAMES[HedSectionKey.Properties]
        properties_section = self._get_elements_by_name(section_name)
        if properties_section:
            properties_section = properties_section[0]

            def_element_name = xml_constants.ELEMENT_NAMES[HedSectionKey.Properties]
            attribute_elements = self._get_elements_by_name(def_element_name, properties_section)
            for element in attribute_elements:
                self._parse_node(element, HedSectionKey.Properties)

    def _populate_attribute_dictionaries(self):
        """Populates a dictionary of dictionaries associated with attributes and their properties

        Parameters
        ----------

        Returns
        -------
        """
        section_name = xml_constants.SECTION_NAMES[HedSectionKey.Attributes]
        attribute_section = self._get_elements_by_name(section_name)
        if attribute_section:
            attribute_section = attribute_section[0]

            def_element_name = xml_constants.ELEMENT_NAMES[HedSectionKey.Attributes]
            attribute_elements = self._get_elements_by_name(def_element_name, attribute_section)
            for element in attribute_elements:
                self._parse_node(element, HedSectionKey.Attributes)

    def _populate_value_class_dictionaries(self):
        section_name = xml_constants.SECTION_NAMES[HedSectionKey.ValueClasses]
        value_class_section = self._get_elements_by_name(section_name)
        if not value_class_section:
            return
        value_class_section = value_class_section[0]
        def_element_name = xml_constants.ELEMENT_NAMES[HedSectionKey.ValueClasses]
        attribute_elements = self._get_elements_by_name(def_element_name, value_class_section)
        for element in attribute_elements:
            self._parse_node(element, HedSectionKey.ValueClasses)

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
            self._parse_node(tag_element, HedSectionKey.AllTags, tag)

    def _populate_unit_class_dictionaries(self):
        """Populates a dictionary of dictionaries associated with all the unit classes, unit class units, and unit
           class default units.

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries associated with all the unit classes, unit class units, and unit class
            default units.

        """
        section_name = xml_constants.SECTION_NAMES[HedSectionKey.UnitClasses]
        units_section_nodes = self._get_elements_by_name(section_name)
        if len(units_section_nodes) == 0:
            return
        units_section = units_section_nodes[0]

        def_element_name = xml_constants.ELEMENT_NAMES[HedSectionKey.UnitClasses]
        unit_class_elements = self._get_elements_by_name(def_element_name, units_section)

        for unit_class_element in unit_class_elements:
            unit_class_entry = self._parse_node(unit_class_element, HedSectionKey.UnitClasses)
            element_units = self._get_elements_by_name(xml_constants.UNIT_CLASS_UNIT_ELEMENT, unit_class_element)
            element_unit_names = [self._get_element_tag_value(element) for element in element_units]

            for unit, element in zip(element_unit_names, element_units):
                unit_class_unit_entry = self._parse_node(element, HedSectionKey.Units)
                unit_class_entry.add_unit(unit_class_unit_entry)

    def _populate_unit_modifier_dictionaries(self):
        """
        Gets all unit modifier definitions from the

        Returns
        -------

        """
        section_name = xml_constants.SECTION_NAMES[HedSectionKey.UnitModifiers]
        unit_modifier_section_nodes = self._get_elements_by_name(section_name)
        if len(unit_modifier_section_nodes) == 0:
            return
        unit_modifier_section = unit_modifier_section_nodes[0]
        def_element_name = xml_constants.ELEMENT_NAMES[HedSectionKey.UnitModifiers]
        node_elements = self._get_elements_by_name(def_element_name, unit_modifier_section)
        for node_element in node_elements:
            self._parse_node(node_element, key_class=HedSectionKey.UnitModifiers)

    def _reformat_xsd_attrib(self, attrib_dict):
        final_attrib = {}
        for attrib_name in attrib_dict:
            if attrib_name == xml_constants.NO_NAMESPACE_XSD_KEY:
                xsd_value = attrib_dict[attrib_name]
                final_attrib[xml_constants.NS_ATTRIB] = xml_constants.XSI_SOURCE
                final_attrib[xml_constants.NO_LOC_ATTRIB] = xsd_value
            else:
                final_attrib[attrib_name] = attrib_dict[attrib_name]

        return final_attrib

    def _get_header_attributes(self):
        """
            Gets the schema attributes form the XML root node

        Returns
        -------
        attribute_dict: {str: str}

        """
        return self._reformat_xsd_attrib(self._root_element.attrib)

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

    def _parse_node(self, node_element, key_class, element_name=None):
        if element_name:
            node_name = element_name
        else:
            node_name = self._get_element_tag_value(node_element)
        attribute_desc = self._get_element_tag_value(node_element, xml_constants.DESCRIPTION_ELEMENT)
        tag_entry = self._schema._add_tag_to_dict(node_name, key_class)
        if attribute_desc:
            tag_entry.description = attribute_desc

        for attribute_element in node_element:
            if attribute_element.tag != xml_constants.ATTRIBUTE_PROPERTY_ELEMENTS[key_class]:
                continue
            attribute_name = self._get_element_tag_value(attribute_element)
            attribute_value_elements = self._get_elements_by_name("value", attribute_element)
            attribute_value = ",".join(element.text for element in attribute_value_elements)
            # Todo: do we need to validate this here?
            if not attribute_value:
                attribute_value = True
            tag_entry.set_attribute_value(attribute_name, attribute_value)

        return tag_entry

    def _get_ancestor_tag_names(self, tag_element):
        """ Get all ancestor tag names of a tag element.

        Parameters:
            tag_element (Element): A tag element in the HED XML file.

        Returns:
            list: Contains all the ancestor tag names of a given tag.

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

    def _get_element_tag_value(self, element, tag_name=xml_constants.NAME_ELEMENT):
        """ Get the value of the element's tag.

        Parameters:
            element (Element): A element in the HED XML file.
            tag_name (str): The name of the XML element's tag. The default is 'name'.

        Returns:
            str: The value of the element's tag.

        Notes:
            If the element doesn't have the tag then it will return an empty string.

        """
        element = element.find(tag_name)
        if element is not None:
            if element.text is None and tag_name != "units":
                raise HedFileError(HedExceptions.HED_SCHEMA_NODE_NAME_INVALID,
                                   f"A Schema node is empty for tag of element name: '{tag_name}'.",
                                   self._schema.filename)
            return element.text
        return ""

    def _get_parent_tag_name(self, tag_element):
        """ Return the name of the tag parent element.

        Parameters:
            tag_element (Element): A tag element in the HED XML file.

        Returns:
            str: The name of the tag element's parent.

        Notes:
            If there is no parent tag then an empty string is returned.

        """
        parent_tag_element = self._parent_map[tag_element]
        if parent_tag_element is not None:
            return parent_tag_element.findtext(xml_constants.NAME_ELEMENT)
        else:
            return ''

    def _get_tag_path_from_tag_element(self, tag_element):
        """ Get the tag path from a given tag element.

        Parameters:
            tag_element (Element): A tag element in the HED XML file.

        Returns:
            str: A tag path which is typically referred to as a tag.

        Notes:
            The tag and it's ancestor tags will be separated by /'s.

        """
        ancestor_tag_names = self._get_ancestor_tag_names(tag_element)
        ancestor_tag_names.insert(0, self._get_element_tag_value(tag_element))
        ancestor_tag_names.reverse()
        return '/'.join(ancestor_tag_names)

    def _get_elements_by_name(self, element_name='node', parent_element=None):
        """ Get the elements that have a specific element name.

        Parameters:
            element_name (str): The name of the element. The default is 'node'.
            parent_element (RestrictedElement or None): The parent element.

        Returns:
            list: A list containing elements that have a specific element name.
        Notes:
            If a parent element is specified then only the children of the
            parent will be returned with the given 'element_name'.
            If not specified the root element will be the parent.

        """
        if parent_element is None:
            elements = self._root_element.findall('.//%s' % element_name)
        else:
            elements = parent_element.findall('.//%s' % element_name)
        return elements
