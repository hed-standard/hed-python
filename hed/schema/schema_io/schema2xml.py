"""Allows output of HedSchema objects as .xml format"""

from xml.etree.ElementTree import Element, SubElement
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.schema.schema_io import xml_constants
from hed.schema.schema_io.schema2base import HedSchema2Base


class HedSchema2XML(HedSchema2Base):
    def __init__(self):
        super().__init__()
        self.hed_node = Element('HED')
        # alias this to output to match baseclass expectation.
        self.output = self.hed_node

    # =========================================
    # Required baseclass function
    # =========================================
    def _output_header(self, attributes, prologue):
        for attrib_name, attrib_value in attributes.items():
            self.hed_node.set(attrib_name, attrib_value)
        if prologue:
            prologue_node = SubElement(self.hed_node, xml_constants.PROLOGUE_ELEMENT)
            prologue_node.text = prologue

    def _output_footer(self, epilogue):
        if epilogue:
            prologue_node = SubElement(self.hed_node, xml_constants.EPILOGUE_ELEMENT)
            prologue_node.text = epilogue

    def _start_section(self, key_class):
        unit_modifier_node = SubElement(self.hed_node, xml_constants.SECTION_NAMES[key_class])
        return unit_modifier_node

    def _end_tag_section(self):
        pass

    def _write_tag_entry(self, tag_entry, parent_node=None, level=0):
        """
            Creates a tag node and adds it to the parent.

        Parameters
        ----------
        tag_entry: HedTagEntry
            The entry for that tag we want to write out
        parent_node: SubElement
            The parent node if any of this tag.
        level: int
            The level of this tag, 0 being a root tag.
        Returns
        -------
        SubElement
            The added node
        """
        key_class = HedSectionKey.AllTags
        tag_element = xml_constants.ELEMENT_NAMES[key_class]
        tag_description = tag_entry.description
        tag_attributes = tag_entry.attributes
        tag_node = SubElement(parent_node, tag_element)
        name_node = SubElement(tag_node, xml_constants.NAME_ELEMENT)
        name_node.text = tag_entry.name.split("/")[-1]
        if tag_description:
            description_node = SubElement(tag_node, xml_constants.DESCRIPTION_ELEMENT)
            description_node.text = tag_description
        if tag_attributes:
            attribute_node_name = xml_constants.ATTRIBUTE_PROPERTY_ELEMENTS[key_class]
            self._add_tag_node_attributes(tag_node, tag_attributes,
                                                   attribute_node_name=attribute_node_name)

        return tag_node

    def _write_entry(self, entry, parent_node=None, include_props=True):
        """
            Creates an entry node and adds it to the parent.

        Parameters
        ----------
        entry: HedSchemaEntry
            The entry for that tag we want to write out
        parent_node: SubElement
            The parent node of this tag, if any
        include_props: bool
            Add the description and attributes to new node.
        Returns
        -------
        SubElement
            The added node
        """
        key_class = entry.section_key
        element = xml_constants.ELEMENT_NAMES[key_class]
        tag_description = entry.description
        tag_attributes = entry.attributes
        tag_node = SubElement(parent_node, element)
        name_node = SubElement(tag_node, xml_constants.NAME_ELEMENT)
        name_node.text = entry.name
        if include_props:
            if tag_description:
                description_node = SubElement(tag_node, xml_constants.DESCRIPTION_ELEMENT)
                description_node.text = tag_description
            if tag_attributes:
                attribute_node_name = xml_constants.ATTRIBUTE_PROPERTY_ELEMENTS[key_class]
                self._add_tag_node_attributes(tag_node, tag_attributes,
                                                       attribute_node_name=attribute_node_name)

        return tag_node

    # =========================================
    # Output helper functions to create nodes
    # =========================================
    def _add_tag_node_attributes(self, tag_node, tag_attributes, attribute_node_name=xml_constants.ATTRIBUTE_ELEMENT):
        """Adds the attributes to a tag.

        Parameters
        ----------
        tag_node: Element
            A tag element.
        tag_attributes: {str:str}
            A dictionary of attributes to add to this node
        attribute_node_name: str
            The type of the node to use for attributes.  Mostly used to override to property for attributes section.
        Returns
        -------
        """
        for attribute, value in tag_attributes.items():
            if value is False:
                continue
            if not self._save_merged and attribute == HedKey.InLibrary:
                continue
            node_name = attribute_node_name
            attribute_node = SubElement(tag_node, node_name)
            name_node = SubElement(attribute_node, xml_constants.NAME_ELEMENT)
            name_node.text = attribute

            if value is True:
                continue
            else:
                if not isinstance(value, list):
                    value = value.split(",")

                for single_value in value:
                    value_node = SubElement(attribute_node, xml_constants.VALUE_ELEMENT)
                    value_node.text = single_value
