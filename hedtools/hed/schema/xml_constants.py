from hed.schema.hed_schema_constants import HedKey


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


UNIT_CLASS_SECTION_ELEMENT_LEGACY = "unitClasses"
UNIT_CLASS_DEF_ELEMENT_LEGACY = "unitClass"
UNIT_MODIFIER_SECTION_ELEMENT_LEGACY = "unitModifiers"
UNIT_MODIFIER_DEF_ELEMENT_LEGACY = "unitModifier"


def get_section_name(key_class, legacy_format=False):
    if not legacy_format:
        section_names = {
            HedKey.UnitClasses: UNIT_CLASS_SECTION_ELEMENT,
            HedKey.UnitModifiers: UNIT_MODIFIER_SECTION_ELEMENT,
            HedKey.Attributes: SCHEMA_ATTRIBUTES_SECTION_ELEMENT,
            HedKey.Properties: SCHEMA_PROPERTIES_SECTION_ELEMENT,
        }
    else:
        section_names = {
            HedKey.UnitClasses: UNIT_CLASS_SECTION_ELEMENT_LEGACY,
            HedKey.UnitModifiers: UNIT_MODIFIER_SECTION_ELEMENT_LEGACY,
            HedKey.Attributes: SCHEMA_ATTRIBUTES_SECTION_ELEMENT,
            HedKey.Properties: SCHEMA_PROPERTIES_SECTION_ELEMENT,
        }

    return section_names.get(key_class, None)


def get_element_name(key_class, legacy_format=False):
    if not legacy_format:
        element_names = {
            HedKey.AllTags: TAG_DEF_ELEMENT,
            HedKey.UnitClasses: UNIT_CLASS_DEF_ELEMENT,
            HedKey.UnitModifiers: UNIT_MODIFIER_DEF_ELEMENT,
            HedKey.Attributes: SCHEMA_ATTRIBUTES_DEF_ELEMENT,
            HedKey.Properties: SCHEMA_PROPERTIES_DEF_ELEMENT,
        }
    else:
        element_names = {
            HedKey.AllTags: TAG_DEF_ELEMENT,
            HedKey.UnitClasses: UNIT_CLASS_DEF_ELEMENT_LEGACY,
            HedKey.UnitModifiers: UNIT_MODIFIER_DEF_ELEMENT_LEGACY,
            HedKey.Attributes: SCHEMA_ATTRIBUTES_DEF_ELEMENT,
            HedKey.Properties: SCHEMA_PROPERTIES_DEF_ELEMENT,
        }

    return element_names.get(key_class, (None, None))


ATTRIBUTE_PROPERTY_ELEMENTS = {
    HedKey.AllTags: ATTRIBUTE_ELEMENT,
    HedKey.UnitClasses: ATTRIBUTE_ELEMENT,
    HedKey.Units: ATTRIBUTE_ELEMENT,
    HedKey.UnitModifiers: ATTRIBUTE_ELEMENT,
    HedKey.Attributes: ATTRIBUTE_PROPERTY_ELEMENT
}
