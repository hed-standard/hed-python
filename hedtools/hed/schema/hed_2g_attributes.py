
# Dictionary of attributes for hed2 schema, so we can add them if not present.
attributes = {
    'allowedCharacter': (("unitClassProperty", ), "An attribute of unit classes schema value placeholders indicating a special character that is allowed in expressing the value of that placeholder."),
    "defaultUnits": (("unitClassProperty", ), "An attribute of unit classes specifying the default units for a tag."),
    "extensionAllowed": (("boolProperty", ), "Users can add unlimited levels of child nodes under this tag."),
    "isNumeric": (("boolProperty", ), "The tag hashtag placeholder must be replaced by a numerical value."),
    "position": ((), "Used to specify the order of the required and recommended tags in canonical order for display. The position attribute value should be an integer and the order can start at 0 or 1. Required or recommended tags without this attribute or with negative position will be shown after the others in canonical ordering."),
    "predicateType": ((), "One of propertyOf, subclassOf, passThrough -- used to facilitate mapping to OWL or RDF."),
    "recommended": (("boolProperty", ), "A HED string tagging an event is recommended to include this tag."),
    "relatedTag": ((), "Additional HED tags suggested to be used with this tag. This attribute is used by tagging tools."),
    "requireChild": (("boolProperty", ), "One of its descendants must be chosen to tag an event."),
    "required": (("boolProperty", ), "Every HED string tagging an event should include this tag."),
    "SIUnit": (("boolProperty", "unitClassProperty"), "Designates the name of an SI unit so it can be modified by multiple and submultiple names. Note that some units such as byte are designated as SI units although they are not part of the standard."),
    "SIUnitModifier": (("boolProperty","unitModifierProperty"), "SI unit modifier indicating a multiple or submultiple of a base unit."),
    "SIUnitSymbolModifier": (("boolProperty", "unitModifierProperty"), "SI unit symbol modifier indicating a multiple or submultiple of a base unit symbol."),
    "suggestedTag": ((), "Additional HED tags suggested to be used with this tag. This attribute is used by tagging tools."),
    "takesValue": (("boolProperty", ), "This tag will have a hashtag placeholder child in the schema which is expected to be replaced with a user-defined value."),
    "unique": (("boolProperty", ), "Only one of this tag or its descendants can be used within a single tag group or event."),
    "unitSymbol": (("boolProperty", "unitClassProperty"), "Abbreviation or symbol representing a type of unit. Unit symbols  represent both the singular and the plural and thus cannot be pluralized."),
    "unitClass": ((), "Specifies the type of a unit for a tag."),
}

