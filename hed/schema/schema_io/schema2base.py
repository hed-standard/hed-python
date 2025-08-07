"""Baseclass for mediawiki/xml writers"""
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.errors.exceptions import HedFileError, HedExceptions


class Schema2Base:
    def __init__(self):
        # Placeholder output variable
        self.output = None
        self._save_lib = False
        self._save_base = False
        self._save_merged = False
        self._strip_out_in_library = False
        self._schema = None

    def process_schema(self, hed_schema, save_merged=False):
        """ Takes a HedSchema object and returns it in the inherited form(mediawiki, xml, etc)

        Parameters:
            hed_schema (HedSchema): The schema to be processed.
            save_merged (bool): If True, save as merged schema if has "withStandard".

        Returns:
            Any: Varies based on inherited class

        """
        if not hed_schema.can_save():
            raise HedFileError(HedExceptions.SCHEMA_LIBRARY_INVALID,
                               "Cannot save a schema merged from multiple library schemas",
                               hed_schema.filename)

        self._initialize_output()
        self._save_lib = False
        self._save_base = False
        self._strip_out_in_library = True
        self._schema = hed_schema  # This is needed to save attributes in dataframes for now
        if hed_schema.with_standard:
            self._save_lib = True
            if save_merged:
                self._save_base = True
                self._strip_out_in_library = False
        else:
            # Saving a standard schema or a library schema without a standard schema
            save_merged = True
            self._save_lib = True
            self._save_base = True

        self._save_merged = save_merged

        self._output_header(hed_schema.get_save_header_attributes(self._save_merged))
        self._output_prologue(hed_schema.prologue)
        self._output_tags(hed_schema.tags)
        self._output_units(hed_schema.unit_classes)
        self._output_section(hed_schema, HedSectionKey.UnitModifiers)
        self._output_section(hed_schema, HedSectionKey.ValueClasses)
        self._output_section(hed_schema, HedSectionKey.Attributes)
        self._output_section(hed_schema, HedSectionKey.Properties)
        self._output_annotations(hed_schema)
        self._output_epilogue(hed_schema.epilogue)
        self._output_extras(hed_schema)  # Allow subclasses to add additional sections if needed
        self._output_footer()

        return self.output

    def _initialize_output(self):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_header(self, attributes, prologue):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_prologue(self, attributes, prologue):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_annotations(self, hed_schema):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_extras(self, hed_schema):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_epilogue(self, epilogue):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_footer(self):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _start_section(self, key_class):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _end_tag_section(self):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _end_units_section(self):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _end_section(self, section_key):
        """ Clean up for sections other than tags and units.

        Parameters:
            section_key (HedSectionKey): The section key to end.
        """
        raise NotImplementedError("This needs to be defined in the subclass")

    def _write_tag_entry(self, tag_entry, parent=None, level=0):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _write_entry(self, entry, parent_node, include_props=True):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_tags(self, tags):
        """ Output the tags section of the schema.

        Parameters:
            tags
        """
        schema_node = self._start_section(HedSectionKey.Tags)

        # This assumes .all_entries is sorted in a reasonable way for output.
        level_adj = 0
        all_nodes = {}  # List of all nodes we've written out.
        for tag_entry in tags.all_entries:
            if self._should_skip(tag_entry):
                continue
            tag = tag_entry.name
            level = tag.count("/")

            # Don't adjust if we're a top level tag(if this is a rooted tag, it will be re-adjusted below)
            if not tag_entry.parent_name:
                level_adj = 0
            if level == 0:
                root_tag = self._write_tag_entry(tag_entry, schema_node, level)
                all_nodes[tag_entry.name] = root_tag
            else:
                # Only output the rooted parent nodes if they have a parent(for duplicates that don't)
                if tag_entry.has_attribute(HedKey.InLibrary) and tag_entry.parent and \
                        not tag_entry.parent.has_attribute(HedKey.InLibrary) and not self._save_merged:
                    if tag_entry.parent.name not in all_nodes:
                        level_adj = level

                parent_node = all_nodes.get(tag_entry.parent_name, schema_node)
                child_node = self._write_tag_entry(tag_entry, parent_node, level - level_adj)
                all_nodes[tag_entry.name] = child_node

        self._end_tag_section()

    def _output_units(self, unit_classes):
        section_node = self._start_section(HedSectionKey.UnitClasses)

        for unit_class_entry in unit_classes.values():
            has_lib_unit = False
            if self._should_skip(unit_class_entry):
                has_lib_unit = any(unit.attributes.get(HedKey.InLibrary) for unit in unit_class_entry.units.values())
                if not self._save_lib or not has_lib_unit:
                    continue

            unit_class_node = self._write_entry(unit_class_entry, section_node, not has_lib_unit)

            unit_types = unit_class_entry.units
            for unit_entry in unit_types.values():
                if self._should_skip(unit_entry):
                    continue

                self._write_entry(unit_entry, unit_class_node)
        self._end_units_section()

    def _output_section(self, hed_schema, key_class):
        parent_node = self._start_section(key_class)
        for entry in hed_schema[key_class].values():
            if self._should_skip(entry):
                continue
            self._write_entry(entry, parent_node)
        self._end_section(key_class)

    def _should_skip(self, entry):
        has_lib_attr = entry.has_attribute(HedKey.InLibrary)
        if not self._save_base and not has_lib_attr:
            return True
        if not self._save_lib and has_lib_attr:
            return True
        return False

    def _attribute_disallowed(self, attribute):
        return self._strip_out_in_library and attribute == HedKey.InLibrary

    def _format_tag_attributes(self, attributes):
        """ Takes a dictionary of tag attributes and returns a string with the .mediawiki representation.

        Parameters:
            attributes: {str:str}: Dictionary with {attribute_name : attribute_value}

        Returns:
            str: The formatted string that should be output to the file.
        """
        prop_string = ""
        final_props = []
        for prop, value in attributes.items():
            # Never save InLibrary if saving merged.
            if self._attribute_disallowed(prop):
                continue
            if value is True:
                final_props.append(prop)
            else:
                if "," in value:
                    split_values = value.split(",")
                    for split_value in split_values:
                        final_props.append(f"{prop}={split_value}")
                else:
                    final_props.append(f"{prop}={value}")

        if final_props:
            interior = ", ".join(final_props)
            prop_string = f"{interior}"

        return prop_string

    @staticmethod
    def _get_attribs_string_from_schema(header_attributes, sep=" "):
        """ Gets the schema attributes and converts it to a string.

        Parameters:
            header_attributes (dict): Attributes to format attributes from.

        Returns:
            str: A string of the attributes that can be written to a .mediawiki formatted file.
        """
        attrib_values = [f"{attr}=\"{value}\"" for attr, value in header_attributes.items()]
        final_attrib_string = sep.join(attrib_values)
        return final_attrib_string
