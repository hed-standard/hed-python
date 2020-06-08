import random
import unittest
import os
import defusedxml
from defusedxml.lxml import parse

from hedvalidation.hed_dictionary import HedDictionary


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        cls.hed_dictionary = HedDictionary(cls.hed_xml)
        cls.unit_class_tag = 'unitClass'
        cls.tag_attributes = ['default', 'extensionAllowed', 'isNumeric', 'position', 'predicateType',
                              'recommended', 'required', 'requireChild', 'takesValue', 'unique', 'unitClass']
        cls.default_tag_attribute = 'default'
        cls.string_list = ['This/Is/A/Tag', 'This/Is/Another/Tag']

    def test_find_root_element(self):
        root_element = self.hed_dictionary._find_root_element(self.hed_xml)
        self.assertIsInstance(root_element, defusedxml.lxml.RestrictedElement)

    def test_get_parent_tag_name(self):
        root_element = self.hed_dictionary._find_root_element(self.hed_xml)
        nodes = root_element.xpath('.//node')
        random_node = random.randint(2, len(nodes) - 1)
        tag_element = nodes[random_node]
        parent_tag_name = self.hed_dictionary._get_parent_tag_name(tag_element)
        self.assertIsInstance(parent_tag_name, str)
        self.assertTrue(parent_tag_name)

    def test__get_tag_from_tag_element(self):
        root_element = self.hed_dictionary.get_root_element()
        nodes = root_element.xpath('.//node')
        random_node = random.randint(2, len(nodes) - 1)
        tag_element = nodes[random_node]
        tag_name = self.hed_dictionary._get_tag_path_from_tag_element(tag_element)
        self.assertIsInstance(tag_name, str)
        self.assertTrue(tag_name)

    def test_get_tag_path_from_tag_element(self):
        root_element = self.hed_dictionary.get_root_element()
        tag_elements = root_element.xpath('.//node')
        random_node = random.randint(2, len(tag_elements) - 1)
        tag_element = tag_elements[random_node]
        tag = self.hed_dictionary._get_tag_path_from_tag_element(tag_element)
        self.assertIsInstance(tag, str)
        self.assertTrue(tag)

    def test_get_all_ancestor_tag_names(self):
        root_element = self.hed_dictionary.get_root_element()
        nodes = root_element.xpath('.//node')
        random_node = random.randint(2, len(nodes) - 1)
        tag_element = nodes[random_node]
        all_ancestor_tags = self.hed_dictionary._get_ancestor_tag_names(tag_element)
        self.assertIsInstance(all_ancestor_tags, list)
        self.assertTrue(all_ancestor_tags)

    def test_get_tags_by_attribute(self):
        for tag_attribute in self.tag_attributes:
            tags, tag_elements = self.hed_dictionary.get_tags_by_attribute(tag_attribute)
            self.assertIsInstance(tags, list)

    def test_string_list_2_lowercase_dictionary(self):
        lowercase_dictionary = self.hed_dictionary._string_list_to_lowercase_dictionary(self.string_list)
        self.assertIsInstance(lowercase_dictionary, dict)
        self.assertTrue(lowercase_dictionary)

    def test_get_elements_by_attribute(self):
        for tag_attribute in self.tag_attributes:
            elements = self.hed_dictionary._get_elements_by_attribute(tag_attribute)
            self.assertIsInstance(elements, list)

    def test_get_elements_by_name(self):
        unit_class_elements = self.hed_dictionary._get_elements_by_name(self.unit_class_tag)
        self.assertIsInstance(unit_class_elements, list)

    def test_get_all_tags(self):
        tags, tag_elements = self.hed_dictionary.get_all_tags()
        self.assertIsInstance(tags, list)
        self.assertIsInstance(tag_elements, list)

    def test_populate_dictionaries(self):
        self.hed_dictionary._populate_dictionaries()
        for hed_dictionary_key in self.hed_dictionary.dictionaries:
            self.assertIsInstance(self.hed_dictionary.dictionaries[hed_dictionary_key], dict)

    def test_get_all_child_tags(self):
        child_tags = self.hed_dictionary._get_all_child_tags()
        child_tags_with_take_value_tags = self.hed_dictionary._get_all_child_tags(exclude_take_value_tags=False)
        self.assertIsInstance(child_tags, list)
        self.assertIsInstance(child_tags_with_take_value_tags, list)
        self.assertNotEqual(len(child_tags), len(child_tags_with_take_value_tags))

    def test_tag_has_attribute(self):
        dictionaries = self.hed_dictionary.get_dictionaries()
        for tag_attribute in self.tag_attributes:
            tag_attribute_keys = list(dictionaries[tag_attribute].keys())
            if tag_attribute_keys:
                tag = tag_attribute_keys[0]
                tag_has_attribute = self.hed_dictionary.tag_has_attribute(tag, tag_attribute)
                self.assertTrue(tag_has_attribute)

    def test_get_dictionary(self):
        dictionaries = self.hed_dictionary.get_dictionaries()
        self.assertIsInstance(dictionaries, dict)

    def test_get_root_element(self):
        root_element = self.hed_dictionary.get_root_element()
        self.assertIsInstance(root_element, defusedxml.lxml.RestrictedElement)

    def test_get_hed_xml_version(self):
        hed_version = HedDictionary.get_hed_xml_version(self.hed_xml)
        self.assertIsInstance(hed_version, str)

if __name__ == '__main__':
    unittest.main()
