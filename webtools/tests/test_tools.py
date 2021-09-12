import unittest
from tests.test_web_base import TestWebBase


class Test(TestWebBase):

    def test_get_key_value(self):
        from hedweb.tools import get_key_value

        dict_values = get_key_value('', [])
        self.assertIsInstance(dict_values, dict, "get_key_value should return dict when column_values empty")
        self.assertFalse(dict_values["HED"], "get_key_value HED key should be empty when column_values empty")
        dict_values = get_key_value('', [], categorical=False)
        self.assertIsInstance(dict_values, dict, "get_key_value should return dict when column_values empty")
        self.assertFalse(dict_values["HED"], "get_key_value HED key should be empty when column_values empty")

        dict_values = get_key_value('blech', {'a': 3, 'b': 2, 'c': 1})
        self.assertIsInstance(dict_values, dict, "get_key_value should return dict when column_values not empty")
        self.assertTrue(dict_values["HED"], "get_key_value HED key should be empty when column_values empty")

    def test_get_sidecar_dict(self):
        from hedweb.tools import get_sidecar_dict

        column1 = {'a': 3, 'b': 2, 'c': 1}
        column2 = {'a1': 6, 'b1': 22}
        columns_info = {'column1': column1, 'column2': column2}
        [hed_dict, issues] = get_sidecar_dict(columns_info, {})
        self.assertFalse(hed_dict, "Dictionary is empty of no columns selected")
        self.assertTrue(issues, "Issues is not empty if no columns selected")

        [hed_dict, issues] = get_sidecar_dict(columns_info, {'banana': False})
        self.assertFalse(hed_dict, " get_sidecar_dict: Dictionary is empty of bad column selected")
        self.assertTrue(issues, " get_sidecar_dict: Issues is not empty if bad columns selected")

        [hed_dict, issues] = get_sidecar_dict(columns_info, {'column1': True, 'banana': False, 'apple': True})
        self.assertTrue(hed_dict, " get_sidecar_dict: Dictionary not empty if at least one good column selected")
        self.assertTrue(issues, " get_sidecar_dict: Issues is not empty if at least one bad column selected")
        self.assertEqual(len(issues), 2, "get_sidecar_dict: Same number of issues as bad columns")

        [hed_dict, issues] = get_sidecar_dict(columns_info, {'column1': True, 'column2': False})
        self.assertTrue(hed_dict, "Dictionary not empty if at least one good column selected")
        self.assertFalse(issues, "Issues is empty if good data provided")


if __name__ == '__main__':
    unittest.main()
