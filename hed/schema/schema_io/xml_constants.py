""" Constants used for the """

from hed.schema.hed_schema_constants import HedSectionKey

# These are only currently used by the XML reader/writer, but that may change.
XSI_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'
NO_NAMESPACE_XSD_KEY = f'{{{XSI_NAMESPACE}}}noNamespaceSchemaLocation'
NAMESPACE_XSD_KEY = f'{{{XSI_NAMESPACE}}}schemaLocation'
XSI_SOURCE = XSI_NAMESPACE

NAME_ELEMENT = "name"
DESCRIPTION_ELEMENT = "description"
VALUE_ELEMENT = "value"

# These should mostly match the HedKey values
# These are repeated here for clarification primarily
ATTRIBUTE_ELEMENT = "attribute"
ATTRIBUTE_PROPERTY_ELEMENT = "property"
UNIT_CLASS_UNIT_ELEMENT = 'unit'
PROLOGUE_ELEMENT = "prologue"
SCHEMA_ELEMENT = "schema"
EPILOGUE_ELEMENT = "epilogue"

TAG_DEF_ELEMENT = "node"
LINK_ELEMENT = "link"
NAMESPACE_ELEMENT = "namespace"
DESCRIPTION_ELEMENT = "description"
ID_ELEMENT = "id"
IRI_ELEMENT = "iri"

UNIT_CLASS_SECTION_ELEMENT = "unitClassDefinitions"
UNIT_CLASS_DEF_ELEMENT = "unitClassDefinition"
UNIT_MODIFIER_SECTION_ELEMENT = "unitModifierDefinitions"
UNIT_MODIFIER_DEF_ELEMENT = "unitModifierDefinition"
SCHEMA_ATTRIBUTES_SECTION_ELEMENT = "schemaAttributeDefinitions"
SCHEMA_ATTRIBUTES_DEF_ELEMENT = "schemaAttributeDefinition"
SCHEMA_PROPERTIES_SECTION_ELEMENT = "propertyDefinitions"
SCHEMA_PROPERTIES_DEF_ELEMENT = "propertyDefinition"
SCHEMA_VALUE_CLASSES_SECTION_ELEMENT = "valueClassDefinitions"
SCHEMA_VALUE_CLASSES_DEF_ELEMENT = "valueClassDefinition"

SCHEMA_SOURCE_SECTION_ELEMENT = "schemaSources"
SCHEMA_SOURCE_DEF_ELEMENT = "schemaSource"

SCHEMA_PREFIX_SECTION_ELEMENT = "schemaPrefixes"
SCHEMA_PREFIX_DEF_ELEMENT = "schemaPrefix"

SCHEMA_EXTERNAL_SECTION_ELEMENT = "externalAnnotations"
SCHEMA_EXTERNAL_DEF_ELEMENT = "externalAnnotation"

SECTION_ELEMENTS = {
    HedSectionKey.Tags: SCHEMA_ELEMENT,
    HedSectionKey.UnitClasses: UNIT_CLASS_SECTION_ELEMENT,
    HedSectionKey.UnitModifiers: UNIT_MODIFIER_SECTION_ELEMENT,
    HedSectionKey.ValueClasses: SCHEMA_VALUE_CLASSES_SECTION_ELEMENT,
    HedSectionKey.Attributes: SCHEMA_ATTRIBUTES_SECTION_ELEMENT,
    HedSectionKey.Properties: SCHEMA_PROPERTIES_SECTION_ELEMENT,
}


ELEMENT_NAMES = {
    HedSectionKey.Tags: TAG_DEF_ELEMENT,
    HedSectionKey.UnitClasses: UNIT_CLASS_DEF_ELEMENT,
    HedSectionKey.Units: UNIT_CLASS_UNIT_ELEMENT,
    HedSectionKey.UnitModifiers: UNIT_MODIFIER_DEF_ELEMENT,
    HedSectionKey.ValueClasses: SCHEMA_VALUE_CLASSES_DEF_ELEMENT,
    HedSectionKey.Attributes: SCHEMA_ATTRIBUTES_DEF_ELEMENT,
    HedSectionKey.Properties: SCHEMA_PROPERTIES_DEF_ELEMENT,
}


ATTRIBUTE_PROPERTY_ELEMENTS = {
    HedSectionKey.Tags: ATTRIBUTE_ELEMENT,
    HedSectionKey.UnitClasses: ATTRIBUTE_ELEMENT,
    HedSectionKey.Units: ATTRIBUTE_ELEMENT,
    HedSectionKey.UnitModifiers: ATTRIBUTE_ELEMENT,
    HedSectionKey.ValueClasses: ATTRIBUTE_ELEMENT,
    HedSectionKey.Attributes: ATTRIBUTE_PROPERTY_ELEMENT,
    HedSectionKey.Properties: ATTRIBUTE_PROPERTY_ELEMENT
}
