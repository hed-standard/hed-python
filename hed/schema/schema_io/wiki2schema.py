"""
This module is used to create a HedSchema object from a .mediawiki file.
"""
import re

from hed.schema.hed_schema_constants import HedSectionKey
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.errors import error_reporter
from hed.schema.schema_io import wiki_constants
from hed.schema.schema_io.text2schema import SchemaLoaderText
from hed.schema.schema_io.wiki_constants import HedWikiSection, SectionStarts, SectionNames
from hed.schema.schema_io import text_util


extend_here_line = 'extend here'
invalid_characters_to_strip = ["&#8203;"]
tag_name_expression = r'(\*+|\'{3})(.*?)(\'{3})?\s*([\[\{]|$)+'
tag_name_re = re.compile(tag_name_expression)
no_wiki_tag = '</?nowiki>'
no_wiki_start_tag = '<nowiki>'
no_wiki_end_tag = '</nowiki>'

required_sections = [
    HedWikiSection.Prologue,
    HedWikiSection.Schema,
    HedWikiSection.EndSchema,
    HedWikiSection.UnitsClasses,
    HedWikiSection.UnitModifiers,
    HedWikiSection.ValueClasses,
    HedWikiSection.Attributes,
    HedWikiSection.Properties,
    HedWikiSection.Epilogue,
    HedWikiSection.EndHed,
]


class SchemaLoaderWiki(SchemaLoaderText):
    """ Load MediaWiki schemas from filenames or strings.

        Expected usage is SchemaLoaderWiki.load(filename)

        SchemaLoaderWiki(filename) will load just the header_attributes
    """

    def __init__(self, filename, schema_as_string=None, schema=None, file_format=None, name=""):
        super().__init__(filename, schema_as_string, schema, file_format, name)
        self._schema.source_format = ".mediawiki"
        self._no_name_msg = "Schema term is empty or the line is malformed",
        self._no_name_error = HedExceptions.WIKI_DELIMITERS_INVALID

    def _open_file(self):
        if self.filename:
            with open(self.filename, 'r', encoding='utf-8', errors='replace') as wiki_file:
                wiki_lines = wiki_file.readlines()
        else:
            # Split this into lines, but keep linebreaks.
            wiki_lines = [line + "\n" for line in self.schema_as_string.split("\n")]

        return wiki_lines

    def _get_header_attributes(self, file_data):
        line = ""
        if file_data:
            line = file_data[0]
            if line.startswith(wiki_constants.HEADER_LINE_STRING):
                hed_attributes = self._get_header_attributes_internal(line[len(wiki_constants.HEADER_LINE_STRING):])
                return hed_attributes
        msg = f"First line of file should be HED, instead found: {line}"
        raise HedFileError(HedExceptions.SCHEMA_HEADER_MISSING, msg, filename=self.name)

    def _parse_data(self):
        wiki_lines_by_section = self._split_lines_into_sections(self.input_data)
        parse_order = {
            HedWikiSection.HeaderLine: self._read_header_section,
            HedWikiSection.Prologue: self._read_prologue,
            HedWikiSection.Epilogue: self._read_epilogue,
            HedWikiSection.Properties: self._read_properties,
            HedWikiSection.Attributes: self._read_attributes,
            HedWikiSection.UnitModifiers: self._read_unit_modifiers,
            HedWikiSection.UnitsClasses: self._read_unit_classes,
            HedWikiSection.ValueClasses: self._read_value_classes,
            HedWikiSection.Schema: self._read_schema,
        }
        self._parse_sections(wiki_lines_by_section, parse_order)

        # Validate we didn't miss any required sections.
        for section in required_sections:
            if section not in wiki_lines_by_section:
                error_code = HedExceptions.SCHEMA_SECTION_MISSING
                msg = f"Required section separator '{SectionNames[section]}' not found in file"
                raise HedFileError(error_code, msg, filename=self.name)

        if self.fatal_errors:
            self.fatal_errors = error_reporter.sort_issues(self.fatal_errors)
            raise HedFileError(self.fatal_errors[0]['code'],
                               f"{len(self.fatal_errors)} issues found when parsing schema.  See the .issues "
                               f"parameter on this exception for more details.", self.name,
                               issues=self.fatal_errors)

    def _parse_sections(self, wiki_lines_by_section, parse_order):
        for section in parse_order:
            lines_for_section = wiki_lines_by_section.get(section, [])
            parse_func = parse_order[section]
            parse_func(lines_for_section)

    def _read_header_section(self, lines):
        """Ensure the header has no content other than the initial line.

        Parameters:
            lines (int, str): Lines for the header section.

        """
        for line_number, line in lines:
            if line.strip():
                msg = f"Extra content [{line}] between HED line and other sections"
                raise HedFileError(HedExceptions.SCHEMA_HEADER_INVALID, msg, filename=self.name)

    def _read_text_block(self, lines):
        text = ""
        for line_number, line in lines:
            text += line
        # We expect one blank line(plus the normal line break).  Any additional lines should be preserved.
        if text.endswith("\n\n"):
            text = text[:-2]
        elif text.endswith("\n"):
            text = text[:-1]
        return text

    def _read_prologue(self, lines):
        """Add the prologue.

        Parameters:
            lines: (int, str): Lines for prologue section.
        """
        self._schema.prologue = self._read_text_block(lines)

    def _read_epilogue(self, lines):
        """Adds the epilogue.

        Parameters:
            lines: (int, str): Lines for the epilogue section.
        """
        self._schema.epilogue = self._read_text_block(lines)

    def _read_schema(self, lines):
        """Add the main schema section

        Parameters:
            lines (int, str): Lines for main schema section.
        """
        self._schema._initialize_attributes(HedSectionKey.Tags)
        parent_tags = []
        level_adj = 0
        for line_number, line in lines:
            if line.startswith(wiki_constants.ROOT_TAG):
                parent_tags = []
                level_adj = 0
            else:
                level = self._get_tag_level(line) + level_adj
                if level < len(parent_tags):
                    parent_tags = parent_tags[:level]
                elif level > len(parent_tags):
                    self._add_fatal_error(line_number, line,
                                          "Line has too many *'s at front.  You cannot skip a level.",
                                          HedExceptions.WIKI_LINE_START_INVALID)
                    continue

            # Create the entry
            tag_entry, parent_tags, level_adj = self._add_tag_meta(parent_tags, line_number, line, level_adj)

    def _read_unit_classes(self, lines):
        """Add the unit classes section.

        Parameters:
            lines (int, str): Lines for the unit class section.
        """
        self._schema._initialize_attributes(HedSectionKey.UnitClasses)
        self._schema._initialize_attributes(HedSectionKey.Units)
        unit_class_entry = None
        for line_number, line in lines:
            unit, _ = self._get_tag_name(line)
            if unit is None:
                self._add_fatal_error(line_number, line)
                continue
            level = self._get_tag_level(line)
            # This is a unit class
            if level == 1:
                unit_class_entry = self._create_entry(line_number, line, HedSectionKey.UnitClasses)
                unit_class_entry = self._add_to_dict(line_number, line, unit_class_entry, HedSectionKey.UnitClasses)
            # This is a unit class unit
            else:
                unit_class_unit_entry = self._create_entry(line_number, line, HedSectionKey.Units)
                self._add_to_dict(line_number, line, unit_class_unit_entry, HedSectionKey.Units)
                unit_class_entry.add_unit(unit_class_unit_entry)

    def _read_section(self, lines, section_key):
        self._schema._initialize_attributes(section_key)
        for line_number, line in lines:
            new_entry = self._create_entry(line_number, line, section_key)
            self._add_to_dict(line_number, line, new_entry, section_key)

    def _read_unit_modifiers(self, lines):
        """Add the unit modifiers section.

        Parameters:
            lines (int, str): Lines for the unit modifiers section.
        """
        self._read_section(lines, HedSectionKey.UnitModifiers)

    def _read_value_classes(self, lines):
        """Add the value classes section.

        Parameters:
            lines (int, str): Lines for the value class section.
        """
        self._read_section(lines, HedSectionKey.ValueClasses)

    def _read_properties(self, lines):
        self._read_section(lines, HedSectionKey.Properties)

    def _read_attributes(self, lines):
        self._read_section(lines, HedSectionKey.Attributes)

    def _get_header_attributes_internal(self, version_line):
        """Extracts all valid attributes like version from the HED line in .mediawiki format.

        Parameters:
            version_line (str): The line in the wiki file that contains the version or other attributes.

        Returns:
            dict: The key is the name of the attribute, value being the value.  eg {'version':'v1.0.1'}
        """
        if "=" not in version_line:
            return self._get_header_attributes_internal_old(version_line)

        attributes, malformed = text_util._parse_header_attributes_line(version_line)

        for m in malformed:
            # todo: May shift this at some point to report all errors
            raise HedFileError(code=HedExceptions.SCHEMA_HEADER_INVALID,
                               message=f"Header line has a malformed attribute {m}",
                               filename=self.name)
        return attributes

    def _get_header_attributes_internal_old(self, version_line):
        """ Extract all valid attributes like version from the HED line in .mediawiki format.

        Parameters:
            version_line (str): The line in the wiki file that contains the version or other attributes.

        Returns:
            dict: The key is the name of the attribute, value being the value.  eg {'version':'v1.0.1'}.
        """
        final_attributes = {}
        attribute_pairs = version_line.split(',')
        for pair in attribute_pairs:
            divider_index = pair.find(':')
            if divider_index == -1:
                msg = f"Found poorly matched key:value pair in header: {pair}"
                raise HedFileError(HedExceptions.SCHEMA_HEADER_INVALID, msg, filename=self.name)
            key, value = pair[:divider_index], pair[divider_index + 1:]
            key = key.strip()
            value = value.strip()
            final_attributes[key] = value

        return final_attributes

    @staticmethod
    def _get_tag_level(row):
        """ Get the tag level from a line in a wiki file.

        Parameters:
            row (str): A tag line.

        Returns:
            int: Gets the tag level.

        Notes:
            The number of asterisks determine what level the tag is on.

        """
        count = 0
        while row[count] == '*':
            count += 1
        if count == 0:
            return 1
        return count

    def _remove_nowiki_tag_from_line(self, line_number, row):
        """Remove the nowiki tag from the  line.

        Parameters:
            line_number (int): The line number to report errors as
            row (str): A tag line.

        Returns:
            str: The line with the nowiki tag removed.
        """
        index1 = row.find(no_wiki_start_tag)
        index2 = row.find(no_wiki_end_tag)
        if index1 == -1 ^ index2 == -1:  # XOR operation, true if exactly one of the conditions is true
            self._add_fatal_error(line_number, row, "Invalid or non matching <nowiki> tags found")
        elif index1 != -1 and index2 <= index1:
            self._add_fatal_error(line_number, row, "</nowiki> appears before <nowiki> on a line")
        row = re.sub(no_wiki_tag, '', row)
        return row

    def _get_tag_name(self, row):
        """ Get the tag name from the tag line.

        Parameters:
            row (str): A tag line.

        Returns:
            str: The tag name.

        """
        if row.find(extend_here_line) != -1:
            return '', 0
        for invalid_chars in invalid_characters_to_strip:
            row = row.replace(invalid_chars, "")
        match = tag_name_re.search(row)
        if match:
            tag_name = match.group(2).strip()
            if tag_name:
                return tag_name, match.regs[4][0]

        return None, 0

    def _get_tag_attributes(self, line_number, row, starting_index):
        """ Get the tag attributes from a line.

        Parameters:
            line_number (int): The line number to report errors as.
            row (str): A tag line.
            starting_index (int): The first index we can check for the brackets.

        Returns:
            dict: Dictionary of attributes.
            int: The last index we found tag attributes at.

        """
        attr_string, starting_index = self._get_line_section(row, starting_index, '{', '}')
        try:
            return text_util.parse_attribute_string(attr_string), starting_index
        except ValueError as e:
            self._add_fatal_error(line_number, attr_string, str(e))
        return {}, starting_index

    @staticmethod
    def _get_line_section(row, starting_index, start_delim='[', end_delim=']'):
        """ Get the portion enclosed by the given delimiters.

        Parameters:
            row (str): A tag line.
            starting_index (int): The first index we can check for the brackets.
            start_delim (str): The string that starts this block.
            end_delim (str): The string that ends this block.

        Returns:
            str: The tag description.
            int: The last index we found tag attributes at.

        """
        count1 = row.count(start_delim)
        count2 = row.count(end_delim)
        if count1 != count2 or count1 > 1 or count2 > 1:
            return None, 0

        row = row[starting_index:]

        index1 = row.find(start_delim)
        index2 = row.find(end_delim)
        if index2 < index1:
            return None, 0

        if count1 == 0:
            return "", starting_index

        return row[index1 + 1: index2], index2 + starting_index

    def _create_entry(self, line_number, row, key_class, full_tag_name=None):
        node_name, index = self._get_tag_name(row)
        if node_name is None:
            self._add_fatal_error(line_number, row)
            return
        if full_tag_name:
            node_name = full_tag_name

        node_attributes, index = self._get_tag_attributes(line_number, row, index)
        if node_attributes is None:
            self._add_fatal_error(line_number, row, "Attributes has mismatched delimiters")
            return

        node_desc, _ = self._get_line_section(row, index)
        if node_desc is None:
            self._add_fatal_error(line_number, row, "Description has mismatched delimiters")
            return

        tag_entry = self._schema._create_tag_entry(node_name, key_class)

        if node_desc:
            tag_entry.description = node_desc.strip()

        for attribute_name, attribute_value in node_attributes.items():
            tag_entry._set_attribute_value(attribute_name, attribute_value)

        return tag_entry

    def _check_for_new_section(self, line, strings_for_section, current_section):
        new_section = None
        for key, section_string in SectionStarts.items():
            if line.startswith(section_string):
                if key in strings_for_section:
                    msg = f"Found section {SectionNames[key]} twice"
                    raise HedFileError(HedExceptions.WIKI_SEPARATOR_INVALID,
                                       msg, filename=self.name)
                if current_section < key:
                    new_section = key
                else:
                    error_code = HedExceptions.SCHEMA_SECTION_MISSING
                    msg = f"Found section {SectionNames[key]} out of order in file"
                    raise HedFileError(error_code, msg, filename=self.name)
                break
        return new_section

    def _handle_bad_section_sep(self, line, current_section):
        if current_section != HedWikiSection.Schema and line.startswith(wiki_constants.ROOT_TAG):
            msg = f"Invalid section separator '{line.strip()}'"
            raise HedFileError(HedExceptions.SCHEMA_SECTION_MISSING, msg, filename=self.name)

        if line.startswith("!#"):
            msg = f"Invalid section separator '{line.strip()}'"
            raise HedFileError(HedExceptions.WIKI_SEPARATOR_INVALID, msg, filename=self.name)

    def _split_lines_into_sections(self, wiki_lines):
        """ Takes a list of lines, and splits it into valid wiki sections.

        Parameters:
           wiki_lines : [str]

        Returns:
            sections: {str: [str]}
            A list of lines for each section of the schema(not including the identifying section line)
        """
        current_section = HedWikiSection.HeaderLine
        strings_for_section = {}
        strings_for_section[HedWikiSection.HeaderLine] = []
        for line_number, line in enumerate(wiki_lines):
            # Header is handled earlier
            if line_number == 0:
                continue

            new_section = self._check_for_new_section(line, strings_for_section, current_section)

            if new_section:
                strings_for_section[new_section] = []
                current_section = new_section
                continue

            self._handle_bad_section_sep(line, current_section)

            if current_section == HedWikiSection.Prologue or current_section == HedWikiSection.Epilogue:
                strings_for_section[current_section].append((line_number + 1, line))
            else:
                line = self._remove_nowiki_tag_from_line(line_number + 1, line.strip())
                if line:
                    strings_for_section[current_section].append((line_number + 1, line))

        return strings_for_section
