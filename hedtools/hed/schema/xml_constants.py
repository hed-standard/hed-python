from hed.schema.hed_schema_constants import HedKey, HedSectionKey

# These are only currently used by the XML reader/writer, but that may change.
XSI_SOURCE = "http://www.w3.org/2001/XMLSchema-instance"
NO_NAMESPACE_XSD_KEY = f"{{{XSI_SOURCE}}}noNamespaceSchemaLocation"
NS_ATTRIB = "xmlns:xsi"
NO_LOC_ATTRIB = "xsi:noNamespaceSchemaLocation"


NAME_ELEMENT = "name"
DESCRIPTION_ELEMENT = "description"
VALUE_ELEMENT = "value"

# These should mostly match the HedKey values
# These are repeated here for clarification primarily
DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE = HedKey.DefaultUnits
DEFAULT_UNIT_FOR_OLD_UNIT_CLASS_ATTRIBUTE = 'default'
ATTRIBUTE_ELEMENT = "attribute"
ATTRIBUTE_PROPERTY_ELEMENT = "property"
UNIT_CLASS_UNIT_ELEMENT = 'unit'
UNIT_CLASS_UNITS_ELEMENT = "units"
PROLOGUE_ELEMENT = "prologue"
SCHEMA_ELEMENT = "schema"
EPILOGUE_ELEMENT = "epilogue"

TAG_DEF_ELEMENT = "node"

TRUE_ATTRIBUTE = "true"


# Sections that vary in legacy xml
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

UNIT_CLASS_SECTION_ELEMENT_LEGACY = "unitClasses"
UNIT_CLASS_DEF_ELEMENT_LEGACY = "unitClass"
UNIT_MODIFIER_SECTION_ELEMENT_LEGACY = "unitModifiers"
UNIT_MODIFIER_DEF_ELEMENT_LEGACY = "unitModifier"


def get_section_name(key_class, legacy_format=False):
    if not legacy_format:
        section_names = {
            HedSectionKey.UnitClasses: UNIT_CLASS_SECTION_ELEMENT,
            HedSectionKey.UnitModifiers: UNIT_MODIFIER_SECTION_ELEMENT,
            HedSectionKey.ValueClasses: SCHEMA_VALUE_CLASSES_SECTION_ELEMENT,
            HedSectionKey.Attributes: SCHEMA_ATTRIBUTES_SECTION_ELEMENT,
            HedSectionKey.Properties: SCHEMA_PROPERTIES_SECTION_ELEMENT,
        }
    else:
        section_names = {
            HedSectionKey.UnitClasses: UNIT_CLASS_SECTION_ELEMENT_LEGACY,
            HedSectionKey.UnitModifiers: UNIT_MODIFIER_SECTION_ELEMENT_LEGACY,
            HedSectionKey.ValueClasses: SCHEMA_VALUE_CLASSES_SECTION_ELEMENT,
            HedSectionKey.Attributes: SCHEMA_ATTRIBUTES_SECTION_ELEMENT,
            HedSectionKey.Properties: SCHEMA_PROPERTIES_SECTION_ELEMENT,
        }

    return section_names.get(key_class, None)


def get_element_name(key_class, legacy_format=False):
    if not legacy_format:
        element_names = {
            HedSectionKey.AllTags: TAG_DEF_ELEMENT,
            HedSectionKey.UnitClasses: UNIT_CLASS_DEF_ELEMENT,
            HedSectionKey.UnitModifiers: UNIT_MODIFIER_DEF_ELEMENT,
            HedSectionKey.ValueClasses: SCHEMA_VALUE_CLASSES_DEF_ELEMENT,
            HedSectionKey.Attributes: SCHEMA_ATTRIBUTES_DEF_ELEMENT,
            HedSectionKey.Properties: SCHEMA_PROPERTIES_DEF_ELEMENT,
        }
    else:
        element_names = {
            HedSectionKey.AllTags: TAG_DEF_ELEMENT,
            HedSectionKey.UnitClasses: UNIT_CLASS_DEF_ELEMENT_LEGACY,
            HedSectionKey.UnitModifiers: UNIT_MODIFIER_DEF_ELEMENT_LEGACY,
            HedSectionKey.ValueClasses: SCHEMA_VALUE_CLASSES_DEF_ELEMENT,
            HedSectionKey.Attributes: SCHEMA_ATTRIBUTES_DEF_ELEMENT,
            HedSectionKey.Properties: SCHEMA_PROPERTIES_DEF_ELEMENT,
        }

    return element_names.get(key_class, (None, None))


ATTRIBUTE_PROPERTY_ELEMENTS = {
    HedSectionKey.AllTags: ATTRIBUTE_ELEMENT,
    HedSectionKey.UnitClasses: ATTRIBUTE_ELEMENT,
    HedSectionKey.Units: ATTRIBUTE_ELEMENT,
    HedSectionKey.UnitModifiers: ATTRIBUTE_ELEMENT,
    HedSectionKey.ValueClasses: ATTRIBUTE_ELEMENT,
    HedSectionKey.Attributes: ATTRIBUTE_PROPERTY_ELEMENT,
    HedSectionKey.Properties: None
}
