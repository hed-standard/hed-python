import os
import unittest
from hed import HedString, HedTag, load_schema_version, Sidecar, TabularInput
from hed.errors import HedFileError
from hed.models import DefinitionEntry
from hed.tools import HedTypeVariable, get_assembled_strings, HedContextManager


class Test(unittest.TestCase):

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
        cls.hed_schema = schema

    def test_constructor(self):
        test_strings1 = [HedString(hed, hed_schema=self.hed_schema) for hed in self.test_strings1]
        var_manager = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema, self.defs)
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager from strings")
        self.assertEqual(len(var_manager._variable_map), 8,
                         "Constructor ConditionVariables should have the right length")

    def test_constructor_from_tabular_input(self):
        test_strings1 = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False).gathered_defs
        var_manager = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema, definitions)
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager from a tabular input")

    def test_constructor_variable_caps(self):
        test_strings1 = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False).gathered_defs
        var_manager = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema,
                                      definitions, variable_type="Condition-variable")
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager variable caps")

    def test_constructor_variable_task(self):
        test_strings1 = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False).gathered_defs
        var_manager = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema,
                                      definitions, variable_type="task")
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager variable task")

    def test_constructor_multiple_values(self):
        test_strings1 = [HedString(hed, hed_schema=self.hed_schema) for hed in self.test_strings2]
        var_manager = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema, self.defs)
        self.assertIsInstance(var_manager, HedTypeVariable,
                              "Constructor should create a HedVariableManager from strings")
        self.assertEqual(len(var_manager._variable_map), 3,
                         "Constructor should have right number of type_variables if multiple")

    def test_constructor_unmatched(self):
        test_strings1 = [HedString(hed, hed_schema=self.hed_schema) for hed in self.test_strings3]
        with self.assertRaises(HedFileError):
            HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema, self.defs)

    def test_summarize_variables(self):
        test_strings1 = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False).gathered_defs
        var_manager = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema, definitions)
        summary = var_manager.summarize()
        self.assertIsInstance(summary, dict, "summarize produces a dictionary if not json")
        self.assertEqual(len(summary), 3, "Summarize_variables has right number of condition type_variables")
        self.assertIn("key-assignment", summary, "summarize has a correct key")
        summary_json = var_manager.summarize(as_json=True)
        self.assertIsInstance(summary_json, str, "summarize as json returns a string")

    def test_extract_definition_variables(self):
        test_strings1 = [HedString(hed, hed_schema=self.hed_schema) for hed in self.test_strings1]
        var_manager = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema, self.defs)
        var_levels = var_manager._variable_map['var3'].levels
        self.assertNotIn('cond3/7', var_levels,
                         "_extract_definition_variables before extraction def/cond3/7 not in levels")
        tag = HedTag("Def/Cond3/7", hed_schema=self.hed_schema)
        var_manager._extract_definition_variables(tag, 5)
        self.assertIn('cond3/7', var_levels,
                      "_extract_definition_variables after extraction def/cond3/7 not in levels")

    def test_get_variable_names(self):
        test_strings1 = [HedString(hed, hed_schema=self.hed_schema) for hed in self.test_strings1]
        conditions1 = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema, self.defs)
        list1 = conditions1.get_variable_names()
        self.assertEqual(len(list1), 8, "get_variable_tags list should have the right length")

    def test_get_variable_def_names(self):
        test_strings1 = [HedString(hed, hed_schema=self.hed_schema) for hed in self.test_strings1]
        conditions1 = HedTypeVariable(HedContextManager(test_strings1, self.hed_schema), self.hed_schema, self.defs)
        list1 = conditions1.get_variable_def_names()
        self.assertEqual(len(list1), 5, "get_variable_def_names list should have the right length")


if __name__ == '__main__':
    unittest.main()
