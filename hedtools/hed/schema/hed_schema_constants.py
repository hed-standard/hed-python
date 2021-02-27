# These need to match the attributes/element name/etc used to load from the xml
class HedKey:
    Default = 'default'
    ExtensionAllowed = 'extensionAllowed'
    # On opening, the extension allowed attribute is propagated down to child tags.
    ExtensionAllowedPropagated = 'extensionAllowedPropagated'
    IsNumeric = 'isNumeric'
    Position = 'position'
    PredicateType = 'predicateType'
    Recommended = 'recommended'
    RequiredPrefix = 'required'
    RequireChild = 'requireChild'
    AllTags = 'tags'
    TakesValue = 'takesValue'
    Unique = 'unique'
    UnitClass = 'unitClass'

    # Default Units for Type
    DefaultUnits = 'defaultUnits'
    Units = 'units'

    # The next 5 are all case sensitive for the keys.
    SIUnit = 'SIUnit'
    UnitSymbol = 'unitSymbol'

    SIUnitModifier = 'SIUnitModifier'
    SIUnitSymbolModifier = 'SIUnitSymbolModifier'

    # for normal tags, the key to this is the full tag name.
    # For unit modifiers and such, prefix the tag with the appropriate HedKey.
    # eg. dictionaries[HedKey.Descriptions][HedKey.SIUnitModifier + 'm']
    Descriptions = 'descriptions'

    # If this is a valid HED3 spec, this allows mapping from short to long.
    ShortTags = 'shortTags'


# List of all dictionary keys that are based off tag attributes.
# These are the only ones directly loaded from or saved to files.
TAG_ATTRIBUTE_KEYS = [HedKey.TakesValue, HedKey.IsNumeric, HedKey.Recommended,
                      HedKey.RequireChild, HedKey.RequiredPrefix, HedKey.Unique, HedKey.PredicateType,
                      HedKey.Position, HedKey.UnitClass, HedKey.Default, HedKey.ExtensionAllowed]
# for these it gets the value of the attribute, rather than treating it as a bool.
STRING_ATTRIBUTE_DICTIONARY_KEYS = [HedKey.Default, HedKey.UnitClass,
                                    HedKey.Position, HedKey.PredicateType, HedKey.DefaultUnits]
# List of all keys that are for tags, including ones derived from other attributes.
ALL_TAG_DICTIONARY_KEYS = [*TAG_ATTRIBUTE_KEYS, HedKey.ExtensionAllowedPropagated, HedKey.AllTags]
UNIT_CLASS_DICTIONARY_KEYS = [HedKey.SIUnit, HedKey.UnitSymbol]
UNIT_MODIFIER_DICTIONARY_KEYS = [HedKey.SIUnitModifier, HedKey.SIUnitSymbolModifier]

UNIT_CLASS_ATTRIBUTES = [HedKey.DefaultUnits, HedKey.SIUnit, HedKey.UnitSymbol]
UNIT_MODIFIER_ATTRIBUTES = [HedKey.SIUnitModifier, HedKey.SIUnitSymbolModifier]

VERSION_ATTRIBUTE = 'version'

