import unittest
import pandas as pd


from hed import load_schema_version
from hed.models.df_util import shrink_defs, expand_defs, convert_to_form, process_def_expands
from hed import DefinitionDict
from hed.models.df_util import _handle_curly_braces_refs, _indexed_dict_from_onsets, _filter_by_index_list, split_delay_tags


class TestShrinkDefs(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version("8.2.0")

    def test_shrink_defs_normal(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"]})
        shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_shrink_defs_placeholder(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_shrink_defs_no_matching_tags(self):
        df = pd.DataFrame({"column1": ["(Event/SomeEvent, Item/SomeItem,Acceleration/25)"]})
        expected_df = pd.DataFrame({"column1": ["(Event/SomeEvent, Item/SomeItem,Acceleration/25)"]})
        shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_shrink_defs_multiple_columns(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"],
                           "column2": ["(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"],
                                     "column2": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        shrink_defs(df, self.schema, ['column1', 'column2'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_shrink_defs_multiple_defs_same_line(self):
        df = pd.DataFrame({"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Acceleration/30"]})
        expected_df = pd.DataFrame({"column1": ["Def/TestDefNormal,Def/TestDefPlaceholder/123,Acceleration/30"]})
        shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_shrink_defs_mixed_tags(self):
        df = pd.DataFrame({"column1": [
            "(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent,(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem,Acceleration/25"]})
        expected_df = pd.DataFrame(
            {"column1": ["Def/TestDefNormal,Event/SomeEvent,Def/TestDefPlaceholder/123,Item/SomeItem,Acceleration/25"]})
        shrink_defs(df, self.schema, ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_shrink_defs_series_normal(self):
        series = pd.Series(["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"])
        expected_series = pd.Series(["Def/TestDefNormal,Event/SomeEvent"])
        shrink_defs(series, self.schema, None)
        pd.testing.assert_series_equal(series, expected_series)

    def test_shrink_defs_series_placeholder(self):
        series = pd.Series(["(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"])
        expected_series = pd.Series(["Def/TestDefPlaceholder/123,Item/SomeItem"])
        shrink_defs(series, self.schema, None)
        pd.testing.assert_series_equal(series, expected_series)


class TestExpandDefs(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version("8.2.0")
        self.def_dict = DefinitionDict(["(Definition/TestDefNormal,(Acceleration/2471,Action/TestDef2))",
                                       "(Definition/TestDefPlaceholder/#,(Acceleration/#,Action/TestDef2))"],
                                       hed_schema=self.schema)

    def test_expand_defs_normal(self):
        df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"]})
        expected_df = pd.DataFrame(
            {"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"]})
        expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_expand_defs_placeholder(self):
        df = pd.DataFrame({"column1": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        expected_df = pd.DataFrame({"column1": [
            "(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"]})
        expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_expand_defs_no_matching_tags(self):
        df = pd.DataFrame({"column1": ["(Event/SomeEvent,Item/SomeItem,Acceleration/25)"]})
        expected_df = pd.DataFrame({"column1": ["(Event/SomeEvent,Item/SomeItem,Acceleration/25)"]})
        expand_defs(df, self.schema, self.def_dict, ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_expand_defs_multiple_columns(self):
        df = pd.DataFrame({"column1": ["Def/TestDefNormal,Event/SomeEvent"],
                           "column2": ["Def/TestDefPlaceholder/123,Item/SomeItem"]})
        expected_df = pd.DataFrame(
            {"column1": ["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"],
             "column2": [
                 "(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"]})
        expand_defs(df, self.schema, self.def_dict, ['column1', 'column2'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_expand_defs_series_normal(self):
        series = pd.Series(["Def/TestDefNormal,Event/SomeEvent"])
        expected_series = pd.Series(["(Def-expand/TestDefNormal,(Acceleration/2471,Action/TestDef2)),Event/SomeEvent"])
        expand_defs(series, self.schema, self.def_dict, None)
        pd.testing.assert_series_equal(series, expected_series)

    def test_expand_defs_series_placeholder(self):
        series = pd.Series(["Def/TestDefPlaceholder/123,Item/SomeItem"])
        expected_series = pd.Series(["(Def-expand/TestDefPlaceholder/123,(Acceleration/123,Action/TestDef2)),Item/SomeItem"])
        expand_defs(series, self.schema, self.def_dict, None)
        pd.testing.assert_series_equal(series, expected_series)


class TestConvertToForm(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version("8.2.0")

    def test_convert_to_form_short_tags(self):
        df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"]})
        expected_df = pd.DataFrame({"column1": ["Azure,See"]})
        convert_to_form(df, self.schema, "short_tag", ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_convert_to_form_long_tags(self):
        df = pd.DataFrame({"column1": ["CSS-color/White-color/Azure,Action/Perceive/See"]})
        expected_df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"]})
        convert_to_form(df, self.schema, "long_tag", ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_convert_to_form_series_short_tags(self):
        series = pd.Series(["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"])
        expected_series = pd.Series(["Azure,See"])
        convert_to_form(series, self.schema, "short_tag")
        pd.testing.assert_series_equal(series, expected_series)

    def test_convert_to_form_series_long_tags(self):
        series = pd.Series(["CSS-color/White-color/Azure,Action/Perceive/See"])
        expected_series = pd.Series(["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Action/Perceive/See"])
        convert_to_form(series, self.schema, "long_tag")
        pd.testing.assert_series_equal(series, expected_series)

    def test_convert_to_form_multiple_tags_short(self):
        df = pd.DataFrame({"column1": ["Visual-attribute/Color/CSS-color/White-color/Azure,Biological-item/Anatomical-item/Body-part/Head/Face/Nose,Spatiotemporal-value/Rate-of-change/Acceleration/4.5 m-per-s^2"]})
        expected_df = pd.DataFrame({"column1": ["Azure,Nose,Acceleration/4.5 m-per-s^2"]})
        convert_to_form(df, self.schema, "short_tag", ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

    def test_convert_to_form_multiple_tags_long(self):
        df = pd.DataFrame({"column1": ["CSS-color/White-color/Azure,Anatomical-item/Body-part/Head/Face/Nose,Rate-of-change/Acceleration/4.5 m-per-s^2"]})
        expected_df = pd.DataFrame({"column1": ["Property/Sensory-property/Sensory-attribute/Visual-attribute/Color/CSS-color/White-color/Azure,Item/Biological-item/Anatomical-item/Body-part/Head/Face/Nose,Property/Data-property/Data-value/Spatiotemporal-value/Rate-of-change/Acceleration/4.5 m-per-s^2"]})
        convert_to_form(df, self.schema, "long_tag", ['column1'])
        pd.testing.assert_frame_equal(df, expected_df)

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

class TestInsertColumns(unittest.TestCase):

    def test_insert_columns_simple(self):
        df = pd.DataFrame({
            "column1": ["{column2}, Event, Action"],
            "column2": ["Item"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Item, Event, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_multiple_rows(self):
        df = pd.DataFrame({
            "column1": ["{column2}, Event, Action", "Event, Action"],
            "column2": ["Item", "Subject"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Item, Event, Action", "Event, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_multiple_columns(self):
        df = pd.DataFrame({
            "column1": ["{column2}, Event, {column3}, Action"],
            "column2": ["Item"],
            "column3": ["Subject"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Item, Event, Subject, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2", "column3"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_four_columns(self):
        df = pd.DataFrame({
            "column1": ["{column2}, Event, {column3}, Action"],
            "column2": ["Item"],
            "column3": ["Subject"],
            "column4": ["Data"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Item, Event, Subject, Action"],
            "column4": ["Data"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2", "column3"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["Item"],
            "column3": ["Subject"],
            "column4": ["Data"]
        })
        expected_df = pd.DataFrame({
            "column1": ["(Item, (Subject, Data)), Event, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses_na_values(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["Data"],
            "column3": ["n/a"],
            "column4": ["n/a"]
        })
        expected_df = pd.DataFrame({
            "column1": ["(Data), Event, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses_na_values2(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["n/a"],
            "column3": ["n/a"],
            "column4": ["Data"]
        })
        expected_df = pd.DataFrame({
            "column1": ["((Data)), Event, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses_mixed_na_values(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["n/a"],
            "column3": ["Subject"],
            "column4": ["n/a"]
        })
        expected_df = pd.DataFrame({
            "column1": ["((Subject)), Event, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_nested_parentheses_all_na_values(self):
        df = pd.DataFrame({
            "column1": ["({column2}, ({column3}, {column4})), Event, Action"],
            "column2": ["n/a"],
            "column3": ["n/a"],
            "column4": ["n/a"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Event, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2", "column3", "column4"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_parentheses(self):
        df = pd.DataFrame({
            "column1": ["({column2}), Event, Action"],
            "column2": ["Item"]
        })
        expected_df = pd.DataFrame({
            "column1": ["(Item), Event, Action"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

    def test_insert_columns_with_parentheses_na_values(self):
        df = pd.DataFrame({
            "column1": ["({column2}), Event, Action"],
            "column2": ["n/a"],
            "column3": ["n/a"]
        })
        expected_df = pd.DataFrame({
            "column1": ["Event, Action"],
            "column3": ["n/a"]
        })
        result = _handle_curly_braces_refs(df, refs=["column2"], column_names=df.columns)
        pd.testing.assert_frame_equal(result, expected_df)

class TestOnsetDict(unittest.TestCase):
    def test_empty_and_single_onset(self):
        self.assertEqual(_indexed_dict_from_onsets([]), {})
        self.assertEqual(_indexed_dict_from_onsets([3.5]), {3.5: [0]})

    def test_identical_and_approx_equal_onsets(self):
        self.assertEqual(_indexed_dict_from_onsets([3.5, 3.5]), {3.5: [0, 1]})
        self.assertEqual(_indexed_dict_from_onsets([3.5, 3.500000001]), {3.5: [0], 3.500000001: [1]})
        self.assertEqual(_indexed_dict_from_onsets([3.5, 3.5000000000001]), {3.5: [0, 1]})

    def test_distinct_and_mixed_onsets(self):
        self.assertEqual(_indexed_dict_from_onsets([3.5, 4.0, 4.4]), {3.5: [0], 4.0: [1], 4.4: [2]})
        self.assertEqual(_indexed_dict_from_onsets([3.5, 3.5, 4.0, 4.4]), {3.5: [0, 1], 4.0: [2], 4.4: [3]})
        self.assertEqual(_indexed_dict_from_onsets([4.0, 3.5, 4.4, 4.4]), {4.0: [0], 3.5: [1], 4.4: [2, 3]})

    def test_complex_onsets(self):
        # Negative, zero, and positive onsets
        self.assertEqual(_indexed_dict_from_onsets([-1.0, 0.0, 1.0]), {-1.0: [0], 0.0: [1], 1.0: [2]})

        # Very close but distinct onsets
        self.assertEqual(_indexed_dict_from_onsets([1.0, 1.0 + 1e-8, 1.0 + 2e-8]),
                         {1.0: [0], 1.0 + 1e-8: [1], 1.0 + 2e-8: [2]})
        # Very close
        self.assertEqual(_indexed_dict_from_onsets([1.0, 1.0 + 1e-10, 1.0 + 2e-10]),
                         {1.0: [0, 1, 2]})

        # Mixed scenario
        self.assertEqual(_indexed_dict_from_onsets([3.5, 3.5, 4.0, 4.4, 4.4, -1.0]),
                         {3.5: [0, 1], 4.0: [2], 4.4: [3, 4], -1.0: [5]})

    def test_empty_and_single_item_series(self):
        self.assertTrue(_filter_by_index_list(pd.Series([], dtype=str), {}).equals(pd.Series([], dtype=str)))
        self.assertTrue(_filter_by_index_list(pd.Series(["apple"]), {0: [0]}).equals(pd.Series(["apple"])))

    def test_two_item_series_with_same_onset(self):
        input_series = pd.Series(["apple", "orange"])
        expected_series = pd.Series(["apple,orange", ""])
        self.assertTrue(_filter_by_index_list(input_series, {0: [0, 1]}).equals(expected_series))

    def test_multiple_item_series(self):
        input_series = pd.Series(["apple", "orange", "banana", "mango"])
        indexed_dict = {0: [0, 1], 1: [2], 2: [3]}
        expected_series = pd.Series(["apple,orange", "", "banana", "mango"])
        self.assertTrue(_filter_by_index_list(input_series, indexed_dict).equals(expected_series))

    def test_complex_scenarios(self):
        # Test with negative, zero and positive onsets
        original = pd.Series(["negative", "zero", "positive"])
        indexed_dict = {-1: [0], 0: [1], 1: [2]}
        expected_series1 = pd.Series(["negative", "zero", "positive"])
        self.assertTrue(_filter_by_index_list(original, indexed_dict).equals(expected_series1))

        # Test with more complex indexed_dict
        original2 = pd.Series(["apple", "orange", "banana", "mango", "grape"])
        indexed_dict2= {0: [0, 1], 1: [2], 2: [3, 4]}
        expected_series2 = pd.Series(["apple,orange", "", "banana", "mango,grape", ""])
        self.assertTrue(_filter_by_index_list(original2, indexed_dict2).equals(expected_series2))

    def test_empty_and_single_item_series_df(self):
        self.assertTrue(_filter_by_index_list(pd.DataFrame([], columns=["HED", "Extra"]), {}).equals(
            pd.DataFrame([], columns=["HED", "Extra"])))
        self.assertTrue(
            _filter_by_index_list(pd.DataFrame([["apple", "extra1"]], columns=["HED", "Extra"]), {0: [0]}).equals(
                pd.DataFrame([["apple", "extra1"]], columns=["HED", "Extra"])))

    def test_two_item_series_with_same_onset_df(self):
        input_df = pd.DataFrame([["apple", "extra1"], ["orange", "extra2"]], columns=["HED", "Extra"])
        expected_df = pd.DataFrame([["apple,orange", "extra1"], ["", "extra2"]], columns=["HED", "Extra"])
        self.assertTrue(_filter_by_index_list(input_df, {0: [0, 1]}).equals(expected_df))

    def test_multiple_item_series_df(self):
        input_df = pd.DataFrame([["apple", "extra1"], ["orange", "extra2"], ["banana", "extra3"], ["mango", "extra4"]],
                                columns=["HED", "Extra"])
        indexed_dict = {0: [0, 1], 1: [2], 2: [3]}
        expected_df = pd.DataFrame(
            [["apple,orange", "extra1"], ["", "extra2"], ["banana", "extra3"], ["mango", "extra4"]],
            columns=["HED", "Extra"])
        self.assertTrue(_filter_by_index_list(input_df, indexed_dict).equals(expected_df))

    def test_complex_scenarios_df(self):
        # Test with negative, zero, and positive onsets
        original = pd.DataFrame([["negative", "extra1"], ["zero", "extra2"], ["positive", "extra3"]],
                                columns=["HED", "Extra"])
        indexed_dict = {-1: [0], 0: [1], 1: [2]}
        expected_df = pd.DataFrame([["negative", "extra1"], ["zero", "extra2"], ["positive", "extra3"]],
                                   columns=["HED", "Extra"])
        self.assertTrue(_filter_by_index_list(original, indexed_dict).equals(expected_df))

        # Test with more complex indexed_dict
        original2 = pd.DataFrame(
            [["apple", "extra1"], ["orange", "extra2"], ["banana", "extra3"], ["mango", "extra4"], ["grape", "extra5"]],
            columns=["HED", "Extra"])
        indexed_dict2 = {0: [0, 1], 1: [2], 2: [3, 4]}
        expected_df2 = pd.DataFrame(
            [["apple,orange", "extra1"], ["", "extra2"], ["banana", "extra3"], ["mango,grape", "extra4"],
             ["", "extra5"]], columns=["HED", "Extra"])
        self.assertTrue(_filter_by_index_list(original2, indexed_dict2).equals(expected_df2))



class TestSplitDelayTags(unittest.TestCase):
    schema = load_schema_version("8.2.0")
    def test_empty_series_and_onsets(self):
        empty_series = pd.Series([], dtype="object")
        empty_onsets = pd.Series([], dtype="float")
        result = split_delay_tags(empty_series, self.schema, empty_onsets)
        self.assertIsInstance(result, pd.DataFrame)

    def test_None_series_and_onsets(self):
        result = split_delay_tags(None, self.schema, None)
        self.assertIsNone(result)

    def test_normal_ordered_series(self):
        series = pd.Series([
            "Tag1,Tag2",
            "Tag3,Tag4"
        ])
        onsets = pd.Series([1.0, 2.0])
        result = split_delay_tags(series, self.schema, onsets)
        self.assertTrue(result.onset.equals(pd.Series([1.0, 2.0])))
        self.assertTrue(result.HED.equals(pd.Series([
            "Tag1,Tag2",
            "Tag3,Tag4"
        ])))

    def test_normal_ordered_series_with_delays(self):
        series = pd.Series([
            "Tag1,Tag2,(Delay/3.0 s,(Tag5))",
            "Tag3,Tag4"
        ])
        onsets = pd.Series([1.0, 2.0])
        result = split_delay_tags(series, self.schema, onsets)
        self.assertTrue(result.onset.equals(pd.Series([1.0, 2.0, 4.0])))
        self.assertTrue(result.HED.equals(pd.Series([
            "Tag1,Tag2",
            "Tag3,Tag4",
            "(Delay/3.0 s,(Tag5))"
        ])))

    def test_normal_ordered_series_with_double_delays(self):
        series = pd.Series([
            "Tag1,Tag2,(Delay/3.0 s,(Tag5))",
            "Tag6,(Delay/2.0 s,(Tag7))",
            "Tag3,Tag4"
        ])
        onsets = pd.Series([1.0, 2.0, 3.0])
        result = split_delay_tags(series, self.schema, onsets)
        self.assertTrue(result.onset.equals(pd.Series([1.0, 2.0, 3.0, 4.0, 4.0])))
        self.assertTrue(result.HED.equals(pd.Series([
            "Tag1,Tag2",
            "Tag6",
            "Tag3,Tag4",
            "(Delay/3.0 s,(Tag5)),(Delay/2.0 s,(Tag7))",
            ""
        ])))
        self.assertTrue(result.original_index.equals(pd.Series([0, 1, 2, 0, 1])))