import os
import unittest
from pandas import DataFrame
from hed.models import DefinitionDict
from hed.models.hed_string import HedString
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_type import HedType
from hed.errors.exceptions import HedFileError
from hed.tools.analysis.hed_type_factors import HedTypeFactors


class Test(unittest.TestCase):
    # TODO: Test different encodings

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        # Set up the definition dictionary
        defs = [
            HedString("(Definition/Cond1, (Condition-variable/Var1, Circle, Square))", hed_schema=schema),
            HedString(
                "(Definition/Cond2, (condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere))", hed_schema=schema
            ),
            HedString(
                "(Definition/Cond3/#, (Organizational-property/Condition-variable/Var3, Label/#, Ellipse, Cross))",
                hed_schema=schema,
            ),
            HedString("(Definition/Cond4, (Condition-variable, Item, Circle))", hed_schema=schema),
            HedString("(Definition/Cond5, (Condition-variable/Lumber, Item, Circle))", hed_schema=schema),
            HedString("(Definition/Cond6/#, (Condition-variable/Lumber, Label/#, Item, Circle))", hed_schema=schema),
        ]
        def_dict = DefinitionDict()
        for value in defs:
            def_dict.check_for_definitions(value)
        cls.setup_dict = def_dict
        test_strings1 = [
            "Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset)",
            "(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4",
            "(Def/Cond1, Offset)",
            "White, Black, Condition-variable/Wonder, Condition-variable/Fast",
            "",
            "(Def/Cond2, Onset)",
            "(Def/Cond3/4.3, Onset)",
            "Arm, Leg, Condition-variable/Fast",
        ]
        test_onsets1 = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        df1 = DataFrame(test_onsets1, columns=["onset"])
        df1["HED"] = test_strings1
        input_data1 = TabularInput(df1)
        cls.event_man1 = EventManager(input_data1, schema, extra_defs=def_dict)
        cls.input_data1 = input_data1
        test_strings2 = [
            "Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
            "Yellow",
            "Def/Cond2, (Def/Cond6/4, Onset)",
            "Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)",
            "Def/Cond2, Def/Cond6/4",
        ]
        test_onsets2 = [0.0, 1.0, 2.0, 3.0, 4.0]
        df2 = DataFrame(test_onsets2, columns=["onset"])
        df2["HED"] = test_strings2
        input_data2 = TabularInput(df2)
        cls.event_man2 = EventManager(input_data2, schema, extra_defs=def_dict)
        test_strings3 = ["(Def/Cond3, Offset)"]
        test_onsets3 = [0.0]
        df3 = DataFrame(test_onsets3, columns=["onset"])
        df3["HED"] = test_strings3
        cls.input_data3 = TabularInput(df3)
        bids_root_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_hed")
        )
        events_path = os.path.realpath(
            os.path.join(bids_root_path, "sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv")
        )
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, "task-FacePerception_events.json"))
        cls.schema = schema
        cls.tab_input = TabularInput(
            events_path,
            sidecar_path,
        )

    def test_with_mixed(self):
        var_manager = HedType(self.event_man1, "run-01")
        var_facts = var_manager.get_type_value_factors("fast")
        self.assertIsInstance(var_facts, HedTypeFactors)
        df = var_facts.get_factors()
        self.assertIsInstance(df, DataFrame)
        self.assertEqual(len(df), len(self.event_man1.event_list))
        self.assertEqual(len(df.columns), 1)
        summary1 = var_facts.get_summary()
        self.assertIsInstance(summary1, dict)

    def test_tabular_input(self):
        var_manager = HedType(EventManager(self.tab_input, self.schema), "run-01")
        self.assertIsInstance(var_manager, HedType)
        var_fact = var_manager.get_type_value_factors("face-type")
        self.assertIsInstance(var_fact, HedTypeFactors)
        this_str = str(var_fact)
        self.assertIsInstance(this_str, str)
        self.assertTrue(len(this_str))
        fact2 = var_fact.get_factors()
        self.assertIsInstance(fact2, DataFrame)
        df2 = var_fact._one_hot_to_categorical(fact2, ["unfamiliar-face-cond", "baloney"])
        self.assertEqual(len(df2), 200)
        self.assertEqual(len(df2.columns), 1)

    def test_constructor_multiple_values(self):
        var_manager = HedType(self.event_man2, "run-01")
        self.assertIsInstance(var_manager, HedType)
        self.assertEqual(len(var_manager._type_map), 3, "Constructor should have right number of type_variables if multiple")
        var_fact1 = var_manager.get_type_value_factors("var2")
        self.assertIsInstance(var_fact1, HedTypeFactors)
        var_fact2 = var_manager.get_type_value_factors("lumber")
        fact2 = var_fact2.get_factors()
        self.assertIsInstance(fact2, DataFrame)
        self.assertEqual(len(fact2), len(self.event_man2.event_list))
        with self.assertRaises(HedFileError) as context:
            var_fact2.get_factors(factor_encoding="categorical")
        self.assertEqual(context.exception.args[0], "MultipleFactorSameEvent")
        with self.assertRaises(ValueError) as context:
            var_fact2.get_factors(factor_encoding="baloney")
        self.assertEqual(context.exception.args[0], "BadFactorEncoding")

    def test_constructor_unmatched(self):
        with self.assertRaises(KeyError) as context:
            HedType(EventManager(self.input_data3, self.schema), "run-01")
        self.assertEqual(context.exception.args[0], "cond3")

    def test_variable_summary(self):
        var_manager = HedType(self.event_man2, "run-01")
        self.assertIsInstance(var_manager, HedType)
        self.assertEqual(len(var_manager._type_map), 3, "Constructor should have right number of type_variables if multiple")
        for variable in var_manager.get_type_value_names():
            var_sum = var_manager.get_type_value_factors(variable)
            summary = var_sum.get_summary()
            self.assertIsInstance(summary, dict, "get_summary returns a dictionary summary")

    def test_get_variable_factors(self):
        var_manager = HedType(self.event_man2, "run-01")
        self.assertIsInstance(var_manager, HedType)
        self.assertEqual(len(var_manager._type_map), 3, "Constructor should have right number of type_variables if multiple")

        for variable in var_manager.get_type_value_names():
            var_sum = var_manager.get_type_value_factors(variable)
            summary = var_sum.get_summary()
            factors = var_sum.get_factors()
            self.assertIsInstance(factors, DataFrame, "get_factors contains dataframe.")
            self.assertEqual(
                len(factors), var_sum.number_elements, "get_factors has factors of same length as number of elements"
            )
            if not var_manager._type_map[variable].levels:
                self.assertEqual(len(factors.columns), 1)
            else:
                self.assertEqual(len(factors.columns), summary["levels"], "get_factors has factors levels")
                self.assertEqual(len(factors.columns), len(var_manager._type_map[variable].levels))

    def test_count_events(self):
        list1 = [0, 2, 6, 1, 2, 0, 0]
        number_events1, number_multiple1, max_multiple1 = HedTypeFactors._count_level_events(list1)
        self.assertEqual(number_events1, 4, "_count_level_events should have right number of events")
        self.assertEqual(number_multiple1, 3, "_count_level_events should have right number of multiple events")
        self.assertEqual(max_multiple1, 6, "_count_level_events should have right maximum multiples")
        list2 = []
        number_events2, number_multiple2, max_multiple2 = HedTypeFactors._count_level_events(list2)
        self.assertEqual(number_events2, 0, "_count_level_events should have 0 events for empty list")
        self.assertEqual(number_multiple2, 0, "_count_level_events should have 0 multiples for empty list")
        self.assertIsNone(max_multiple2, "_count_level_events should not have a max multiple for empty list")

    def test_get_summary(self):
        var_manager = HedType(EventManager(self.tab_input, self.schema), "run-01")
        var_key = var_manager.get_type_value_factors("key-assignment")
        sum_key = var_key.get_summary()
        self.assertEqual(sum_key["events"], 200, "get_summary has right number of events")
        self.assertEqual(sum_key["max_refs_per_event"], 1, "Get_summary has right multiple maximum")
        self.assertIsInstance(sum_key["level_counts"], dict, "get_summary level counts is a dictionary")
        self.assertEqual(sum_key["level_counts"]["right-sym-cond"], 200, "get_summary level counts value correct.")
        var_face = var_manager.get_type_value_factors("face-type")
        sum_key = var_face.get_summary()
        self.assertEqual(sum_key["events"], 52, "get_summary has right number of events")
        self.assertEqual(sum_key["max_refs_per_event"], 1, "Get_summary has right multiple maximum")
        self.assertIsInstance(sum_key["level_counts"], dict, "get_summary level counts is a dictionary")
        self.assertEqual(sum_key["level_counts"]["unfamiliar-face-cond"], 20, "get_summary level counts value correct.")


if __name__ == "__main__":
    unittest.main()
