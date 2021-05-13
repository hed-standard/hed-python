"""
This module is used to create a HedSchema object from a .mediawiki file.
"""
import re
from hed.schema.hed_schema_constants import HedKey
from hed.util.exceptions import HedFileError, HedExceptions
from hed.schema.hed_schema import HedSchema
from hed.schema import schema_validation_util
from hed.schema import wiki_constants


level_expression = r'\*+'
attributes_expression = r'\{.*\}'
description_expression = r'\[.*\]'
extend_here_line = 'extend here'
invalid_characters_to_strip = ["&#8203;"]
tag_name_regexp = r'([<>=#\-a-zA-Z0-9$:()\^µ]+\s*)+'
no_wiki_tag = '</?nowiki>'
square_bracket_removal_expression = r'[\[\]]'


# these must always be in order under the current spec.
class HedSection:
    HeaderLine = 2
    Prologue = 3
    Schema = 4
    EndSchema = 5
    UnitsClasses = 6
    UnitModifiers = 7
    Attributes = 8
    EndHed = 9


SectionStarts = {
    HedSection.Schema: wiki_constants.START_HED_STRING,
    HedSection.EndSchema: wiki_constants.END_SCHEMA_STRING,
    HedSection.UnitsClasses: wiki_constants.UNIT_CLASS_STRING,
    HedSection.UnitModifiers: wiki_constants.UNIT_MODIFIER_STRING,
    HedSection.Attributes: wiki_constants.ATTRIBUTE_DEFINITION_STRING,
    HedSection.EndHed: wiki_constants.END_HED_STRING
}


SectionNames = {
    HedSection.HeaderLine: "Header",
    HedSection.Prologue: "Prologue",
    HedSection.Schema: "Schema",
    HedSection.EndSchema: "EndSchema",
    HedSection.UnitsClasses: "Unit Classes",
    HedSection.UnitModifiers: "Unit Modifiers",
    HedSection.Attributes: "Attributes",
    HedSection.EndHed: "EndHed"
}

ErrorsBySection = {
    HedSection.Schema: HedExceptions.SCHEMA_START_MISSING,
    HedSection.EndSchema: HedExceptions.SCHEMA_END_INVALID,
    HedSection.EndHed: HedExceptions.HED_END_INVALID
}
required_sections = [HedSection.Schema, HedSection.EndSchema, HedSection.EndHed]


class HedSchemaWikiParser:
    def __init__(self, wiki_file_path, schema_as_string):
        self.filename = wiki_file_path
        self.issues = []

        self._schema = HedSchema()
        self._schema.filename = wiki_file_path
        # Variables used while parsing.
        self._found_sections = {}
        self._current_section = HedSection.HeaderLine

        try:
            if wiki_file_path and schema_as_string:
                raise HedFileError(HedExceptions.BAD_PARAMETERS, "Invalid parameters to schema creation.",
                                   wiki_file_path)
            if wiki_file_path:
                with open(wiki_file_path, 'r', encoding='utf-8', errors='replace') as wiki_file:
                    wiki_lines = wiki_file.readlines()
            else:
                wiki_lines = schema_as_string.split("\n")
            self._read_wiki(wiki_lines)
        except FileNotFoundError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, wiki_file_path)

        self._schema.finalize_dictionaries()

    @staticmethod
    def load_wiki(wiki_file_path=None, schema_as_string=None):
        parser = HedSchemaWikiParser(wiki_file_path, schema_as_string)

        return parser._schema

    def _get_line_iter(self, wiki_lines):
        """ This function iterates over the file line by line, keeping track of which file section it is currently in.
        Parameters
        ----------
        wiki_lines : iter(str)
            An opened .mediawiki file or other list of lines
        """
        for line in wiki_lines:
            found_section = False
            for key, section_string in SectionStarts.items():
                if line.startswith(section_string):
                    if key in self._found_sections:
                        raise HedFileError(HedExceptions.INVALID_SECTION_SEPARATOR,
                                           f"Found section {SectionNames[key]} twice", filename=self.filename)
                    self._found_sections[key] = True

                    if self._current_section < key:
                        self._current_section = key
                        # this line is already handled and we are in a new section
                        yield False
                        found_section = True
                        break
                    else:
                        error_code = HedExceptions.INVALID_SECTION_SEPARATOR
                        if key in ErrorsBySection:
                            error_code = ErrorsBySection[key]

                        raise HedFileError(error_code,
                                           f"Found section {SectionNames[key]} out of order in file",
                                           filename=self.filename)

            if found_section:
                continue

            if line.startswith("!#"):
                raise HedFileError(HedExceptions.INVALID_SECTION_SEPARATOR,
                                   f"Invalid section separator '{line.strip()}'", filename=self.filename)

            if self._current_section == HedSection.Prologue or self._current_section == HedSection.EndHed:
                if line.strip():
                    # we want to preserve all formatting in the prologue and epilogue.
                    if line.endswith("\n"):
                        line = line[:-1]
                    yield line
            else:
                line = self._remove_nowiki_tag_from_line(line.strip())
                if line:
                    yield line

        self._current_section = None

    def _read_wiki(self, wiki_lines):
        """
        Calls the parsers for each section as this goes through the file.

        Parameters
        ----------
        wiki_lines : iter(str)
            An opened .mediawiki file
        """
        self._current_section = HedSection.HeaderLine

        parsers_pass1 = {
            HedSection.HeaderLine: self._read_header_line,
            HedSection.Prologue: self._read_prologue,
            HedSection.Schema: self._skip_read_section,
            HedSection.EndSchema: self._skip_read_section,
            HedSection.UnitsClasses: self._skip_read_section,
            HedSection.UnitModifiers: self._skip_read_section,
            HedSection.Attributes: self._read_attributes,
            HedSection.EndHed: self._read_epilogue,
        }

        parsers_pass2 = {
            HedSection.HeaderLine: self._skip_read_section,
            HedSection.Prologue: self._skip_read_section,
            HedSection.Schema: self._read_schema,
            HedSection.EndSchema: self._skip_read_section,
            HedSection.UnitsClasses: self._read_unit_classes,
            HedSection.UnitModifiers: self._read_unit_modifiers,
            HedSection.Attributes: self._skip_read_section,
            HedSection.EndHed: self._skip_read_section,
        }

        file_iter = self._get_line_iter(wiki_lines)
        while self._current_section is not None:
            # The iterator is responsible for updating the current_section variable.
            # it will be set to None when at the end of the file.
            parsers_pass1[self._current_section](file_iter)

        self._schema.add_hed2_attributes()

        self._found_sections = {}
        self._current_section = HedSection.HeaderLine
        file_iter = self._get_line_iter(wiki_lines)
        while self._current_section is not None:
            # The iterator is responsible for updating the current_section variable.
            # it will be set to None when at the end of the file.
            parsers_pass2[self._current_section](file_iter)

        # Validate we didn't miss any required sections.
        for section in required_sections:
            if section not in self._found_sections:
                error_code = HedExceptions.INVALID_SECTION_SEPARATOR
                if section in ErrorsBySection:
                    error_code = ErrorsBySection[section]
                raise HedFileError(error_code,
                                   f"Required section separator '{SectionNames[section]}' not found in file",
                                   filename=self.filename)

    def _read_header_line(self, file_iter):
        """Adds the header line

        Parameters
        ----------
        file_iter: iter
            An iterator from self._get_line_iter.
        """
        first_line = next(file_iter)

        # First line MUST be the HED line with full proper formatting.
        if first_line.startswith(wiki_constants.HEADER_LINE_STRING):
            hed_attributes = self._get_header_attributes(first_line[len(wiki_constants.HEADER_LINE_STRING):])
            self.issues = schema_validation_util.validate_attributes(hed_attributes, filename=self.filename)
            self.header_attributes = hed_attributes
            self._schema.issues = self.issues
            self._schema.header_attributes = hed_attributes
        else:
            raise HedFileError(HedExceptions.SCHEMA_HEADER_MISSING,
                               f"First line of file should be HED, instead found: {first_line}", filename=self.filename)

        self._current_section = HedSection.Prologue

    def _read_prologue(self, file_iter):
        """Adds the prologue

        Parameters
        ----------
        file_iter: iter
            An iterator from self._get_line_iter.
        """
        prologue = ""
        for line in file_iter:
            if line is False:
                self.prologue = prologue
                self._schema.prologue = prologue
                return

            if prologue:
                prologue += "\n"
            prologue += line

    def _read_epilogue(self, file_iter):
        """Adds the epilogue

        Parameters
        ----------
        file_iter: iter
            An iterator from self._get_line_iter.
        """
        epilogue = ""
        for line in file_iter:
            if line is False:
                break

            if epilogue:
                epilogue += "\n"
            epilogue += line

        self.epilogue = epilogue
        self._schema.epilogue = epilogue

    def _read_schema(self, file_iter):
        """Adds the main schema section

        Parameters
        ----------
        file_iter: iter
            An iterator from self._get_line_iter.
        """
        parent_tags = []
        for line in file_iter:
            if line is False:
                return

            if line.startswith(wiki_constants.ROOT_TAG):
                parent_tags = []
                new_tag = self._add_tag_line(parent_tags, line)
                parent_tags.append(new_tag)
            else:
                level = self._get_tag_level(line)
                if level < len(parent_tags):
                    parent_tags = parent_tags[:level]
                new_tag = self._add_tag_line(parent_tags, line)
                parent_tags.append(new_tag)

    def _skip_read_section(self, file_iter):
        """Reads from the file until it reaches a new section, discarding all lines.

        Parameters
        ----------
        file_iter: iter
            An iterator from self._get_line_iter.
        """
        for line in file_iter:
            if line is False:
                return

    def _read_unit_classes(self, file_iter):
        """Adds the unit classes section

        Parameters
        ----------
        file_iter: iter
            An iterator from self._get_line_iter.
        """
        current_unit_class = ""

        for line in file_iter:
            if line is False:
                return

            unit_class = self._get_tag_name(line)
            level = self._get_tag_level(line)
            # This is a unit class
            if level == 1:
                current_unit_class = unit_class
                self._schema._add_unit_class_unit(current_unit_class, None)
            # This is a unit class unit
            else:
                self._schema._add_unit_class_unit(current_unit_class, unit_class)
            self._add_single_line(line, HedKey.Units, skip_adding_name=True)

    def _read_unit_modifiers(self, file_iter):
        """Adds the unit modifiers section

        Parameters
        ----------
        file_iter: iter
            An iterator from self._get_line_iter.
        """
        for line in file_iter:
            if line is False:
                return

            self._add_single_line(line, HedKey.UnitModifiers)

    def _read_attributes(self, file_iter):
        self.attributes = {}
        for line in file_iter:
            if line is False:
                return
            attribute_name = self._get_tag_name(line)

            self._schema._add_attribute_name_to_dict(attribute_name)
            self._add_single_line(line, HedKey.Attributes)

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
        final_attributes = {}
        attribute_pairs = version_line.split(',')
        for pair in attribute_pairs:
            if pair.count(':') != 1:
                raise HedFileError(HedExceptions.SCHEMA_HEADER_INVALID,
                                   f"Found poorly matched key:value pair in header: {pair}", filename=self.filename)
            key, value = pair.split(':')
            key = key.strip()
            value = value.strip()
            final_attributes[key] = value

        return final_attributes

    @staticmethod
    def _get_tag_level(tag_line):
        """Gets the tag level from a line in a wiki file.

        Parameters
        ----------
        tag_line: string
            A tag line.

        Returns
        -------
        int
            Gets the tag level. The number of asterisks determine what level the tag is on.
        """
        level = re.compile(level_expression)
        match = level.search(tag_line)
        if match:
            return match.group().count('*')
        else:
            return 1

    @staticmethod
    def _remove_nowiki_tag_from_line(tag_line):
        """Removes the nowiki tag from the  line.

        Parameters
        ----------
        tag_line: string
            A tag line.

        Returns
        -------
        string
            The line with the nowiki tag removed.
        """
        tag_line = re.sub(no_wiki_tag, '', tag_line)
        return tag_line

    @staticmethod
    def _get_tag_name(tag_line):
        """Gets the tag name from the tag line.

        Parameters
        ----------
        tag_line: string
            A tag line.

        Returns
        -------
        string
            The tag name.
        """
        if tag_line.find(extend_here_line) != -1:
            return ''
        name = re.compile(tag_name_regexp)
        for invalid_chars in invalid_characters_to_strip:
            tag_line = tag_line.replace(invalid_chars, "")
        match = name.search(tag_line)
        if match:
            return match.group().strip()
        else:
            return ''

    @staticmethod
    def _get_tag_attributes(tag_line):
        """Gets the tag attributes from a line.

        Parameters
        ----------
        tag_line: string
            A tag line.

        Returns
        -------
        {}
            Dict containing the attributes
        """
        attributes = re.compile(attributes_expression)
        match = attributes.search(tag_line)
        if match:
            attributes_split = [x.strip() for x in re.sub('[{}]', '', match.group()).split(',')]
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
            return final_attributes
        else:
            return {}

    @staticmethod
    def _get_tag_description(tag_line):
        """Gets the tag description from a line.

        Parameters
        ----------
        tag_line: string
            A tag line.

        Returns
        -------
        string
            The tag description.
        """
        description = re.compile(description_expression)
        match = description.search(tag_line)
        if match:
            return re.sub(square_bracket_removal_expression, '', match.group()).strip()
        else:
            return ''

    def _add_tag_line(self, parent_tags, tag_line):
        """Add a tag to the dictionaries, including attributes and description.

        Parameters
        ----------
        parent_tags: [str]
            A list of parent tags in order.
        tag_line: string
            A tag line.

        Returns
        -------
        tag_name: str
            The name of the added tag
        """
        tag_name = self._get_tag_name(tag_line)
        if tag_name:
            if parent_tags:
                long_tag_name = "/".join(parent_tags) + "/" + tag_name
            else:
                long_tag_name = tag_name
            self._add_single_line(tag_line, HedKey.AllTags, long_tag_name)

        return tag_name

    def _add_single_line(self, tag_line, key_class, element_name=None, skip_adding_name=False):
        if element_name:
            node_name = element_name
        else:
            node_name = self._get_tag_name(tag_line)

        node_desc = self._get_tag_description(tag_line)
        node_attributes = self._get_tag_attributes(tag_line)
        if not skip_adding_name:
            self._schema._add_tag_to_dict(node_name, key_class, node_name)
        self._schema._add_description_to_dict(node_name, node_desc, key_class)

        for attribute_name, attribute_value in node_attributes.items():
            self._schema._add_attribute_to_dict(node_name, attribute_name, attribute_value, key_class)
