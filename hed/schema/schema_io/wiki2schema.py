"""
This module is used to create a HedSchema object from a .mediawiki file.
"""
import re
from hed.schema.hed_schema_constants import HedSectionKey
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema import HedSchema
from hed.schema import schema_validation_util
from hed.schema.schema_io import wiki_constants

header_attr_expression = "([^ ]+?)=\"(.*?)\""
attr_re = re.compile(header_attr_expression)
extend_here_line = 'extend here'
invalid_characters_to_strip = ["&#8203;"]
tag_name_expression = r'(\*+|\'{3})(.*?)(\'{3})?\s*([\[\{]|$)+'
tag_name_re = re.compile(tag_name_expression)
no_wiki_tag = '</?nowiki>'
no_wiki_start_tag = '<nowiki>'
no_wiki_end_tag = '</nowiki>'


# these must always be in order under the current spec.
class HedWikiSection:
    HeaderLine = 2
    Prologue = 3
    Schema = 4
    EndSchema = 5
    UnitsClasses = 6
    UnitModifiers = 7
    ValueClasses = 8
    Attributes = 9
    Properties = 10
    Epilogue = 11
    EndHed = 12


SectionStarts = {
    HedWikiSection.Prologue: wiki_constants.PROLOGUE_SECTION_ELEMENT,
    HedWikiSection.Schema: wiki_constants.START_HED_STRING,
    HedWikiSection.EndSchema: wiki_constants.END_SCHEMA_STRING,
    HedWikiSection.UnitsClasses: wiki_constants.UNIT_CLASS_STRING,
    HedWikiSection.UnitModifiers: wiki_constants.UNIT_MODIFIER_STRING,
    HedWikiSection.ValueClasses: wiki_constants.VALUE_CLASS_STRING,
    HedWikiSection.Attributes: wiki_constants.ATTRIBUTE_DEFINITION_STRING,
    HedWikiSection.Properties: wiki_constants.ATTRIBUTE_PROPERTY_STRING,
    HedWikiSection.Epilogue: wiki_constants.EPILOGUE_SECTION_ELEMENT,
    HedWikiSection.EndHed: wiki_constants.END_HED_STRING
}

SectionNames = {
    HedWikiSection.HeaderLine: "Header",
    HedWikiSection.Prologue: "Prologue",
    HedWikiSection.Schema: "Schema",
    HedWikiSection.EndSchema: "EndSchema",
    HedWikiSection.UnitsClasses: "Unit Classes",
    HedWikiSection.UnitModifiers: "Unit Modifiers",
    HedWikiSection.ValueClasses: "Value Classes",
    HedWikiSection.Attributes: "Attributes",
    HedWikiSection.Properties: "Properties",
    HedWikiSection.EndHed: "EndHed"
}

ErrorsBySection = {
    HedWikiSection.Schema: HedExceptions.SCHEMA_START_MISSING,
    HedWikiSection.EndSchema: HedExceptions.SCHEMA_END_INVALID,
    HedWikiSection.EndHed: HedExceptions.HED_END_INVALID
}
required_sections = [HedWikiSection.Schema, HedWikiSection.EndSchema, HedWikiSection.EndHed]


class HedSchemaWikiParser:
    def __init__(self, wiki_file_path, schema_as_string):
        self.filename = wiki_file_path
        self.fatal_errors = []
        self._schema = HedSchema()
        self._schema.filename = wiki_file_path

        try:
            if wiki_file_path and schema_as_string:
                raise HedFileError(HedExceptions.BAD_PARAMETERS, "Invalid parameters to schema creation.",
                                   wiki_file_path)
            if wiki_file_path:
                with open(wiki_file_path, 'r', encoding='utf-8', errors='replace') as wiki_file:
                    wiki_lines = wiki_file.readlines()
            else:
                # Split this into lines, but keep linebreaks.
                wiki_lines = [line + "\n" for line in schema_as_string.split("\n")]

            self._read_wiki(wiki_lines)
        except FileNotFoundError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, wiki_file_path)

        if self.fatal_errors:
            self.fatal_errors.sort(key = lambda x: x.get("line_number", -1))
            raise HedFileError(HedExceptions.HED_WIKI_DELIMITERS_INVALID,
                               f"{len(self.fatal_errors)} issues found when parsing schema.  See the .issues "
                               f"parameter on this exception for more details.", self.filename,
                               issues=self.fatal_errors)
        self._schema.finalize_dictionaries()

    @staticmethod
    def load_wiki(wiki_file_path=None, schema_as_string=None):
        parser = HedSchemaWikiParser(wiki_file_path, schema_as_string)
        return parser._schema

    def _read_wiki(self, wiki_lines):
        """
        Calls the parsers for each section as this goes through the file.

        Parameters
        ----------
        wiki_lines : iter(str)
            An opened .mediawiki file
        """
        # Read header line as we need it to determine if this is a hed3 schema or not before locating sections
        self._read_header_line(wiki_lines[0])

        wiki_lines_by_section = self._split_lines_into_sections(wiki_lines)
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
                error_code = HedExceptions.INVALID_SECTION_SEPARATOR
                if section in ErrorsBySection:
                    error_code = ErrorsBySection[section]
                msg = f"Required section separator '{SectionNames[section]}' not found in file"
                raise HedFileError(error_code, msg, filename=self.filename)

    def _split_lines_into_sections(self, wiki_lines):
        """
            Takes a list of lines, and splits it into valid wiki sections.

        Parameters
        ----------
        wiki_lines : [str]

        Returns
        -------
        sections: {str: [str]}
            A list of lines for each section of the schema(not including the identifying section line)
        """
        # We start having found the header and may still be in it
        current_section = HedWikiSection.HeaderLine
        found_section = True
        strings_for_section = {}
        for line_number, line in enumerate(wiki_lines):
            for key, section_string in SectionStarts.items():
                if line.startswith(section_string):
                    if key in strings_for_section:
                        msg = f"Found section {SectionNames[key]} twice"
                        raise HedFileError(HedExceptions.INVALID_SECTION_SEPARATOR,
                                           msg, filename=self.filename)

                    if current_section < key:
                        current_section = key
                        found_section = True
                        break
                    else:
                        error_code = HedExceptions.INVALID_SECTION_SEPARATOR
                        if key in ErrorsBySection:
                            error_code = ErrorsBySection[key]
                        msg = f"Found section {SectionNames[key]} out of order in file"
                        raise HedFileError(error_code, msg, filename=self.filename)

            if found_section:
                strings_for_section[current_section] = []
                found_section = False
                continue

            if (current_section != HedWikiSection.Schema and line.startswith(wiki_constants.ROOT_TAG) and
                    not (line.startswith(wiki_constants.OLD_SYNTAX_SECTION_NAME) and not self._schema.is_hed3_schema)):
                msg = f"Invalid section separator '{line.strip()}'"
                raise HedFileError(HedExceptions.INVALID_SECTION_SEPARATOR, msg, filename=self.filename)

            if line.startswith("!#"):
                msg = f"Invalid section separator '{line.strip()}'"
                raise HedFileError(HedExceptions.INVALID_SECTION_SEPARATOR, msg, filename=self.filename)

            if current_section == HedWikiSection.Prologue or current_section == HedWikiSection.Epilogue:
                strings_for_section[current_section].append((line_number + 1, line))
            else:
                line = self._remove_nowiki_tag_from_line(line_number + 1, line.strip())
                if line:
                    strings_for_section[current_section].append((line_number + 1, line))

        return strings_for_section

    def _parse_sections(self, wiki_lines_by_section, parse_order):
        for section in parse_order:
            lines_for_section = wiki_lines_by_section.get(section, [])
            parse_func = parse_order[section]
            parse_func(lines_for_section)

    def _read_header_line(self, line):
        if line.startswith(wiki_constants.HEADER_LINE_STRING):
            hed_attributes = self._get_header_attributes(line[len(wiki_constants.HEADER_LINE_STRING):])
            schema_validation_util.validate_attributes(hed_attributes, filename=self.filename)
            self.header_attributes = hed_attributes
            self._schema.header_attributes = hed_attributes
            return
        msg = f"First line of file should be HED, instead found: {line}"
        raise HedFileError(HedExceptions.SCHEMA_HEADER_MISSING, msg, filename=self.filename)

    def _read_header_section(self, lines):
        """Ensures the header has no content other than the initial line.

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        for line_number, line in lines:
            if line.strip():
                msg = f"Extra content [{line}] between HED line and other sections"
                raise HedFileError(HedExceptions.HED_SCHEMA_HEADER_INVALID, msg,  filename=self.filename)

    def _read_text_block(self, lines):
        text = ""
        for line_number, line in lines:
            text += line
        # We expect one blank line(plus the normal line break).  Any more should be preserved
        if text.endswith("\n\n"):
            text = text[:-2]
        elif text.endswith("\n"):
            text = text[:-1]
        return text

    def _read_prologue(self, lines):
        """Adds the prologue

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        self._schema.prologue = self._read_text_block(lines)

    def _read_epilogue(self, lines):
        """Adds the epilogue

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        self._schema.epilogue = self._read_text_block(lines)

    def _read_schema(self, lines):
        """Adds the main schema section

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        parent_tags = []
        for line_number, line in lines:
            if line.startswith(wiki_constants.ROOT_TAG):
                parent_tags = []
            else:
                level = self._get_tag_level(line)
                if level < len(parent_tags):
                    parent_tags = parent_tags[:level]
                elif level > len(parent_tags):
                    self._add_fatal_error(line, "Line has too many *'s at the front.  You cannot skip a level.")
                    continue
            new_tag_name = self._add_tag_line(parent_tags, line_number, line)
            if not new_tag_name:
                if new_tag_name != "":
                    self._add_fatal_error(line_number, line)
                continue

            parent_tags.append(new_tag_name)

    def _read_unit_classes(self, lines):
        """Adds the unit classes section

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        unit_class_entry = None
        for line_number, line in lines:
            unit_class_unit, _ = self._get_tag_name(line)
            if unit_class_unit is None:
                self._add_fatal_error(line_number, line)
                continue
            level = self._get_tag_level(line)
            # This is a unit class
            if level == 1:
                unit_class_entry = self._add_single_line(line_number, line, HedSectionKey.UnitClasses)
            # This is a unit class unit
            else:
                unit_class_unit_entry = self._add_single_line(line_number, line, HedSectionKey.Units)
                unit_class_entry.add_unit(unit_class_unit_entry)

    def _read_unit_modifiers(self, lines):
        """Adds the unit modifiers section

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        for line_number, line in lines:
            self._add_single_line(line_number, line, HedSectionKey.UnitModifiers)

    def _read_value_classes(self, lines):
        """Adds the unit modifiers section

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        for line_number, line in lines:
            self._add_single_line(line_number, line, HedSectionKey.ValueClasses)

    def _read_properties(self, lines):
        for line_number, line in lines:
            self._add_single_line(line_number, line, HedSectionKey.Properties)

    def _read_attributes(self, lines):
        self.attributes = {}
        for line_number, line in lines:
            self._add_single_line(line_number, line, HedSectionKey.Attributes)

    def _get_header_attributes(self, version_line):
        """Extracts all valid attributes like version from the HED line in .mediawiki format.

        Parameters
        ----------
        version_line: string
            The line in the wiki file that contains the version or other attributes.

        Returns
        -------
        {}: The key is the name of the attribute, value being the value.  eg {'version':'v1.0.1'}
        """
        if "=" not in version_line:
            return self._get_header_attributes_old(version_line)

        final_attributes = {}

        for match in attr_re.finditer(version_line):
            attr_name = match.group(1)
            attr_value = match.group(2)
            final_attributes[attr_name] = attr_value

        return final_attributes

    def _get_header_attributes_old(self, version_line):
        """Extracts all valid attributes like version from the HED line in .mediawiki format.

        Parameters
        ----------
        version_line: string
            The line in the wiki file that contains the version or other attributes.

        Returns
        -------
        {}: The key is the name of the attribute, value being the value.  eg {'version':'v1.0.1'}
        """
        final_attributes = {}
        attribute_pairs = version_line.split(',')
        for pair in attribute_pairs:
            divider_index = pair.find(':')
            if divider_index == -1:
                msg = f"Found poorly matched key:value pair in header: {pair}"
                raise HedFileError(HedExceptions.HED_SCHEMA_HEADER_INVALID, msg, filename=self.filename)
            key, value = pair[:divider_index], pair[divider_index + 1:]
            key = key.strip()
            value = value.strip()
            final_attributes[key] = value

        return final_attributes

    @staticmethod
    def _get_tag_level(tag_line):
        """ Get the tag level from a line in a wiki file.

        Parameters:
            tag_line (str): A tag line.

        Returns:
            int: Gets the tag level.

        Notes:
            The number of asterisks determine what level the tag is on.

        """
        count = 0
        while tag_line[count] == '*':
            count += 1
        if count == 0:
            return 1
        return count

    def _remove_nowiki_tag_from_line(self, line_number, tag_line):
        """Removes the nowiki tag from the  line.

        Parameters
        ----------
        line_number (int): The line number to report errors as
        tag_line (string): A tag line.

        Returns
        -------
        string
            The line with the nowiki tag removed.
        """
        index1 = tag_line.find(no_wiki_start_tag)
        index2 = tag_line.find(no_wiki_end_tag)
        if (index1 == -1 and index2 != -1) or (index2 == -1 and index1 != -1):
            self._add_fatal_error(line_number, tag_line, "Invalid or non matching <nowiki> tags found")
        elif index1 != -1 and index2 != -1 and index2 <= index1:
            self._add_fatal_error(line_number, tag_line, "</nowiki> appears before <nowiki> on a line")
        tag_line = re.sub(no_wiki_tag, '', tag_line)
        return tag_line

    def _get_tag_name(self, tag_line):
        """ Get the tag name from the tag line.

        Parameters:
            tag_line (str): A tag line.

        Returns:
            str: The tag name.

        """
        if tag_line.find(extend_here_line) != -1:
            return '', 0
        for invalid_chars in invalid_characters_to_strip:
            tag_line = tag_line.replace(invalid_chars, "")
        match = tag_name_re.search(tag_line)
        if match:
            tag_name = match.group(2).strip()
            if tag_name:
                return tag_name, match.regs[4][0]

        return None, 0

    @staticmethod
    def _get_tag_attributes(tag_line, starting_index):
        """ Get the tag attributes from a line.

        Parameters:
            tag_line (str): A tag line.
            starting_index (int): The first index we can check for the brackets.

        Returns:
            dict: Dictionary of attributes.
            int: The last index we found tag attributes at.

        """
        attr_string, starting_index = HedSchemaWikiParser._get_line_section(tag_line, starting_index, '{', '}')
        if attr_string is None:
            return None, starting_index
        if attr_string:
            attributes_split = [x.strip() for x in attr_string.split(',')]
            # Filter out attributes with spaces.
            attributes_split = [a for a in attributes_split if " " not in a]

            final_attributes = {}
            for attribute in attributes_split:
                split_attribute = attribute.split("=")
                if len(split_attribute) == 1:
                    final_attributes[split_attribute[0]] = True
                else:
                    if split_attribute[0] in final_attributes:
                        final_attributes[split_attribute[0]] += "," + split_attribute[1]
                    else:
                        final_attributes[split_attribute[0]] = split_attribute[1]
            return final_attributes, starting_index
        else:
            return {}, starting_index

    @staticmethod
    def _get_line_section(tag_line, starting_index, start_delim='[', end_delim=']'):
        """ Get the portion enclosed by the given delimiters.

        Parameters:
            tag_line (str): A tag line.
            starting_index (int): The first index we can check for the brackets.
            start_delim (str): The string that starts this block.
            end_delim (str): The string that ends this block.

        Returns:
            str: The tag description.
            int: The last index we found tag attributes at.

        """
        count1 = tag_line.count(start_delim)
        count2 = tag_line.count(end_delim)
        if count1 != count2 or count1 > 1 or count2 > 1:
            return None, 0

        tag_line = tag_line[starting_index:]

        index1 = tag_line.find(start_delim)
        index2 = tag_line.find(end_delim)
        if index2 < index1:
            return None, 0

        if count1 == 0:
            return "", starting_index

        return tag_line[index1 + 1: index2], index2 + starting_index

    def _add_tag_line(self, parent_tags, line_number, tag_line):
        """ Add a tag to the dictionaries.

        Parameters:
            parent_tags (list): A list of parent tags in order.
            line_number (int): The line number to report errors as
            tag_line (str): A tag line.

        Returns:
            HedSchemaEntry: The entry for the added tag.

        Notes:
            Includes attributes and description.
        """
        tag_name, _ = self._get_tag_name(tag_line)
        if tag_name:
            if parent_tags:
                long_tag_name = "/".join(parent_tags) + "/" + tag_name
            else:
                long_tag_name = tag_name
            self._add_single_line(line_number, tag_line, HedSectionKey.AllTags, long_tag_name)

        return tag_name

    def _add_single_line(self, line_number, tag_line, key_class, element_name=None):
        node_name, index = self._get_tag_name(tag_line)
        if node_name is None:
            self._add_fatal_error(line_number, tag_line)
            return
        if element_name:
            node_name = element_name

        node_attributes, index = self._get_tag_attributes(tag_line, index)
        if node_attributes is None:
            self._add_fatal_error(line_number, tag_line, "Attributes has mismatched delimiters")
            return

        node_desc, _ = self._get_line_section(tag_line, index)
        if node_desc is None:
            self._add_fatal_error(line_number, tag_line, "Description has mismatched delimiters")
            return

        tag_entry = self._schema._add_tag_to_dict(node_name, key_class)
        if node_desc:
            tag_entry.description = node_desc.strip()

        for attribute_name, attribute_value in node_attributes.items():
            tag_entry.set_attribute_value(attribute_name, attribute_value)

        return tag_entry

    def _add_fatal_error(self, line_number, line, warning_message="Schema term is empty or the line is malformed"):
        self.fatal_errors.append(
            {"line_number": line_number,
             "line": line,
             "message": warning_message})