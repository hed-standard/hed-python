import unittest
import pandas as pd


from hed import load_schema_version
from hed.models.df_util import shrink_defs, expand_defs
from hed import DefinitionDict


class TestShrinkDefs(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version()

    def test_shrink_defs_normal(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2)),Event/SomeEvent"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_placeholder(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2)),Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_no_matching_tags(self):
        df = pd.DataFrame({"column1": ["(Event/SomeEvent, Item/SomeItem,Age/25)"]})
        expected_df = pd.DataFrame({"column1": ["(Event/SomeEvent, Item/SomeItem,Age/25)"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_multiple_columns(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2)),Event/SomeEvent"],
                           "column2": ["(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2)),Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"],
                                     "column2": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        result = shrink_defs(df, self.schema, ['column1', 'column2'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_multiple_defs_same_line(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2)),(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2)),Age/30"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Def/TestDefPlaceholder/123,Age/30"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_mixed_tags(self):
        df = pd.DataFrame({"column1": [
            "(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2)),Event/SomeEvent,(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2)),Item/SomeItem,Age/25"]})
        expected_df = pd.DataFrame(
            {"column1": ["Def/TestDefNormal,Event/SomeEvent,Def/TestDefPlaceholder/123,Item/SomeItem,Age/25"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_series_normal(self):
        series = pd.Series(["(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2)),Event/SomeEvent"])
        expected_series = pd.Series(["Def/TestDefNormal,Event/SomeEvent"])
        result = shrink_defs(series, self.schema, None)
        pd.testing.assert_series_equal(result, expected_series)

    def test_shrink_defs_series_placeholder(self):
        series = pd.Series(["(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2)),Item/SomeItem"])
        expected_series = pd.Series(["Def/TestDefPlaceholder/123,Item/SomeItem"])
        result = shrink_defs(series, self.schema, None)
        pd.testing.assert_series_equal(result, expected_series)


class TestExpandDefs(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version()
        self.def_dict = DefinitionDict(["(Definition/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2))",
                                       "(Definition/TestDefPlaceholder/#,(Action/TestDef1/#,Action/TestDef2))"],
                                       hed_schema=self.schema)

    def test_expand_defs_normal(self):
        df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"]})
        expected_df = pd.DataFrame(
            {"column1": ["(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2)),Event/SomeEvent"]})
        result = expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_expand_defs_placeholder(self):
        df = pd.DataFrame({"column1": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": [
            "(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2)),Item/SomeItem"]})
        result = expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_expand_defs_no_matching_tags(self):
        df = pd.DataFrame({"column1": ["(Event/SomeEvent,Item/SomeItem,Age/25)"]})
        expected_df = pd.DataFrame({"column1": ["(Event/SomeEvent,Item/SomeItem,Age/25)"]})
        result = expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_expand_defs_multiple_columns(self):
        df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"],
                           "column2": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        expected_df = pd.DataFrame(
            {"column1": ["(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2)),Event/SomeEvent"],
             "column2": [
                 "(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2)),Item/SomeItem"]})
        result = expand_defs(df, self.schema, self.def_dict, ['column1', 'column2'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_expand_defs_series_normal(self):
        series = pd.Series(["Def/TestDefNormal,Event/SomeEvent"])
        expected_series = pd.Series(["(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2)),Event/SomeEvent"])
        result = expand_defs(series, self.schema, self.def_dict, None)
        pd.testing.assert_series_equal(result, expected_series)

    def test_expand_defs_series_placeholder(self):
        series = pd.Series(["Def/TestDefPlaceholder/123,Item/SomeItem"])
        expected_series = pd.Series(["(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2)),Item/SomeItem"])
        result = expand_defs(series, self.schema, self.def_dict, None)
# <<<<<<< HEAD
#         pd.testing.assert_series_equal(result, expected_series)
# 
# 
# class TestConvertToForm(unittest.TestCase):
#     def setUp(self):
#         self.schema = load_schema_version()
# 
#     def test_convert_to_form_short_tags(self):
#         df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"]})
#         expected_df = pd.DataFrame({"column1": ["Azure,See"]})
#         result = convert_to_form(df, self.schema, "short_tag", ['column1'])
#         pd.testing.assert_frame_equal(result, expected_df)
# 
#     def test_convert_to_form_long_tags(self):
#         df = pd.DataFrame({"column1": ["CSS-color/White-color/Azure,Action/Perceive/See"]})
#         expected_df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"]})
#         result = convert_to_form(df, self.schema, "long_tag", ['column1'])
#         pd.testing.assert_frame_equal(result, expected_df)
# 
#     def test_convert_to_form_series_short_tags(self):
#         series = pd.Series(["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"])
#         expected_series = pd.Series(["Azure,See"])
#         result = convert_to_form(series, self.schema, "short_tag")
#         pd.testing.assert_series_equal(result, expected_series)
# 
#     def test_convert_to_form_series_long_tags(self):
#         series = pd.Series(["CSS-color/White-color/Azure,Action/Perceive/See"])
#         expected_series = pd.Series(["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"])
#         result = convert_to_form(series, self.schema, "long_tag")
#         pd.testing.assert_series_equal(result, expected_series)
# 
#     def test_convert_to_form_multiple_tags_short(self):
#         df = pd.DataFrame({"column1": ["Visual-attribute/Color/CSS-color/White-color/Azure,Biological-item/Anatomical-item/Body-part/Head/Face/Nose,Spatiotemporal-value/Rate-of-change/Acceleration/4.5 m-per-s^2"]})
#         expected_df = pd.DataFrame({"column1": ["Azure,Nose,Acceleration/4.5 m-per-s^2"]})
#         result = convert_to_form(df, self.schema, "short_tag", ['column1'])
#         pd.testing.assert_frame_equal(result, expected_df)
# 
#     def test_convert_to_form_multiple_tags_long(self):
#         df = pd.DataFrame({"column1": ["CSS-color/White-color/Azure,Anatomical-item/Body-part/Head/Face/Nose,Rate-of-change/Acceleration/4.5 m-per-s^2"]})
#         expected_df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Item/Biological-item/Anatomical-item/Body-part/Head/Face/Nose,Property/Data-property/Data-value/Spatiotemporal-value/Rate-of-change/Acceleration/4.5 m-per-s^2"]})
#         result = convert_to_form(df, self.schema, "long_tag", ['column1'])
#         pd.testing.assert_frame_equal(result, expected_df)
# =======
        pd.testing.assert_series_equal(result, expected_series)
# >>>>>>> 5bab6c620505fd4e97629d846a7abfbe68dc150a
