# """Allows output of HedSchema objects as .xml format"""
#
# from hed.schema.hed_schema_constants import HedSectionKey, HedKey
# from hed.schema.schema_io import owl_constants
# from hed.schema.schema_io.schema2base import Schema2Base
# from rdflib import Graph, RDF, RDFS, Literal, URIRef, OWL, XSD
#
# from hed.schema.schema_io.owl_constants import HED, HEDT, HEDU, HEDUM
# import re
#
#
# HED_URIS = {
#     None: HED,
#     HedSectionKey.Tags: HEDT,
#     HedSectionKey.UnitClasses: HEDU,
#     HedSectionKey.Units: HEDU,
#     HedSectionKey.UnitModifiers: HEDUM,
#     HedSectionKey.ValueClasses: HEDU,
#     HedSectionKey.Attributes: HED,
#     HedSectionKey.Properties: HED,
# }
#
# HED_ATTR = {
#     "unitClass": HEDU,
#     "valueClass": HEDU,
#     "unit": HEDU,
#     "unitModifier": HEDUM,
#     "property": HED,
#     "suggestedTag": HEDT,
#     "relatedTag": HEDT,
#     "rooted": HEDT,
# }
#
# float_attributes = {"conversionFactor"}
#
# hed_keys_with_types = {
#     HedKey.ExtensionAllowed: XSD["boolean"],
#     HedKey.Recommended: XSD["boolean"],
#     HedKey.Required: XSD["boolean"],
#     HedKey.RequireChild: XSD["boolean"],
#     HedKey.TagGroup: XSD["boolean"],
#     HedKey.TakesValue: XSD["boolean"],
#     HedKey.TopLevelTagGroup: XSD["boolean"],
#     HedKey.Unique: XSD["boolean"],
#     HedKey.UnitClass: HED["HedUnitClass"],
#     HedKey.ValueClass: HED["HedValueClass"],
#     HedKey.RelatedTag: HED["HedTag"],
#     HedKey.SuggestedTag: HED["HedTag"],
#     HedKey.Rooted: HED["HedTag"],
#     HedKey.DeprecatedFrom: XSD["string"],
#     HedKey.ConversionFactor: XSD["string"],
#     HedKey.Reserved: XSD["boolean"],
#     HedKey.SIUnit: XSD["boolean"],
#     HedKey.UnitSymbol: XSD["boolean"],
#     HedKey.DefaultUnits: HED["HedUnit"],
#     HedKey.UnitPrefix: XSD["boolean"],
#     HedKey.SIUnitModifier: XSD["boolean"],
#     HedKey.SIUnitSymbolModifier: XSD["boolean"],
#     HedKey.AllowedCharacter: XSD["string"],
#     HedKey.InLibrary: XSD["string"]
# }
#
# object_properties = {key for key, value in hed_keys_with_types.items() if value.startswith(HED)}
#
#
# class Schema2Owl(Schema2Base):
#     def __init__(self):
#         super().__init__()
#         self.owl_graph = Graph()
#         self.output = self.owl_graph
#         self.owl_graph.bind("hed", HED)
#         self.owl_graph.bind("hedt", HEDT)
#         self.owl_graph.bind("hedu", HEDU)
#         self.owl_graph.bind("hedum", HEDUM)
#
#     # =========================================
#     # Required baseclass function
#     # =========================================
#     def _output_header(self, attributes, prologue):
#         # Create a dictionary mapping label names to property URIs
#         property_uris = {
#             "library": HED.Library,
#             "unmerged": HED.Unmerged,
#             "version": HED.Version,
#             "withStandard": HED.WithStandard,
#             "xmlns:xsi": HED.XSI,
#             "xsi:noNamespaceSchemaLocation": HED.XSINoNamespaceSchemaLocation
#         }
#
#         for attrib_label, attrib_value in attributes.items():
#             prop_uri = property_uris.get(attrib_label)
#             if prop_uri:
#                 self.owl_graph.add((prop_uri, RDF.type, HED.HeaderMember))
#                 self.owl_graph.add((prop_uri, RDFS.label, Literal(attrib_label)))
#                 self.owl_graph.add((prop_uri, HED.HeaderAttribute, Literal(attrib_value)))
#
#         self.owl_graph.add((HED.Prologue, RDF.type, HED.HedElement))
#         self.owl_graph.add((HED.Prologue, RDFS.label, Literal("epilogue")))
#         if prologue:
#             self.owl_graph.add((HED.Prologue, HED["elementValue"], Literal(prologue)))
#
#     def _output_footer(self, epilogue):
#         self.owl_graph.add((HED.Epilogue, RDF.type, HED.HedElement))
#         self.owl_graph.add((HED.Epilogue, RDFS.label, Literal("epilogue")))
#         if epilogue:
#             self.owl_graph.add((HED.Epilogue, HED["elementValue"], Literal(epilogue)))
#
#     def _start_section(self, key_class):
#         return None
#
#     def _end_tag_section(self):
#         pass
#
#     def _write_attributes(self, entry_uri, entry):
#         for attribute, value in entry.attributes.items():
#             is_bool = entry.attribute_has_property(attribute, "boolProperty") \
#                       or entry.section_key == HedSectionKey.Attributes
#
#             if self._attribute_disallowed(attribute):
#                 continue
#
#             if is_bool:
#                 self.owl_graph.add((entry_uri, HED[attribute], Literal(True)))
#
#             elif attribute in float_attributes:
#                 # Treat as a string for now
#                 self.owl_graph.add((entry_uri, HED[attribute], Literal(value)))
#             else:
#                 # Todo: further develop this if needed or merge into base tools
#                 values = value.split(",")
#                 for val2 in values:
#                     clean_value = val2
#                     if attribute in HED_ATTR:
#                         attribute_uri = HED_ATTR[attribute][clean_value]
#                     else:
#                         attribute_uri = Literal(clean_value)
#
#                     self.owl_graph.add((entry_uri, HED[attribute], attribute_uri))
#
#     def _add_entry(self, base_uri, tag_name, label, comment, parent=None, entry=None,
#                    tag_type=HED.HedTag, unit_class_uri=None):
#         is_takes_value = entry.has_attribute("takesValue")
#         if is_takes_value:
#             tag_type = HED.HedPlaceholder
#             tag_name = entry.short_tag_name + "-Placeholder"
#             label = "#"
#
#         tag_name = sanitize_for_turtle(tag_name)
#         uri = f"{base_uri}{tag_name}"
#         hed_tag_uri = URIRef(uri)
#
#         self.owl_graph.add((hed_tag_uri, RDF.type, tag_type))
#         self.owl_graph.add((hed_tag_uri, RDFS.label, Literal(label)))
#         if comment:
#             self.owl_graph.add((hed_tag_uri, RDFS.comment, Literal(comment)))
#         # Don't store the parent in unmerged rooted nodes
#         if parent is not None and (HedKey.Rooted not in entry.attributes or self._save_merged):
#             parent_uri = HEDT[parent]
#             self.owl_graph.add((hed_tag_uri, HED.hasHedParent, parent_uri))
#         if unit_class_uri is not None:
#             self.owl_graph.add((hed_tag_uri, HED.unitClass, unit_class_uri))
#         self._write_attributes(hed_tag_uri, entry)
#         return hed_tag_uri
#
#     def _add_property(self, base_uri, name, label, comment, entry,
#                       data_type, sub_type):
#         name = sanitize_for_turtle(name)
#         uri = f"{base_uri}{name}"
#         hed_tag_uri = URIRef(uri)
#
#         self.owl_graph.add((hed_tag_uri, RDF.type, data_type))
#         self.owl_graph.add((hed_tag_uri, RDFS.subPropertyOf, sub_type))
#         self.owl_graph.add((hed_tag_uri, RDFS.range, XSD.boolean))
#         self.owl_graph.add((hed_tag_uri, RDFS.label, Literal(label)))
#         self.owl_graph.add((hed_tag_uri, RDFS.comment, Literal(comment)))
#         self._write_attributes(hed_tag_uri, entry)
#
#         return hed_tag_uri
#
#     def _get_element_domains(self, entry):
#         domain_table = {HedKey.ValueClassProperty: "HedValueClass",
#                         HedKey.UnitModifierProperty: "HedUnitModifier",
#                         HedKey.UnitProperty: "HedUnit",
#                         HedKey.ElementProperty: "HedElement",
#                         HedKey.UnitClassProperty: "HedUnitClass",
#                         HedKey.NodeProperty: "HedTag"
#                         }
#         domains = []
#         for attribute in entry.attributes:
#             if attribute in domain_table:
#                 domains.append(domain_table[attribute])
#
#         if not domains:
#             domains.append(domain_table[HedKey.NodeProperty])
#
#         return domains
#
#     def _add_attribute(self, base_uri, name, label, comment, entry):
#         domains = self._get_element_domains(entry)
#         name = sanitize_for_turtle(name)
#         uri = f"{base_uri}{name}"
#         hed_tag_uri = URIRef(uri)
#         data_type = OWL.ObjectProperty
#         sub_type = HED.schemaAttributeObjectProperty
#         if name not in object_properties:
#             data_type = OWL.DatatypeProperty
#             sub_type = HED.schemaAttributeDatatypeProperty
#         self.owl_graph.add((hed_tag_uri, RDF.type, data_type))
#         for domain in domains:
#             self.owl_graph.add((hed_tag_uri, RDFS.domain, HED[domain]))
#         self.owl_graph.add((hed_tag_uri, RDFS.subPropertyOf, sub_type))
#         self.owl_graph.add((hed_tag_uri, RDFS.range, hed_keys_with_types[name]))
#         self.owl_graph.add((hed_tag_uri, RDFS.label, Literal(label)))
#         self.owl_graph.add((hed_tag_uri, RDFS.comment, Literal(comment)))
#         self._write_attributes(hed_tag_uri, entry)
#
#         return hed_tag_uri
#
#     def _write_tag_entry(self, tag_entry, parent_node=None, level=0):
#         """
#             Creates a tag node and adds it to the parent.
#
#         Parameters
#         ----------
#         tag_entry: HedTagEntry
#             The entry for that tag we want to write out
#         parent_node: Any
#             Unused
#         level: Any
#             Unused
#
#         Returns
#         -------
#         SubElement
#             The added node
#         """
#         tag_name = tag_entry.short_tag_name
#         parent = tag_entry.parent
#         if parent:
#             parent = parent.short_tag_name
#         comment = tag_entry.description
#         return self._add_entry(
#             HEDT,
#             tag_name=tag_name,
#             label=tag_name,
#             comment=comment,
#             parent=parent,
#             entry=tag_entry
#         )
#
#     def _write_entry(self, entry, parent_node=None, include_props=True):
#         """
#             Creates an entry node and adds it to the parent.
#
#         Parameters:
#             entry(HedSchemaEntry): The entry for that tag we want to write out
#             parent_node(str): URI for unit class owner, if this is a unit
#             include_props(bool): Add the description and attributes to new node.
#         Returns:
#             str: The added URI
#         """
#         key_class = entry.section_key
#         prefix = HED_URIS[key_class]
#         name = entry.name
#         comment = entry.description
#         if key_class == HedSectionKey.Attributes:
#             uri = self._add_attribute(
#                 prefix,
#                 name=name,
#                 label=name,
#                 comment=comment,
#                 entry=entry
#             )
#         elif key_class == HedSectionKey.Properties:
#             uri = self._add_property(
#                 prefix,
#                 name=name,
#                 label=name,
#                 comment=comment,
#                 entry=entry,
#                 data_type=OWL.AnnotationProperty,
#                 sub_type=HED.schemaProperty
#             )
#         else:
#             unit_class_uri = None
#             if key_class == HedSectionKey.Units:
#                 unit_class_uri = parent_node
#             uri = self._add_entry(
#                 prefix,
#                 tag_name=name,
#                 label=name,
#                 comment=comment,
#                 entry=entry,
#                 tag_type=HED[owl_constants.ELEMENT_NAMES[key_class]],
#                 unit_class_uri=unit_class_uri
#             )
#         return uri
#
#
# def sanitize_for_turtle(name):
#     """ Sanitizes a string to be a valid IRIREF in Turtle, based on the SPARQL grammar.
#
#     Excludes: `control characters, space, <, >, double quote, {, }, |, ^, backtick, and backslash.`
#         Replacing them with underscores
#
#     Parameters:
#         name (str): The string to sanitize.
#
#     Returns:
#         str: A sanitized string suitable for use as an IRIREF in Turtle.
#     """
#     invalid_chars_pattern = r'[\x00-\x20<>"{}\|^`\\]'
#     return re.sub(invalid_chars_pattern, '_', name)
