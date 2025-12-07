"""Constants used for JSON schema format."""

from hed.schema.hed_schema_constants import HedSectionKey

# Top-level JSON keys
VERSION_KEY = "version"
LIBRARY_KEY = "library"
WITH_STANDARD_KEY = "withStandard"
UNMERGED_KEY = "unmerged"
PROLOGUE_KEY = "prologue"
EPILOGUE_KEY = "epilogue"
TAGS_KEY = "tags"
UNITS_KEY = "units"
UNIT_CLASSES_KEY = "unit_classes"
UNIT_MODIFIERS_KEY = "unit_modifiers"
VALUE_CLASSES_KEY = "value_classes"
SCHEMA_ATTRIBUTES_KEY = "schema_attributes"
PROPERTIES_KEY = "properties"

# Extra sections
SOURCES_KEY = "sources"
PREFIXES_KEY = "prefixes"
EXTERNAL_ANNOTATIONS_KEY = "external_annotations"

# Tag entry keys
SHORT_FORM_KEY = "short_form"
LONG_FORM_KEY = "long_form"
DESCRIPTION_KEY = "description"
PARENT_KEY = "parent"
CHILDREN_KEY = "children"
ATTRIBUTES_KEY = "attributes"
EXPLICIT_ATTRIBUTES_KEY = "explicitAttributes"  # Attributes explicitly set on this tag (not inherited)
PLACEHOLDER_KEY = "placeholder"  # Optional key for tags that take values

# Unit class keys
UNITS_LIST_KEY = "units"  # List of unit names belonging to this class
DEFAULT_UNITS_KEY = "default_units"

# Value class keys
ALLOWED_CHARACTERS_KEY = "allowed_characters"

# Attribute keys
ATTRIBUTE_NAME_KEY = "name"
ATTRIBUTE_VALUE_KEY = "value"

# Schema attribute/property keys
PROPERTY_NAME_KEY = "name"
PROPERTY_DESCRIPTION_KEY = "description"
PROPERTY_DOMAIN_KEY = "domain"
PROPERTY_RANGE_KEY = "range"

# Mapping between HedSectionKey and JSON keys
SECTION_KEYS = {
    HedSectionKey.Tags: TAGS_KEY,
    HedSectionKey.Units: UNITS_KEY,
    HedSectionKey.UnitClasses: UNIT_CLASSES_KEY,
    HedSectionKey.UnitModifiers: UNIT_MODIFIERS_KEY,
    HedSectionKey.ValueClasses: VALUE_CLASSES_KEY,
    HedSectionKey.Attributes: SCHEMA_ATTRIBUTES_KEY,
    HedSectionKey.Properties: PROPERTIES_KEY,
}
