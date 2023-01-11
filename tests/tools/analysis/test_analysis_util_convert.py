import os
import unittest
from pandas import DataFrame
from hed import schema as hedschema
from hed.models import HedTag, HedString, HedGroup
from hed.tools.analysis.analysis_util import hed_to_str


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../data/schema_tests/HED8.1.0.xml'))
        cls.hed_schema = hedschema.load_schema(schema_path)

    def test_convert_list(self):
        pass

    def test_convert_hed_tag(self):
        tag1 = HedTag('Label/Cond1')
        str1 = hed_to_str(tag1)
        self.assertIsInstance(str1, str)
        self.assertEqual(str1, 'Label/Cond1')
        tag2 = HedTag('Label/Cond1', hed_schema=self.hed_schema)
        str2 = hed_to_str(tag2)
        self.assertIsInstance(str2, str)
        self.assertEqual(str2, 'Label/Cond1')
        tag3 = HedTag('Label/Cond1', hed_schema=self.hed_schema)
        tag3.convert_to_canonical_forms(tag3._schema)
        str3 = hed_to_str(tag3)
        self.assertIsInstance(str3, str)
        self.assertEqual(str3, 'Label/Cond1')

    def test_hed_to_str_other(self):
        str1 = hed_to_str(None)
        self.assertFalse(str1)
        str2 = 'test/node1'
        str3 = hed_to_str(str2)
        self.assertIsInstance(str2, str)
        self.assertEqual(str2, str3)
        dict1 = {'first': 'Red'}
        with self.assertRaises(TypeError) as context:
            hed_to_str(dict1)
        self.assertEqual(context.exception.args[0], "ContentsWrongClass")


    def test_hed_to_str_obj(self):
        str_obj1 = HedString('Label/Cond1')
        str1 = hed_to_str(str_obj1)
        self.assertIsInstance(str1, str)
        self.assertEqual(str1, 'Label/Cond1')
        str_obj2 = HedString('Label/Cond1', hed_schema=self.hed_schema)
        str2 = hed_to_str(str_obj2)
        self.assertIsInstance(str2, str)
        self.assertEqual(str2, 'Label/Cond1')
        str_obj3 = HedString('Label/Cond1', hed_schema=self.hed_schema)
        str_obj3.convert_to_canonical_forms(self.hed_schema)
        str3 = hed_to_str(str_obj3)
        self.assertIsInstance(str3, str)
        self.assertEqual(str3, 'Label/Cond1')
        str_obj4 = HedString('(Label/Cond1, Offset), Red', hed_schema=self.hed_schema)
        str4 = hed_to_str(str_obj4)
        self.assertIsInstance(str4, str)
        self.assertEqual(str4, '(Label/Cond1,Offset),Red')
        str_obj5 = HedString('(Label/Cond1, Offset), Red, (Offset)', hed_schema=self.hed_schema)
        tuples = str_obj5.find_tags(["offset"], recursive=True, include_groups=2)
        str_obj5.remove([tuples[0][0], tuples[1][0]])
        str5 = str(str_obj5)
        self.assertEqual(str5, '(Label/Cond1),Red')
        for tup in tuples:
            if len(tup[1]._children) == 1:
                str_obj5.replace(tup[1], tup[1]._children[0])
        str5a = str(str_obj5)
        self.assertEqual(str5a, 'Label/Cond1,Red')

    def test_hed_to_str_group(self):
        test1 = '(Label/Cond1, Offset)'
        str_obj1 = HedString(test1, hed_schema=self.hed_schema)
        grp1 = str_obj1.children[0]
        str1 = hed_to_str(grp1)
        self.assertIsInstance(str1, str)
        self.assertEqual(str1, '(Label/Cond1,Offset)')

    def test_hed_to_str_list(self):
        list1 = []
        str1 = hed_to_str(list1)
        self.assertIsInstance(str1, str)
        self.assertFalse(str1)
        list2 = [HedString('Label/Cond1', hed_schema=self.hed_schema),
                 HedString("Red,Blue", hed_schema=self.hed_schema)]
        str2 = hed_to_str(list2)
        self.assertIsInstance(str2, str)
        self.assertEqual(str2, 'Label/Cond1,Red,Blue')

    def test_hed_to_str_remove_parentheses(self):
        str_obj1 = HedString('((Label/Cond1))', hed_schema=self.hed_schema)
        str1 = hed_to_str(str_obj1, remove_parentheses=True)
        self.assertIsInstance(str1, str)
        self.assertEqual(str1, '(Label/Cond1)')
        str_obj2 = HedString('(Red, (Label/Cond1))', hed_schema=self.hed_schema)
        str2 = hed_to_str(str_obj2, remove_parentheses=True)
        self.assertIsInstance(str2, str)
        self.assertEqual(str2, '(Red,(Label/Cond1))')
        str_obj3 = HedString('(Label/Cond1)', hed_schema=self.hed_schema)
        str3 = hed_to_str(str_obj3, remove_parentheses=True)
        self.assertIsInstance(str3, str)
        self.assertEqual(str3, 'Label/Cond1')

if __name__ == '__main__':
    unittest.main()
