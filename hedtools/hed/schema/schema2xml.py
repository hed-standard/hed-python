"""Allows output of HedSchema objects as .xml format"""

from hed.schema.hed_schema_constants import HedKey
from hed.schema import hed_schema_constants as constants
from xml.etree.ElementTree import Element, SubElement

TAG_ELEMENT = "node"
TAG_NAME_ELEMENT = "name"
TAG_DESCRIPTION_ELEMENT = "description"
TRUE_ATTRIBUTE = "true"
FALSE_ATTRIBUTE = "false"
unit_class_element = 'unitClass'
unit_class_name_element = 'name'
unit_class_units_element = 'units'
unit_class_unit_element = 'unit'
unit_modifier_element = 'unitModifier'
unit_modifier_name_element = 'name'
unit_modifier_description_element = 'description'


class HedSchema2XML:
    def __init__(self):
        self.hed_node = None

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
        self._output_footer(hed_schema)
        return self.hed_node

    # =========================================
    # Top level output functions
    # =========================================
    def _output_header(self, hed_schema):
        for attrib_name, attrib_value in hed_schema.schema_attributes.items():
            self.hed_node.set(attrib_name, attrib_value)

    def _output_tags(self, hed_schema):
        all_tags = hed_schema.get_all_tags()
        tag_levels = {}
        for tag in all_tags:
            if "/" not in tag:
                root_tag = self._add_tag_node(hed_schema, self.hed_node, tag)
                tag_levels[0] = root_tag
            else:
                level = tag.count("/")
                short_tag = tag.split("/")[-1]
                parent_tag = tag_levels[level - 1]
                child_tag = self._add_tag_node(hed_schema, parent_tag, tag, short_tag)
                tag_levels[level] = child_tag

    def _output_units(self, hed_schema):
        if not hed_schema.has_unit_classes:
            return
        unit_class_node = SubElement(self.hed_node, 'unitClasses')
        for unit_class, unit_types in hed_schema.dictionaries[HedKey.Units].items():
            unit_class_attributes = hed_schema.get_all_tag_attributes(unit_class, keys=constants.UNIT_CLASS_ATTRIBUTES)
            unit_class_units = []
            unit_class_units_attributes = []

            for unit_class_unit in unit_types:
                unit_class_unit_attributes = hed_schema.get_all_tag_attributes(unit_class_unit,
                                                                               keys=constants.UNIT_CLASS_ATTRIBUTES)
                unit_class_units.append(unit_class_unit)
                unit_class_units_attributes.append(unit_class_unit_attributes)

            self._add_unit_class_node(unit_class_node, unit_class, unit_class_units,
                                      unit_class_attributes, unit_class_units_attributes)

    def _output_unit_modifiers(self, hed_schema):
        if not hed_schema.has_unit_modifiers:
            return
        unit_modifier_node = SubElement(self.hed_node, 'unitModifiers')
        for modifier_name in hed_schema.dictionaries[HedKey.SIUnitModifier]:
            unit_modifier_attributes = hed_schema.get_all_tag_attributes(modifier_name,
                                                                         keys=constants.UNIT_MODIFIER_ATTRIBUTES)
            unit_modifier_description = hed_schema.get_tag_description(modifier_name, HedKey.SIUnitModifier)
            self._add_unit_modifier_node(unit_modifier_node, modifier_name,
                                         unit_modifier_attributes, unit_modifier_description)

    def _output_footer(self, hed_schema):
        pass

    # =========================================
    # Output helper functions to create nodes
    # =========================================
    @staticmethod
    def _add_tag_node_attributes(tag_node, tag_attributes):
        """Adds the attributes to a tag.

        Parameters
        ----------
        tag_node: Element
            A tag element.
        tag_attributes: {str:str}
            A dictionary of attributes to add to this node

        Returns
        -------

        """
        for attribute, value in tag_attributes.items():
            if value is True:
                tag_node.set(attribute, TRUE_ATTRIBUTE)
            elif value is False:
                continue
            else:
                tag_node.set(attribute, value)

    @staticmethod
    def _add_tag_node(hed_schema, parent_node, tag_name, short_tag_name=None):
        """
            Creates a tag node and adds it to the parent.

        Parameters
        ----------
        hed_schema : HedSchema
            HedSchema to pull tag info from
        parent_node : Element
            The parent tag node
        tag_name : str
            Long version of the tag name
        short_tag_name : str
            Short version of the tag name(even in HED 2G)

        Returns
        -------
        Element
            The added node
        """
        tag_node = None
        if short_tag_name is None:
            short_tag_name = tag_name
        if tag_name:
            tag_description = hed_schema.get_tag_description(tag_name)
            tag_attributes = hed_schema.get_all_tag_attributes(tag_name)
            tag_node = SubElement(parent_node, TAG_ELEMENT)
            name_node = SubElement(tag_node, TAG_NAME_ELEMENT)
            name_node.text = short_tag_name
            if tag_description:
                description_node = SubElement(tag_node, TAG_DESCRIPTION_ELEMENT)
                description_node.text = tag_description
            if tag_attributes:
                HedSchema2XML._add_tag_node_attributes(tag_node, tag_attributes)
        return tag_node

    @staticmethod
    def _add_unit_class_node(parent_node, unit_class, unit_class_units, unit_class_attributes,
                             unit_class_unit_attributes):
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
            HedSchema2XML._add_tag_node_attributes(unit_node, attributes)
            unit_node.text = unit
        if unit_class_attributes:
            HedSchema2XML._add_tag_node_attributes(unit_class_node, unit_class_attributes)
        return unit_class_node

    @staticmethod
    def _add_unit_modifier_node(parent_node, unit_modifier, unit_modifier_attributes, unit_modifier_description):
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
            HedSchema2XML._add_tag_node_attributes(unit_modifier_node, unit_modifier_attributes)
        return unit_modifier_node
