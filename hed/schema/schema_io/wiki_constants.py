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

wiki_section_headers = {
    HedSectionKey.Tags: START_HED_STRING,
    HedSectionKey.UnitClasses: UNIT_CLASS_STRING,
    HedSectionKey.Units: None,
    HedSectionKey.UnitModifiers: UNIT_MODIFIER_STRING,
    HedSectionKey.ValueClasses: VALUE_CLASS_STRING,
    HedSectionKey.Attributes: ATTRIBUTE_DEFINITION_STRING,
    HedSectionKey.Properties: ATTRIBUTE_PROPERTY_STRING,
}


# these must always be in order under the current spec.
class HedWikiSection:
    HeaderLine = 2
    Prologue = 3
    Schema = 4
    EndSchema = 5
    UnitsClasses = 6
    UnitModifiers = 7
    ValueClasses = 8
    Attributes = 9
    Properties = 10
    Epilogue = 11
    EndHed = 12


SectionStarts = {
    HedWikiSection.Prologue: PROLOGUE_SECTION_ELEMENT,
    HedWikiSection.Schema: START_HED_STRING,
    HedWikiSection.EndSchema: END_SCHEMA_STRING,
    HedWikiSection.UnitsClasses: UNIT_CLASS_STRING,
    HedWikiSection.UnitModifiers: UNIT_MODIFIER_STRING,
    HedWikiSection.ValueClasses: VALUE_CLASS_STRING,
    HedWikiSection.Attributes: ATTRIBUTE_DEFINITION_STRING,
    HedWikiSection.Properties: ATTRIBUTE_PROPERTY_STRING,
    HedWikiSection.Epilogue: EPILOGUE_SECTION_ELEMENT,
    HedWikiSection.EndHed: END_HED_STRING
}

SectionNames = {
    HedWikiSection.HeaderLine: "Header",
    HedWikiSection.Prologue: "Prologue",
    HedWikiSection.Schema: "Schema",
    HedWikiSection.EndSchema: "EndSchema",
    HedWikiSection.UnitsClasses: "Unit Classes",
    HedWikiSection.UnitModifiers: "Unit Modifiers",
    HedWikiSection.ValueClasses: "Value Classes",
    HedWikiSection.Attributes: "Attributes",
    HedWikiSection.Properties: "Properties",
    HedWikiSection.EndHed: "EndHed"
}
