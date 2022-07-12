import os
import unittest
import pandas as pd
from hed import HedString, load_schema_version, Sidecar, TabularInput
from hed.errors import HedFileError
from hed.models import DefinitionEntry
from hed.tools import VariableManager, VariableSummary, get_assembled_strings


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        cls.test_strings1 = [HedString(f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
                                       f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4", hed_schema=schema),
                             HedString('(Def/Cond1, Offset)', hed_schema=schema),
                             HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast',
                                       hed_schema=schema),
                             HedString('', hed_schema=schema),
                             HedString('(Def/Cond2, Onset)', hed_schema=schema),
                             HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
                             HedString('Arm, Leg, Condition-variable/Fast', hed_schema=schema)]
        cls.test_strings2 = [HedString(f"Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
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
                                          '../../data/bids/eeg_ds003654s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.schema = schema

    def test_constructor(self):
        var_manager = VariableManager(self.test_strings1, self.schema, self.defs)
        var1_summary = var_manager.get_variable('var1')
        self.assertIsInstance(var1_summary, VariableSummary)
        self.assertEqual(var1_summary.number_elements, len(var_manager.hed_strings),
                         "The constructor should have the same number of elements as there are hed strings")

    def test_constructor_from_tabular_input(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False)
        var_manager = VariableManager(hed_strings, self.schema, definitions)
        self.assertIsInstance(var_manager, VariableManager,
                              "Constructor should create a VariableManager from a tabular input")
        var_sum = var_manager.get_variable('face-type')
        self.assertIsInstance(var_sum, VariableSummary)
        self.assertEqual(var_sum.number_elements, len(var_manager.hed_strings),
                         "The constructor should have the same number of elements as there are hed strings")

    def test_constructor_multiple_values(self):
        var_manager = VariableManager(self.test_strings2, self.schema, self.defs)
        self.assertIsInstance(var_manager, VariableManager, "Constructor should create a VariableManager from strings")
        self.assertEqual(len(var_manager._variable_map), 3,
                         "Constructor should have right number of variables if multiple")
        self.assertEqual(len(var_manager.hed_strings), len(var_manager._contexts),
                         "Variable managers have context same length as hed_strings")
        var_sum = var_manager.get_variable('var2')
        self.assertIsInstance(var_sum, VariableSummary)
        self.assertEqual(var_sum.number_elements, len(var_manager.hed_strings),
                         "The constructor should have the same number of elements as there are hed strings")

    def test_constructor_unmatched(self):
        with self.assertRaises(HedFileError):
            VariableManager(self.test_strings3, self.schema, self.defs)

    def test_variable_summary(self):
        var_manager = VariableManager(self.test_strings2, self.schema, self.defs)
        self.assertIsInstance(var_manager, VariableManager, "Constructor should create a VariableManager from strings")
        self.assertEqual(len(var_manager._variable_map), 3,
                         "Constructor should have right number of variables if multiple")
        self.assertEqual(len(var_manager.hed_strings), len(var_manager._contexts),
                         "Variable managers have context same length as hed_strings")
        for variable in var_manager.variables:
            var_sum = var_manager.get_variable(variable)
            self.assertEqual(var_sum.number_elements, len(var_manager.hed_strings))
            summary = var_sum.get_summary()
            self.assertIsInstance(summary, dict, "get_summary returns a dictionary summary")

    def test_get_variable_factors(self):
        var_manager = VariableManager(self.test_strings2, self.schema, self.defs)
        self.assertIsInstance(var_manager, VariableManager,
                              "Constructor should create a VariableManager from strings")
        self.assertEqual(len(var_manager._variable_map), 3,
                         "Constructor should have right number of variables if multiple")
        self.assertEqual(len(var_manager.hed_strings), len(var_manager._contexts),
                         "Variable managers have context same length as hed_strings")
        for variable in var_manager.variables:
            var_sum = var_manager.get_variable(variable)
            self.assertEqual(var_sum.number_elements, len(var_manager.hed_strings))
            summary = var_sum.get_summary()
            factors = var_sum.get_variable_factors()
            self.assertIsInstance(factors, pd.DataFrame, "get_variable_factors contains dataframe.")
            self.assertEqual(len(factors), var_sum.number_elements,
                             "get_variable_factors has factors of same length as number of elements")
            self.assertEqual(len(factors.columns), summary["levels"] + 1,
                             'get_variable_factors has factors levels + 1 (direct references)')

    def test_count_events(self):
        list1 = [0, 2, 6, 1, 2, 0, 0]
        number_events, number_multiple, max_multiple = VariableSummary.count_events(list1)
        self.assertEqual(number_events, 4, "count_events should have right number of events")
        self.assertEqual(number_multiple, 3, "count_events should have right number of multiple events")
        self.assertEqual(max_multiple, 6, "count_events should have right maximum multiples")

    def test_get_summary(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False)
        var_manager = VariableManager(hed_strings, self.schema, definitions)
        var_key = var_manager.get_variable('key-assignment')
        sum_key = var_key.get_summary()
        self.assertEqual(sum_key['number events'], 200, "get_summary has right number of events")
        self.assertEqual(sum_key['multiple maximum'], 1, "Get_summary has right multiple maximum")
        self.assertIsInstance(sum_key['level counts'], dict, "get_summary level counts is a dictionary")
        self.assertEqual(sum_key['level counts']['right-sym-cond'], 200, "get_summary level counts value correct.")
        var_face = var_manager.get_variable('face-type')
        sum_key = var_face.get_summary()
        self.assertEqual(sum_key['number events'], 52, "get_summary has right number of events")
        self.assertEqual(sum_key['multiple maximum'], 1, "Get_summary has right multiple maximum")
        self.assertIsInstance(sum_key['level counts'], dict, "get_summary level counts is a dictionary")
        self.assertEqual(sum_key['level counts']['unfamiliar-face-cond'], 20, "get_summary level counts value correct.")


if __name__ == '__main__':
    unittest.main()
