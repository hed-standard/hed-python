"""
This module is used to create a HedSchema object from a .mediawiki file.
"""
import re
from hed.schema import hed_schema_constants as constants
from hed.schema.hed_schema_constants import HedKey
from hed.util.exceptions import HedFileError, HedExceptions
from hed.schema import HedSchema

ATTRIBUTE_DEFINITION_STRING = '\'\'\'Attribute Definitions:'
CHANGE_LOG_STRING = 'Changelog'
SYNTAX_STRING = '\'\'\'Syntax'
ROOT_TAG = '\'\'\''
HED_NODE_STRING = "HED"
START_STRING = '!# start hed'
UNIT_CLASS_STRING = '\'\'\'Unit classes'
UNIT_MODIFIER_STRING = '\'\'\'Unit modifiers'
END_STRING = '!# end hed'


level_expression = r'\*+'
attributes_expression = r'\{.*\}'
description_expression = r'\[.*\]'
extend_here_line = 'extend here'
invalid_characters_to_strip = ["&#8203;"]
tag_name_regexp = r'([<>=#\-a-zA-Z0-9$:()\^µ]+\s*)+'
no_wiki_tag = '</?nowiki>'
square_bracket_removal_expression = r'[\[\]]'


class HedSchemaWikiParser:
    def __init__(self, wiki_file_path):
        # Required properties
        self.schema_attributes = {}
        self.dictionaries = HedSchema.create_empty_dictionaries()

        try:
            with open(wiki_file_path, 'r', encoding='utf-8', errors='replace') as wiki_file:
                self._populate_dictionaries(wiki_file)
        except FileNotFoundError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, wiki_file_path)

    def _populate_dictionaries(self, wiki_file):
        line = wiki_file.readline()
        while line:
            line = line.strip()
            if not line:
                pass
            if line.startswith(HED_NODE_STRING):
                hed_attributes = self._get_schema_attributes(line[len(HED_NODE_STRING):])
                self.schema_attributes = hed_attributes
            elif line.startswith(START_STRING):
                self._add_tags(wiki_file)
                break
            line = wiki_file.readline()

    @staticmethod
    def _get_schema_attributes(version_line):
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
                continue
            key, value = pair.split(':')
            key = key.strip()
            value = value.strip()
            if key not in constants.HED_VALID_ATTRIBUTES:
                continue

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

    def _add_tags(self, wiki_file):
        """Adds the tags to the HED element.

        Parameters
        ----------
        wiki_file: file object.
            A file object that points to the HED wiki file.

        Returns
        -------

        """
        parent_tags = []
        line = wiki_file.readline()
        while line:
            line = self._remove_nowiki_tag_from_line(line.strip())
            if not line:
                pass
            elif line.startswith(UNIT_MODIFIER_STRING):
                self.add_unit_modifiers(wiki_file)
                break
            elif line.startswith(UNIT_CLASS_STRING):
                self.add_unit_classes(wiki_file)
            elif line.startswith(ROOT_TAG):
                parent_tags = []
                new_tag = self._add_tag_line(parent_tags, line)
                parent_tags.append(new_tag)
            else:
                level = self._get_tag_level(line)
                if level < len(parent_tags):
                    parent_tags = parent_tags[:level]
                new_tag = self._add_tag_line(parent_tags, line)
                parent_tags.append(new_tag)
            line = wiki_file.readline()

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
                    final_attributes[split_attribute[0]] = "true"
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
            tag_description = self._get_tag_description(tag_line)
            tag_attributes = self._get_tag_attributes(tag_line)
            if parent_tags:
                long_tag_name = "/".join(parent_tags) + "/" + tag_name
            else:
                long_tag_name = tag_name
            self.dictionaries[HedKey.AllTags][long_tag_name.lower()] = long_tag_name
            if tag_description:
                self.dictionaries[HedKey.Descriptions][long_tag_name] = tag_description
            for tag_attribute in tag_attributes:
                if tag_attribute in constants.STRING_ATTRIBUTE_DICTIONARY_KEYS:
                    attribute_value = tag_attributes[tag_attribute]
                else:
                    attribute_value = long_tag_name
                if tag_attribute in constants.TAG_ATTRIBUTE_KEYS:
                    self.dictionaries[tag_attribute][long_tag_name.lower()] = attribute_value

        return tag_name

    def add_unit_classes(self, wiki_file):
        self.dictionaries[HedKey.DefaultUnits] = {}
        self.dictionaries[HedKey.Units] = {}
        for unit_class_key in constants.UNIT_CLASS_DICTIONARY_KEYS:
            self.dictionaries[unit_class_key] = {}

        line = wiki_file.readline()
        current_unit_class = ""
        while line:
            line = self._remove_nowiki_tag_from_line(line.strip())
            if not line:
                break
            else:
                level = self._get_tag_level(line)
                # This is a unit class
                if level == 1:
                    unit_class = self._get_tag_name(line)
                    unit_class_attributes = self._get_tag_attributes(line)
                    current_unit_class = unit_class
                    unit_class_desc = self._get_tag_description(line)
                    if unit_class_desc:
                        self.dictionaries[HedKey.Descriptions][HedKey.Units + unit_class] = unit_class_desc
                    for tag_attribute in unit_class_attributes:
                        if tag_attribute in constants.STRING_ATTRIBUTE_DICTIONARY_KEYS:
                            attribute_value = unit_class_attributes[tag_attribute]
                        else:
                            attribute_value = unit_class
                        self.dictionaries[tag_attribute][unit_class] = attribute_value
                else:
                    unit_class_unit = self._get_tag_name(line)
                    unit_class_unit_attributes = self._get_tag_attributes(line)
                    unit_class_desc = self._get_tag_description(line)
                    if unit_class_desc:
                        self.dictionaries[HedKey.Descriptions][HedKey.Units + unit_class_unit] = unit_class_desc

                    if current_unit_class not in self.dictionaries[HedKey.Units]:
                        self.dictionaries[HedKey.Units][current_unit_class] = []
                    self.dictionaries[HedKey.Units][current_unit_class].append(unit_class_unit)

                    for unit_class_key in constants.UNIT_CLASS_DICTIONARY_KEYS:
                        self.dictionaries[unit_class_key][unit_class_unit] = unit_class_unit_attributes.get(unit_class_key)

            line = wiki_file.readline()

    def add_unit_modifiers(self, wiki_file):
        self.dictionaries[HedKey.SIUnitModifier] = {}
        self.dictionaries[HedKey.SIUnitSymbolModifier] = {}

        line = wiki_file.readline()
        while line:
            line = self._remove_nowiki_tag_from_line(line.strip())
            if not line:
                break
            elif line.startswith(END_STRING):
                break
            else:
                unit_modifier = self._get_tag_name(line)
                unit_modifier_attributes = self._get_tag_attributes(line)
                unit_modifier_desc = self._get_tag_description(line)

                if unit_modifier_desc:
                    self.dictionaries[HedKey.Descriptions][HedKey.SIUnitModifier + unit_modifier] = unit_modifier_desc

                for unit_modifier_key in constants.UNIT_MODIFIER_DICTIONARY_KEYS:
                    self.dictionaries[unit_modifier_key][unit_modifier] = unit_modifier_attributes.get(unit_modifier_key)

            line = wiki_file.readline()
