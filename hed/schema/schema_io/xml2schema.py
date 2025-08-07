"""
This module is used to create a HedSchema object from an XML file or tree.
"""

from defusedxml import ElementTree
import xml
import pandas as pd

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.hed_schema_constants import HedSectionKey, HedKey, NS_ATTRIB, NO_LOC_ATTRIB
from hed.schema.schema_io import xml_constants, df_constants
from hed.schema.schema_io.base2schema import SchemaLoader
from functools import partial


class SchemaLoaderXML(SchemaLoader):
    """ Loads XML schemas from filenames or strings.

        Expected usage is SchemaLoaderXML.load(filename)

        SchemaLoaderXML(filename) will load just the header_attributes
    """
    def __init__(self, filename, schema_as_string=None, schema=None, file_format=None, name=""):
        super().__init__(filename, schema_as_string, schema, file_format, name)
        self._root_element = None
        self._parent_map = {}
        self._schema.source_format = ".xml"

    def _open_file(self):
        """Parses an XML file and returns the root element."""
        try:
            if self.filename:
                hed_xml_tree = ElementTree.parse(self.filename)
                root = hed_xml_tree.getroot()
            else:
                root = ElementTree.fromstring(self.schema_as_string)
        except xml.etree.ElementTree.ParseError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_XML, e.msg, self.name)

        return root

    def _get_header_attributes(self, root_element):
        """Gets the schema attributes from the XML root node"""
        return self._reformat_xsd_attrib(root_element.attrib)

    def _parse_data(self):
        self._root_element = self.input_data
        self._parent_map = {c: p for p in self._root_element.iter() for c in p}

        parse_order = {
            HedSectionKey.Properties: partial(self._populate_section, HedSectionKey.Properties),
            HedSectionKey.Attributes: partial(self._populate_section, HedSectionKey.Attributes),
            HedSectionKey.UnitModifiers: partial(self._populate_section, HedSectionKey.UnitModifiers),
            HedSectionKey.UnitClasses: self._populate_unit_class_dictionaries,
            HedSectionKey.ValueClasses: partial(self._populate_section, HedSectionKey.ValueClasses),
            HedSectionKey.Tags: self._populate_tag_dictionaries,
        }
        self._schema.prologue = self._read_prologue()
        self._schema.epilogue = self._read_epilogue()
        self._read_extras()
        self._parse_sections(self._root_element, parse_order)

    def _parse_sections(self, root_element, parse_order):
        for section_key in parse_order:
            section_name = xml_constants.SECTION_ELEMENTS[section_key]
            section_element = self._get_elements_by_name(section_name, root_element)
            if section_element:
                section_element = section_element[0]
            if isinstance(section_element, list):
                raise HedFileError(HedExceptions.INVALID_HED_FORMAT,
                                   "Attempting to load an outdated or invalid XML schema", self.name)
            parse_func = parse_order[section_key]
            parse_func(section_element)

    def _populate_section(self, key_class, section):
        self._schema._initialize_attributes(key_class)
        def_element_name = xml_constants.ELEMENT_NAMES[key_class]
        attribute_elements = self._get_elements_by_name(def_element_name, section)
        for element in attribute_elements:
            new_entry = self._parse_node(element, key_class)
            self._add_to_dict(new_entry, key_class)

    def _read_prologue(self):
        prologue_elements = self._get_elements_by_name(xml_constants.PROLOGUE_ELEMENT)
        if len(prologue_elements) == 1:
            return prologue_elements[0].text
        return ""

    def _read_epilogue(self):
        epilogue_elements = self._get_elements_by_name(xml_constants.EPILOGUE_ELEMENT)
        if len(epilogue_elements) == 1:
            return epilogue_elements[0].text
        return ""

    def _read_extras(self):
        self._schema.extras = {}
        self._read_sources()
        self._read_prefixes()
        self._read_external_annotations()

    def _read_sources(self):
        source_elements = self._get_elements_by_name(xml_constants.SCHEMA_SOURCE_DEF_ELEMENT)
        data = []
        for source_element in source_elements:
            source_name = self._get_element_value(source_element, xml_constants.NAME_ELEMENT)
            source_link = self._get_element_value(source_element, xml_constants.LINK_ELEMENT)
            description = self._get_element_value(source_element, xml_constants.DESCRIPTION_ELEMENT)
            data.append({df_constants.source: source_name, df_constants.link: source_link,
                         df_constants.description: description})
        self._schema.extras[df_constants.SOURCES_KEY] = pd.DataFrame(data, columns=df_constants.source_columns)

    def _read_prefixes(self):
        prefix_elements = self._get_elements_by_name(xml_constants.SCHEMA_PREFIX_DEF_ELEMENT)
        data = []
        for prefix_element in prefix_elements:
            prefix_name = self._get_element_value(prefix_element, xml_constants.NAME_ELEMENT)
            prefix_namespace= self._get_element_value(prefix_element, xml_constants.NAMESPACE_ELEMENT)
            prefix_description = self._get_element_value(prefix_element, xml_constants.DESCRIPTION_ELEMENT)
            data.append({df_constants.prefix: prefix_name, df_constants.namespace: prefix_namespace,
                         df_constants.description: prefix_description})
        self._schema.extras[df_constants.PREFIXES_KEY] = pd.DataFrame(data, columns=df_constants.prefix_columns)

    def _read_external_annotations(self):
        external_elements = self._get_elements_by_name(xml_constants.SCHEMA_EXTERNAL_DEF_ELEMENT)
        data = []
        for external_element in external_elements:
            external_name = self._get_element_value(external_element, xml_constants.NAME_ELEMENT)
            external_id = self._get_element_value(external_element, xml_constants.ID_ELEMENT)
            external_iri = self._get_element_value(external_element, xml_constants.IRI_ELEMENT)
            external_description = self._get_element_value(external_element, xml_constants.DESCRIPTION_ELEMENT)
            data.append({df_constants.prefix: external_name, df_constants.id: external_id,
                         df_constants.iri: external_iri, df_constants.description: external_description})
        self._schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY] = pd.DataFrame(data, columns=df_constants.external_annotation_columns)

    def _add_tags_recursive(self, new_tags, parent_tags):
        for tag_element in new_tags:
            current_tag = self._get_element_tag_value(tag_element)
            parents_and_child = parent_tags + [current_tag]
            full_tag = "/".join(parents_and_child)

            tag_entry = self._parse_node(tag_element, HedSectionKey.Tags, full_tag)

            rooted_entry = self.find_rooted_entry(tag_entry, self._schema, self._loading_merged)
            if rooted_entry:
                loading_from_chain = rooted_entry.name + "/" + tag_entry.short_tag_name
                loading_from_chain_short = tag_entry.short_tag_name

                full_tag = full_tag.replace(loading_from_chain_short, loading_from_chain)
                tag_entry = self._parse_node(tag_element, HedSectionKey.Tags, full_tag)
                parents_and_child = full_tag.split("/")

            self._add_to_dict(tag_entry, HedSectionKey.Tags)
            child_tags = tag_element.findall("node")
            self._add_tags_recursive(child_tags, parents_and_child)

    def _populate_tag_dictionaries(self, tag_section):
        """Populates a dictionary of dictionaries associated with tags and their attributes."""
        self._schema._initialize_attributes(HedSectionKey.Tags)
        root_tags = tag_section.findall("node")

        self._add_tags_recursive(root_tags, [])

    def _populate_unit_class_dictionaries(self, unit_section):
        """Populates a dictionary of dictionaries associated with all the unit classes, unit class units, and unit
           class default units."""
        self._schema._initialize_attributes(HedSectionKey.UnitClasses)
        self._schema._initialize_attributes(HedSectionKey.Units)
        def_element_name = xml_constants.ELEMENT_NAMES[HedSectionKey.UnitClasses]
        unit_class_elements = self._get_elements_by_name(def_element_name, unit_section)

        for unit_class_element in unit_class_elements:
            unit_class_entry = self._parse_node(unit_class_element, HedSectionKey.UnitClasses)
            unit_class_entry = self._add_to_dict(unit_class_entry, HedSectionKey.UnitClasses)
            if unit_class_entry is None:
                continue
            element_units = self._get_elements_by_name(xml_constants.UNIT_CLASS_UNIT_ELEMENT, unit_class_element)

            for element in element_units:
                unit_class_unit_entry = self._parse_node(element, HedSectionKey.Units)
                self._add_to_dict(unit_class_unit_entry, HedSectionKey.Units)
                unit_class_entry.add_unit(unit_class_unit_entry)

    # def _reformat_xsd_attrib(self, attrib_dict):
    #     final_attrib = {}
    #     for attrib_name in attrib_dict:
    #         if attrib_name == xml_constants.NO_NAMESPACE_XSD_KEY:
    #             xsd_value = attrib_dict[attrib_name]
    #             final_attrib[NS_ATTRIB] = xml_constants.XSI_SOURCE
    #             final_attrib[NO_LOC_ATTRIB] = xsd_value
    #         else:
    #             final_attrib[attrib_name] = attrib_dict[attrib_name]
    #
    #     return final_attrib

    def _reformat_xsd_attrib(self, attrib_dict):
        final_attrib = {}
        for attrib_name in attrib_dict:
            if attrib_name == xml_constants.NO_NAMESPACE_XSD_KEY:
                xsd_value = attrib_dict[attrib_name]
                final_attrib[NS_ATTRIB] = xml_constants.XSI_SOURCE
                final_attrib[NO_LOC_ATTRIB] = xsd_value

            elif attrib_name == xml_constants.NAMESPACE_XSD_KEY:
                schema_value = attrib_dict[attrib_name].strip()
                parts = schema_value.split()

                if len(parts) != 2:
                    raise HedFileError(HedExceptions.HED_SCHEMA_INVALID,
                                       "schemaLocation must contain exactly one namespace and location",
                                       self.name)

                namespace_uri, location_uri = parts
                final_attrib[NS_ATTRIB] = namespace_uri
                final_attrib[NO_LOC_ATTRIB] = location_uri

            else:
                final_attrib[attrib_name] = attrib_dict[attrib_name]

        return final_attrib

    def _parse_node(self, node_element, key_class, element_name=None):
        if element_name:
            node_name = element_name
        else:
            node_name = self._get_element_tag_value(node_element)
        attribute_desc = self._get_element_tag_value(node_element, xml_constants.DESCRIPTION_ELEMENT)

        tag_entry = self._schema._create_tag_entry(node_name, key_class)

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
            tag_entry._set_attribute_value(attribute_name, attribute_value)

        return tag_entry

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
                                   self.name)
            return element.text
        return ""

    @staticmethod
    def _get_element_value(element, tag_name):
        this_element = element.find(tag_name)
        if this_element is None or this_element.text is None:
            return ''
        else:
            return this_element.text

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

    def _add_to_dict(self, entry, key_class):
        if entry.has_attribute(HedKey.InLibrary) and not self._loading_merged and not self.appending_to_schema:
            raise HedFileError(HedExceptions.IN_LIBRARY_IN_UNMERGED,
                               "Library tag in unmerged schema has InLibrary attribute",
                               self.name)

        return self._add_to_dict_base(entry, key_class)
