# from rdflib import Namespace
#
# from hed.schema.hed_schema_constants import HedSectionKey
#
#
# # Default file associations(notably owl maps to XML format, as we already use XML)
# ext_to_format = {
#     ".ttl": "turtle",
#     ".owl": "xml",
#     ".json-ld": "json-ld"
# }
#
# # Core schema structural types in owl
# HED = Namespace("https://purl.org/hed#")
# # Tags
# HEDT = Namespace("https://purl.org/hed/tag#")
# # Unit classes, value classes, and units
# HEDU = Namespace("https://purl.org/hed/aux#")
# # Unit Modifiers
# HEDUM = Namespace("https://purl.org/hed/aux/unit_modifier#")
#
# # Some of this stuff may be commented back in later if needed
#
# # SECTION_ELEMENT_NAME = {
# #     HedSectionKey.Tags: "StartSchemaSection",
# #     HedSectionKey.UnitClasses: "UnitClassSection",
# #     HedSectionKey.Units: "UnitSection",
# #     HedSectionKey.UnitModifiers: "UnitModifiersSection",
# #     HedSectionKey.ValueClasses: "ValueClassesSection",
# #     HedSectionKey.Attributes: "AttributesSection",
# #     HedSectionKey.Properties: "PropertiesSection",
# # }
# #
# # SECTION_ELEMENT_TYPE = {
# #     HedSectionKey.Tags: "HedStartSchemaSection",
# #     HedSectionKey.UnitClasses: "HedUnitClassSection",
# #     HedSectionKey.Units: "HedUnitSection",
# #     HedSectionKey.UnitModifiers: "HedUnitModifiersSection",
# #     HedSectionKey.ValueClasses: "HedValueClassesSection",
# #     HedSectionKey.Attributes: "HedAttributesSection",
# #     HedSectionKey.Properties: "HedPropertiesSection",
# # }
#
# ELEMENT_NAMES = {
#     HedSectionKey.Tags: "HedTag",
#     HedSectionKey.Units: "HedUnit",
#     HedSectionKey.UnitClasses: "HedUnitClass",
#     HedSectionKey.UnitModifiers: "HedUnitModifier",
#     HedSectionKey.ValueClasses: "HedValueClass",
# }
