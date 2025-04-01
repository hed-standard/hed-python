from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema import hed_schema_constants

KEY_COLUMN_NAME = 'rdfs.label'

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

PREFIXES_KEY = "Prefixes"
EXTERNAL_ANNOTATION_KEY = "AnnotationPropertyExternal"

PROPERTY_KEYS = [ANNOTATION_KEY, DATA_KEY, OBJECT_KEY]
DF_SUFFIXES = {TAG_KEY, STRUCT_KEY, VALUE_CLASS_KEY,
               UNIT_CLASS_KEY, UNIT_KEY, UNIT_MODIFIER_KEY,
               *PROPERTY_KEYS, ATTRIBUTE_PROPERTY_KEY, PREFIXES_KEY, EXTERNAL_ANNOTATION_KEY}


DF_EXTRA_SUFFIXES = {PREFIXES_KEY, EXTERNAL_ANNOTATION_KEY}
#DF_SUFFIXES_OMN = {*DF_SUFFIXES, *DF_EXTRA_SUFFIXES}
DF_SUFFIXES_OMN = DF_SUFFIXES

section_mapping_hed_id = {
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
#annotations = "Annotations"

struct_columns = [hed_id, name, attributes, subclass_of, description]
tag_columns = [hed_id, name, level, subclass_of, attributes, description]
unit_columns = [hed_id, name, subclass_of, has_unit_class, attributes, description]

# The columns for unit class, value class, and unit modifier
other_columns = [hed_id, name, subclass_of, attributes, description]

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

# todo: this should be retrieved directly from the appropriate spreadsheet
valid_omn_attributes = {
    hed_schema_constants.VERSION_ATTRIBUTE: "HED_0000300",
    hed_schema_constants.LIBRARY_ATTRIBUTE: "HED_0000301",
    hed_schema_constants.WITH_STANDARD_ATTRIBUTE: "HED_0000302",
    hed_schema_constants.UNMERGED_ATTRIBUTE: "HED_0000303"
}

# Extra spreadsheet column ideas
Prefix = "Prefix"
ID = "ID"
NamespaceIRI = "Namespace IRI"
