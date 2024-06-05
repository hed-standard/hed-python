from hed.schema.hed_schema_constants import HedSectionKey

# Known tsv format suffixes

STRUCT_KEY = "Structure"
TAG_KEY = "Tag"
UNIT_KEY = "Unit"
UNIT_CLASS_KEY = "UnitClass"
UNIT_MODIFIER_KEY = "UnitModifier"
VALUE_CLASS_KEY = "ValueClass"

ANNOTATION_KEY = "AnnotationProperty"
DATA_KEY = "DataProperty"
OBJECT_KEY = "ObjectProperty"

ATTRIBUTE_PROPERTY_KEY = "AttributeProperty"

PROPERTY_KEYS = [ANNOTATION_KEY, DATA_KEY, OBJECT_KEY]
DF_SUFFIXES = {TAG_KEY, STRUCT_KEY, VALUE_CLASS_KEY,
                 UNIT_CLASS_KEY, UNIT_KEY, UNIT_MODIFIER_KEY,
                 *PROPERTY_KEYS, ATTRIBUTE_PROPERTY_KEY}

section_mapping = {
    STRUCT_KEY: None,
    TAG_KEY: HedSectionKey.Tags,
    VALUE_CLASS_KEY: HedSectionKey.ValueClasses,
    UNIT_CLASS_KEY: HedSectionKey.UnitClasses,
    UNIT_KEY: HedSectionKey.Units,
    UNIT_MODIFIER_KEY: HedSectionKey.UnitModifiers,
    ANNOTATION_KEY: HedSectionKey.Attributes,
    DATA_KEY: HedSectionKey.Attributes,
    OBJECT_KEY: HedSectionKey.Attributes,
    ATTRIBUTE_PROPERTY_KEY: HedSectionKey.Properties,
}

# Spreadsheet column ids
hed_id = "hedId"
level = "Level"
name = "rdfs:label"
subclass_of = "omn:SubClassOf"
attributes = "Attributes"
description = "dc:description"
equivalent_to = "omn:EquivalentTo"
has_unit_class = "hasUnitClass"

struct_columns = [hed_id, name, attributes, subclass_of, description]
tag_columns = [hed_id, name, level, subclass_of, attributes, description, equivalent_to]
unit_columns = [hed_id, name, subclass_of, has_unit_class, attributes, description, equivalent_to]

# The columns for unit class, value class, and unit modifier
other_columns = [hed_id, name, subclass_of, attributes, description, equivalent_to]

# for schema attributes
property_type = "Type"
property_domain = "omn:Domain"
property_range = "omn:Range"
properties = "Properties"
property_columns = [hed_id, name, property_type, property_domain, property_range, properties, description]

# For the schema properties
property_columns_reduced = [hed_id, name, property_type, description]

# HED_00X__YY where X is the library starting index, and Y is the entity number below.
struct_base_ids = {
    "HedEntity": 1,
    "HedStructure": 2,
    "HedElement": 3,
    "HedSchema": 4,
    "HedTag": 5,
    "HedUnitClass": 6,
    "HedUnit": 7,
    "HedUnitModifier": 8,
    "HedValueClass": 9,
    "HedHeader": 10,
    "HedPrologue": 11,
    "HedEpilogue": 12
}

