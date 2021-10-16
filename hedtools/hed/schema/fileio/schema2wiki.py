"""Allows output of HedSchema objects as .mediawiki format"""

from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.fileio import wiki_constants


class HedSchema2Wiki:
    def __init__(self):
        self.current_tag_string = ""
        self.current_tag_extra = ""
        self.output = []

    def process_schema(self, hed_schema):
        """
        Takes a HedSchema object and returns a list of strings representing it's .mediawiki version.

        Parameters
        ----------
        hed_schema : HedSchema

        Returns
        -------
        mediawiki_strings: [str]
            A list of strings representing the .mediawiki version of this schema.
        """
        self.output = []

        self._output_header(hed_schema)
        self._output_tags(hed_schema)
        self.current_tag_string = wiki_constants.END_SCHEMA_STRING
        self._flush_current_tag()
        self._output_units(hed_schema)
        self._output_unit_modifiers(hed_schema)
        self._output_value_classes(hed_schema)
        self._output_attributes(hed_schema)
        self._output_properties(hed_schema)
        self._output_footer(hed_schema)

        return self.output

    def _output_header(self, hed_schema):
        hed_attrib_string = self._get_attribs_string_from_schema(hed_schema)
        self.current_tag_string = f"{wiki_constants.HEADER_LINE_STRING} {hed_attrib_string}"
        self._flush_current_tag()
        self._add_blank_line()
        self.current_tag_string = wiki_constants.PROLOGUE_SECTION_ELEMENT
        self._flush_current_tag()
        self.current_tag_string += hed_schema.prologue
        self._flush_current_tag()
        self._add_blank_line()
        self.current_tag_string = wiki_constants.START_HED_STRING
        self._flush_current_tag()

    def _output_footer(self, hed_schema):
        self.current_tag_string = wiki_constants.EPILOGUE_SECTION_ELEMENT
        self._flush_current_tag()
        self.current_tag_string += hed_schema.epilogue
        self._flush_current_tag()
        self._add_blank_line()
        self.current_tag_string = wiki_constants.END_HED_STRING
        self._flush_current_tag()

    def _output_tags(self, hed_schema):
        all_tags = hed_schema.get_all_schema_tags()

        for tag in all_tags:
            if "/" not in tag:
                self._add_blank_line()
                self.current_tag_string += f"'''{tag}'''"
            else:
                count = tag.count("/")
                short_tag = tag.split("/")[-1]
                # takes value tags should appear after the nowiki tag.
                if short_tag.endswith("#"):
                    self.current_tag_string += f"{'*' * count}"
                    self.current_tag_extra += short_tag + " "
                else:
                    self.current_tag_string += f"{'*' * count} {short_tag}"
            self.current_tag_extra += self._format_props_and_desc(hed_schema, tag)
            self._flush_current_tag()

        self._add_blank_line()
        self._add_blank_line()

    def _output_units(self, hed_schema):
        if not hed_schema.unit_classes:
            return

        self.current_tag_string += wiki_constants.UNIT_CLASS_STRING
        self._flush_current_tag()
        for unit_class, unit_entry in hed_schema[HedSectionKey.UnitClasses].items():
            unit_types = unit_entry.value
            self.current_tag_string += f"* {unit_class}"
            self.current_tag_extra += self._format_props_and_desc(hed_schema, unit_class, HedSectionKey.UnitClasses)
            self._flush_current_tag()

            for unit_type in unit_types:
                self.current_tag_string += f"** {unit_type}"
                self.current_tag_extra += self._format_props_and_desc(
                    hed_schema, unit_type, HedSectionKey.Units)
                self._flush_current_tag()

        self._add_blank_line()

    def _output_section(self, hed_schema, key_class):
        if not hed_schema._sections[key_class]:
            return
        self._add_blank_line()
        self.current_tag_string += wiki_constants.wiki_section_headers[key_class]
        self._flush_current_tag()
        for value_name in hed_schema[key_class]:
            self.current_tag_string += f"* {value_name}"
            self.current_tag_extra += self._format_props_and_desc(hed_schema, value_name, key_class)
            self._flush_current_tag()

    def _output_unit_modifiers(self, hed_schema):
        self._output_section(hed_schema, HedSectionKey.UnitModifiers)
        return

    def _output_value_classes(self, hed_schema):
        self._output_section(hed_schema, HedSectionKey.ValueClasses)

    def _output_attributes(self, hed_schema):
        self._output_section(hed_schema, HedSectionKey.Attributes)

    def _output_properties(self, hed_schema):
        self._output_section(hed_schema, HedSectionKey.Properties)

    def _flush_current_tag(self):
        if self.current_tag_string or self.current_tag_extra:
            if self.current_tag_extra:
                new_tag = f"{self.current_tag_string} <nowiki>{self.current_tag_extra}</nowiki>"
            else:
                new_tag = self.current_tag_string
            self.output.append(new_tag)
            self.current_tag_string = ""
            self.current_tag_extra = ""

    def _add_blank_line(self):
        self.output.append("")

    # Should this be a function?
    def _format_props_and_desc(self, hed_schema, tag_name, key_class=HedSectionKey.AllTags):
        prop_string = ""
        tag_props = hed_schema.get_all_tag_attributes(tag_name, key_class=key_class)
        if tag_props:
            prop_string += self._format_tag_props(tag_props)
        desc = hed_schema.get_tag_description(tag_name, key_class)
        if desc:
            if tag_props:
                prop_string += " "
            prop_string += f"[{desc}]"

        return prop_string

    @staticmethod
    def _format_tag_props(tag_props):
        """
            Takes a dictionary of tag attributes and returns a string with the .mediawiki representation

        Parameters
        ----------
        tag_props : {str:str}
            {attribute_name : attribute_value}
        Returns
        -------
        str:
            The formatted string that should be output to the file.
        """
        prop_string = ""
        final_props = []
        for prop, value in tag_props.items():
            if value is None or value is False:
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
            prop_string += "{"
            final_prop_string = ", ".join(final_props)
            prop_string += final_prop_string
            prop_string += "}"

        return prop_string

    @staticmethod
    def _get_attribs_string_from_schema(hed_schema):
        """
        Gets the schema attributes and converts it to a string.

        Parameters
        ----------
        hed_schema : HedSchema
            The schema to get attributes from

        Returns
        -------
        str:
            A string of the attributes that can be written to a .mediawiki formatted file
        """
        # Hardcode version to always be the first thing in attributes
        attrib_values = [f"version=\"{hed_schema.header_attributes['version']}\""]
        attrib_values.extend([f"{attr}=\"{value}\"" for attr, value in
                              hed_schema.header_attributes.items() if attr != "version"])
        final_attrib_string = " ".join(attrib_values)
        return final_attrib_string
