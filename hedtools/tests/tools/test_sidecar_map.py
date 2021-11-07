import os
import unittest
from hed.tools.sidecar_map import SidecarMap
from hed.tools.map_utils import get_new_dataframe
from hed.errors.exceptions import HedFileError


class Test(unittest.TestCase):

    def test_flatten(self):
        sr = SidecarMap()
        sidecar1 = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"}, "b": "blech2"}
        df1 = sr.flatten(sidecar1)
        self.assertEqual(9, len(df1), "flatten should return a dataframe with correct number of rows")
        self.assertEqual(2, len(df1.columns), "flatten should return a dataframe with 2 columns")

    def test_flatten_with_array(self):
        sr = SidecarMap()
        sidecar1 = {"a": {"c": ["blech3", "blech3a"], "d": "blech4", "e": "blech5"}, "b": "blech2"}
        try:
            sr.flatten(sidecar1)
        except HedFileError:
            pass
        except Exception:
            self.fail('process threw the wrong exception when array included in JSON')
        else:
            self.fail('process should have thrown a HedFileError when array included in JSON')

    def test_flatten_sidecar_with_empty(self):
        sr = SidecarMap()
        # top level value is empty
        sidecar1 = {"a": {"c": "blech3", "d": "blech4", "e": "blech5"}, "b": "",
                    "af": {"c": {"af": "blech6"}, "df_new": "blech7"}}
        df1 = sr.flatten(sidecar1)
        self.assertEqual(12, len(df1), "flatten should return a dataframe with correct number of rows")
        self.assertEqual(2, len(df1.columns), "flatten should return a dataframe with 2 columns")

        # other value is empty
        sidecar2 = {"a": {"c": "blech3", "d": "blech4", "e": "blech5"}, "b": "blech2",
                    "af": {"c": {"af": "blech6"}, "df_new": ""}}
        df2 = sr.flatten(sidecar2)
        self.assertEqual(12, len(df2), "flatten should return a dataframe with correct number of rows")
        self.assertEqual(2, len(df2.columns), "flatten should return a dataframe with 2 columns")

    def test_flatten_col(self):
        sr = SidecarMap()
        column_dict1 = {"a": "blech1", "b": "blech2"}
        col_keys1, col_values1 = sr.flatten_col("tell", column_dict1)
        self.assertEqual(len(col_keys1), len(column_dict1.keys()) + 2,
                         "flatten_col simple dictionary append should have a header key and footer key")
        self.assertEqual(len(col_keys1), len(col_values1),
                         "flatten_col column keys and values should be of the same length")
        self.assertEqual(col_values1[0], 'n/a', "flatten_col header key values should be n/a")
        col_keys1a, col_values1a = sr.flatten_col("tell", column_dict1, append_header=False)
        self.assertEqual(len(col_keys1a), len(column_dict1.keys()) + 1,
                         "flatten_col simple dictionary no append should have a header key and no footer key")
        self.assertEqual(len(col_keys1a), len(col_values1a),
                         "flatten_col column keys and values should be of the same length")
        self.assertEqual(col_values1a[0], 'n/a', "flatten_col header key values should be n/a")

    def test_flatten_col_dict(self):
        # Test 1 level of dictionary
        sr = SidecarMap()
        column_dict1 = {"a": "blech1", "b": "blech2"}
        [keys1, values1] = sr.flatten_col_dict(column_dict1)
        self.assertEqual(2, len(keys1), "flatten_col_dict should return keys for each element dictionary")
        self.assertEqual(2, len(values1), "flatten_col_dict should return values for each element dictionary")

        # Test 2 levels of dictionary
        column_dict2 = {"a": {"c": "blech3", "d": "blech4", "e": "blech5"}, "b": "blech2"}
        [keys2, values2] = sr.flatten_col_dict(column_dict2)
        self.assertEqual(6, len(keys2), "flatten_col_dict should return keys for each element + 2 for header")
        self.assertEqual(6, len(values2), "flatten_col_dict should return values for each element + 2 for header")
        column_dict3 = {"a": {"c": "blech3", "d": "blech4", "e": "blech5"}, "b": "blech2",
                        "af": {"c": {"af": "blech6"}, "df_new": "blech7"},
                        "eg": {"ef": "blech8", "eh": {"eg": "blech9"}}}
        [keys3, values3] = sr.flatten_col_dict(column_dict3)
        self.assertEqual(18, len(keys3), "flatten_col_dict should return keys for each element + 2 for each header")
        self.assertEqual(18, len(values3), "flatten_col_dict should return values for each element + 2 for each header")

    def test_flatten_hed(self):
        sr = SidecarMap()
        # One categorical column
        sidecar1 = {"a_col": {"HED": {"b": "Label/B", "c": "Label/C"}}}
        df1 = sr.flatten_hed(sidecar1)
        self.assertEqual(len(df1), 3, "flatten_hed dataframe should have 1 more entry than HED entries for dictionary")
        self.assertEqual(len(df1.columns), 2, "flatten_hed dataframe should have 2 columns")
        self.assertEqual(df1.iloc[1]['column'], 'b', "flatten_hed dataframe should have right value in key")

        # One value column
        sidecar2 = {"a_col": {"HED": "Label/#"}}
        df2 = sr.flatten_hed(sidecar2)
        self.assertEqual(len(df2), 1, "flatten_hed dataframe should have same number of entries as dictionary")
        self.assertEqual(len(df2.columns), 2, "flatten_hed dataframe should have 2 columns")
        self.assertEqual(df2.iloc[0]['column'], '_*_a_col_*_', "flatten_hed dataframe should have right value in key")

        # A combination with other columns
        sidecar3 = {"a_col": {"HED": {"b": "Label/B", "c": "Label/C"}, "d": {"a1": "b1"}}, "b_col": {"HED": "Label/#"}}
        df3 = sr.flatten_hed(sidecar3)
        self.assertEqual(len(df3), 4,
                         "flatten_hed dataframe should have 1 more entries than HED entries for dictionary")
        self.assertEqual(len(df3.columns), 2, "flatten_hed dataframe should have 2 columns")
        self.assertEqual(df3.iloc[0]['column'], '_*_a_col_*_', "flatten_hed dataframe should have right value in key")
        self.assertEqual(df3.iloc[3]['column'], '_*_b_col_*_', "flatten_hed dataframe should have right value in key")

    def test_get_marked_key(self):
        sr = SidecarMap()
        marked1 = sr.get_marked_key("a_b", 1)
        self.assertEqual(marked1, "_*_a_b_*_", "get_marked_key returns right level 1 value")
        marked2 = sr.get_marked_key("a_b", 2)
        self.assertEqual(marked2, "__*__a_b__*__", "get_marked_key returns right level 2 value")
        marked3 = sr.get_marked_key("a_b", 0)
        self.assertEqual(marked3, "a_b", "get_marked_key returns right level 0 value")
        marked4 = sr.get_marked_key("", 1)
        self.assertEqual(marked4, "_*__*_", "get_marked_key returns right empty key marked value")

    def test_get_unmarked_key(self):
        sr = SidecarMap()
        unmarked1 = sr.get_unmarked_key("_*_a_b_*_")
        self.assertEqual(unmarked1, "a_b", "get_unmarked_key returns right level 1 value")
        marked2 = sr.get_unmarked_key("__*__a_b__*__")
        self.assertEqual(marked2, "a_b", "get_unmarked_key returns right level 2 value")
        marked3 = sr.get_unmarked_key("a_b")
        self.assertEqual(marked3, "a_b", "get_marked_key returns right level 0 unmarked value")
        marked4 = sr.get_unmarked_key("_*__*_")
        self.assertEqual(marked4, None, "get_marked_key returns None when no key")
        marked5 = sr.get_unmarked_key("___*__*_")
        self.assertEqual(marked5, None, "get_marked_key returns None when invalid")

    def test_unflatten(self):
        sr = SidecarMap()
        sidecar1 = {"a": "blech1", "d": "blech4", "e": "blech5"}
        df1 = sr.flatten(sidecar1)
        unflat1 = sr.unflatten(df1)
        self.assertEqual(sidecar1, unflat1, "unflatten should unflatten when sidecar unnested")
        sidecar2 = {"a": {"c1": "blech3", "c2": "blech3a"}, "d": "apple"}
        df2 = sr.flatten(sidecar2)
        unflat2 = sr.unflatten(df2)
        self.assertEqual(sidecar2, unflat2, "unflatten should unflatten when sidecar has single dictionary")
        sidecar3 = {"b": "banana", "a": {"c1": "blech3", "c2": "blech3a"}, "d": "apple"}
        df3 = sr.flatten(sidecar3)
        unflat3 = sr.unflatten(df3)
        self.assertEqual(sidecar3, unflat3, "unflatten should unflatten when sidecar has embedded dictionary")
        sidecar4 = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"}, "b": "blech2"}
        df4 = sr.flatten(sidecar4)
        unflat4 = sr.unflatten(df4)
        self.assertEqual(sidecar4, unflat4, "unflatten should unflatten when sidecar has nested dictionaries")

    def test_unflatten_hed(self):
        sr = SidecarMap()
        sidecar1 = {"a_col": {"HED": {"b": "Label/B", "c": "Label/C"}}}
        df1 = sr.flatten_hed(sidecar1)
        undf1 = sr.unflatten_hed(df1)
        self.assertEqual(len(undf1.keys()), 1, "unflatten_hed dictionary should unpack correctly")
        self.assertTrue("a_col" in undf1.keys(), "The correct key is recovered")

        # One value column
        sidecar2 = {"a_col": {"HED": "Label/#"}}
        df2 = sr.flatten_hed(sidecar2)
        undf2 = sr.unflatten_hed(df2)
        self.assertEqual(len(undf2.keys()), 1, "unflatten_hed dictionary should unpack correctly")
        self.assertTrue("a_col" in undf2.keys(), "The correct key is recovered")

        # A combination with other columns
        sidecar3 = {"a_col": {"HED": {"b": "Label/B", "c": "Label/C"}, "d": {"a1": "b1"}},
                    "b_col": {"HED": "Label/#"}, "c_col": {"levels": "e"}}
        df3 = sr.flatten_hed(sidecar3)
        undf3 = sr.unflatten_hed(df3)
        self.assertEqual(len(undf3.keys()), 2, "unflatten_hed dictionary should unpack correctly")

    def test_unflatten_hed_from_file(self):
        sr = SidecarMap()
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "../data/sternberg/sternberg_flattened.tsv")
        df = get_new_dataframe(file_path)
        sr.unflatten_hed(df)

    def test_flatten_hed_column_names(self):
        sr = SidecarMap()
        # One categorical column
        sidecar1 = {"a1_col": {"HED": {"b1": "Label/B1", "c1": "Label/C1"}},
                    "a2_col": {"HED": {"b2": "Label/B2", "c2": "Label/C2"}},
                    "a3_col": {"HED": {"b3": "Label/B2", "c3": "Label/C2"}}}
        df1 = sr.flatten_hed(sidecar1)
        self.assertEqual(len(df1), 9, "When all columns are used should have all entries")
        df2 = sr.flatten_hed(sidecar1, ["a1_col", "a3_col"])
        self.assertEqual(len(df2), 6, "When some columns are used should have appropriate entries")
        self.assertEqual(len(df1.columns), 2, "flatten_hed dataframe should have 2 columns")
        self.assertEqual(df1.iloc[1]['column'], 'b1', "flatten_hed dataframe should have right value in key")
        df2 = sr.flatten_hed(sidecar1, ["a1_col", "a3_col"])
        self.assertEqual(len(df2), 6,
                         "flatten_hed dataframe should have 1 more entry than HED entries for dictionary")
        self.assertEqual(len(df2.columns), 2, "flatten_hed dataframe should have 2 columns")
        self.assertEqual(df2.iloc[1]['column'], 'b1', "flatten_hed dataframe should have right value in key")

    def test_get_key_value(self):
        dict_values = SidecarMap.get_key_value('', [])
        self.assertIsInstance(dict_values, dict, "get_key_value should return dict when column_values empty")
        self.assertFalse(dict_values["HED"], "get_key_value HED key should be empty when column_values empty")
        dict_values = SidecarMap.get_key_value('', [], categorical=False)
        self.assertIsInstance(dict_values, dict, "get_key_value should return dict when column_values empty")
        self.assertFalse(dict_values["HED"], "get_key_value HED key should be empty when column_values empty")

        dict_values = SidecarMap.get_key_value('blech', {'a': 3, 'b': 2, 'c': 1})
        self.assertIsInstance(dict_values, dict, "get_key_value should return dict when column_values not empty")
        self.assertTrue(dict_values["HED"], "get_key_value HED key should be empty when column_values empty")

    def test_get_sidecar_dict(self):
        column1 = {'a': 3, 'b': 2, 'c': 1}
        column2 = {'a1': 6, 'b1': 22}
        columns_info = {'column1': column1, 'column2': column2}
        [hed_dict, issues] = SidecarMap.get_sidecar_dict(columns_info, {})
        self.assertFalse(hed_dict, "Dictionary is empty of no columns selected")
        self.assertTrue(issues, "Issues is not empty if no columns selected")

        [hed_dict, issues] = SidecarMap.get_sidecar_dict(columns_info, {'banana': False})
        self.assertFalse(hed_dict, " get_sidecar_dict: Dictionary is empty of bad column selected")
        self.assertTrue(issues, " get_sidecar_dict: Issues is not empty if bad columns selected")

        [hed_dict, issues] = SidecarMap.get_sidecar_dict(columns_info,
                                                         {'column1': True, 'banana': False, 'apple': True})
        self.assertTrue(hed_dict, " get_sidecar_dict: Dictionary not empty if at least one good column selected")
        self.assertTrue(issues, " get_sidecar_dict: Issues is not empty if at least one bad column selected")
        self.assertEqual(len(issues), 2, "get_sidecar_dict: Same number of issues as bad columns")

        [hed_dict, issues] = SidecarMap.get_sidecar_dict(columns_info, {'column1': True, 'column2': False})
        self.assertTrue(hed_dict, "Dictionary not empty if at least one good column selected")
        self.assertFalse(issues, "Issues is empty if good data provided")


if __name__ == '__main__':
    unittest.main()
