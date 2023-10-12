from enum import Enum


class HedSectionKey(Enum):
    """ Kegs designating specific sections in a HedSchema object.
    """
    # overarching category listing all tags
    Tags = 'tags'
    # Overarching category listing all unit classes
    UnitClasses = 'unitClasses'
    # Overarching category listing all units(not divided by type)
    Units = 'units'
    # Overarching category listing all unit modifiers.
    UnitModifiers = 'unitModifiers'
    # Overarching category listing all value classes
    ValueClasses = "valueClasses"
    # These are the allowed attributes list, gathered from the schema on load.
    Attributes = 'attributes'
    # These are the allowed attribute property list, gathered from the schema on load.
    Properties = 'properties'


class HedKey:
    """ Known property and attribute names.

    Notes:
        - These names should match the attribute values in the XML/wiki.

    """
    # Tag attributes
    ExtensionAllowed = 'extensionAllowed'
    Recommended = 'recommended'
    Required = 'required'
    RequireChild = 'requireChild'
    TagGroup = 'tagGroup'
    TakesValue = 'takesValue'
    TopLevelTagGroup = 'topLevelTagGroup'
    Unique = 'unique'
    UnitClass = 'unitClass'
    ValueClass = "valueClass"
    RelatedTag = "relatedTag"
    SuggestedTag = "suggestedTag"
    Rooted = "rooted"
    DeprecatedFrom = "deprecatedFrom"
    ConversionFactor = "conversionFactor"

    # All known properties
    BoolProperty = 'boolProperty'
    UnitClassProperty = 'unitClassProperty'
    UnitProperty = 'unitProperty'
    UnitModifierProperty = 'unitModifierProperty'
    ValueClassProperty = 'valueClassProperty'
    ElementProperty = 'elementProperty'
    IsInheritedProperty = 'isInheritedProperty'

    SIUnit = 'SIUnit'
    UnitSymbol = 'unitSymbol'
    # Default Units for Type
    DefaultUnits = 'defaultUnits'
    UnitPrefix = 'unitPrefix'

    SIUnitModifier = 'SIUnitModifier'
    SIUnitSymbolModifier = 'SIUnitSymbolModifier'

    # value class attributes
    AllowedCharacter = 'allowedCharacter'

    # Node attributes
    InLibrary = "inLibrary"


VERSION_ATTRIBUTE = 'version'
LIBRARY_ATTRIBUTE = 'library'
WITH_STANDARD_ATTRIBUTE = "withStandard"
UNMERGED_ATTRIBUTE = "unmerged"
NS_ATTRIB = "xmlns:xsi"
NO_LOC_ATTRIB = "xsi:noNamespaceSchemaLocation"

# A list of all attributes that can appear in the header line
valid_header_attributes = {
    VERSION_ATTRIBUTE,
    LIBRARY_ATTRIBUTE,
    WITH_STANDARD_ATTRIBUTE,
    NS_ATTRIB,
    NO_LOC_ATTRIB,
    UNMERGED_ATTRIBUTE
}
