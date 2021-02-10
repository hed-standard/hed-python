"""
This module contains the HedSchema class which encapsulates all HED tags, tag attributes, unit classes, and
unit class attributes in a dictionary.

The dictionary is a dictionary of dictionaries. The dictionary names are the list in HedKey.
"""

from defusedxml.ElementTree import parse
import xml
from hed.util.exceptions import HedFileError, HedExceptions


# These need to match the attributes/element name/etc used to load from the xml
class HedKey:
    Default = 'default'
    ExtensionAllowed = 'extensionAllowed'
    # On opening, the extension allowed attribute is propagated down to child tags.
    ExtensionAllowedPropagated = 'extensionAllowedPropagated'
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

    # The next 5 are all case sensitive for the keys.
    SIUnit = 'SIUnit'
    UnitSymbol = 'unitSymbol'

    SIUnitModifier = 'SIUnitModifier'
    SIUnitSymbolModifier = 'SIUnitSymbolModifier'

    # for normal tags, the key to this is the full tag name.  
    # For unit modifiers and such, prefix the tag with the appropriate HedKey.  
    # eg. dictionaries[HedKey.Descriptions][HedKey.SIUnitModifier + 'm']
    Descriptions = 'descriptions'

    # If this is a valid HED3 spec, this allows mapping from short to long.
    ShortTags = 'shortTags'


class HedSchema:
    # List of all dictionary keys that are based off tag attributes.
    # These are the only ones directly loaded from or saved to files.
    TAG_ATTRIBUTE_KEYS = [HedKey.TakesValue, HedKey.IsNumeric, HedKey.Recommended,
                          HedKey.RequireChild, HedKey.RequiredPrefix, HedKey.Unique, HedKey.PredicateType,
                          HedKey.Position, HedKey.UnitClass, HedKey.Default, HedKey.ExtensionAllowed]
    # for these it gets the value of the attribute, rather than treating it as a bool.
    STRING_ATTRIBUTE_DICTIONARY_KEYS = [HedKey.Default, HedKey.UnitClass,
                                        HedKey.Position, HedKey.PredicateType]
    # List of all keys that are for tags, including ones derived from other attributes.
    ALL_TAG_DICTIONARY_KEYS = [*TAG_ATTRIBUTE_KEYS, HedKey.ExtensionAllowedPropagated, HedKey.AllTags]
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
        """Constructor for the HedSchema class.

        Parameters
        ----------
        hed_xml_file_path: str
            The path to a HED XML file.
        Returns
        -------
        HedSchema
            A HedSchema object.

        """
        self.no_duplicate_tags = True
        self.root_element = self._parse_hed_xml_file(hed_xml_file_path)
        self.schema_attributes = self._get_schema_attributes()
        # Used to find parent elements of XML nodes during file parsing
        self._parent_map = {c: p for p in self.root_element.iter() for c in p}
        self._populate_dictionaries()

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
        prefix_string = ""
        if return_detailed_info:
            prefix_string = "\t"
        for tag_name in duplicate_dict:
            if return_detailed_info:
                yield f"Duplicate tag found {tag_name} - {len(duplicate_dict[tag_name])} versions:"
            for tag_entry in duplicate_dict[tag_name]:
                yield f"{prefix_string}{tag_entry}"

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
            if isinstance(short_tag_dict[tag_name], list):
                duplicate_dict[tag_name] = short_tag_dict[tag_name]

        return duplicate_dict

    def get_desc_dict(self):
        """
            Helper to return HedKey.Descriptions dictionary

        Returns
        -------
        descriptions_dict: {str:str}
        """
        return self.dictionaries[HedKey.Descriptions]

    def get_tag_description(self, tag_name, tag_class=HedKey.AllTags):
        """
            If a description exists for the given name, returns it

        Parameters
        ----------
        tag_name : str
            A hed tag name(or unit/unit modifier etc) with proper capitalization.
        tag_class: str, default HedKey.AllTags
            A HedKey indicating what type of description you are asking for.  (All tags, Units, Unit modifier)

        Returns
        -------
        description: str or None
        """
        if tag_class == HedKey.AllTags:
            tag_class = ""
        return self.dictionaries[HedKey.Descriptions].get(tag_class + tag_name, None)

    def get_all_tags(self, return_short_form=False):
        """
        Gets a single copy of all hed terms from the schema, for hed2 or hed3 compatible.

        Returns
        -------
        term_list: [str]
            A list of all terms(short tags) from the schema.
        """
        final_list = []
        if not self.has_duplicate_tags():
            for lower_tag, org_tag in self.short_tag_mapping.items():
                if return_short_form:
                    final_list.append(org_tag.split('/')[-1])
                else:
                    final_list.append(org_tag)
        # Fallback for hed2 style schema validation
        else:
            for lower_tag, org_tag in self.dictionaries[HedKey.AllTags].items():
                if return_short_form:
                    final_list.append(org_tag.split('/')[-1])
                else:
                    final_list.append(org_tag)
        return final_list

    def get_all_tag_attributes(self, tag_name, keys=None):
        """
            Gathers all attributes for a given tag name.  If keys is none, gets all normal hed tag attributes.

        Parameters
        ----------
        tag_name : str
            The name of the tag to check
        keys : [str]
            A list of HedKey tags.

        Returns
        -------
        tag_values: {str: str}
            {key_name : attribute_value}
        """
        if keys is None:
            keys = self.TAG_ATTRIBUTE_KEYS
        attributes = {}
        for key in keys:
            check_name = tag_name
            if key in self.TAG_ATTRIBUTE_KEYS:
                check_name = tag_name.lower()
            if check_name in self.dictionaries[key]:
                # A tag attribute is considered True if the tag name and dictionary value are the same, ignoring capitalization
                if self.dictionaries[key][check_name] and check_name.lower() == self.dictionaries[key][check_name].lower():
                    attributes[key] = True
                else:
                    attributes[key] = self.dictionaries[key][check_name]

        return attributes

    def get_all_forms_of_tag(self, short_tag_to_check):
        """
        Given a short tag, return all the longer versions of it.  Always returns empty list if not a valid HED3G schema.

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
        except (KeyError, TypeError):
            return []

        split_tags = tag_entry.lower().split("/")
        final_tag = ""
        all_forms = []
        for tag in reversed(split_tags):
            final_tag = tag + "/" + final_tag
            all_forms.append(final_tag)

        return all_forms

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
        root_node = HedSchema._parse_hed_xml_file(hed_xml_file_path)
        return root_node.attrib[HedSchema.VERSION_ATTRIBUTE]

    def has_duplicate_tags(self):
        """
        Returns True if this is a valid hed3 schema with no duplicate short tags.

        Returns
        -------
        bool
            Returns True if this is a valid hed3 schema with no duplicate short tags.
        """
        return not self.no_duplicate_tags

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

    # ===========================================================================
    # Functions below here are for getting the tags from the XML tree
    # and do not need to be called after the constructor is done.
    # ===========================================================================
    @staticmethod
    def _parse_hed_xml_file(hed_xml_file_path):
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
            raise HedFileError(HedExceptions.CANNOT_PARSE_XML, e.msg, hed_xml_file_path)
        except FileNotFoundError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, e.strerror, hed_xml_file_path)
        except TypeError as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), hed_xml_file_path)

        return hed_xml_tree.getroot()

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

    def _populate_tag_dictionaries(self):
        """Populates a dictionary of dictionaries associated with tags and their attributes.

        Parameters
        ----------

        Returns
        -------
        {}
            A dictionary of dictionaries that has been populated with dictionaries associated with tag attributes.

        """
        for dict_key in HedSchema.TAG_ATTRIBUTE_KEYS:
            tags, tag_elements = self._get_tags_by_attribute(dict_key)
            if HedKey.ExtensionAllowed == dict_key:
                child_tags = self._get_all_child_tags(tag_elements)
                child_tags_dictionary = self._string_list_to_lowercase_dictionary(child_tags)
                tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
                tag_dictionary.update(child_tags_dictionary)
                self.dictionaries[HedKey.ExtensionAllowedPropagated] = tag_dictionary
                tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
            elif dict_key in self.STRING_ATTRIBUTE_DICTIONARY_KEYS:
                tag_dictionary = self._create_tag_to_attribute_dictionary(tags, tag_elements, dict_key)
            else:
                tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
            self.dictionaries[dict_key] = tag_dictionary

        # Finally handle the "special case" of all tags.
        tags, tag_elements = self._get_all_tags()
        tag_dictionary = self._string_list_to_lowercase_dictionary(tags)
        self.dictionaries[HedKey.Descriptions] = self._get_element_desc(tags, tag_elements)
        self.dictionaries[HedKey.AllTags] = tag_dictionary

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
        Gets all unit modifier definitions from the schema.

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
            unit_modifier_desc = self._get_element_tag_value(unit_modifier_element, "description")
            if unit_modifier_desc:
                self.dictionaries[HedKey.Descriptions][HedKey.SIUnitModifier + unit_modifier_name] = unit_modifier_desc
            for unit_modifier_key in self.UNIT_MODIFIER_DICTIONARY_KEYS:
                self.dictionaries[unit_modifier_key][unit_modifier_name] = unit_modifier_element.get(unit_modifier_key)

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
                # if it's a takes value tag, we should also include the parent.
                short_tag = split_tags[-2] + "/#"
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
            for dict_key in self.ALL_TAG_DICTIONARY_KEYS:
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
            element_desc = self._get_element_tag_value(unit_class_element, "description")
            if element_desc:
                self.dictionaries[HedKey.Descriptions][HedKey.Units + element_name] = element_desc
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
            unit_class_desc = self._get_element_tag_value(unit_class_element, "description")
            default_unit = unit_class_element.get(self.DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE)
            if default_unit is None:
                self.dictionaries[HedKey.DefaultUnits][unit_class_element_name] = \
                    unit_class_element.attrib[HedSchema.DEFAULT_UNIT_FOR_OLD_UNIT_CLASS_ATTRIBUTE]
            else:
                self.dictionaries[HedKey.DefaultUnits][unit_class_element_name] = default_unit

    def _create_tag_to_attribute_dictionary(self, tag_list, tag_element_list, attribute_name):
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
        element = element.find(tag_name)
        if element is not None:
            return element.text
        return ""

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

    def _get_schema_attributes(self):
        """
            Gets the schema attributes form the XML root node

        Returns
        -------
        attribute_dict: {str: str}

        """
        return self.root_element.attrib

    def _get_tags_by_attribute(self, attribute_name):
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

    def _get_all_tags(self, tag_element_name='node'):
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

    def _get_element_desc(self, tags, tag_elements):
        """
            Create a dictionary of descriptions for the given tags and elements

        Parameters
        ----------
        tags : [str]
            The list of tags to get descriptions for
        tag_elements : [Element]
            The matching list of XML elements to get descriptions from
        Returns
        -------
        desc_dict: {str: str}
            {tag : description} for any tags that have one.
        """
        tags_desc = {}
        for tag, tag_element in zip(tags, tag_elements):
            for child in tag_element:
                if child.tag == "description":
                    tags_desc[tag] = child.text
        return tags_desc

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
        for tag_element in tag_elements:
            tag_element_children = self._get_elements_by_name(element_name, tag_element)
            for child_tag_element in tag_element_children:
                tag = self._get_tag_path_from_tag_element(child_tag_element)
                if exclude_take_value_tags and tag[-1] == '#':
                    continue
                child_tags.append(tag)
        return child_tags

