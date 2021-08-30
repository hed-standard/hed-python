"""
This module is used to create a HedSchema object from a .mediawiki file.
"""
import re
from hed.schema.hed_schema_constants import HedKey
from hed.errors.exceptions import HedFileError, HedExceptions
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
    ValueClasses = 8
    Attributes = 9
    Properties = 10
    Epilogue = 11
    EndHed = 12


SectionStarts = {
    HedSection.Prologue: wiki_constants.PROLOGUE_SECTION_ELEMENT,
    HedSection.Schema: wiki_constants.START_HED_STRING,
    HedSection.EndSchema: wiki_constants.END_SCHEMA_STRING,
    HedSection.UnitsClasses: wiki_constants.UNIT_CLASS_STRING,
    HedSection.UnitModifiers: wiki_constants.UNIT_MODIFIER_STRING,
    HedSection.ValueClasses: wiki_constants.VALUE_CLASS_STRING,
    HedSection.Attributes: wiki_constants.ATTRIBUTE_DEFINITION_STRING,
    HedSection.Properties: wiki_constants.ATTRIBUTE_PROPERTY_STRING,
    HedSection.Epilogue: wiki_constants.EPILOGUE_SECTION_ELEMENT,
    HedSection.EndHed: wiki_constants.END_HED_STRING
}


SectionNames = {
    HedSection.HeaderLine: "Header",
    HedSection.Prologue: "Prologue",
    HedSection.Schema: "Schema",
    HedSection.EndSchema: "EndSchema",
    HedSection.UnitsClasses: "Unit Classes",
    HedSection.UnitModifiers: "Unit Modifiers",
    HedSection.ValueClasses: "Value Classes",
    HedSection.Attributes: "Attributes",
    HedSection.Properties: "Properties",
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
            HedSection.HeaderLine: self._read_header_section,
            HedSection.Prologue: self._read_prologue,
            HedSection.Properties: self._read_properties,
            HedSection.Epilogue: self._read_epilogue,
            # Pass 2
            HedSection.Attributes: self._read_attributes,
            # Pass3
            HedSection.Schema: self._read_schema,
            HedSection.UnitsClasses: self._read_unit_classes,
            HedSection.UnitModifiers: self._read_unit_modifiers,
            HedSection.ValueClasses: self._read_value_classes,
        }
        self._parse_sections(wiki_lines_by_section, parse_order)

        # Validate we didn't miss any required sections.
        for section in required_sections:
            if section not in wiki_lines_by_section:
                error_code = HedExceptions.INVALID_SECTION_SEPARATOR
                if section in ErrorsBySection:
                    error_code = ErrorsBySection[section]
                raise HedFileError(error_code,
                                   f"Required section separator '{SectionNames[section]}' not found in file",
                                   filename=self.filename)

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
        current_section = HedSection.HeaderLine
        found_section = True
        strings_for_section = {}
        for line in wiki_lines:
            for key, section_string in SectionStarts.items():
                if line.startswith(section_string):
                    if key in strings_for_section:
                        raise HedFileError(HedExceptions.INVALID_SECTION_SEPARATOR,
                                           f"Found section {SectionNames[key]} twice", filename=self.filename)

                    if current_section < key:
                        current_section = key
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
                strings_for_section[current_section] = []
                found_section = False
                continue

            if (current_section != HedSection.Schema and line.startswith(wiki_constants.ROOT_TAG) and
                    not (line.startswith(wiki_constants.OLD_SYNTAX_SECTION_NAME) and not self._schema.is_hed3_schema)):
                raise HedFileError(HedExceptions.INVALID_SECTION_SEPARATOR,
                                   f"Invalid section separator '{line.strip()}'", filename=self.filename)

            if line.startswith("!#"):
                raise HedFileError(HedExceptions.INVALID_SECTION_SEPARATOR,
                                   f"Invalid section separator '{line.strip()}'", filename=self.filename)

            if current_section == HedSection.Prologue or current_section == HedSection.Epilogue:
                if line.strip():
                    # we want to preserve all formatting in the prologue and epilogue.
                    if line.endswith("\n"):
                        line = line[:-1]
                    strings_for_section[current_section].append(line)
            else:
                line = self._remove_nowiki_tag_from_line(line.strip())
                if line:
                    strings_for_section[current_section].append(line)

        return strings_for_section

    def _parse_sections(self, wiki_lines_by_section, parse_order):
        for section in parse_order:
            lines_for_section = wiki_lines_by_section.get(section, [])
            parse_func = parse_order[section]
            parse_func(lines_for_section)

    def _read_header_line(self, line):
        if line.startswith(wiki_constants.HEADER_LINE_STRING):
            hed_attributes = self._get_header_attributes(line[len(wiki_constants.HEADER_LINE_STRING):])
            self.issues = schema_validation_util.validate_attributes(hed_attributes, filename=self.filename)
            self.header_attributes = hed_attributes
            self._schema.issues = self.issues
            self._schema.header_attributes = hed_attributes
            return
        raise HedFileError(HedExceptions.SCHEMA_HEADER_MISSING,
                           f"First line of file should be HED, instead found: {line}", filename=self.filename)

    def _read_header_section(self, lines):
        """Ensures the header has no content other than the initial line.

        Parameters
        ----------
        lines: [str]
            Lines for this section
        """
        for line in lines:
            if line.strip():
                raise HedFileError(HedExceptions.SCHEMA_HEADER_INVALID,
                                   f"There should be no other content in the between the HED line in the header and either the prologue or schema sections.", filename=self.filename)

    def _read_prologue(self, lines):
        """Adds the prologue

        Parameters
        ----------
        lines: [str]
            Lines for this section
        """
        prologue = ""
        for line in lines:
            if prologue:
                prologue += "\n"
            prologue += line
        self._schema.prologue = prologue

    def _read_epilogue(self, lines):
        """Adds the epilogue

        Parameters
        ----------
        lines: [str]
            Lines for this section
        """
        epilogue = ""
        for line in lines:
            if epilogue:
                epilogue += "\n"
            epilogue += line
        self._schema.epilogue = epilogue

    def _read_schema(self, lines):
        """Adds the main schema section

        Parameters
        ----------
        lines: [str]
            Lines for this section
        """
        parent_tags = []
        for line in lines:
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

    def _read_unit_classes(self, lines):
        """Adds the unit classes section

        Parameters
        ----------
        lines: [str]
            Lines for this section
        """
        current_unit_class = ""

        for line in lines:
            unit_class = self._get_tag_name(line)
            level = self._get_tag_level(line)
            # This is a unit class
            if level == 1:
                current_unit_class = unit_class
                self._schema._add_unit_class_unit(current_unit_class, None)
                self._add_single_line(line, HedKey.UnitClasses, skip_adding_name=True)
            # This is a unit class unit
            else:
                self._schema._add_unit_class_unit(current_unit_class, unit_class)
                self._add_single_line(line, HedKey.Units, skip_adding_name=True)

    def _read_unit_modifiers(self, lines):
        """Adds the unit modifiers section

        Parameters
        ----------
        lines: [str]
            Lines for this section
        """
        for line in lines:
            self._add_single_line(line, HedKey.UnitModifiers)

    def _read_value_classes(self, lines):
        """Adds the unit modifiers section

        Parameters
        ----------
        lines: [str]
            Lines for this section
        """
        for line in lines:
            self._add_single_line(line, HedKey.ValueClasses)

    def _read_properties(self, lines):
        for line in lines:
            prop_name = self._get_tag_name(line)
            prop_desc = self._get_tag_description(line)
            self._schema._add_property_name_to_dict(prop_name, prop_desc)
        self._schema.add_default_properties()

    def _read_attributes(self, lines):
        self.attributes = {}
        for line in lines:
            attribute_name = self._get_tag_name(line)

            self._schema._add_attribute_name_to_dict(attribute_name)
            self._add_single_line(line, HedKey.Attributes)
        self._schema.add_hed2_attributes()

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

        attr_pattern = "([^ ]+?)=\"(.*?)\""
        attr_re = re.compile(attr_pattern)

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
                raise HedFileError(HedExceptions.SCHEMA_HEADER_INVALID,
                                   f"Found poorly matched key:value pair in header: {pair}", filename=self.filename)
            key, value = pair[:divider_index], pair[divider_index + 1:]
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
