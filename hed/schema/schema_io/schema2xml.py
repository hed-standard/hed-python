"""Allows output of HedSchema objects as .xml format"""

from xml.etree.ElementTree import Element, SubElement
from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.schema_io import xml_constants


class HedSchema2XML:
    def __init__(self):
        self.hed_node = None

    def process_schema(self, hed_schema):
        """
        Takes a HedSchema object and returns an XML tree version.

        Parameters
        ----------
        hed_schema : HedSchema

        Returns
        -------
        mediawiki_strings: [str]
            A list of strings representing the .mediawiki version of this schema.
        """
        self.hed_node = Element('HED')

        self._output_header(hed_schema)
        self._output_tags(hed_schema)
        self._output_units(hed_schema)
        self._output_unit_modifiers(hed_schema)
        self._output_value_classes(hed_schema)
        self._output_attributes(hed_schema)
        self._output_properties(hed_schema)
        self._output_footer(hed_schema)
        return self.hed_node

    # =========================================
    # Top level output functions
    # =========================================
    def _output_header(self, hed_schema):
        for attrib_name, attrib_value in hed_schema.header_attributes.items():
            self.hed_node.set(attrib_name, attrib_value)
        if hed_schema.prologue:
            prologue_node = SubElement(self.hed_node, xml_constants.PROLOGUE_ELEMENT)
            prologue_node.text = hed_schema.prologue

    def _output_tags(self, hed_schema):
        schema_node = SubElement(self.hed_node, xml_constants.SCHEMA_ELEMENT)
        all_tags = hed_schema.get_all_schema_tags()
        tag_levels = {}
        for tag in all_tags:
            if "/" not in tag:
                root_tag = self._add_node(hed_schema, schema_node, tag)
                tag_levels[0] = root_tag
            else:
                level = tag.count("/")
                short_tag = tag.split("/")[-1]
                parent_tag = tag_levels[level - 1]
                child_tag = self._add_node(hed_schema, parent_tag, tag, short_tag_name=short_tag)
                tag_levels[level] = child_tag

    def _output_units(self, hed_schema):
        if not hed_schema.unit_classes:
            return
        unit_section_node = SubElement(self.hed_node, xml_constants.SECTION_NAMES[HedSectionKey.UnitClasses])
        for unit_class, unit_class_entry in hed_schema[HedSectionKey.UnitClasses].items():
            unit_types = unit_class_entry.unit_class_units
            unit_class_node = self._add_node(hed_schema, unit_section_node, unit_class, HedSectionKey.UnitClasses)
            for unit_class_unit in unit_types:
                self._add_node(hed_schema, unit_class_node, unit_class_unit, HedSectionKey.Units,
                               sub_node_name="unit")

    def _output_section(self, hed_schema, key_class):
        if not hed_schema._sections[key_class]:
            return
        unit_modifier_node = SubElement(self.hed_node, xml_constants.SECTION_NAMES[key_class])
        for modifier_name in hed_schema[key_class]:
            self._add_node(hed_schema, unit_modifier_node, modifier_name, key_class)

    def _output_unit_modifiers(self, hed_schema):
        self._output_section(hed_schema, HedSectionKey.UnitModifiers)
        return

    def _output_value_classes(self, hed_schema):
        self._output_section(hed_schema, HedSectionKey.ValueClasses)

    def _output_attributes(self, hed_schema):
        self._output_section(hed_schema, HedSectionKey.Attributes)

    def _output_properties(self, hed_schema):
        self._output_section(hed_schema, HedSectionKey.Properties)

    def _output_footer(self, hed_schema):
        if hed_schema.epilogue:
            prologue_node = SubElement(self.hed_node, xml_constants.EPILOGUE_ELEMENT)
            prologue_node.text = hed_schema.epilogue

    # =========================================
    # Output helper functions to create nodes
    # =========================================
    @staticmethod
    def _add_tag_node_attributes(tag_node, tag_attributes, attribute_node_name=xml_constants.ATTRIBUTE_ELEMENT):
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

    def _add_node(self, hed_schema, parent_node, full_name, key_class=HedSectionKey.AllTags, short_tag_name=None,
                  sub_node_name=None):
        """
            Creates a tag node and adds it to the parent.

        Parameters
        ----------
        hed_schema : HedSchema
            HedSchema to pull tag info from
        parent_node : Element
            The parent tag node
        full_name : str
            Long version of the tag/modifier/unit name
        key_class: str
            The type of node we are adding.  e.g. HedSectionKey.AllTags, HedSectionKey.UnitModifiers, etc.
        short_tag_name : str
            The short version of the tag if this is a tag.  Even for hed2g.
        sub_node_name: str or None
            Overrides the default node element name if present.
        Returns
        -------
        Element
            The added node
        """
        tag_node = None
        if short_tag_name is None:
            short_tag_name = full_name

        if sub_node_name:
            tag_element = sub_node_name
        else:
            tag_element = xml_constants.ELEMENT_NAMES[key_class]
        if full_name:
            tag_description = hed_schema.get_tag_description(full_name, key_class=key_class)
            tag_attributes = hed_schema.get_all_tag_attributes(full_name, key_class=key_class)
            tag_node = SubElement(parent_node, tag_element)
            name_node = SubElement(tag_node, xml_constants.NAME_ELEMENT)
            name_node.text = short_tag_name
            if tag_description:
                description_node = SubElement(tag_node, xml_constants.DESCRIPTION_ELEMENT)
                description_node.text = tag_description
            if tag_attributes:
                attribute_node_name = xml_constants.ATTRIBUTE_PROPERTY_ELEMENTS[key_class]
                HedSchema2XML._add_tag_node_attributes(tag_node, tag_attributes,
                                                       attribute_node_name=attribute_node_name)
        return tag_node
