
class HedKey:
    """
        Used to access the hed schema dictionaries

        These names should match the attribute values in the XML/wiki.
    """
    # overarching category listing all tags
    AllTags = 'tags'
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

    # Tag attributes
    ExtensionAllowed = 'extensionAllowed'
    # On opening, the extension allowed attribute is propagated down to child tags.
    ExtensionAllowedPropagated = 'extensionAllowedPropagated'
    IsNumeric = 'isNumeric'
    Position = 'position'
    PredicateType = 'predicateType'
    Recommended = 'recommended'
    RequiredPrefix = 'required'
    RequireChild = 'requireChild'
    TagGroup = 'tagGroup'
    TakesValue = 'takesValue'
    TopLevelTagGroup = 'topLevelTagGroup'
    Unique = 'unique'
    UnitClass = 'unitClass'
    ValueClass = "valueClass"

    # All known properties
    BoolProperty = 'boolProperty'
    UnitClassProperty = 'unitClassProperty'
    UnitProperty = 'unitProperty'
    UnitModifierProperty = 'unitModifierProperty'
    ValueClassProperty = 'valueClassProperty'

    # Attributes found in file, but not definitions
    UnknownAttributes = 'unknownAttributes'

    SIUnit = 'SIUnit'
    UnitSymbol = 'unitSymbol'
    # Default Units for Type
    DefaultUnits = 'defaultUnits'
    UnitPrefix = 'unitPrefix'

    SIUnitModifier = 'SIUnitModifier'
    SIUnitSymbolModifier = 'SIUnitSymbolModifier'

    AllowedCharacter = 'allowedCharacter'

    # for normal tags, the key to this is the full tag name.
    # For unit modifiers and such, prefix the tag with the appropriate HedKey.
    # eg. dictionaries[HedKey.Descriptions][HedKey.UnitModifiers + 'm']
    Descriptions = 'descriptions'

    # If this is a valid HED3 spec, this allows mapping from short to long.
    # this is in dictionaries, not tag dictionaries.
    ShortTags = 'shortTags'


VERSION_ATTRIBUTE = 'version'

