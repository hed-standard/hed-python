"""
This module contains the Hed_Dictionary class which encapsulates all HED tags, tag attributes, unit classes, and
unit class attributes in a dictionary.

The dictionary is a dictionary of dictionaries. The dictionary names are
'default', 'extensionAllowed', 'isNumeric', 'position', 'predicateType', 'recommended', 'required', 'requireChild',
'tags', 'takesValue', 'unique', 'units', and 'unitClass'.
"""

from defusedxml.ElementTree import parse
import xml
from hed.util.exceptions import SchemaFileError
from hed.util.error_types import SchemaErrors


# These need to match the attributes/element name/etc used to load from the xml
class HedKey:
    Default = 'default'
    ExtensionAllowed = 'extensionAllowed'
    IsNumeric = 'isNumeric'
    Position = 'position'
    PredicateType = 'predicateType'
    Recommended = 'recommended'
    RequiredPrefix = 'required'
    RequireChild = 'requireChild'
    AllTags = 'tags'
    TakesValue = 'takesValue'
    Unique = 'unique'
    UnitClass = 'unitClass'

    # Default Units for Type
    DefaultUnits = 'defaultUnits'
    Units = 'units'

    SIUnit = 'SIUnit'
    UnitSymbol = 'unitSymbol'

    SIUnitModifier = 'SIUnitModifier'
    SIUnitSymbolModifier = 'SIUnitSymbolModifier'

    # If this is a valid HED3 spec, this allow mapping from short to long.
    ShortTags = 'shortTags'


class HedDictionary:
    TAG_DICTIONARY_KEYS = [HedKey.Default, HedKey.ExtensionAllowed, HedKey.IsNumeric, HedKey.Position,
                           HedKey.PredicateType, HedKey.Recommended, HedKey.RequiredPrefix, HedKey.RequireChild,
                           HedKey.AllTags, HedKey.TakesValue, HedKey.Unique, HedKey.UnitClass]
    UNIT_CLASS_DICTIONARY_KEYS = [HedKey.SIUnit, HedKey.UnitSymbol]
    UNIT_MODIFIER_DICTIONARY_KEYS = [HedKey.SIUnitModifier, HedKey.SIUnitSymbolModifier]

    # These should mostly match the HedKey values above.
    # These are repeated here for clarification primarily
    DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE = HedKey.DefaultUnits
    DEFAULT_UNIT_FOR_OLD_UNIT_CLASS_ATTRIBUTE = HedKey.Default
    UNIT_CLASS_ELEMENT = HedKey.UnitClass
    UNIT_CLASS_UNIT_ELEMENT = 'unit'
    UNIT_CLASS_UNITS_ELEMENT = HedKey.Units
    UNIT_MODIFIER_ELEMENT = 'unitModifier'

    VERSION_ATTRIBUTE = 'version'

    def __init__(self, hed_xml_file_path):
        """Constructor for the Hed_Dictionary class.

        Parameters
        ----------
        hed_xml_file_path: str
            The path to a HED XML file.

        Returns
        -------
        HedDictionary
            A Hed_Dictionary object.

        """
        self.no_duplicate_tags = True
        self.root_element = self.parse_hed_xml_file(hed_xml_file_path)
        # Used to find parent elements of XML nodes for file parsing
        self._parent_map = {c: p for p in self.root_element.iter() for c in p}
        self._populate_dictionaries()

    def get_root_element(self):
        """Gets the root element of the HED XML file.

        Parameters
        ----------

        Returns
        -------
        Element
            The root element of the HED XML file.

        """
        return self.root_element

    def get_dictionaries(self):
        """Gets a dictionary of dictionaries that contains all of the tags, tag attributes, unit class units, and unit
           class attributes

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries that contains all of the tags, tag attributes, unit class units, and unit
            class attributes

        """
        return self.dictionaries

    def has_duplicate_tags(self):
        """
        Returns True if this is a valid hed3 schema with no duplicate short tags.

        Returns
        -------
        bool
            Returns True if this is a valid hed3 schema with no duplicate short tags.
        """
        return not self.no_duplicate_tags

    def _populate_dictionaries(self):
        """Populates a dictionary of dictionaries that contains all of the tags, tag attributes, unit class units,
           and unit class attributes.

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries that contains all of the tags, tag attributes, unit class units, and unit class
            attributes.

        """
        self.dictionaries = {}
        self._populate_tag_dictionaries()
        self._populate_unit_class_dictionaries()
        self._populate_unit_modifier_dictionaries()
        self._populate_short_tag_dict()
        self._add_hed3_compatible_tags()

    @property
    def short_tag_mapping(self):
        """
        This returns the short->long tag dictionary if we have a hed3 compatible schema.

        Returns
        -------
        short_tag_dict: {}
            Returns the short tag mapping dictionary, or None if this is not a hed3 compatible schema.
        """
        if self.no_duplicate_tags:
            return self.dictionaries[HedKey.ShortTags]
        return None

    def get_all_forms_of_tag(self, short_tag_to_check):
        """
        Given a short tag, return all the longer versions of it.

        eg: "definition" will return
                ["definition", "informational/definition", "attribute/informational/definition"]

        Parameters
        ----------
        short_tag_to_check : str
            The short version of a hed tag we are interested in.

        Returns
        -------
        tag_versions: [str]
            A list of all short, intermediate, and long versions of the passed in short tag.
            Returns empty list if no versions found.
        """
        try:
            tag_entry = self.short_tag_mapping[short_tag_to_check.lower()]
        except KeyError:
            return []

        split_tags = tag_entry.lower().split("/")
        final_tag = ""
        all_forms = []
        for tag in reversed(split_tags):
            final_tag = tag + "/" + final_tag
            all_forms.append(final_tag)

        return all_forms

    def _populate_tag_dictionaries(self):
        """Populates a dictionary of dictionaries associated with tags and their attributes.

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries that has been populated with dictionaries associated with tag attributes.

        """
        for dict_key in HedDictionary.TAG_DICTIONARY_KEYS:
            tags, tag_elements = self.get_tags_by_attribute(dict_key)
            if HedKey.ExtensionAllowed == dict_key:
                child_tags = self._get_all_child_tags(tag_elements)
                child_tags_dictionary = self._string_list_to_lowercase_dictionary(child_tags)
                tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
                tag_dictionary.update(child_tags_dictionary)
            elif HedKey.Default == dict_key or \
                    HedKey.UnitClass == dict_key:
                tag_dictionary = self._populate_tag_to_attribute_dictionary(tags, tag_elements, dict_key)
            elif HedKey.AllTags == dict_key:
                tags = self.get_all_tags()[0]
                tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
            else:
                tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
            self.dictionaries[dict_key] = tag_dictionary

    def _populate_unit_class_dictionaries(self):
        """Populates a dictionary of dictionaries associated with all of the unit classes, unit class units, and unit
           class default units.

        Parameters
        ----------

        Returns
        -------
        dict
            A dictionary of dictionaries associated with all of the unit classes, unit class units, and unit class
            default units.

        """
        unit_class_elements = self._get_elements_by_name(self.UNIT_CLASS_ELEMENT)
        if len(unit_class_elements) == 0:
            self.has_unit_classes = False
            return
        self.has_unit_classes = True
        self._populate_unit_class_default_unit_dictionary(unit_class_elements)
        self._populate_unit_class_units_dictionary(unit_class_elements)

    def _populate_unit_modifier_dictionaries(self):
        """
        Gathers all unit modifier definitions from the schema.

        Returns
        -------

        """
        unit_modifier_elements = self._get_elements_by_name(self.UNIT_MODIFIER_ELEMENT)
        if len(unit_modifier_elements) == 0:
            self.has_unit_modifiers = False
            return
        self.has_unit_modifiers = True
        for unit_modifier_key in self.UNIT_MODIFIER_DICTIONARY_KEYS:
            self.dictionaries[unit_modifier_key] = {}
        for unit_modifier_element in unit_modifier_elements:
            unit_modifier_name = self._get_element_tag_value(unit_modifier_element)
            for unit_modifier_key in self.UNIT_MODIFIER_DICTIONARY_KEYS:
                self.dictionaries[unit_modifier_key][unit_modifier_name] = unit_modifier_element.get(unit_modifier_key)

    def find_duplicate_tags(self):
        """Finds all tags that are not unique.

        Returns
        -------
        duplicate_tag_dict: {str: [str]}
            A dictionary of all duplicate short tags as keys, with the values being a list of
            long tags sharing that short tag
        """
        duplicate_dict = {}
        short_tag_dict = self.dictionaries[HedKey.ShortTags]
        for tag_name in short_tag_dict:
            modified_name = f'{tag_name}'
            if isinstance(short_tag_dict[tag_name], list):
                duplicate_dict[modified_name] = short_tag_dict[tag_name]

        return duplicate_dict

    def dupe_tag_iter(self, return_detailed_info=False):
        """
        An iterator that goes over each line of the duplicate tags dict, including descriptive ones.

        Parameters
        ----------
        return_detailed_info : bool
            If true, also returns header lines listing the number of duplicate tags for each short tag.

        Yields
        -------
        text_line: str
            A list of long tags that have duplicates, with optional descriptive short tag lines.
        """
        duplicate_dict = self.find_duplicate_tags()
        for tag_name in duplicate_dict:
            if return_detailed_info:
                yield f"Duplicate tag found {tag_name} - {len(duplicate_dict[tag_name])} versions:"
            for tag_entry in duplicate_dict[tag_name]:
                yield f"\t{tag_entry}"

    def _populate_short_tag_dict(self):
        """
        Create a mapping from the short version of a tag to the long version and
        determines if this is a hed3 compatible schema.

        Returns
        -------
        """
        self.no_duplicate_tags = True
        base_tag_dict = self.dictionaries[HedKey.AllTags]
        new_short_tag_dict = {}
        for tag, unformatted_tag in base_tag_dict.items():
            split_tags = unformatted_tag.split("/")
            short_tag = split_tags[-1]
            if short_tag == "#":
                continue
            short_clean_tag = short_tag.lower()
            new_tag_entry = unformatted_tag
            if short_clean_tag not in new_short_tag_dict:
                new_short_tag_dict[short_clean_tag] = new_tag_entry
            else:
                self.no_duplicate_tags = False
                if not isinstance(new_short_tag_dict[short_clean_tag], list):
                    new_short_tag_dict[short_clean_tag] = [new_short_tag_dict[short_clean_tag]]
                new_short_tag_dict[short_clean_tag].append(new_tag_entry)
        self.dictionaries[HedKey.ShortTags] = new_short_tag_dict

    def _add_hed3_compatible_tags(self):
        """
        Updates the normal tag dictionaries with all the intermediate forms if this is a hed3 compatible schema."

        Returns
        -------
        """
        if self.no_duplicate_tags:
            for dict_key in self.TAG_DICTIONARY_KEYS:
                tag_dictionary = self.dictionaries[dict_key]
                new_entries = {}
                for full_tag, value in tag_dictionary.items():
                    split_tags = full_tag.split("/")
                    final_tag = ""
                    for tag in reversed(split_tags):
                        final_tag = tag + "/" + final_tag
                        # We need to include the #, but make sure we don't create a tag with just # alone.
                        if tag == "#":
                            continue
                        # Remove extra trailing slash.
                        new_entries[final_tag[:-1]] = value
                tag_dictionary.update(new_entries)

    def _populate_unit_class_units_dictionary(self, unit_class_elements):
        """Populates a dictionary that contains unit class units.

        Parameters
        ----------
        unit_class_elements: list
            A list of unit class elements.

        Returns
        -------
        dict
            A dictionary that contains all the unit class units.

        """
        self.dictionaries[HedKey.Units] = {}
        for unit_class_key in self.UNIT_CLASS_DICTIONARY_KEYS:
            self.dictionaries[unit_class_key] = {}
        for unit_class_element in unit_class_elements:
            element_name = self._get_element_tag_value(unit_class_element)
            element_units = self._get_elements_by_name(self.UNIT_CLASS_UNIT_ELEMENT, unit_class_element)
            if not element_units:
                element_units = self._get_element_tag_value(unit_class_element, self.UNIT_CLASS_UNITS_ELEMENT)
                units = element_units.split(',')
                units_list = list(map(lambda unit: unit.lower(), units))
                self.dictionaries[HedKey.Units][element_name] = units_list
                continue
            element_unit_names = list(map(lambda element: element.text, element_units))
            self.dictionaries[HedKey.Units][element_name] = element_unit_names
            for element_unit in element_units:
                unit_name = element_unit.text
                for unit_class_key in self.UNIT_CLASS_DICTIONARY_KEYS:
                    self.dictionaries[unit_class_key][unit_name] = element_unit.get(unit_class_key)

    def _populate_unit_class_default_unit_dictionary(self, unit_class_elements):
        """Populates a dictionary that contains unit class default units.

        Parameters
        ----------
        unit_class_elements: list
            A list of unit class elements.

        Returns
        -------
        dict
            A dictionary that contains all the unit class default units.

        """
        self.dictionaries[HedKey.DefaultUnits] = {}
        for unit_class_element in unit_class_elements:
            unit_class_element_name = self._get_element_tag_value(unit_class_element)
            default_unit = unit_class_element.get(self.DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE)
            if default_unit is None:
                self.dictionaries[HedKey.DefaultUnits][unit_class_element_name] = \
                    unit_class_element.attrib[HedDictionary.DEFAULT_UNIT_FOR_OLD_UNIT_CLASS_ATTRIBUTE]
            else:
                self.dictionaries[HedKey.DefaultUnits][unit_class_element_name] = default_unit

    def _populate_tag_to_attribute_dictionary(self, tag_list, tag_element_list, attribute_name):
        """Populates the dictionaries associated with default unit tags in the attribute dictionary.

        Parameters
        ----------
        tag_list: []
            A list containing tags that have a specific attribute.
        tag_element_list: []
            A list containing tag elements that have a specific attribute.
        attribute_name: str
            The name of the attribute associated with the tags and tag elements.

        Returns
        -------
        {}
            The attribute dictionary that has been populated with dictionaries associated with tags.

        """
        dictionary = {}
        for index, tag in enumerate(tag_list):
            dictionary[tag.lower()] = tag_element_list[index].attrib[attribute_name]
        return dictionary

    def _string_list_to_lowercase_dictionary(self, string_list):
        """Converts a string list into a dictionary. The keys in the dictionary will be the lowercase values of the
           strings in the list.

        Parameters
        ----------
        string_list: list
            A list containing string elements.

        Returns
        -------
        dict
            A dictionary containing the strings in the list.

        """
        lowercase_dictionary = {}
        for string_element in string_list:
            lowercase_dictionary[string_element.lower()] = string_element
        return lowercase_dictionary

    @staticmethod
    def parse_hed_xml_file(hed_xml_file_path):
        """Parses a XML file and returns the root element.

        Parameters
        ----------
        hed_xml_file_path: str
            The path to a HED XML file.

        Returns
        -------
        RestrictedElement
            The root element of the HED XML file.

        """
        try:
            hed_xml_tree = parse(hed_xml_file_path)
        except xml.etree.ElementTree.ParseError as e:
            raise SchemaFileError(SchemaErrors.CANNOT_PARSE_XML, e.msg, hed_xml_file_path)
        except FileNotFoundError as e:
            raise SchemaFileError(SchemaErrors.FILE_NOT_FOUND, e.strerror, hed_xml_file_path)
        return hed_xml_tree.getroot()

    def _get_ancestor_tag_names(self, tag_element):
        """Gets all the ancestor tag names of a tag element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        []
            A list containing all of the ancestor tag names of a given tag.

        """
        ancestor_tags = []
        parent_tag_name = self._get_parent_tag_name(tag_element)
        parent_element = self._parent_map[tag_element]
        while parent_tag_name:
            ancestor_tags.append(parent_tag_name)
            parent_tag_name = self._get_parent_tag_name(parent_element)
            if parent_tag_name:
                parent_element = self._parent_map[parent_element]
        return ancestor_tags

    def _get_element_tag_value(self, element, tag_name='name'):
        """Gets the value of the element's tag.

        Parameters
        ----------
        element: Element
            A element in the HED XML file.
        tag_name: str
            The name of the XML element's tag. The default is 'name'.

        Returns
        -------
        str
            The value of the element's tag. If the element doesn't have the tag then it will return an empty string.

        """
        return element.find(tag_name).text

    def _get_parent_tag_name(self, tag_element):
        """Gets the name of the tag parent element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        str
            The name of the tag element's parent. If there is no parent tag then an empty string is returned.

        """
        parent_tag_element = self._parent_map[tag_element]
        if parent_tag_element is not None:
            return parent_tag_element.findtext('name')
        else:
            return ''

    def _get_tag_path_from_tag_element(self, tag_element):
        """Gets the tag path from a given tag element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        str
            A tag path which is typically referred to as a tag. The tag and it's ancestor tags will be separated by /'s.

        """
        ancestor_tag_names = self._get_ancestor_tag_names(tag_element)
        ancestor_tag_names.insert(0, self._get_element_tag_value(tag_element))
        ancestor_tag_names.reverse()
        return '/'.join(ancestor_tag_names)

    def get_tags_by_attribute(self, attribute_name):
        """Gets the tag that have a specific attribute.

        Parameters
        ----------
        attribute_name: str
            The name of the attribute associated with the tags.

        Returns
        -------
        tuple
            A tuple containing tags and tag elements that have a specified attribute.

        """
        tags = []
        tag_elements = self.root_element.findall('.//node[@%s]' % attribute_name)
        for attribute_tag_element in tag_elements:
            tag = self._get_tag_path_from_tag_element(attribute_tag_element)
            tags.append(tag)
        return tags, tag_elements

    def get_all_tags(self, tag_element_name='node'):
        """Gets the tags that have a specific attribute.

        Parameters
        ----------
        tag_element_name: str
            The XML tag name of the tag elements. The default is 'node'.

        Returns
        -------
        tuple
            A tuple containing all the tags and tag elements in the XML file.

        """
        tags = []
        tag_elements = self.root_element.findall('.//%s' % tag_element_name)
        for tag_element in tag_elements:
            tag = self._get_tag_path_from_tag_element(tag_element)
            tags.append(tag)
        return tags, tag_elements

    # def _get_elements_by_attribute(self, attribute_name, element_name='node'):
    #     """Gets the elements that have a specific attribute.
    #
    #     Parameters
    #     ----------
    #     attribute_name: str
    #         The name of the attribute associated with the element.
    #     element_name: str
    #         The name of the XML element tag name. The default is 'node'.
    #
    #     Returns
    #     -------
    #     list
    #         A list containing elements that have a specified attribute.
    #
    #     """
    #     tag_elements = self.root_element.xpath('.//%s[@%s]' % (element_name, attribute_name))
    #     return tag_elements

    def _get_elements_by_name(self, element_name='node', parent_element=None):
        """Gets the elements that have a specific element name.

        Parameters
        ----------
        element_name: str
            The name of the element. The default is 'node'.
        parent_element: RestrictedElement
            The parent element. The default is 'None'. If a parent element is specified then only the children of the
            parent will be returned with the given 'element_name'. If not specified the root element will be the parent.

        Returns
        -------
        []
            A list containing elements that have a specific element name.

        """
        if parent_element is None:
            elements = self.root_element.findall('.//%s' % element_name)
        else:
            elements = parent_element.findall('.//%s' % element_name)
        return elements

    def _get_all_child_tags(self, tag_elements=None, element_name='node', exclude_take_value_tags=True):
        """Gets the tag elements that are children of the given nodes

        Parameters
        ----------
        tag_elements: list of nodes
            The list to return all child tags from
        element_name: str
            The name of the XML tag elements. The default is 'node'.
        exclude_take_value_tags: bool
            True if to exclude tags that take values. False, if otherwise. The default is True.

        Returns
        -------
        list
            A list containing the tags that are child nodes.

        """
        child_tags = []
        if tag_elements is None:
            tag_elements = self._get_elements_by_name(element_name)
        for tag_element in tag_elements:
            tag_element_children = self._get_elements_by_name(element_name, tag_element)
            for child_tag_element in tag_element_children:
                tag = self._get_tag_path_from_tag_element(child_tag_element)
                if exclude_take_value_tags and tag[-1] == '#':
                    continue
                child_tags.append(tag)
        return child_tags

    def tag_has_attribute(self, tag, tag_attribute):
        """Checks to see if the tag has a specific attribute.

        Parameters
        ----------
        tag: str
            A tag.
        tag_attribute: str
            A tag attribute.
        Returns
        -------
        bool
            True if the tag has the specified attribute. False, if otherwise.

        """
        if self.dictionaries[tag_attribute].get(tag.lower()):
            return True
        return False

    @staticmethod
    def get_hed_xml_version(hed_xml_file_path):
        """Gets the version number from a HED XML file.

        Parameters
        ----------
        hed_xml_file_path: str
            The path to a HED XML file.
        Returns
        -------
        str
            The version number of the HED XML file.

        """
        root_node = HedDictionary.parse_hed_xml_file(hed_xml_file_path)
        return root_node.attrib[HedDictionary.VERSION_ATTRIBUTE]
