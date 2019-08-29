'''
This module contains the Hed_Dictionary class which encapsulates all HED tags, tag attributes, unit classes, and
unit class attributes in a dictionary. The dictionary is a dictionary of dictionaries. The dictionary names are
'default', 'extensionAllowed', 'isNumeric', 'position', 'predicateType', 'recommended', 'required', 'requireChild',
'tags', 'takesValue', 'unique', 'units', and 'unitClass'.
Created on Sept 21, 2017

@author: Jeremy Cockfield

'''

from defusedxml.lxml import parse;


class HedDictionary:
    DEFAULT_UNIT_ATTRIBUTE = 'default';
    DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE = 'default_units'
    EXTENSION_ALLOWED_ATTRIBUTE = 'extensionAllowed';
    TAG_DICTIONARY_KEYS = ['default', 'extensionAllowed', 'isNumeric', 'position', 'predicateType', 'recommended',
                           'required', 'requireChild', 'tags', 'takesValue', 'unique', 'unitClass'];
    TAGS_DICTIONARY_KEY = 'tags';
    TAG_UNIT_CLASS_ATTRIBUTE = 'unitClass';
    UNIT_CLASS_ELEMENT = 'unitClass';
    UNIT_CLASS_UNITS_ELEMENT = 'units';
    UNIT_CLASS_DICTIONARY_KEYS = ['default_units', 'units'];
    UNITS_ELEMENT = 'units';
    VERSION_ATTRIBUTE = 'version';
    dictionaries = None;
    root_element = None;

    def __init__(self, hed_xml_file_path):
        """Constructor for the Hed_Dictionary class.

        Parameters
        ----------
        hed_xml_file_path: string
            The path to a HED XML file.

        Returns
        -------
        HedDictionary
            A Hed_Dictionary object.

        """
        self.root_element = self._find_root_element(hed_xml_file_path);
        self.dictionaries = self._populate_dictionaries();


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
        dictionary
            A dictionary of dictionaries that contains all of the tags, tag attributes, unit class units, and unit
            class attributes

        """
        return self.dictionaries;

    def _populate_dictionaries(self):
        """Populates a dictionary of dictionaries that contains all of the tags, tag attributes, unit class units, and unit
           class attributes.

        Parameters
        ----------

        Returns
        -------
        dictionary
            A dictionary of dictionaries that contains all of the tags, tag attributes, unit class units, and unit class
            attributes.

        """
        dictionaries = {};
        tag_dictionaries = self._populate_tag_dictionaries();
        unit_class_dictionaries = self._populate_unit_class_dictionaries();
        dictionaries.update(tag_dictionaries);
        dictionaries.update(unit_class_dictionaries);
        return dictionaries;

    def _populate_tag_dictionaries(self):
        """Populates a dictionary of dictionaries associated with tags and their attributes.

        Parameters
        ----------

        Returns
        -------
        dictionary
            A dictionary of dictionaries that has been populated with dictionaries associated with tag attributes.

        """
        tag_dictionaries = {};
        for TAG_DICTIONARY_KEY in HedDictionary.TAG_DICTIONARY_KEYS:
            tags, tag_elements = self.get_tags_by_attribute(TAG_DICTIONARY_KEY);
            if HedDictionary.EXTENSION_ALLOWED_ATTRIBUTE == TAG_DICTIONARY_KEY:
                child_tags = self._get_all_child_tags(tag_elements)
                child_tags_dictionary = self._string_list_2_lowercase_dictionary(child_tags);
                tag_dictionary = self._string_list_2_lowercase_dictionary(tags);
                tag_dictionary.update(child_tags_dictionary);
            elif HedDictionary.DEFAULT_UNIT_ATTRIBUTE == TAG_DICTIONARY_KEY or \
                 HedDictionary.TAG_UNIT_CLASS_ATTRIBUTE == TAG_DICTIONARY_KEY:
                tag_dictionary = self._populate_tag_to_attribute_dictionary(tags, tag_elements, TAG_DICTIONARY_KEY);
            elif HedDictionary.TAGS_DICTIONARY_KEY == TAG_DICTIONARY_KEY:
                tags = self.get_all_tags()[0];
                tag_dictionary = self._string_list_2_lowercase_dictionary(tags);
            else:
                tag_dictionary = self._string_list_2_lowercase_dictionary(tags);
            tag_dictionaries[TAG_DICTIONARY_KEY] = tag_dictionary;
        return tag_dictionaries;

    def _populate_unit_class_dictionaries(self):
        """Populates a dictionary of dictionaries associated with all of the unit classes, unit class units, and unit
           class default units.

        Parameters
        ----------

        Returns
        -------
        dictionary
            A dictionary of dictionaries associated with all of the unit classes, unit class units, and unit class
            default units.

        """
        unit_class_dictionaries = {};
        for UNIT_CLASS_DICTIONARY_KEY in HedDictionary.UNIT_CLASS_DICTIONARY_KEYS:
            unit_class_dictionary = {};
            unit_class_elements = self._get_elements_by_name(HedDictionary.UNIT_CLASS_ELEMENT);
            if HedDictionary.UNITS_ELEMENT == UNIT_CLASS_DICTIONARY_KEY:
                unit_class_dictionary = self._populate_unit_class_units_dictionary(unit_class_elements);
            elif HedDictionary.DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE == UNIT_CLASS_DICTIONARY_KEY:
                unit_class_dictionary = self._populate_unit_class_default_unit_dictionary(unit_class_elements);
            unit_class_dictionaries[UNIT_CLASS_DICTIONARY_KEY] = unit_class_dictionary;
        return unit_class_dictionaries;

    def _populate_unit_class_units_dictionary(self, unit_class_elements):
        """Populates a dictionary that contains unit class units.

        Parameters
        ----------
        unit_class_elements: list
            A list of unit class elements.

        Returns
        -------
        dictionary
            A dictionary that contains all the unit class units.

        """
        unit_class_units_dictionary = {};
        for unit_class_element in unit_class_elements:
            unit_class_element_name = self._get_element_tag_value(unit_class_element);
            unit_class_element_units = self._get_element_tag_value(unit_class_element,
                                                                   HedDictionary.UNIT_CLASS_UNITS_ELEMENT);
            unit_class_units_dictionary[unit_class_element_name] = unit_class_element_units.split(',');
        return unit_class_units_dictionary;

    def _populate_unit_class_default_unit_dictionary(self, unit_class_elements):
        """Populates a dictionary that contains unit class default units.

        Parameters
        ----------
        unit_class_elements: list
            A list of unit class elements.

        Returns
        -------
        dictionary
            A dictionary that contains all the unit class default units.

        """
        unit_class_default_unit_dictionary = {};
        for unit_class_element in unit_class_elements:
            unit_class_element_name = self._get_element_tag_value(unit_class_element);
            unit_class_default_unit_dictionary[unit_class_element_name] = \
                unit_class_element.attrib[HedDictionary.DEFAULT_UNIT_ATTRIBUTE];
        return unit_class_default_unit_dictionary;

    def _populate_tag_to_attribute_dictionary(self, tag_list, tag_element_list, attribute_name):
        """Populates the dictionaries associated with default unit tags in the attribute dictionary.

        Parameters
        ----------
        tag_list: list
            A list containing tags that have a specific attribute.
        tag_element_list: list
            A list containing tag elements that have a specific attribute.
        attribute_name: string
            The name of the attribute associated with the tags and tag elements.

        Returns
        -------
        dictionary
            The attribute dictionary that has been populated with dictionaries associated with tags.

        """
        dictionary = {};
        for index, tag in enumerate(tag_list):
            dictionary[tag.lower()] = tag_element_list[index].attrib[attribute_name];
        return dictionary;

    def _string_list_2_lowercase_dictionary(self, string_list):
        """Converts a string list into a dictionary. The keys in the dictionary will be the lowercase values of the
           strings in the list.

        Parameters
        ----------
        string_list: list
            A list containing string elements.

        Returns
        -------
        dictionary
            A dictionary containing the strings in the list.

        """
        lowercase_dictionary = {};
        for string_element in string_list:
            lowercase_dictionary[string_element.lower()] = string_element;
        return lowercase_dictionary;

    def _find_root_element(self, hed_xml_file_path):
        """Parses a XML file and returns the root element.

        Parameters
        ----------
        hed_xml_file_path: string
            The path to a HED XML file.

        Returns
        -------
        RestrictedElement
            The root element of the HED XML file.

        """
        tree = parse(hed_xml_file_path);
        return tree.getroot();

    def _get_ancestor_tag_names(self, tag_element):
        """Gets all the ancestor tag names of a tag element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        list
            A list containing all of the ancestor tag names of a given tag.

        """
        ancestor_tags = [];
        parent_tag_name = self._get_parent_tag_name(tag_element);
        parent_element = tag_element.getparent();
        while parent_tag_name:
            ancestor_tags.append(parent_tag_name);
            parent_tag_name = self._get_parent_tag_name(parent_element);
            parent_element = parent_element.getparent();
        return ancestor_tags;

    def _get_element_tag_value(self, element, tag_name='name'):
        """Gets the value of the element's tag.

        Parameters
        ----------
        element: Element
            A element in the HED XML file.
        tag_name: string
            The name of the XML element's tag. The default is 'name'.

        Returns
        -------
        string
            The value of the element's tag. If the element doesn't have the tag then it will return an empty string.

        """
        return element.find(tag_name).text;

    def _get_parent_tag_name(self, tag_element):
        """Gets the name of the tag parent element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        string
            The name of the tag element's parent. If there is no parent tag then an empty string is returned.

        """
        parent_tag_element = tag_element.getparent();
        if parent_tag_element is not None:
            return parent_tag_element.findtext('name');
        else:
            return '';

    def _get_tag_path_from_tag_element(self, tag_element):
        """Gets the tag path from a given tag element.

        Parameters
        ----------
        tag_element: Element
            A tag element in the HED XML file.

        Returns
        -------
        string
            A tag path which is typically referred to as a tag. The tag and it's ancestor tags will be separated by /'s.

        """
        ancestor_tag_names = self._get_ancestor_tag_names(tag_element);
        ancestor_tag_names.insert(0, self._get_element_tag_value(tag_element));
        ancestor_tag_names.reverse();
        return '/'.join(ancestor_tag_names);

    def get_tags_by_attribute(self, attribute_name):
        """Gets the tag that have a specific attribute.

        Parameters
        ----------
        attribute_name: string
            The name of the attribute associated with the tags.

        Returns
        -------
        tuple
            A tuple containing tags and tag elements that have a specified attribute.

        """
        tags = [];
        tag_elements = self.root_element.xpath('.//node[@%s]' % attribute_name);
        for attribute_tag_element in tag_elements:
            tag = self._get_tag_path_from_tag_element(attribute_tag_element);
            tags.append(tag);
        return tags, tag_elements;


    def get_all_tags(self, tag_element_name='node'):
        """Gets the tags that have a specific attribute.

        Parameters
        ----------
        tag_element_name: string
            The XML tag name of the tag elements. The default is 'node'.

        Returns
        -------
        tuple
            A tuple containing all the tags and tag elements in the XML file.

        """
        tags = [];
        tag_elements = self.root_element.xpath('.//%s' % tag_element_name);
        for tag_element in tag_elements:
            tag = self._get_tag_path_from_tag_element(tag_element);
            tags.append(tag);
        return tags, tag_elements;

    def _get_elements_by_attribute(self, attribute_name, element_name='node'):
        """Gets the elements that have a specific attribute.

        Parameters
        ----------
        attribute_name: string
            The name of the attribute associated with the element.
        element_name: string
            The name of the XML element tag name. The default is 'node'.

        Returns
        -------
        list
            A list containing elements that have a specified attribute.

        """
        return self.root_element.xpath('.//%s[@%s]' % (element_name, attribute_name));

    def _get_elements_by_name(self, element_name='node', parent_element=None):
        """Gets the elements that have a specific element name.

        Parameters
        ----------
        element_name: string
            The name of the element. The default is 'node'.
        parent_element: string
            The parent element. The default is 'None'. If a parent element is specified then only the children of the
            parent will be returned with the given 'element_name'. If not specified the root element will be the parent.

        Returns
        -------
        list
            A list containing elements that have a specific element name.

        """
        if parent_element is None:
            elements = self.root_element.xpath('.//%s' % element_name);
        else:
            elements = parent_element.xpath('.//%s' % element_name);
        return elements;

    def _get_all_child_tags(self, tag_elements=None, element_name='node', exclude_take_value_tags=True):
        """Gets the tag elements that are children of the given nodes

        Parameters
        ----------
        tag_elements: list of nodes
            The list to return all child tags from
        element_name: string
            The name of the XML tag elements. The default is 'node'.
        exclude_take_value_tags: boolean
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
        tag: string
            A tag.
        tag_attribute: string
            A tag attribute.
        Returns
        -------
        boolean
            True if the tag has the specified attribute. False, if otherwise.

        """
        if tag.lower() in self.dictionaries[tag_attribute]:
                return True;
        return False;

    @staticmethod
    def get_hed_xml_version(hed_xml_file_path):
        """Gets the version number from a HED XML file.

        Parameters
        ----------
        hed_xml_file_path: string
            The path to a HED XML file.
        Returns
        -------
        string
            The version number of the HED XML file.

        """
        tree = parse(hed_xml_file_path);
        root_node = tree.getroot();
        return root_node.attrib[HedDictionary.VERSION_ATTRIBUTE];