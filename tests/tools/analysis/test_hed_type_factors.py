import os
import unittest
import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.models import DefinitionEntry
from hed.models.hed_string import HedString
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.analysis.hed_type_values import HedTypeValues
from hed.tools.analysis.hed_type_factors import HedTypeFactors
from hed.models.df_util import get_assembled


class Test(unittest.TestCase):
    # TODO: Test different encodings

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        cls.test_strings1 = [HedString("Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
                                       "(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4", hed_schema=schema),
                             HedString('(Def/Cond1, Offset)', hed_schema=schema),
                             HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast',
                                       hed_schema=schema),
                             HedString('', hed_schema=schema),
                             HedString('(Def/Cond2, Onset)', hed_schema=schema),
                             HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
                             HedString('Arm, Leg, Condition-variable/Fast', hed_schema=schema)]
        cls.test_strings2 = [HedString("Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
                                       hed_schema=schema),
                             HedString("Yellow", hed_schema=schema),
                             HedString("Def/Cond2, (Def/Cond6/4, Onset)", hed_schema=schema),
                             HedString("Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)", hed_schema=schema),
                             HedString("Def/Cond2, Def/Cond6/4", hed_schema=schema)]

        def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=schema)
        def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=schema)
        def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
                         hed_schema=schema)
        def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=schema)
        def5 = HedString('(Condition-variable/Lumber, Apple, Banana)', hed_schema=schema)
        def6 = HedString('(Condition-variable/Lumber, Label/#, Apple, Banana)', hed_schema=schema)
        cls.defs = {'Cond1': DefinitionEntry('Cond1', def1, False, None),
                    'Cond2': DefinitionEntry('Cond2', def2, False, None),
                    'Cond3': DefinitionEntry('Cond3', def3, True, None),
                    'Cond4': DefinitionEntry('Cond4', def4, False, None),
                    'Cond5': DefinitionEntry('Cond5', def5, False, None),
                    'Cond6': DefinitionEntry('Cond6', def6, True, None)
                    }

        cls.test_strings3 = [HedString('(Def/Cond3, Offset)', hed_schema=schema)]

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids_tests/eeg_ds003645s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.sidecar1 = sidecar1
        cls.schema = schema

    def test_with_mixed(self):
        var_manager = HedTypeValues(HedContextManager(self.test_strings1, self.schema), self.defs, 'run-01')
        var_facts = var_manager.get_type_value_factors('fast')
        self.assertIsInstance(var_facts, HedTypeFactors)
        df = var_facts.get_factors()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), len(self.test_strings1))
        self.assertEqual(len(df.columns), 1)
        summary1 = var_facts.get_summary()
        self.assertIsInstance(summary1, dict)

    def test_tabular_input(self):
        hed_strings, definitions = get_assembled(self.input_data, self.sidecar1, self.schema, extra_def_dicts=None,
                                                 join_columns=True, shrink_defs=True, expand_defs=False)
        var_manager = HedTypeValues(HedContextManager(hed_strings, self.schema), definitions, 'run-01')
        self.assertIsInstance(var_manager, HedTypeValues,
                              "Constructor should create a HedTypeManager from a tabular input")
        var_fact = var_manager.get_type_value_factors('face-type')
        self.assertIsInstance(var_fact, HedTypeFactors)
        this_str = str(var_fact)
        self.assertIsInstance(this_str, str)
        self.assertTrue(len(this_str))
        fact2 = var_fact.get_factors()
        self.assertIsInstance(fact2, pd.DataFrame)
        df2 = var_fact._one_hot_to_categorical(fact2, ["unfamiliar-face-cond", "baloney"])
        self.assertEqual(len(df2), 200)
        self.assertEqual(len(df2.columns), 1)

    def test_constructor_multiple_values(self):
        var_manager = HedTypeValues(HedContextManager(self.test_strings2, self.schema), self.defs, 'run-01')
        self.assertIsInstance(var_manager, HedTypeValues,
                              "Constructor should create a HedTypeManager from strings")
        self.assertEqual(len(var_manager._type_value_map), 3,
                         "Constructor should have right number of type_variables if multiple")
        var_fact1 = var_manager.get_type_value_factors('var2')
        self.assertIsInstance(var_fact1, HedTypeFactors)
        var_fact2 = var_manager.get_type_value_factors('lumber')
        fact2 = var_fact2.get_factors()
        self.assertIsInstance(fact2, pd.DataFrame)
        self.assertEqual(len(fact2), len(self.test_strings2))
        with self.assertRaises(HedFileError) as context:
            var_fact2.get_factors(factor_encoding="categorical")
        self.assertEqual(context.exception.args[0], "MultipleFactorSameEvent")
        with self.assertRaises(ValueError) as context:
            var_fact2.get_factors(factor_encoding="baloney")
        self.assertEqual(context.exception.args[0], "BadFactorEncoding")

    def test_constructor_unmatched(self):
        with self.assertRaises(HedFileError) as context:
            HedTypeValues(HedContextManager(self.test_strings3, self.schema), self.defs, 'run-01')
        self.assertEqual(context.exception.args[0], 'UnmatchedOffset')

    def test_variable_summary(self):
        var_manager = HedTypeValues(HedContextManager(self.test_strings2, self.schema), self.defs, 'run-01')
        self.assertIsInstance(var_manager, HedTypeValues,
                              "Constructor should create a HedTypeManager from strings")
        self.assertEqual(len(var_manager._type_value_map), 3,
                         "Constructor should have right number of type_variables if multiple")
        for variable in var_manager.get_type_value_names():
            var_sum = var_manager.get_type_value_factors(variable)
            summary = var_sum.get_summary()
            self.assertIsInstance(summary, dict, "get_summary returns a dictionary summary")

    def test_get_variable_factors(self):
        var_manager = HedTypeValues(HedContextManager(self.test_strings2, self.schema), self.defs, 'run-01')
        self.assertIsInstance(var_manager, HedTypeValues,
                              "Constructor should create a HedTypeManager from strings")
        self.assertEqual(len(var_manager._type_value_map), 3,
                         "Constructor should have right number of type_variables if multiple")

        for variable in var_manager.get_type_value_names():
            var_sum = var_manager.get_type_value_factors(variable)
            summary = var_sum.get_summary()
            factors = var_sum.get_factors()
            self.assertIsInstance(factors, pd.DataFrame, "get_factors contains dataframe.")
            self.assertEqual(len(factors), var_sum.number_elements,
                             "get_factors has factors of same length as number of elements")
            if not var_manager._type_value_map[variable].levels:
                self.assertEqual(len(factors.columns), 1)
            else:
                self.assertEqual(len(factors.columns), summary["levels"], 'get_factors has factors levels')
                self.assertEqual(len(factors.columns), len(var_manager._type_value_map[variable].levels))

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
        hed_strings, definitions = get_assembled(self.input_data, self.sidecar1, self.schema, extra_def_dicts=None,
                                                 join_columns=True, shrink_defs=True, expand_defs=False)
        var_manager = HedTypeValues(HedContextManager(hed_strings, self.schema), definitions, 'run-01')
        var_key = var_manager.get_type_value_factors('key-assignment')
        sum_key = var_key.get_summary()
        self.assertEqual(sum_key['events'], 200, "get_summary has right number of events")
        self.assertEqual(sum_key['max_refs_per_event'], 1, "Get_summary has right multiple maximum")
        self.assertIsInstance(sum_key['level_counts'], dict, "get_summary level counts is a dictionary")
        self.assertEqual(sum_key['level_counts']['right-sym-cond'], 200, "get_summary level counts value correct.")
        var_face = var_manager.get_type_value_factors('face-type')
        sum_key = var_face.get_summary()
        self.assertEqual(sum_key['events'], 52, "get_summary has right number of events")
        self.assertEqual(sum_key['max_refs_per_event'], 1, "Get_summary has right multiple maximum")
        self.assertIsInstance(sum_key['level_counts'], dict, "get_summary level counts is a dictionary")
        self.assertEqual(sum_key['level_counts']['unfamiliar-face-cond'], 20, "get_summary level counts value correct.")


if __name__ == '__main__':
    unittest.main()
