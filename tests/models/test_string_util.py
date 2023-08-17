import unittest
from hed import HedString, load_schema_version
from hed.models.string_util import split_base_tags, split_def_tags
import copy


class TestHedStringSplit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version()

    def check_split_base_tags(self, hed_string, base_tags, expected_string, expected_string2):
        # Test case 1: remove_group=False
        hed_string_copy = copy.deepcopy(hed_string)
        remaining_hed, found_hed = split_base_tags(hed_string_copy, base_tags, remove_group=False)

        self.assertIsInstance(remaining_hed, HedString)
        self.assertIsInstance(found_hed, HedString)
        self.assertEqual(str(remaining_hed), expected_string)

        self.assertTrue(all(tag in [str(t) for t in found_hed.get_all_tags()] for tag in base_tags))
        self.assertTrue(all(tag not in [str(t) for t in remaining_hed.get_all_tags()] for tag in base_tags))

        # Test case 2: remove_group=True
        hed_string_copy = copy.deepcopy(hed_string)
        remaining_hed, found_hed = split_base_tags(hed_string_copy, base_tags, remove_group=True)

        self.assertIsInstance(remaining_hed, HedString)
        self.assertIsInstance(found_hed, HedString)
        self.assertEqual(str(remaining_hed), expected_string2)

        self.assertTrue(all(tag in [str(t) for t in found_hed.get_all_tags()] for tag in base_tags))
        self.assertTrue(all(tag not in [str(t) for t in remaining_hed.get_all_tags()] for tag in base_tags))

    def test_case_1(self):
        hed_string = HedString('Memorize,Action,Area', self.schema)
        base_tags = ['Area', 'Action']
        expected_string = 'Memorize'
        expected_string2 = 'Memorize'
        self.check_split_base_tags(hed_string, base_tags, expected_string, expected_string2)

    def test_case_2(self):
        hed_string = HedString('Area,LightBlue,Handedness', self.schema)
        base_tags = ['Area', 'LightBlue']
        expected_string = 'Handedness'
        expected_string2 = 'Handedness'
        self.check_split_base_tags(hed_string, base_tags, expected_string, expected_string2)

    def test_case_3(self):
        hed_string = HedString('(Wink,Communicate),Face,HotPink', self.schema)
        base_tags = ['Wink', 'Face']
        expected_string = '(Communicate),HotPink'
        expected_string2 = "HotPink"
        self.check_split_base_tags(hed_string, base_tags, expected_string, expected_string2)

    def test_case_4(self):
        hed_string = HedString('(Area,(LightBlue,Handedness,(Wink,Communicate))),Face,HotPink', self.schema)
        base_tags = ['Area', 'LightBlue']
        expected_string = '((Handedness,(Wink,Communicate))),Face,HotPink'
        expected_string2 = 'Face,HotPink'
        self.check_split_base_tags(hed_string, base_tags, expected_string, expected_string2)

    def test_case_5(self):
        hed_string = HedString('(Memorize,(Action,(Area,LightBlue),Handedness),Wink)', self.schema)
        base_tags = ['Area', 'LightBlue']
        expected_string = '(Memorize,(Action,Handedness),Wink)'
        expected_string2 = '(Memorize,(Action,Handedness),Wink)'
        self.check_split_base_tags(hed_string, base_tags, expected_string, expected_string2)

class TestHedStringSplitDef(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version()

    def check_split_def_tags(self, hed_string, def_names, expected_string, expected_string2):
        # Test case 1: remove_group=False
        hed_string_copy1 = copy.deepcopy(hed_string)
        remaining_hed1, found_hed1 = split_def_tags(hed_string_copy1, def_names, remove_group=False)

        self.assertIsInstance(remaining_hed1, HedString)
        self.assertIsInstance(found_hed1, HedString)
        self.assertEqual(str(remaining_hed1), expected_string)

        self.assertTrue(all(tag.short_base_tag == "Def" for tag in found_hed1.get_all_tags()))
        self.assertTrue(all(tag.short_base_tag != "Def" for tag in remaining_hed1.get_all_tags()))

        # Test case 2: remove_group=True
        hed_string_copy2 = copy.deepcopy(hed_string)
        remaining_hed2, found_hed2 = split_def_tags(hed_string_copy2, def_names, remove_group=True)

        self.assertIsInstance(remaining_hed2, HedString)
        self.assertIsInstance(found_hed2, HedString)
        self.assertEqual(str(remaining_hed2), expected_string2)

        #self.assertTrue(all(tag.short_base_tag == "Def" for tag in found_hed.get_all_tags()))
        self.assertTrue(all(tag.short_base_tag != "Def" for tag in remaining_hed2.get_all_tags()))

    def test_case_1(self):
        hed_string = HedString('Memorize,Action,def/CustomTag1', self.schema)
        def_names = ['CustomTag1']
        expected_string = 'Memorize,Action'
        expected_string2 = 'Memorize,Action'
        self.check_split_def_tags(hed_string, def_names, expected_string, expected_string2)

    def test_case_2(self):
        hed_string = HedString('def/CustomTag1,LightBlue,def/CustomTag2/123', self.schema)
        def_names = ['CustomTag1', 'CustomTag2']
        expected_string = 'LightBlue'
        expected_string2 = 'LightBlue'
        self.check_split_def_tags(hed_string, def_names, expected_string, expected_string2)

    def test_case_3(self):
        hed_string = HedString('(def/CustomTag1,Communicate),Face,def/CustomTag3/abc', self.schema)
        def_names = ['CustomTag1', 'CustomTag3']
        expected_string = '(Communicate),Face'
        expected_string2 = 'Face'
        self.check_split_def_tags(hed_string, def_names, expected_string, expected_string2)

    def test_case_4(self):
        hed_string = HedString('(def/CustomTag1,(LightBlue,def/CustomTag2/123,(Wink,Communicate))),Face,def/CustomTag3/abc', self.schema)
        def_names = ['CustomTag1', 'CustomTag2', 'CustomTag3']
        expected_string = '((LightBlue,(Wink,Communicate))),Face'
        expected_string2 = 'Face'
        self.check_split_def_tags(hed_string, def_names, expected_string, expected_string2)

    def test_case_5(self):
        hed_string = HedString('(Memorize,(Action,(def/CustomTag1,LightBlue),def/CustomTag2/123),Wink)', self.schema)
        def_names = ['CustomTag1', 'CustomTag2']
        expected_string = '(Memorize,(Action,(LightBlue)),Wink)'
        expected_string2 = '(Memorize,Wink)'
        self.check_split_def_tags(hed_string, def_names, expected_string, expected_string2)


if __name__ == '__main__':
    unittest.main()