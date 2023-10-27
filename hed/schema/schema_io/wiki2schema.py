"""
This module is used to create a HedSchema object from a .mediawiki file.
"""
import re

from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.errors import ErrorContext, error_reporter
from hed.schema import schema_validation_util
from hed.schema.schema_io import wiki_constants
from .base2schema import SchemaLoader
from .wiki_constants import HedWikiSection, SectionStarts, SectionNames

header_attr_expression = "([^ ]+?)=\"(.*?)\""
attr_re = re.compile(header_attr_expression)
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


class SchemaLoaderWiki(SchemaLoader):
    """ Loads MediaWiki schemas from filenames or strings.

        Expected usage is SchemaLoaderWiki.load(filename)

        SchemaLoaderWiki(filename) will load just the header_attributes
    """
    def __init__(self, filename, schema_as_string=None):
        super().__init__(filename, schema_as_string)
        self.fatal_errors = []

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
        raise HedFileError(HedExceptions.SCHEMA_HEADER_MISSING, msg, filename=self.filename)

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
                raise HedFileError(error_code, msg, filename=self.filename)

        if self.fatal_errors:
            self.fatal_errors = error_reporter.sort_issues(self.fatal_errors)
            raise HedFileError(self.fatal_errors[0]['code'],
                               f"{len(self.fatal_errors)} issues found when parsing schema.  See the .issues "
                               f"parameter on this exception for more details.", self.filename,
                               issues=self.fatal_errors)

    def _parse_sections(self, wiki_lines_by_section, parse_order):
        for section in parse_order:
            lines_for_section = wiki_lines_by_section.get(section, [])
            parse_func = parse_order[section]
            parse_func(lines_for_section)

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
                raise HedFileError(HedExceptions.SCHEMA_HEADER_INVALID, msg,  filename=self.filename)

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
                                          "Line has too many *'s at the front.  You cannot skip a level."
                                          , HedExceptions.WIKI_LINE_START_INVALID)
                    continue
            # Create the entry
            tag_entry = self._add_tag_line(parent_tags, line_number, line)

            if not tag_entry:
                # This will have already raised an error
                continue

            try:
                rooted_entry = schema_validation_util.find_rooted_entry(tag_entry, self._schema, self._loading_merged)
                if rooted_entry:
                    parent_tags = rooted_entry.long_tag_name.split("/")
                    level_adj = len(parent_tags)
                    # Create the entry again for rooted tags, to get the full name.
                    tag_entry = self._add_tag_line(parent_tags, line_number, line)
            except HedFileError as e:
                self._add_fatal_error(line_number, line, e.message, e.code)
                continue

            tag_entry = self._add_to_dict(line_number, line, tag_entry, HedSectionKey.Tags)

            parent_tags.append(tag_entry.short_tag_name)

    def _read_unit_classes(self, lines):
        """Adds the unit classes section

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
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
        """Adds the unit modifiers section

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        self._read_section(lines, HedSectionKey.UnitModifiers)

    def _read_value_classes(self, lines):
        """Adds the unit modifiers section

        Parameters
        ----------
        lines: [(int, str)]
            Lines for this section
        """
        self._read_section(lines, HedSectionKey.ValueClasses)

    def _read_properties(self, lines):
        self._read_section(lines, HedSectionKey.Properties)

    def _read_attributes(self, lines):
        self._read_section(lines, HedSectionKey.Attributes)

    def _get_header_attributes_internal(self, version_line):
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
            return self._get_header_attributes_internal_old(version_line)

        attributes, malformed = self._parse_attributes_line(version_line)

        for m in malformed:
            # todo: May shift this at some point to report all errors
            raise HedFileError(code=HedExceptions.SCHEMA_HEADER_INVALID,
                               message=f"Header line has a malformed attribute {m}",
                               filename=self.filename)
        return attributes

    @staticmethod
    def _parse_attributes_line(version_line):
        matches = {}
        unmatched = []
        last_end = 0

        for match in attr_re.finditer(version_line):
            start, end = match.span()

            # If there's unmatched content between the last match and the current one
            if start > last_end:
                unmatched.append(version_line[last_end:start])

            matches[match.group(1)] = match.group(2)
            last_end = end

        # If there's unmatched content after the last match
        if last_end < len(version_line):
            unmatched.append(version_line[last_end:])

        unmatched = [m.strip() for m in unmatched if m.strip()]
        return matches, unmatched

    def _get_header_attributes_internal_old(self, version_line):
        """ Extracts all valid attributes like version from the HED line in .mediawiki format.

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
                raise HedFileError(HedExceptions.SCHEMA_HEADER_INVALID, msg, filename=self.filename)
            key, value = pair[:divider_index], pair[divider_index + 1:]
            key = key.strip()
            value = value.strip()
            final_attributes[key] = value

        return final_attributes

    def _add_to_dict(self, line_number, line, entry, key_class):
        if entry.has_attribute(HedKey.InLibrary) and not self._loading_merged:
            self._add_fatal_error(line_number, line,
                                  f"Library tag in unmerged schema has InLibrary attribute",
                                  HedExceptions.IN_LIBRARY_IN_UNMERGED)
        return self._schema._add_tag_to_dict(entry.name, entry, key_class)

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
        if index1 == -1 ^ index2 == -1:  # XOR operation, true if exactly one of the conditions is true
            self._add_fatal_error(line_number, tag_line, "Invalid or non matching <nowiki> tags found")
        elif index1 != -1 and index2 <= index1:
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
    def _validate_attribute_string(attribute_string):
        pattern = r'^[A-Za-z]+(=.+)?$'
        match = re.fullmatch(pattern, attribute_string)
        if match:
            return match.group()

    def _get_tag_attributes(self, line_number, tag_line, starting_index):
        """ Get the tag attributes from a line.

        Parameters:
            line_number (int): The line number to report errors as
            tag_line (str): A tag line.
            starting_index (int): The first index we can check for the brackets.

        Returns:
            dict: Dictionary of attributes.
            int: The last index we found tag attributes at.

        """
        attr_string, starting_index = SchemaLoaderWiki._get_line_section(tag_line, starting_index, '{', '}')
        if attr_string is None:
            return None, starting_index
        if attr_string:
            attributes_split = [x.strip() for x in attr_string.split(',')]

            final_attributes = {}
            for attribute in attributes_split:
                if self._validate_attribute_string(attribute) is None:
                    self._add_fatal_error(line_number, tag_line,
                                          f"Malformed attribute found {attribute}.  "
                                          f"Valid formatting is: attribute, or attribute=\"value\".")
                    continue
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
            return self._create_entry(line_number, tag_line, HedSectionKey.Tags, long_tag_name)

        self._add_fatal_error(line_number, tag_line)
        return None

    def _create_entry(self, line_number, tag_line, key_class, element_name=None):
        node_name, index = self._get_tag_name(tag_line)
        if node_name is None:
            self._add_fatal_error(line_number, tag_line)
            return
        if element_name:
            node_name = element_name

        node_attributes, index = self._get_tag_attributes(line_number, tag_line, index)
        if node_attributes is None:
            self._add_fatal_error(line_number, tag_line, "Attributes has mismatched delimiters")
            return

        node_desc, _ = self._get_line_section(tag_line, index)
        if node_desc is None:
            self._add_fatal_error(line_number, tag_line, "Description has mismatched delimiters")
            return

        tag_entry = self._schema._create_tag_entry(node_name, key_class)

        if node_desc:
            tag_entry.description = node_desc.strip()

        for attribute_name, attribute_value in node_attributes.items():
            tag_entry._set_attribute_value(attribute_name, attribute_value)

        return tag_entry

    def _add_fatal_error(self, line_number, line, warning_message="Schema term is empty or the line is malformed",
                         error_code=HedExceptions.WIKI_DELIMITERS_INVALID):
        self.fatal_errors.append(
            {'code': error_code,
             ErrorContext.ROW: line_number,
             ErrorContext.LINE: line,
             "message": f"{warning_message}"
             }
        )

    def _check_for_new_section(self, line, strings_for_section, current_section):
        new_section = None
        for key, section_string in SectionStarts.items():
            if line.startswith(section_string):
                if key in strings_for_section:
                    msg = f"Found section {SectionNames[key]} twice"
                    raise HedFileError(HedExceptions.WIKI_SEPARATOR_INVALID,
                                       msg, filename=self.filename)
                if current_section < key:
                    new_section = key
                else:
                    error_code = HedExceptions.SCHEMA_SECTION_MISSING
                    msg = f"Found section {SectionNames[key]} out of order in file"
                    raise HedFileError(error_code, msg, filename=self.filename)
                break
        return new_section

    def _handle_bad_section_sep(self, line, current_section):
        if current_section != HedWikiSection.Schema and line.startswith(wiki_constants.ROOT_TAG):
            msg = f"Invalid section separator '{line.strip()}'"
            raise HedFileError(HedExceptions.SCHEMA_SECTION_MISSING, msg, filename=self.filename)

        if line.startswith("!#"):
            msg = f"Invalid section separator '{line.strip()}'"
            raise HedFileError(HedExceptions.WIKI_SEPARATOR_INVALID, msg, filename=self.filename)

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
