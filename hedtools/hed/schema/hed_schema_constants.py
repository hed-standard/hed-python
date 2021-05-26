
class HedKey:
    """
        Used to access the hed schema dictionaries

        These names should match the attribute values in the XML/wiki.
    """
    # overarching category listing all tags
    AllTags = 'tags'
    # Overarching category listing all units
    Units = 'units'
    # Overarching category listing all unit modifiers.
    UnitModifiers = 'unitModifiers'
    # These are the allowed attributes list, gathered from the schema on load.
    Attributes = 'attributes'

    AllowedCharacter = 'allowedCharacter'
    ExtensionAllowed = 'extensionAllowed'
    # On opening, the extension allowed attribute is propagated down to child tags.
    ExtensionAllowedPropagated = 'extensionAllowedPropagated'
    IsNumeric = 'isNumeric'
    Position = 'position'
    PredicateType = 'predicateType'
    Recommended = 'recommended'
    RequiredPrefix = 'required'
    RequireChild = 'requireChild'
    TakesValue = 'takesValue'
    Unique = 'unique'
    UnitClass = 'unitClass'

    BoolProperty = 'boolProperty'
    UnitClassProperty = 'unitClassProperty'
    UnitModifierProperty = 'unitModifierProperty'

    # Attributes found in file, but not definitions
    UnknownAttributes = 'unknownAttributes'

    SIUnit = 'SIUnit'
    UnitSymbol = 'unitSymbol'
    # Default Units for Type
    DefaultUnits = 'defaultUnits'

    SIUnitModifier = 'SIUnitModifier'
    SIUnitSymbolModifier = 'SIUnitSymbolModifier'

    # for normal tags, the key to this is the full tag name.
    # For unit modifiers and such, prefix the tag with the appropriate HedKey.
    # eg. dictionaries[HedKey.Descriptions][HedKey.UnitModifiers + 'm']
    Descriptions = 'descriptions'

    # If this is a valid HED3 spec, this allows mapping from short to long.
    ShortTags = 'shortTags'


ATTRIBUTE_PROPERTIES = [HedKey.BoolProperty, HedKey.UnitClassProperty, HedKey.UnitModifierProperty]
VERSION_ATTRIBUTE = 'version'

