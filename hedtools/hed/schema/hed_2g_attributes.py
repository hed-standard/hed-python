
# Dictionary of attributes for hed2 schema, so we can add them if not present.
attributes = {
    "allowedCharacter": (("valueClassProperty", ),
                         "A schema attribute of value classes specifying a special character that is allowed in "
                         "expressing the value of a placeholder with those units."),
    "defaultUnits": (("unitClassProperty", ),
                     "A schema attribute of unit classes specifying the default units for a tag."),
    "extensionAllowed": (("boolProperty", ),
                         "A schema attribute indicating that users can add unlimited levels of child nodes under this "
                         "tag."),
    "isNumeric": (("boolProperty", ),
                  "A schema attribute indicating that the tag hashtag placeholder must be replaced by a numerical "
                  "value."),
    "position": ((),
                 "Used to specify the order of the required and recommended tags in canonical order for display. The "
                 "position attribute value should be an integer and the order can start at 0 or 1. Required or "
                 "recommended tags without this attribute or with negative position will be shown after the others in "
                 "canonical ordering."),
    "predicateType": ((),
                      "One of propertyOf, subclassOf, passThrough -- used to facilitate mapping to OWL or RDF."),
    "recommended": (("boolProperty", ),
                    "A schema attribute indicating that the event-level HED string should include this tag."),
    "relatedTag": ((),
                   "A schema attribute suggesting HED tags that are closely related to this tag. This attribute is "
                   "used by tagging tools."),
    "requireChild": (("boolProperty", ),
                     "A schema attribute indicating that one of the node elements descendants must be included when "
                     "using this tag."),
    "required": (("boolProperty", ),
                 "A schema attribute indicating that every event-level HED string should include this tag."),
    "SIUnit": (("boolProperty", "unitProperty"),
               "A schema attribute indicating that this unit element is an SI unit and can be modified by multiple "
               "and submultiple names. Note that some units such as byte are designated as SI units although they are "
               "not part of the standard."),
    "SIUnitModifier": (("boolProperty", "unitModifierProperty"),
                       "A schema attribute indicating that this SI unit modifier represents a multiple or submultiple "
                       "of a base unit rather than a unit symbol."),
    "SIUnitSymbolModifier": (("boolProperty", "unitModifierProperty"),
                             "A schema attribute indicating that this SI unit modifier represents a multiple or "
                             "submultiple of a unit symbol rather than a base symbol."),
    "suggestedTag": ((),
                     "A schema attribute that indicates another tag  that is often associated with this tag. This "
                     "attribute is used by tagging tools to provide tagging suggestions."),
    "tagGroup": (("boolProperty", ),
                 "A schema attribute indicating the tag can only appear inside a tag group."),
    "takesValue": (("boolProperty", ),
                   "A schema attribute indicating the tag is a hashtag placeholder which is expected to be replaced "
                   "with a user-defined value."),
    "topLevelTagGroup": (("boolProperty", ),
                         "A schema attribute indicating that this tag (or its descendants) can only appear in a "
                         "top-level tag group."),
    "unique": (("boolProperty", ),
               "A schema attribute indicating that only one of this tag or its descendants can be used  in the "
               "event-level HED string."),
    "unitClass": ((),
                  "A schema attribute specifying which unit class this value tag belongs to."),
    "unitPrefix": (("boolProperty", "unitProperty"),
                   "A schema attribute applied specifically to unit elements to designate that the unit indicator is "
                   "a prefix (e.g., dollar sign in the currency units)."),
    "unitSymbol": (("boolProperty", "unitProperty"),
                   "A schema attribute indicating this tag is an abbreviation or symbol representing a type of unit. "
                   "Unit symbols represent both the singular and the plural and thus cannot be pluralized."),
    "valueClass": ((),
                   "A schema attribute indicating this is a value class."),
}

properties = {
    "boolProperty": "Indicates that the schema attribute represents something that is either true or false and does "
                    "not have a value. Attributes without this value are assumed to have string values.",
    "unitClassProperty": "Indicates that the schema attribute is meant to be applied to unit classes.",
    "unitModifierProperty": "Indicates that the schema attribute is meant to be applied to unit modifier classes.",
    "unitProperty": "Indicates that the schema attribute is meant to be applied to units within a unit class.",
    "valueClassProperty": "Indicates that the schema attribute is meant to be applied to value classes.",
}
