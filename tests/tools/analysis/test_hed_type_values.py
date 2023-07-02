import os
import unittest
from pandas import DataFrame
from hed.errors.exceptions import HedFileError
from hed.models import DefinitionEntry
from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.analysis.hed_type_values import HedTypeValues
from hed.models.df_util import get_assembled


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        cls.test_strings1 = ["Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
                             "(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4",
                             '(Def/Cond1, Offset)',
                             'White, Black, Condition-variable/Wonder, Condition-variable/Fast',
                             '',
                             '(Def/Cond2, Onset)',
                             '(Def/Cond3/4.3, Onset)',
                             'Arm, Leg, Condition-variable/Fast']
        cls.test_strings2 = ["Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
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
                                          '../../data/bids_tests/eeg_ds003645s_hed'))
        cls.events_path = os.path.realpath(os.path.join(bids_root_path,
                                           'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        cls.sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        cls.schema = schema

    def test_constructor(self):
        strings1 = [HedString(hed, hed_schema=self.schema) for hed in self.test_strings1]
        con_man = HedContextManager(strings1, hed_schema=self.schema)
        type_var = HedTypeValues(con_man, self.defs, 'run-01')
        self.assertIsInstance(type_var, HedTypeValues,
                              "Constructor should create a HedTypeManager from strings")
        self.assertEqual(len(type_var._type_value_map), 8,
                         "Constructor ConditionVariables should have the right length")

    def test_constructor_from_tabular_input(self):
        sidecar1 = Sidecar(self.sidecar_path, name='face_sub1_json')
        input_data = TabularInput(self.events_path, sidecar=sidecar1, name="face_sub1_events")
        test_strings1, definitions = get_assembled(input_data, sidecar1, self.schema, extra_def_dicts=None,
                                                   join_columns=True, shrink_defs=True, expand_defs=False)
        var_manager = HedTypeValues(HedContextManager(test_strings1, self.schema), definitions, 'run-01')
        self.assertIsInstance(var_manager, HedTypeValues,
                              "Constructor should create a HedTypeManager from a tabular input")

    def test_constructor_variable_caps(self):
        sidecar1 = Sidecar(self.sidecar_path, name='face_sub1_json')
        input_data = TabularInput(self.events_path, sidecar1, name="face_sub1_events")
        test_strings1, definitions = get_assembled(input_data, sidecar1, self.schema, extra_def_dicts=None,
                                                   join_columns=True, shrink_defs=True, expand_defs=False)
        var_manager = HedTypeValues(HedContextManager(test_strings1, self.schema),
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
        self.assertEqual(len(var_manager._type_value_map), 3,
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
        var_levels = var_manager._type_value_map['var3'].levels
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
