"""Baseclass for mediawiki/xml writers"""
from hed.schema.hed_schema_constants import HedSectionKey, HedKey


class Schema2Base:
    def __init__(self):
        # Placeholder output variable
        self.output = None
        self._save_lib = False
        self._save_base = False
        self._save_merged = False
        self._strip_out_in_library = False

    @classmethod
    def process_schema(cls, hed_schema, save_merged=False):
        """
        Takes a HedSchema object and returns a list of strings representing its .mediawiki version.

        Parameters
        ----------
        hed_schema : HedSchema
        save_merged: bool
            If True, this will save the schema as a merged schema if it is a "withStandard" schema.
            If it is not a "withStandard" schema, this setting has no effect.

        Returns
        -------
        converted_output: Any
            Varies based on inherited class

        """
        saver = cls()
        saver._save_lib = False
        saver._save_base = False
        saver._strip_out_in_library = True
        if hed_schema.with_standard:
            saver._save_lib = True
            if save_merged:
                saver._save_base = True
                saver._strip_out_in_library = False
        else:
            # Saving a standard schema or a library schema without a standard schema
            save_merged = True
            saver._save_lib = True
            saver._save_base = True

        saver._save_merged = save_merged

        saver._output_header(hed_schema.get_save_header_attributes(saver._save_merged), hed_schema.prologue)
        saver._output_tags(hed_schema.tags)
        saver._output_units(hed_schema.unit_classes)
        saver._output_section(hed_schema, HedSectionKey.UnitModifiers)
        saver._output_section(hed_schema, HedSectionKey.ValueClasses)
        saver._output_section(hed_schema, HedSectionKey.Attributes)
        saver._output_section(hed_schema, HedSectionKey.Properties)
        saver._output_footer(hed_schema.epilogue)

        return saver.output

    def _output_header(self, attributes, prologue):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_footer(self, epilogue):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _start_section(self, key_class):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _end_tag_section(self):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _write_tag_entry(self, tag_entry, parent=None, level=0):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _write_entry(self, entry, parent_node, include_props=True):
        raise NotImplementedError("This needs to be defined in the subclass")

    def _output_tags(self, tags):
        schema_node = self._start_section(HedSectionKey.Tags)

        # This assumes .all_entries is sorted in a reasonable way for output.
        level_adj = 0
        all_nodes = {}  # List of all nodes we've written out.
        for tag_entry in tags.all_entries:
            if self._should_skip(tag_entry):
                continue
            tag = tag_entry.name
            level = tag.count("/")

            if not tag_entry.has_attribute(HedKey.InLibrary):
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

    def _output_section(self, hed_schema, key_class):
        parent_node = self._start_section(key_class)
        for entry in hed_schema[key_class].values():
            if self._should_skip(entry):
                continue
            self._write_entry(entry, parent_node)

    def _should_skip(self, entry):
        has_lib_attr = entry.has_attribute(HedKey.InLibrary)
        if not self._save_base and not has_lib_attr:
            return True
        if not self._save_lib and has_lib_attr:
            return True
        return False

    def _attribute_disallowed(self, attribute):
        return self._strip_out_in_library and attribute == HedKey.InLibrary
