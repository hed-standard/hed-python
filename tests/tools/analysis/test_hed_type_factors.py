import os
import unittest
from hed import HedString, HedTag, load_schema_version, Sidecar, TabularInput
from hed.errors import HedFileError
from hed.models import DefinitionEntry
<<<<<<< HEAD:tests/tools/analysis/test_hed_type_factors.py
from hed.tools import HedContextManager, HedTypeVariable, HedTypeFactors, get_assembled_strings
=======
from hed.tools import VariableManager, VariableSummary, VariableCounts, get_assembled_strings
>>>>>>> d27d7b69f9b65ee020625cf4eea5a11cf163805c:tests/tools/analysis/test_variable_summary.py


class Test(unittest.TestCase):
    # TODO: Test different encodings

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        cls.test_strings1 = [f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
                             f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4",
                             '(Def/Cond1, Offset)',
                             'White, Black, Condition-variable/Wonder, Condition-variable/Fast',
                             '',
                             '(Def/Cond2, Onset)',
                             '(Def/Cond3/4.3, Onset)',
                             'Arm, Leg, Condition-variable/Fast']
        cls.test_strings2 = [f"Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
                             "Yellow",
                             "Def/Cond2, (Def/Cond6/4, Onset)",
                             "Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)",
                             "Def/Cond2, Def/Cond6/4"]
        cls.test_strings3 = ['(Def/Cond3, Offset)']

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

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.schema = schema

<<<<<<< HEAD:tests/tools/analysis/test_hed_type_factors.py
    def test_constructor(self):
        var_manager = HedTypeVariable(HedContextManager(self.test_strings1, self.schema), self.schema, self.defs)
        var1_summary = var_manager.get_variable('var1')
        self.assertIsInstance(var1_summary, HedTypeFactors)

    def test_constructor_from_tabular_input(self):
        test_strings1 = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False)
        var_manager = HedTypeVariable(HedContextManager(test_strings1, self.schema), self.schema, definitions)
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager from a tabular input")
        var_sum = var_manager.get_variable('face-type')
        self.assertIsInstance(var_sum, HedTypeFactors)

    def test_constructor_multiple_values(self):
        var_manager = HedTypeVariable(HedContextManager(self.test_strings2, self.schema), self.schema, self.defs)
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager from strings")
        self.assertEqual(len(var_manager._variable_map), 3,
                         "Constructor should have right number of type_variables if multiple")
        var_sum = var_manager.get_variable('var2')
        self.assertIsInstance(var_sum, HedTypeFactors)

    def test_constructor_unmatched(self):
        with self.assertRaises(HedFileError):
            HedTypeVariable(HedContextManager(self.test_strings3, self.schema), self.schema, self.defs)

    def test_variable_summary(self):
        var_manager = HedTypeVariable(HedContextManager(self.test_strings2, self.schema), self.schema, self.defs)
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager from strings")
        self.assertEqual(len(var_manager._variable_map), 3,
                         "Constructor should have right number of type_variables if multiple")
        for variable in var_manager.get_variable_names():
            var_sum = var_manager.get_variable(variable)
            summary = var_sum.get_summary()
            self.assertIsInstance(summary, dict, "get_summary returns a dictionary summary")

    def test_get_variable_factors(self):
        var_manager = HedTypeVariable(HedContextManager(self.test_strings2, self.schema), self.schema, self.defs)
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager from strings")
        self.assertEqual(len(var_manager._variable_map), 3,
                         "Constructor should have right number of type_variables if multiple")

        for variable in var_manager.get_variable_names():
            var_sum = var_manager.get_variable(variable)
            summary = var_sum.get_summary()
            factors = var_sum.get_factors()
            self.assertIsInstance(factors, pd.DataFrame, "get_factors contains dataframe.")
            self.assertEqual(len(factors), var_sum.number_elements,
                             "get_factors has factors of same length as number of elements")
            self.assertEqual(len(factors.columns), summary["levels"] + 1,
                             'get_factors has factors levels + 1 (direct references)')

    def test_count_events(self):
        list1 = [0, 2, 6, 1, 2, 0, 0]
        number_events1, number_multiple1, max_multiple1 = HedTypeFactors.count_events(list1)
        self.assertEqual(number_events1, 4, "count_events should have right number of events")
        self.assertEqual(number_multiple1, 3, "count_events should have right number of multiple events")
        self.assertEqual(max_multiple1, 6, "count_events should have right maximum multiples")
        list2 = []
        number_events2, number_multiple2, max_multiple2 = HedTypeFactors.count_events(list2)
        self.assertEqual(number_events2, 0, "count_events should have 0 events for empty list")
        self.assertEqual(number_multiple2, 0, "count_events should have 0 multiples for empty list")
        self.assertIsNone(max_multiple2, "count_events should not have a max multiple for empty list")

    def test_get_summary(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False)
        var_manager = HedTypeVariable(HedContextManager(hed_strings, self.schema), self.schema, definitions)
        var_key = var_manager.get_variable('key-assignment')
        sum_key = var_key.get_summary()
        self.assertEqual(sum_key['number_type_events'], 200, "get_summary has right number of events")
        self.assertEqual(sum_key['multiple_event_maximum'], 1, "Get_summary has right multiple maximum")
        self.assertIsInstance(sum_key['level_counts'], dict, "get_summary level counts is a dictionary")
        self.assertEqual(sum_key['level_counts']['right-sym-cond'], 200, "get_summary level counts value correct.")
        var_face = var_manager.get_variable('face-type')
        sum_key = var_face.get_summary()
        self.assertEqual(sum_key['number_type_events'], 52, "get_summary has right number of events")
        self.assertEqual(sum_key['multiple_event_maximum'], 1, "Get_summary has right multiple maximum")
        self.assertIsInstance(sum_key['level_counts'], dict, "get_summary level counts is a dictionary")
        self.assertEqual(sum_key['level_counts']['unfamiliar-face-cond'], 20, "get_summary level counts value correct.")
=======
    def test_variable_summary_get_summaries(self):
        hed_strings1 = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        definitions1 = self.input_data.get_definitions(as_strings=False)
        var_manager1 = VariableManager(hed_strings1, self.schema, definitions1)
        var_summary1 = VariableSummary(variable_type="condition-variable")
        self.assertIsInstance(var_summary1, VariableSummary,
                              "Constructor should create a VariableSummary")
        summary1 = var_summary1.get_summaries(as_json=False)
        self.assertIsInstance(summary1, dict, "get_summaries should return a dictionary when empty")
        self.assertFalse(summary1, "get_summaries should create a empty dictionary before updates")
        for man_var in var_manager1.variables:
            var_factor = var_manager1.get_variable(man_var)
            var_summary1.update_summary(var_factor)

        summary1 = var_summary1.get_summaries(as_json=False)
        self.assertIsInstance(summary1, dict, "get_summaries should return a dictionary")
        self.assertEqual(len(summary1), 3, "get_summaries should have correct length when updated with tabular input")

        var_summary1 = VariableSummary(variable_type="condition-variable")
        self.assertIsInstance(var_summary1, VariableSummary,
                              "Constructor should create a VariableSummary")
        summary1 = var_summary1.get_summaries(as_json=False)
        self.assertIsInstance(summary1, dict, "get_summaries should return a dictionary when empty")
        self.assertFalse(summary1, "get_summaries should create a empty dictionary before updates")
        for man_var in var_manager1.variables:
            var_factor = var_manager1.get_variable(man_var)
            var_summary1.update_summary(var_factor)

        summary1 = var_summary1.get_summaries(as_json=False)
        self.assertIsInstance(summary1, dict, "get_summaries should return a dictionary")
        self.assertEqual(len(summary1), 3, "get_summaries should have correct length when updated with tabular input")

        hed_strings2 = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        definitions2 = self.input_data.get_definitions(as_strings=False)
        var_manager2 = VariableManager(hed_strings2, self.schema, definitions2)
        var_summary2 = VariableSummary(variable_type="condition-variable")
        for man_var in var_manager2.variables:
            var_factor = var_manager2.get_variable(man_var)
            var_summary2.update_summary(var_factor)

        hed_strings2a = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        definitions2a = self.input_data.get_definitions(as_strings=False)
        var_manager2a = VariableManager(hed_strings2a, self.schema, definitions2a)
        for man_var in var_manager2.variables:
            var_factor = var_manager2a.get_variable(man_var)
            var_summary2.update_summary(var_factor)
>>>>>>> d27d7b69f9b65ee020625cf4eea5a11cf163805c:tests/tools/analysis/test_variable_summary.py

        summary2 = var_summary2.get_summaries(as_json=False)
        self.assertIsInstance(summary2, dict, "get_summaries should return a dictionary")
        self.assertEqual(len(summary2), 3, "get_summaries should have correct length when updated with tabular input")
        face_type1 = summary1["face-type"]
        face_type2 = summary2["face-type"]
        self.assertEqual(2*face_type1["number_type_events"], face_type2["number_type_events"],
                         "get_summaries should have twice as many type events if the data is summarized twice")

if __name__ == '__main__':
    unittest.main()
