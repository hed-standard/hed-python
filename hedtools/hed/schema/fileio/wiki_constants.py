from hed.schema.hed_schema_constants import HedSectionKey
START_HED_STRING = "!# start schema"
END_SCHEMA_STRING = "!# end schema"
END_HED_STRING = "!# end hed"

ROOT_TAG = "'''"
HEADER_LINE_STRING = "HED"
UNIT_CLASS_STRING = "'''Unit classes'''"
UNIT_MODIFIER_STRING = "'''Unit modifiers'''"
ATTRIBUTE_DEFINITION_STRING = "'''Schema attributes'''"
ATTRIBUTE_PROPERTY_STRING = "'''Properties'''"
VALUE_CLASS_STRING = "'''Value classes'''"
PROLOGUE_SECTION_ELEMENT = "'''Prologue'''"
EPILOGUE_SECTION_ELEMENT = "'''Epilogue'''"
OLD_SYNTAX_SECTION_NAME = "'''Syntax'''"

wiki_section_headers = {
    HedSectionKey.AllTags: None,
    HedSectionKey.UnitClasses: UNIT_CLASS_STRING,
    HedSectionKey.Units: None,
    HedSectionKey.UnitModifiers: UNIT_MODIFIER_STRING,
    HedSectionKey.ValueClasses: VALUE_CLASS_STRING,
    HedSectionKey.Attributes: ATTRIBUTE_DEFINITION_STRING,
    HedSectionKey.Properties: ATTRIBUTE_PROPERTY_STRING,
}
