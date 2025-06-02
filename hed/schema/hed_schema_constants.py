from enum import Enum


class HedSectionKey(Enum):
    """ Keys designating specific sections in a HedSchema object.
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
    Reserved = "reserved"

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
    HedID = 'hedId'

    UnitClassDomain = "unitClassDomain"
    UnitDomain = "unitDomain"
    UnitModifierDomain = "unitModifierDomain"
    ValueClassDomain = "valueClassDomain"
    ElementDomain = "elementDomain"
    TagDomain = "tagDomain"
    AnnotationProperty = "annotationProperty"

    BoolRange = "boolRange"
    TagRange = "tagRange"
    NumericRange = "numericRange"
    StringRange = "stringRange"
    UnitClassRange = "unitClassRange"
    UnitRange = "unitRange"
    ValueClassRange = "valueClassRange"


class HedKeyOld:
    # Fully Deprecated properties
    BoolProperty = 'boolProperty'
    UnitClassProperty = 'unitClassProperty'
    UnitProperty = 'unitProperty'
    UnitModifierProperty = 'unitModifierProperty'
    ValueClassProperty = 'valueClassProperty'
    ElementProperty = 'elementProperty'
    NodeProperty = 'nodeProperty'
    IsInheritedProperty = 'isInheritedProperty'


VERSION_ATTRIBUTE = 'version'
LIBRARY_ATTRIBUTE = 'library'
WITH_STANDARD_ATTRIBUTE = "withStandard"
UNMERGED_ATTRIBUTE = "unmerged"
NS_SPEC = 'xmlns'
NS_ATTRIB = "xmlns:xsi"
NO_LOC_ATTRIB = "xsi:noNamespaceSchemaLocation"
LOC_ATTRIB = 'xsi:schemaLocation'

# A list of all attributes that can appear in the header line
valid_header_attributes = {
    VERSION_ATTRIBUTE,
    LIBRARY_ATTRIBUTE,
    WITH_STANDARD_ATTRIBUTE,
    NS_ATTRIB,
    NS_SPEC,
    NO_LOC_ATTRIB,
    LOC_ATTRIB,
    UNMERGED_ATTRIBUTE
}

character_types = {
    "ascii": set([chr(x) for x in range(0, 127)]),
    "nonascii": "nonascii",  # Special case for all other printable unicode characters
    "printable": set([chr(x) for x in range(32, 127)]),
    "lowercase": set("abcdefghijklmnopqrstuvwxyz"),
    "uppercase": set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    "digits": set("0123456789"),
    "tab": set("\t"),
    "newline": set("\n"),
    "blank": set(" "),
    "exclamation": set("!"),
    "double-quote": set('"'),
    "number-sign": set("#"),
    "dollar": set("$"),
    "percent-sign": set("%"),
    "ampersand": set("&"),
    "single-quote": set("'"),
    "left-paren": set("("),
    "right-paren": set(")"),
    "asterisk": set("*"),
    "plus": set("+"),
    "comma": set(","),
    "hyphen": set("-"),
    "period": set("."),
    "slash": set("/"),
    "colon": set(":"),
    "semicolon": set(";"),
    "less-than": set("<"),
    "equals": set("="),
    "greater-than": set(">"),
    "question-mark": set("?"),
    "at-sign": set("@"),
    "backslash": set("\\"),
    "caret": set("^"),
    "underscore": set("_"),
    "vertical-bar": set("|"),
    "tilde": set("~"),
}

banned_delimiters = set(",[]{}")

# Compound types
character_types["letters"] = character_types["lowercase"] | character_types["uppercase"]
character_types["alphanumeric"] = character_types["letters"] | character_types["digits"]
character_types["text"] = character_types["printable"].copy()
character_types["text"].add("nonascii")
character_types["text"] -= banned_delimiters
character_types["name"] = (character_types["alphanumeric"] | character_types["hyphen"] |
                           character_types["period"] | character_types["underscore"])
character_types["name"].add("nonascii")
