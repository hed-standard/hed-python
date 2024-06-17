"""Allows output of HedSchema objects as .mediawiki format"""

from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.schema_io import wiki_constants
from hed.schema.schema_io.schema2base import Schema2Base


class Schema2Wiki(Schema2Base):
    def __init__(self):
        super().__init__()
        self.current_tag_string = ""
        self.current_tag_extra = ""

    # =========================================
    # Required baseclass function
    # =========================================
    def _initialize_output(self):
        self.current_tag_string = ""
        self.current_tag_extra = ""
        self.output = []

    def _output_header(self, attributes, prologue):
        hed_attrib_string = self._get_attribs_string_from_schema(attributes)
        self.current_tag_string = f"{wiki_constants.HEADER_LINE_STRING} {hed_attrib_string}"
        self._flush_current_tag()
        self._add_blank_line()
        self.current_tag_string = wiki_constants.PROLOGUE_SECTION_ELEMENT
        self._flush_current_tag()
        self.current_tag_string += prologue
        self._flush_current_tag()

    def _output_footer(self, epilogue):
        self.current_tag_string = wiki_constants.EPILOGUE_SECTION_ELEMENT
        self._flush_current_tag()
        self.current_tag_string += epilogue
        self._flush_current_tag()
        self._add_blank_line()
        self.current_tag_string = wiki_constants.END_HED_STRING
        self._flush_current_tag()

    def _start_section(self, key_class):
        self._add_blank_line()
        self.current_tag_string += wiki_constants.wiki_section_headers[key_class]
        self._flush_current_tag()

    def _end_tag_section(self):
        self._add_blank_line()
        self._add_blank_line()

        self.current_tag_string = wiki_constants.END_SCHEMA_STRING
        self._flush_current_tag()

    def _write_tag_entry(self, tag_entry, parent_node=None, level=0):
        tag = tag_entry.name
        if level == 0:
            if "/" in tag:
                tag = tag_entry.short_tag_name
            self._add_blank_line()
            self.current_tag_string += f"'''{tag}'''"
        else:
            short_tag = tag.split("/")[-1]
            tab_char = ''  # GitHub mangles these, so remove spacing for now.
            # takes value tags should appear after the nowiki tag.
            if short_tag.endswith("#"):
                self.current_tag_string += f"{tab_char * level}{'*' * level} "
                self.current_tag_extra += short_tag + " "
            else:
                self.current_tag_string += f"{tab_char * level}{'*' * level} {short_tag}"
        self.current_tag_extra += self._format_props_and_desc(tag_entry)
        self._flush_current_tag()

    def _write_entry(self, entry, parent_node, include_props=True):
        entry_name = entry.name
        depth = 1
        if entry.section_key == HedSectionKey.Units:
            depth = 2
        self.current_tag_string += f"{'*' * depth} {entry_name}"
        if include_props:
            self.current_tag_extra += self._format_props_and_desc(entry)
        self._flush_current_tag()

    # =========================================
    # Helper functions to write out lines
    # =========================================
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

    def _format_props_and_desc(self, schema_entry):
        prop_string = ""
        tag_props = schema_entry.attributes
        if tag_props:
            prop_string += f"{{{self._format_tag_attributes(tag_props)}}}"
        desc = schema_entry.description
        if desc:
            if tag_props:
                prop_string += " "
            prop_string += f"[{desc}]"

        return prop_string
