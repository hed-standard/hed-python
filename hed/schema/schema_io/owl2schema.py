"""
This module is used to create a HedSchema object from an OWL file or graph.
"""


from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.schema import schema_validation_util
from .base2schema import SchemaLoader
import rdflib
from rdflib.exceptions import ParserError
from rdflib import Graph, RDF, RDFS, Literal, URIRef, OWL, XSD
from collections import defaultdict

from hed.schema.schema_io.owl_constants import HED, HEDT, HEDU, HEDUM


class SchemaLoaderOWL(SchemaLoader):
    """ Loads XML schemas from filenames or strings.

        Expected usage is SchemaLoaderXML.load(filename)

        SchemaLoaderXML(filename) will load just the header_attributes
    """
    def __init__(self, filename, schema_as_string=None, schema=None, file_format=None, name=""):
        if schema_as_string and not file_format:
            raise HedFileError(HedExceptions.BAD_PARAMETERS,
                               "Must pass a file_format if loading owl schema as a string.",
                               name)
        super().__init__(filename, schema_as_string, schema, file_format, name)

        self._schema.source_format = ".owl"
        self.graph = None
        # When loading, this stores rooted tag name -> full root path pairs
        self._rooted_cache = {}

    def _open_file(self):
        """Parses a Turtle/owl/etc file and returns the RDF graph."""

        graph = rdflib.Graph()
        try:
            if self.filename:
                graph.parse(self.filename, format=self.file_format)
            else:
                graph.parse(data=self.schema_as_string, format=self.file_format)
        except FileNotFoundError as fnf_error:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(fnf_error), self.name)
        except ParserError as parse_error:
            raise HedFileError(HedExceptions.CANNOT_PARSE_RDF, str(parse_error), self.name)

        return graph

    def _read_prologue(self):
        """Reads the Prologue section from the ontology."""
        prologue = self.graph.value(subject=HED.Prologue, predicate=HED.elementValue, any=False)
        return str(prologue) if prologue else ""

    def _read_epilogue(self):
        """Reads the Epilogue section from the ontology."""
        epilogue = self.graph.value(subject=HED.Epilogue, predicate=HED.elementValue, any=False)
        return str(epilogue) if epilogue else ""

    def _get_header_attributes(self, graph):
        """Parses header attributes from an RDF graph into a dictionary."""
        header_attributes = {}
        for s, _, _ in graph.triples((None, RDF.type, HED.HeaderMember)):
            label = graph.value(s, RDFS.label)
            if label:
                header_attribute = graph.value(s, HED.HeaderAttribute)
                header_attributes[str(label)] = str(header_attribute) if header_attribute else None
        return header_attributes

    def _parse_data(self):
        self.graph = self.input_data
        self.graph.bind("hed", HED)
        self.graph.bind("hedt", HEDT)
        self.graph.bind("hedu", HEDU)
        self.graph.bind("hedum", HEDUM)


        self._schema.epilogue = self._read_epilogue()
        self._schema.prologue = self._read_prologue()
        self._get_header_attributes(self.graph)
        self._read_properties()
        self._read_attributes()
        self._read_units()
        self._read_section(HedSectionKey.ValueClasses, HED.HedValueClass)
        self._read_section(HedSectionKey.UnitModifiers, HED.HedUnitModifier)
        self._read_tags()

        breakHere = 3

    def get_local_names_from_uris(parent_chain, tag_uri):
        """
        Extracts local names from URIs using RDFlib's n3() method.
        """
        full_names = []
        for uri in parent_chain + [tag_uri]:
            # Serialize the URI into N3 format and extract the local name
            name = uri.n3(namespace_manager=HED.namespace_manager).split(':')[-1]
            full_names.append(name)

        return full_names

    def sort_classes_by_hierarchy(self, classes):
        """
            Sorts all tags based on assembled full name

        Returns:
            list of tuples.
            Left Tag URI, right side is parent labels(not including self)
        """
        parent_chains = []
        full_tag_names = []
        for tag_uri in classes:
            parent_chain = self._get_parent_chain(tag_uri)
            parent_chain = [uri.n3(namespace_manager=self.graph.namespace_manager).split(':')[-1] for uri in parent_chain + [tag_uri]]
            # parent_chain = [self.graph.value(p, RDFS.label) or p for p in parent_chain + [tag_uri]]
            full_tag_names.append("/".join(parent_chain))
            parent_chains.append((tag_uri, parent_chain[:-1]))

        # Sort parent_chains by full_tag_names.
        _, parent_chains = zip(*sorted(zip(full_tag_names, parent_chains)))

        return parent_chains

    def _get_parent_chain(self, cls):
        """ Recursively builds the parent chain for a given class. """
        parent = self.graph.value(subject=cls, predicate=HED.hasHedParent)
        if parent is None:
            return []
        return self._get_parent_chain(parent) + [parent]

    def _parse_uri(self, uri, key_class, name=None):
        if name:
            label = name
        else:
            label = self.graph.value(subject=uri, predicate=RDFS.label)
        if not label:
            raise ValueError(f"Empty label value found in owl file in uri {uri}")
        label = str(label)

        tag_entry = self._schema._create_tag_entry(label, key_class)

        description = self.graph.value(subject=uri, predicate=RDFS.comment)
        if description:
            tag_entry.description = str(description)

        section = self._schema._sections[key_class]
        valid_attributes = section.valid_attributes

        new_values = defaultdict(list)
        for predicate, obj in self.graph.predicate_objects(subject=uri):
            # Convert predicate URI to a readable string, assuming it's in a known namespace
            attr_name = predicate.n3(self.graph.namespace_manager).split(':')[1]

            if attr_name in valid_attributes:
                if isinstance(obj, URIRef):
                    attr_value = obj.n3(self.graph.namespace_manager).split(':')[1]
                else:
                    attr_value = str(obj)

                new_values[attr_name].append(attr_value)

        for name, value in new_values.items():
            value = ",".join(value)
            if value == "true":
                value = True
            tag_entry._set_attribute_value(name, value)

        return tag_entry

    def _get_classes_with_subproperty(self, subproperty_uri, base_type):
        """Iterates over all classes that have a specified rdfs:subPropertyOf."""
        classes = set()
        for s in self.graph.subjects(RDF.type, base_type):
            if (s, RDFS.subPropertyOf, subproperty_uri) in self.graph:
                classes.add(s)
        return classes

    def _get_all_subclasses(self, base_type):
        """
        Recursively finds all subclasses of the given base_type.
        """
        subclasses = set()
        for subclass in self.graph.subjects(RDFS.subClassOf, base_type):
            subclasses.add(subclass)
            subclasses.update(self._get_all_subclasses(subclass))
        return subclasses

    def _get_classes(self, base_type):
        """
        Retrieves all instances of the given base_type, including instances of its subclasses.
        """
        classes = set()
        # Add instances of the base type
        for s in self.graph.subjects(RDF.type, base_type):
            classes.add(s)
        # Add instances of all subclasses
        for subclass in self._get_all_subclasses(base_type):
            for s in self.graph.subjects(RDF.type, subclass):
                classes.add(s)
        return classes

    def _read_properties(self):
        key_class = HedSectionKey.Properties
        self._schema._initialize_attributes(key_class)
        prop_uris = self._get_classes_with_subproperty(HED.schemaProperty, OWL.AnnotationProperty)
        for uri in prop_uris:
            new_entry = self._parse_uri(uri, key_class)
            self._add_to_dict(new_entry, key_class)

    def _read_attributes(self):
        key_class = HedSectionKey.Attributes
        self._schema._initialize_attributes(key_class)
        prop_uris = self._get_classes_with_subproperty(HED.schemaAttributeDatatypeProperty, OWL.DatatypeProperty)
        prop_uris.update(self._get_classes_with_subproperty(HED.schemaAttributeObjectProperty, OWL.ObjectProperty))

        for uri in prop_uris:
            new_entry = self._parse_uri(uri, key_class)
            self._add_to_dict(new_entry, key_class)

    def _read_section(self, key_class, node_uri):
        self._schema._initialize_attributes(key_class)
        classes = self._get_classes(node_uri)
        for uri in classes:
            new_entry = self._parse_uri(uri, key_class)
            self._add_to_dict(new_entry, key_class)

    def _read_units(self):
        self._schema._initialize_attributes(HedSectionKey.UnitClasses)
        self._schema._initialize_attributes(HedSectionKey.Units)
        key_class = HedSectionKey.UnitClasses
        classes = self._get_classes(HED.HedUnitClass)
        unit_classes = {}
        for uri in classes:
            new_entry = self._parse_uri(uri, key_class)
            self._add_to_dict(new_entry, key_class)
            unit_classes[uri] = new_entry



        key_class = HedSectionKey.Units
        units = self._get_classes(HED.HedUnit)
        for uri in units:
            new_entry = self._parse_uri(uri, key_class)
            self._add_to_dict(new_entry, key_class)
            unit_class_uri = self.graph.value(subject=uri, predicate=HED.unitClass)
            class_entry = unit_classes.get(unit_class_uri)
            class_entry.add_unit(new_entry)
            breakHere = 3

    def _add_tag_internal(self, uri, parent_tags):
        tag_name = self.graph.value(uri, RDFS.label)
        if not tag_name:
            raise ValueError(f"No label for uri {uri}")
        tag_name = str(tag_name)
        parents_and_child = parent_tags + [tag_name]
        if parent_tags and parents_and_child[0] in self._rooted_cache:
            full_tag = "/".join([self._rooted_cache[parents_and_child[0]]] + parents_and_child[1:])
        else:
            full_tag = "/".join(parents_and_child)

        tag_entry = self._parse_uri(uri, HedSectionKey.Tags, full_tag)

        rooted_entry = schema_validation_util.find_rooted_entry(tag_entry, self._schema, self._loading_merged)
        if rooted_entry:
            loading_from_chain = rooted_entry.name + "/" + tag_entry.short_tag_name
            loading_from_chain_short = tag_entry.short_tag_name
            self._rooted_cache[tag_entry.short_tag_name] = loading_from_chain
            full_tag = full_tag.replace(loading_from_chain_short, loading_from_chain)
            tag_entry = self._parse_uri(uri, HedSectionKey.Tags, full_tag)

        self._add_to_dict(tag_entry, HedSectionKey.Tags)

    def _read_tags(self):
        """Populates a dictionary of dictionaries associated with tags and their attributes."""
        classes = self._get_classes(HED.HedTag)
        classes.update(self._get_classes(HED.HedPlaceholder))
        sorted_classes = self.sort_classes_by_hierarchy(classes)
        self._schema._initialize_attributes(HedSectionKey.Tags)
        for uri, parents in sorted_classes:
            self._add_tag_internal(uri, parents)

    def _add_to_dict(self, entry, key_class):
        if entry.has_attribute(HedKey.InLibrary) and not self._loading_merged and not self.appending_to_schema:
            raise HedFileError(HedExceptions.IN_LIBRARY_IN_UNMERGED,
                               f"Library tag in unmerged schema has InLibrary attribute",
                               self.name)

        return self._add_to_dict_base(entry, key_class)
