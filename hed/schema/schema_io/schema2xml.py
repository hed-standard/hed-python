"""Allows output of HedSchema objects as .xml format"""

from xml.etree.ElementTree import Element, SubElement
from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.schema_io import xml_constants, df_constants as df_constants
from hed.schema.schema_io.schema2base import Schema2Base


class Schema2XML(Schema2Base):
    def __init__(self):
        super().__init__()
        self.hed_node = None
        self.output = None

    # =========================================
    # Required baseclass function
    # =========================================
    def _initialize_output(self):
        self.hed_node = Element('HED')
        # alias this to output to match baseclass expectation.
        self.output = self.hed_node

    def _output_header(self, attributes):
        for attrib_name, attrib_value in attributes.items():
            self.hed_node.set(attrib_name, attrib_value)

    def _output_prologue(self, prologue):
        if prologue:
            prologue_node = SubElement(self.hed_node, xml_constants.PROLOGUE_ELEMENT)
            prologue_node.text = prologue

    def _output_annotations(self, hed_schema):
        pass

    def _output_extras(self, hed_schema):
        """
        Allow subclasses to add additional sections if needed.
        This is a placeholder for any additional output that needs to be done after the main sections.
        """
        # In the base class, we do nothing, but subclasses can override this method.
        self._output_sources(hed_schema)
        self._output_prefixes(hed_schema)
        self._output_external_annotations(hed_schema)

    def _output_sources(self, hed_schema):
        sources = hed_schema.get_extras(df_constants.SOURCES_KEY)
        if sources is None:
            return
        sources_node = SubElement(self.hed_node, xml_constants.SCHEMA_SOURCE_SECTION_ELEMENT)
        for _, row in sources.iterrows():
            source_node = SubElement(sources_node, xml_constants.SCHEMA_SOURCE_DEF_ELEMENT)
            source_name = SubElement(source_node, xml_constants.NAME_ELEMENT)
            source_name.text = row[df_constants.source]
            source_link = SubElement(source_node, xml_constants.LINK_ELEMENT)
            source_link.text = row[df_constants.link]
            description = SubElement(source_node, xml_constants.DESCRIPTION_ELEMENT)
            description.text = row[df_constants.description]

    def _output_prefixes(self, hed_schema):
        prefixes = hed_schema.get_extras(df_constants.PREFIXES_KEY)
        if prefixes is None:
            return
        prefixes_node = SubElement(self.hed_node, xml_constants.SCHEMA_PREFIX_SECTION_ELEMENT)
        for _, row in prefixes.iterrows():
            prefix_node = SubElement(prefixes_node, xml_constants.SCHEMA_PREFIX_DEF_ELEMENT)
            prefix_name = SubElement(prefix_node, xml_constants.NAME_ELEMENT)
            prefix_name.text = row[df_constants.prefix]
            prefix_namespace = SubElement(prefix_node, xml_constants.NAMESPACE_ELEMENT)
            prefix_namespace.text = row[df_constants.namespace]
            prefix_description = SubElement(prefix_node, xml_constants.DESCRIPTION_ELEMENT)
            prefix_description.text = row[df_constants.description]

    def _output_external_annotations(self, hed_schema):
        externals = hed_schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        if externals is None:
            return
        externals_node = SubElement(self.hed_node, xml_constants.SCHEMA_EXTERNAL_SECTION_ELEMENT)
        for _, row in externals.iterrows():
            external_node = SubElement(externals_node, xml_constants.SCHEMA_EXTERNAL_DEF_ELEMENT)
            external_name = SubElement(external_node, xml_constants.NAME_ELEMENT)
            external_name.text = row[df_constants.prefix]
            external_id = SubElement(external_node, xml_constants.ID_ELEMENT)
            external_id.text = row[df_constants.id]
            external_iri = SubElement(external_node, xml_constants.IRI_ELEMENT)
            external_iri.text = row[df_constants.iri]
            external_description = SubElement(external_node, xml_constants.DESCRIPTION_ELEMENT)
            external_description.text = row[df_constants.description]

    def _output_epilogue(self, epilogue):
        if epilogue:
            prologue_node = SubElement(self.hed_node, xml_constants.EPILOGUE_ELEMENT)
            prologue_node.text = epilogue

    def _output_footer(self):
        pass

    def _start_section(self, key_class):
        unit_modifier_node = SubElement(self.hed_node, xml_constants.SECTION_ELEMENTS[key_class])
        return unit_modifier_node

    def _end_tag_section(self):
        pass

    def _end_units_section(self):
        pass

    def _end_section(self, section_key):
        pass

    def _write_tag_entry(self, tag_entry, parent_node=None, level=0):
        """ Create a tag node and adds it to the parent.

        Parameters:
            tag_entry (HedTagEntry): The entry for that tag we want to write out.
            parent_node (SubElement): The parent node if any of this tag.
            level (int): The level of this tag, 0 being a root tag.

        Returns:
            SubElement: The added node.
        """
        key_class = HedSectionKey.Tags
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
        """ Create an entry node and adds it to the parent.

        Parameters:
            entry (HedSchemaEntry): The entry for that tag we want to write out.
            parent_node (SubElement): The parent node of this tag, if any.
            include_props (bool): Whether to include the properties and description of this tag.

        Returns:
            SubElement: The added node
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
        """Add the attributes to a tag.

        Parameters:
            tag_node (Element):  A tag element.
            tag_attributes ({str:str}): A dictionary of attributes to add to this node.
            attribute_node_name (str): The type of the node to use for attributes.  Mostly used to override to property for attributes section.

        """
        for attribute, value in tag_attributes.items():
            if self._attribute_disallowed(attribute):
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
