"""Allows output of HedSchema objects as .xml format"""

from xml.etree.ElementTree import Element, SubElement
from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.fileio import xml_constants


class HedSchema2XML:
    def __init__(self, save_as_legacy_format=True):
        self.hed_node = None
        self.save_as_legacy_format = save_as_legacy_format

    def process_schema(self, hed_schema):
        """
        Takes a HedSchema object and returns a an XML tree version.

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
        if not self.save_as_legacy_format:
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
        schema_node = self.hed_node
        if not self.save_as_legacy_format:
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
        unit_section_node = SubElement(self.hed_node, xml_constants.get_section_name(HedSectionKey.UnitClasses,
                                                                                     self.save_as_legacy_format))
        for unit_class, unit_entry in hed_schema[HedSectionKey.UnitClasses].items():
            unit_types = unit_entry.value
            unit_class_node = self._add_node(hed_schema, unit_section_node, unit_class, HedSectionKey.UnitClasses)
            if self.save_as_legacy_format:
                unit_class_node = SubElement(unit_class_node, xml_constants.UNIT_CLASS_UNITS_ELEMENT)

            for unit_class_unit in unit_types:
                # These units nodes are the only "special case" from the old schema where behavior differs.
                if self.save_as_legacy_format:
                    unit_node = SubElement(unit_class_node, xml_constants.UNIT_CLASS_UNIT_ELEMENT)
                    attributes = hed_schema.get_all_tag_attributes(unit_class_unit, key_class=HedSectionKey.Units)
                    HedSchema2XML._add_tag_node_attributes_old_format(unit_node, attributes)
                    unit_node.text = unit_class_unit
                else:
                    self._add_node(hed_schema, unit_class_node, unit_class_unit, HedSectionKey.Units,
                                   sub_node_name="unit")

    def _output_section(self, hed_schema, key_class):
        if not hed_schema._sections[key_class]:
            return
        unit_modifier_node = SubElement(self.hed_node, xml_constants.get_section_name(key_class,
                                                                                      self.save_as_legacy_format))
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

    @staticmethod
    def _add_tag_node_attributes_old_format(tag_node, tag_attributes):
        """Adds the attributes to a tag.

        Parameters
        ----------
        tag_node: Element
            A tag element.
        tag_attributes: {str:str}
            A dictionary of attributes to add to this node
        """
        for attribute, value in tag_attributes.items():
            if value is True:
                tag_node.set(attribute, xml_constants.TRUE_ATTRIBUTE)
            elif value is False:
                continue
            else:
                tag_node.set(attribute, value)

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
            The type of node we are adding.  eg HedSectionKey.AllTags, HedSectionKey.UnitModifiers, etc.
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
            tag_element = xml_constants.get_element_name(key_class, self.save_as_legacy_format)
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
                if not self.save_as_legacy_format:
                    attribute_node_name = xml_constants.ATTRIBUTE_PROPERTY_ELEMENTS[key_class]
                    HedSchema2XML._add_tag_node_attributes(tag_node, tag_attributes,
                                                           attribute_node_name=attribute_node_name)
                else:
                    HedSchema2XML._add_tag_node_attributes_old_format(tag_node, tag_attributes)
        return tag_node
