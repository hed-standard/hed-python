import os
import unittest
from pandas import DataFrame
from hed.errors.exceptions import HedFileError
from hed.models import DefinitionDict
from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_types import HedTypes
from hed.models.df_util import get_assembled


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        # Set up the definition dictionary
        defs = [HedString('(Definition/Cond1, (Condition-variable/Var1, Circle, Square))', hed_schema=schema),
                HedString('(Definition/Cond2, (condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere))', 
                          hed_schema=schema),
                HedString('(Definition/Cond3, (Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross))',
                          hed_schema=schema),
                HedString('(Definition/Cond4, (Condition-variable, Apple, Banana))', hed_schema=schema),
                HedString('(Definition/Cond5, (Condition-variable/Lumber, Apple, Banana))', hed_schema=schema),
                HedString('(Definition/Cond6/#, (Condition-variable/Lumber, Label/#, Apple, Banana))', 
                          hed_schema=schema)]
        def_dict = DefinitionDict()
        for value in defs:
            def_dict.check_for_definitions(value)

        test_strings1 = ["Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset)",
                         "(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4",
                         "(Def/Cond1, Offset)",
                         "White, Black, Condition-variable/Wonder, Condition-variable/Fast",
                         "",
                         "(Def/Cond2, Onset)",
                         "(Def/Cond3/4.3, Onset)",
                         "Arm, Leg, Condition-variable/Fast"]
        test_onsets1 = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        df1 = DataFrame(test_onsets1, columns=['onset'])
        df1['HED'] = test_strings1
        input_data = TabularInput(df1)
        event_man1 = EventManager(input_data, schema, extra_defs=def_dict)
        event_man1.def_dict = def_dict
        cls.event_man1 = event_man1
        cls.test_strings2 = ["Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
                             "Yellow",
                             "Def/Cond2, (Def/Cond6/4, Onset)",
                             "Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)",
                             "Def/Cond2, Def/Cond6/4"]
        cls.test_strings3 = ['(Def/Cond3, Offset)']

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids_tests/eeg_ds003645s_hed'))
        cls.events_path = os.path.realpath(os.path.join(bids_root_path,
                                           'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        cls.sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        cls.schema = schema

    def test_constructor(self):
        type_var = HedTypes(self.event_man1, 'test-it')
        self.assertIsInstance(type_var, HedTypes,"Constructor should create a HedTypes from an event manager")
        self.assertEqual(len(type_var._type_map), 8,
                         "Constructor ConditionVariables should have the right length")

    def test_constructor_from_tabular_input(self):
        sidecar1 = Sidecar(self.sidecar_path, name='face_sub1_json')
        input_data = TabularInput(self.events_path, sidecar=sidecar1, name="face_sub1_events")
        event_man = EventManager(input_data, self.schema)
        var_man = HedTypes(event_man, 'face')
        self.assertIsInstance(var_man, HedTypes,"Constructor should create a HedTypeManager from a tabular input")

    def test_constructor_variable_caps(self):
        sidecar1 = Sidecar(self.sidecar_path, name='face_sub1_json')
        input_data = TabularInput(self.events_path, sidecar1, name="face_sub1_events")
        event_man = EventManager(input_data, self.schema)
        var_manager = HedTypes(HedContextManager(test_strings1, self.schema),
                                    definitions, 'run-01', type_tag="Condition-variable")
        self.assertIsInstance(var_manager, HedTypeValues,
                              "Constructor should create a HedTypeManager variable caps")

    def test_constructor_variable_task(self):
        sidecar1 = Sidecar(self.sidecar_path, name='face_sub1_json')
        input_data = TabularInput(self.events_path, sidecar=sidecar1, name="face_sub1_events")
        test_strings1, definitions = get_assembled(input_data, sidecar1, self.schema, extra_def_dicts=None,
                                                   join_columns=True, shrink_defs=True, expand_defs=False)
        var_manager = HedTypeValues(HedContextManager(test_strings1, self.schema),
                                    definitions, 'run-01', type_tag="task")
        self.assertIsInstance(var_manager, HedTypeValues,
                              "Constructor should create a HedTypeManager variable task")

    def test_constructor_multiple_values(self):
        hed_strings = [HedString(hed, self.schema) for hed in self.test_strings2]
        var_manager = HedTypeValues(HedContextManager(hed_strings, self.schema), self.defs, 'run-01')
        self.assertIsInstance(var_manager, HedTypeValues,
                              "Constructor should create a HedTypeManager from strings")
        self.assertEqual(len(var_manager._type_map), 3,
                         "Constructor should have right number of type_variables if multiple")

    def test_constructor_unmatched(self):
        hed_strings = [HedString(hed, self.schema) for hed in self.test_strings3]
        with self.assertRaises(HedFileError) as context:
            HedTypeValues(HedContextManager(hed_strings, self.schema), self.defs, 'run-01')
        self.assertEqual(context.exception.args[0], 'UnmatchedOffset')

    def test_get_variable_factors(self):
        sidecar1 = Sidecar(self.sidecar_path, name='face_sub1_json')
        input_data = TabularInput(self.events_path, sidecar1, name="face_sub1_events")
        test_strings1, definitions = get_assembled(input_data, sidecar1, self.schema, extra_def_dicts=None,
                                                   join_columns=True, shrink_defs=True, expand_defs=False)
        var_manager = HedTypeValues(HedContextManager(test_strings1, self.schema), definitions, 'run-01')
        df_new1 = var_manager.get_type_factors()
        self.assertIsInstance(df_new1, DataFrame)
        self.assertEqual(len(df_new1), 200)
        self.assertEqual(len(df_new1.columns), 7)
        df_new2 = var_manager.get_type_factors(type_values=["face-type"])
        self.assertEqual(len(df_new2), 200)
        self.assertEqual(len(df_new2.columns), 3)
        df_new3 = var_manager.get_type_factors(type_values=["junk"])
        self.assertIsNone(df_new3)

    def test_str(self):
        sidecar1 = Sidecar(self.sidecar_path, name='face_sub1_json')
        input_data = TabularInput(self.events_path, sidecar1, name="face_sub1_events")
        test_strings1, definitions = get_assembled(input_data, sidecar1, self.schema, extra_def_dicts=None,
                                                   join_columns=True, shrink_defs=True, expand_defs=False)
        var_manager = HedTypeValues(HedContextManager(test_strings1, self.schema), definitions, 'run-01')
        new_str = str(var_manager)
        self.assertIsInstance(new_str, str)

    def test_summarize_variables(self):
        sidecar1 = Sidecar(self.sidecar_path, name='face_sub1_json')
        input_data = TabularInput(self.events_path, sidecar1, name="face_sub1_events")
        test_strings1, definitions = get_assembled(input_data, sidecar1, self.schema, extra_def_dicts=None,
                                                   join_columns=True, shrink_defs=True, expand_defs=False)
        var_manager = HedTypeValues(HedContextManager(test_strings1, self.schema), definitions, 'run-01')
        summary = var_manager.get_summary()
        self.assertIsInstance(summary, dict, "get_summary produces a dictionary if not json")
        self.assertEqual(len(summary), 3, "Summarize_variables has right number of condition type_variables")
        self.assertIn("key-assignment", summary, "get_summary has a correct key")

    def test_extract_definition_variables(self):
        hed_strings = [HedString(hed, self.schema) for hed in self.test_strings1]
        var_manager = HedTypeValues(HedContextManager(hed_strings, self.schema), self.defs, 'run-01')
        var_levels = var_manager._type_map['var3'].levels
        self.assertNotIn('cond3/7', var_levels,
                         "_extract_definition_variables before extraction def/cond3/7 not in levels")
        tag = HedTag("Def/Cond3/7", hed_schema=self.schema)
        var_manager._extract_definition_variables(tag, 5)
        self.assertIn('cond3/7', var_levels,
                      "_extract_definition_variables after extraction def/cond3/7 not in levels")

    def test_get_variable_names(self):
        hed_strings = [HedString(hed, self.schema) for hed in self.test_strings1]
        conditions1 = HedTypeValues(HedContextManager(hed_strings, self.schema), self.defs, 'run-01')
        list1 = conditions1.get_type_value_names()
        self.assertEqual(len(list1), 8, "get_variable_tags list should have the right length")

    def test_get_variable_def_names(self):
        hed_strings = [HedString(hed, self.schema) for hed in self.test_strings1]
        conditions1 = HedTypeValues(HedContextManager(hed_strings, self.schema), self.defs, 'run-01')
        list1 = conditions1.get_type_def_names()
        self.assertEqual(len(list1), 5, "get_type_def_names list should have the right length")


if __name__ == '__main__':
    unittest.main()
