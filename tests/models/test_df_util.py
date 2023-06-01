import unittest
import pandas as pd


from hed import load_schema_version
from hed.models.df_util import shrink_defs, expand_defs, convert_to_form, process_def_expands
from hed import DefinitionDict


class TestShrinkDefs(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version()

    def test_shrink_defs_normal(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_placeholder(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_no_matching_tags(self):
        df = pd.DataFrame({"column1": ["(Event/SomeEvent, Item/SomeItem,Acceleration/25)"]})
        expected_df = pd.DataFrame({"column1": ["(Event/SomeEvent, Item/SomeItem,Acceleration/25)"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_multiple_columns(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"],
                           "column2": ["(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"],
                                     "column2": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        result = shrink_defs(df, self.schema, ['column1', 'column2'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_multiple_defs_same_line(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Acceleration/30"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Def/TestDefPlaceholder/123,Acceleration/30"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_mixed_tags(self):
        df = pd.DataFrame({"column1": [
            "(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent,(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem,Acceleration/25"]})
        expected_df = pd.DataFrame(
            {"column1": ["Def/TestDefNormal,Event/SomeEvent,Def/TestDefPlaceholder/123,Item/SomeItem,Acceleration/25"]})
        result = shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_shrink_defs_series_normal(self):
        series = pd.Series(["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"])
        expected_series = pd.Series(["Def/TestDefNormal,Event/SomeEvent"])
        result = shrink_defs(series, self.schema, None)
        pd.testing.assert_series_equal(result, expected_series)

    def test_shrink_defs_series_placeholder(self):
        series = pd.Series(["(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"])
        expected_series = pd.Series(["Def/TestDefPlaceholder/123,Item/SomeItem"])
        result = shrink_defs(series, self.schema, None)
        pd.testing.assert_series_equal(result, expected_series)


class TestExpandDefs(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version()
        self.def_dict = DefinitionDict(["(Definition/TestDefNormal,(Acceleration/2471,Action/TestDef2))",
                                       "(Definition/TestDefPlaceholder/#,(Acceleration/#,Action/TestDef2))"],
                                       hed_schema=self.schema)

    def test_expand_defs_normal(self):
        df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"]})
        expected_df = pd.DataFrame(
            {"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"]})
        result = expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_expand_defs_placeholder(self):
        df = pd.DataFrame({"column1": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": [
            "(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"]})
        result = expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_expand_defs_no_matching_tags(self):
        df = pd.DataFrame({"column1": ["(Event/SomeEvent,Item/SomeItem,Acceleration/25)"]})
        expected_df = pd.DataFrame({"column1": ["(Event/SomeEvent,Item/SomeItem,Acceleration/25)"]})
        result = expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_expand_defs_multiple_columns(self):
        df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"],
                           "column2": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        expected_df = pd.DataFrame(
            {"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"],
             "column2": [
                 "(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"]})
        result = expand_defs(df, self.schema, self.def_dict, ['column1', 'column2'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_expand_defs_series_normal(self):
        series = pd.Series(["Def/TestDefNormal,Event/SomeEvent"])
        expected_series = pd.Series(["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"])
        result = expand_defs(series, self.schema, self.def_dict, None)
        pd.testing.assert_series_equal(result, expected_series)

    def test_expand_defs_series_placeholder(self):
        series = pd.Series(["Def/TestDefPlaceholder/123,Item/SomeItem"])
        expected_series = pd.Series(["(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"])
        result = expand_defs(series, self.schema, self.def_dict, None)
        pd.testing.assert_series_equal(result, expected_series)


class TestConvertToForm(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version()

    def test_convert_to_form_short_tags(self):
        df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"]})
        expected_df = pd.DataFrame({"column1": ["Azure,See"]})
        result = convert_to_form(df, self.schema, "short_tag", ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_convert_to_form_long_tags(self):
        df = pd.DataFrame({"column1": ["CSS-color/White-color/Azure,Action/Perceive/See"]})
        expected_df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"]})
        result = convert_to_form(df, self.schema, "long_tag", ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_convert_to_form_series_short_tags(self):
        series = pd.Series(["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"])
        expected_series = pd.Series(["Azure,See"])
        result = convert_to_form(series, self.schema, "short_tag")
        pd.testing.assert_series_equal(result, expected_series)

    def test_convert_to_form_series_long_tags(self):
        series = pd.Series(["CSS-color/White-color/Azure,Action/Perceive/See"])
        expected_series = pd.Series(["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"])
        result = convert_to_form(series, self.schema, "long_tag")
        pd.testing.assert_series_equal(result, expected_series)

    def test_convert_to_form_multiple_tags_short(self):
        df = pd.DataFrame({"column1": ["Visual-attribute/Color/CSS-color/White-color/Azure,Biological-item/Anatomical-item/Body-part/Head/Face/Nose,Spatiotemporal-value/Rate-of-change/Acceleration/4.5 m-per-s^2"]})
        expected_df = pd.DataFrame({"column1": ["Azure,Nose,Acceleration/4.5 m-per-s^2"]})
        result = convert_to_form(df, self.schema, "short_tag", ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_convert_to_form_multiple_tags_long(self):
        df = pd.DataFrame({"column1": ["CSS-color/White-color/Azure,Anatomical-item/Body-part/Head/Face/Nose,Rate-of-change/Acceleration/4.5 m-per-s^2"]})
        expected_df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Item/Biological-item/Anatomical-item/Body-part/Head/Face/Nose,Property/Data-property/Data-value/Spatiotemporal-value/Rate-of-change/Acceleration/4.5 m-per-s^2"]})
        result = convert_to_form(df, self.schema, "long_tag", ['column1'])
        pd.testing.assert_frame_equal(result, expected_df)

    def test_basic_expand_detection(self):
        # all simple cases with no duplicates
        test_strings = [
            "(Def-expand/A1/1, (Action/1, Acceleration/5, Item-count/3))",
            "(Def-expand/A1/2, (Action/2, Acceleration/5, Item-count/3))",
            "(Def-expand/B2/3, (Action/3, Collection/animals, Alert))",
            "(Def-expand/B2/4, (Action/4, Collection/animals, Alert))",
            "(Def-expand/C3/5, (Action/5, Joyful, Event))",
            "(Def-expand/C3/6, (Action/6, Joyful, Event))"
        ]
        process_def_expands(test_strings, self.schema)

    def test_mixed_detection(self):
        # Cases where you can only retroactively identify the first def-expand
        test_strings = [
            # Basic example first just to verify
            "(Def-expand/A1/1, (Action/1, Acceleration/5, Item-count/2))",
            "(Def-expand/A1/2, (Action/2, Acceleration/5, Item-count/2))",
            # Out of order ambiguous
            "(Def-expand/B2/3, (Action/3, Collection/animals, Acceleration/3))",
            "(Def-expand/B2/4, (Action/4, Collection/animals, Acceleration/3))",
            # Multiple tags
            "(Def-expand/C3/5, (Action/5, Acceleration/5, Item-count/5))",
            "(Def-expand/C3/6, (Action/6, Acceleration/5, Item-count/5))",
            # Multiple tags2
            "(Def-expand/D4/7, (Action/7, Acceleration/7, Item-count/8))",
            "(Def-expand/D4/8, (Action/8, Acceleration/7, Item-count/8))"
            # Multiple tags3
            "(Def-expand/D5/7, (Action/7, Acceleration/7, Item-count/8, Event))",
            "(Def-expand/D5/8, (Action/8, Acceleration/7, Item-count/8, Event))"
        ]
        def_dict, ambiguous_defs, _ = process_def_expands(test_strings, self.schema)
        self.assertEqual(len(def_dict), 5)

    def test_ambiguous_defs(self):
        # Cases that can't be identified
        test_strings = [
            "(Def-expand/A1/2, (Action/2, Acceleration/5, Item-count/2))",
            "(Def-expand/B2/3, (Action/3, Collection/animals, Acceleration/3))",
            "(Def-expand/C3/5, (Action/5, Acceleration/5, Item-count/5))",
            "(Def-expand/D4/7, (Action/7, Acceleration/7, Item-count/8))",
            "(Def-expand/D5/7, (Action/7, Acceleration/7, Item-count/8, Event))",
        ]
        _, ambiguous_defs, _ = process_def_expands(test_strings, self.schema)
        self.assertEqual(len(ambiguous_defs), 5)

    def test_ambiguous_conflicting_defs(self):
        # This is invalid due to conflicting defs
        test_strings = [
            "(Def-expand/A1/2, (Action/2, Age/5, Item-count/2))",
            "(Def-expand/A1/3, (Action/3, Age/4, Item-count/3))",

            # This could be identified, but fails due to the above raising errors
            "(Def-expand/A1/4, (Action/4, Age/5, Item-count/2))",
        ]
        defs, ambiguous, errors = process_def_expands(test_strings, self.schema)
        self.assertEqual(len(defs), 0)
        self.assertEqual(len(ambiguous), 0)
        self.assertEqual(len(errors["a1"]), 3)

    def test_errors(self):
        # Basic recognition of conflicting errors
        test_strings = [
            "(Def-expand/A1/1, (Action/1, Age/5, Item-count/2))",
            "(Def-expand/A1/2, (Action/2, Age/5, Item-count/2))",
            "(Def-expand/A1/3, (Action/3, Age/5, Item-count/3))",
        ]
        _, _, errors = process_def_expands(test_strings, self.schema)
        self.assertEqual(len(errors), 1)

    def test_errors_ambiguous(self):
        # Verify we recognize errors when we had a def that can't be resolved.
        test_strings = [
            "(Def-expand/A1/1, (Action/1, Age/5, Item-count/1))",
            "(Def-expand/A1/2, (Action/2, Age/5, Item-count/3))",
            "(Def-expand/A1/3, (Action/3, Age/5, Item-count/3))",
        ]
        known, ambiguous, errors = process_def_expands(test_strings, self.schema)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(errors["a1"]), 3)

    def test_errors_unresolved(self):
        # Verify we recognize errors when we had a def that can't be resolved.
        test_strings = [
            "(Def-expand/A1/1, (Action/1, Age/5, Item-count/1))",
            "(Def-expand/A1/2, (Action/2, Age/5, Item-count/3))",
        ]
        known, ambiguous, errors = process_def_expands(test_strings, self.schema)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(errors["a1"]), 2)

    def test_def_expand_detection(self):
        test_strings = [
            "(Def-expand/A1/1, (Action/1, Acceleration/5, Item-Count/2))",
            "(Def-expand/A1/2, (Action/2, Acceleration/5, Item-Count/2))",
            "(Def-expand/B2/3, (Action/3, Collection/animals, Alert))",
            "(Def-expand/B2/4, (Action/4, Collection/animals, Alert))",
            "(Def-expand/C3/5, (Action/5, Joyful, Event))",
            "(Def-expand/C3/6, (Action/6, Joyful, Event))",
            "((Def-expand/A1/7, (Action/7, Acceleration/5, Item-Count/2)), Event, Acceleration/10)",
            "((Def-expand/A1/8, (Action/8, Acceleration/5, Item-Count/2)), Collection/toys, Item-Count/5)",
            "((Def-expand/B2/9, (Action/9, Collection/animals, Alert)), Event, Collection/plants)",
            "((Def-expand/B2/10, (Action/10, Collection/animals, Alert)), Joyful, Item-Count/3)",
            "((Def-expand/C3/11, (Action/11, Joyful, Event)), Collection/vehicles, Acceleration/20)",
            "((Def-expand/C3/12, (Action/12, Joyful, Event)), Alert, Item-Count/8)",
            "((Def-expand/A1/13, (Action/13, Acceleration/5, Item-Count/2)), (Def-expand/B2/13, (Action/13, Collection/animals, Alert)), Event)",
            "((Def-expand/A1/14, (Action/14, Acceleration/5, Item-Count/2)), Joyful, (Def-expand/C3/14, (Action/14, Joyful, Event)))",
            "(Def-expand/B2/15, (Action/15, Collection/animals, Alert)), (Def-expand/C3/15, (Action/15, Joyful, Event)), Acceleration/30",
            "((Def-expand/A1/16, (Action/16, Acceleration/5, Item-Count/2)), (Def-expand/B2/16, (Action/16, Collection/animals, Alert)), Collection/food)",
            "(Def-expand/C3/17, (Action/17, Joyful, Event)), (Def-expand/A1/17, (Action/17, Acceleration/5, Item-Count/2)), Item-Count/6",
            "((Def-expand/B2/18, (Action/18, Collection/animals, Alert)), (Def-expand/C3/18, (Action/18, Joyful, Event)), Alert)",
            "(Def-expand/D1/Apple, (Task/Apple, Collection/cars, Attribute/color))",
            "(Def-expand/D1/Banana, (Task/Banana, Collection/cars, Attribute/color))",
            "(Def-expand/E2/Carrot, (Collection/Carrot, Collection/plants, Attribute/type))",
            "(Def-expand/E2/Dog, (Collection/Dog, Collection/plants, Attribute/type))",
            "((Def-expand/D1/Elephant, (Task/Elephant, Collection/cars, Attribute/color)), (Def-expand/E2/Fox, (Collection/Fox, Collection/plants, Attribute/type)), Event)",
            "((Def-expand/D1/Giraffe, (Task/Giraffe, Collection/cars, Attribute/color)), Joyful, (Def-expand/E2/Horse, (Collection/Horse, Collection/plants, Attribute/type)))",
            "(Def-expand/D1/Iguana, (Task/Iguana, Collection/cars, Attribute/color)), (Def-expand/E2/Jaguar, (Collection/Jaguar, Collection/plants, Attribute/type)), Acceleration/30",
            "(Def-expand/F1/Lion, (Task/Lion, Collection/boats, Attribute/length))",
            "(Def-expand/F1/Monkey, (Task/Monkey, Collection/boats, Attribute/length))",
            "(Def-expand/G2/Nest, (Collection/Nest, Collection/instruments, Attribute/material))",
            "(Def-expand/G2/Octopus, (Collection/Octopus, Collection/instruments, Attribute/material))",
            "((Def-expand/F1/Panda, (Task/Panda, Collection/boats, Attribute/length)), (Def-expand/G2/Quail, (Collection/Quail, Collection/instruments, Attribute/material)), Event)",
            "((Def-expand/F1/Rabbit, (Task/Rabbit, Collection/boats, Attribute/length)), Joyful, (Def-expand/G2/Snake, (Collection/Snake, Collection/instruments, Attribute/material)))",
            "(Def-expand/F1/Turtle, (Task/Turtle, Collection/boats, Attribute/length)), (Def-expand/G2/Umbrella, (Collection/Umbrella, Collection/instruments, Attribute/material))"
        ]

        def_dict, ambiguous, errors = process_def_expands(test_strings, self.schema)
        self.assertEqual(len(def_dict), 7)
        self.assertEqual(len(ambiguous), 0)
        self.assertEqual(len(errors), 0)

