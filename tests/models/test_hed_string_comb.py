import unittest
import os

from hed import schema
from hed.models import HedString
from hed.models import HedTag
from hed.models.hed_string_comb import HedStringComb
import copy


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "schema_test_data/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)

    def test_remove_groups(self):
        string1 = HedString("Item/Object", self.hed_schema)
        string2 = HedString("Event, (Event, Square)", self.hed_schema)
        comb_string = HedStringComb([string1, string2])
        self.assertEqual(len(comb_string.get_all_tags()), 4)
        self.assertEqual(len(string1.get_all_tags()), 1)
        self.assertEqual(len(string2.get_all_tags()), 3)
        tags = comb_string.find_tags(["Object".lower()], include_groups=0)
        comb_string.remove_groups(tags)
        self.assertEqual(len(string1.get_all_tags()), 0)
        self.assertEqual(len(string2.get_all_tags()), 3)
        self.assertEqual(len(comb_string.get_all_tags()), 3)

        tags = comb_string.find_tags(["Event".lower()], recursive=True, include_groups=0)
        comb_string.remove_groups(tags)
        self.assertEqual(len(string2.get_all_tags()), 1)
        self.assertEqual(len(comb_string.get_all_tags()), 1)

        tags = comb_string.find_tags(["Square".lower()], recursive=True, include_groups=0)
        comb_string.remove_groups(tags)
        self.assertEqual(len(string2.get_all_tags()), 0)
        self.assertEqual(len(comb_string.get_all_tags()), 0)

    def test_replace_tag(self):
        string1 = HedString("Item/Object", self.hed_schema)
        string2 = HedString("Event, (Event, Square)", self.hed_schema)
        new_contents = HedTag("Def/TestTag", hed_schema=self.hed_schema)
        comb_string = HedStringComb([string1, string2])
        self.assertEqual(len(string1.get_all_tags()), 1)
        self.assertEqual(len(string2.get_all_tags()), 3)
        self.assertEqual(len(comb_string.get_all_tags()), 4)
        tags = comb_string.find_tags(["Object".lower()], include_groups=0)
        comb_string.replace_tag(tags[0], copy.copy(new_contents))

        self.assertEqual(len(string1.get_all_tags()), 1)
        self.assertEqual(len(string2.get_all_tags()), 3)
        self.assertEqual(len(comb_string.get_all_tags()), 4)

        tags = comb_string.find_tags(["Event".lower()], include_groups=0)
        comb_string.replace_tag(tags[0], copy.copy(new_contents))
        self.assertEqual(len(string1.get_all_tags()), 1)
        self.assertEqual(len(string2.get_all_tags()), 3)
        self.assertEqual(len(comb_string.get_all_tags()), 4)

        tag_group = comb_string.find_tags(["Event".lower()], recursive=True, include_groups=2)
        tag, group = tag_group[0][0], tag_group[0][1]
        group.replace_tag(tag, copy.copy(new_contents))
        self.assertEqual(len(string1.get_all_tags()), 1)
        self.assertEqual(len(string2.get_all_tags()), 3)
        self.assertEqual(len(comb_string.get_all_tags()), 4)

