import os
import unittest
from hed import HedString, HedTag, load_schema_version, Sidecar, TabularInput
from hed.errors import HedFileError
from hed.models import DefinitionEntry
from hed.tools import VariableManager, VariableSummary, VariableCounts, get_assembled_strings


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
        cls.schema = schema

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

        summary2 = var_summary2.get_summaries(as_json=False)
        self.assertIsInstance(summary2, dict, "get_summaries should return a dictionary")
        self.assertEqual(len(summary2), 3, "get_summaries should have correct length when updated with tabular input")
        face_type1 = summary1["face-type"]
        face_type2 = summary2["face-type"]
        self.assertEqual(2*face_type1["number_type_events"], face_type2["number_type_events"],
                         "get_summaries should have twice as many type events if the data is summarized twice")

if __name__ == '__main__':
    unittest.main()
