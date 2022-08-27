import os
import unittest
from hed import load_schema_version, Sidecar, TabularInput
from hed.tools import HedTypeFactors, HedTypeVariable, HedVariableManager, get_assembled_strings


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.hed_schema = schema

    def test_constructor(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        self.assertIsInstance(var_manager, HedVariableManager,
                              "Constructor should create a HedVariableManager from a tabular input")
        self.assertEqual(len(var_manager.context_manager.hed_strings), len(var_manager.context_manager.contexts),
                         "Variable managers have context same length as hed_strings")
        self.assertFalse(var_manager._variable_type_map, "constructor has empty map")

    def test_add_type_variable(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        self.assertFalse(var_manager._variable_type_map, "constructor has empty map")
        var_manager.add_type_variable("Condition-variable")
        self.assertEqual(len(var_manager._variable_type_map), 1,
                         "add_type_variable has 1 element map after one type added")
        self.assertIn("condition-variable", var_manager._variable_type_map,
                      "add_type_variable converts type elements to lower case")
        var_manager.add_type_variable("Condition-variable")
        self.assertEqual(len(var_manager._variable_type_map), 1,
                         "add_type_variable has 1 element map after same type is added twice")
        var_manager.add_type_variable("task")
        self.assertEqual(len(var_manager._variable_type_map), 2,
                         "add_type_variable has 2 element map after two types are added")

    def test_get_factor_vectors(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        base_length = len(hed_strings)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        var_manager.add_type_variable("Condition-variable")
        var_manager.add_type_variable("task")
        df_cond = var_manager.get_factor_vectors("condition-variable")
        df_task = var_manager.get_factor_vectors("task")
        self.assertEqual(len(df_cond), base_length, "get_factor_vectors returns df same length as original")
        self.assertEqual(len(df_task), base_length, "get_factor_vectors returns df same length as original if 2 types")
        self.assertEqual(len(df_cond.columns), 10, "get_factor_vectors has right number of factors")
        self.assertEqual(len(df_task.columns), 4, "get_factor_vectors has right number of factors if 2 types")
        df_baloney = var_manager.get_factor_vectors("baloney")
        self.assertIsNone(df_baloney, "get_factor_vectors returns None if no factors")

    def test_get_type_variable(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        var_manager.add_type_variable("Condition-variable")
        type_var = var_manager.get_type_variable_map("condition-variable")
        self.assertIsInstance(type_var, HedTypeVariable,
                              "get_type_variable returns a HedTypeVariable if the key exists")
        type_var = var_manager.get_type_variable_map("baloney")
        self.assertIsNone(type_var, "get_type_variable returns None if the key does not exist")

    def test_get_type_variable_def_names(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        var_manager.add_type_variable("Condition-variable")
        def_names = var_manager.get_type_variable_def_names("condition-variable")
        self.assertEqual(len(def_names), 7,
                         "get_type_variable_def_names has right length if condition-variable exists")
        self.assertIn('scrambled-face-cond', def_names,
                      "get_type_variable_def_names returns a list with a correct value if condition-variable exists")
        def_names = var_manager.get_type_variable_def_names("baloney")
        self.assertFalse(def_names, "get_type_variable_def_names returns empty if the type does not exist")

    def test_get_variable_type_map(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        var_manager.add_type_variable("Condition-variable")
        this_map1 = var_manager.get_type_variable_map("condition-variable")
        self.assertIsInstance(this_map1, HedTypeVariable,
                              "get_type_variable_map returns a non-empty map when key lower case")
        self.assertEqual(len(this_map1.type_variables), 3,
                         "get_type_variable_map map has right length when key lower case")
        this_map2 = var_manager.get_type_variable_map("Condition-variable")
        self.assertIsInstance(this_map2, HedTypeVariable,
                              "get_type_variable_map returns a non-empty map when key upper case")
        self.assertEqual(len(this_map2.type_variables), 3,
                         "get_type_variable_map map has right length when key upper case")

    def test_get_type_variable_factor(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        var_manager.add_type_variable("Condition-variable")
        var_factor1 = var_manager.get_type_variable_factor("condition-variable", "key-assignment")
        self.assertIsInstance(var_factor1, HedTypeFactors,
                              "get_type_variable_factor returns a HedTypeFactors if type variable factor exists")
        var_factor2 = var_manager.get_type_variable_factor("condition-variable", "baloney")
        self.assertIsNone(var_factor2, "get_type_variable_factor returns None if type variable factor does not exist")
        var_factor3 = var_manager.get_type_variable_factor("baloney1", "key-assignment")
        self.assertIsNone(var_factor3, "get_type_variable_factor returns None if type variable does not exist")

    def test_type_variables(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        vars1 = var_manager.type_variables
        self.assertFalse(vars1, "type_variables is empty if no types have been added")
        var_manager.add_type_variable("Condition-variable")
        var_manager.add_type_variable("task")
        vars2 = var_manager.type_variables
        self.assertIsInstance(vars2, list, "type_variables returns a list ")
        self.assertEqual(len(vars2), 2, "type_variables return list is right length")

    def test_summarize_all(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        def_mapper = self.input_data._def_mapper
        var_manager = HedVariableManager(hed_strings, self.hed_schema, def_mapper)
        summary1 = var_manager.summarize_all()
        self.assertIsInstance(summary1, dict, "summarize_all returns a dictionary when nothing has been added")
        self.assertFalse(summary1, "summarize_all return dictionary is empty when nothing has been added")
        vars1 = var_manager.type_variables
        self.assertFalse(vars1, "type_variables is empty if no types have been added")
        var_manager.add_type_variable("Condition-variable")
        var_manager.add_type_variable("task")
        summary2 = var_manager.summarize_all()
        self.assertIsInstance(summary2, dict, "summarize_all returns a dictionary after additions")
        self.assertEqual(len(summary2), 2,
                         "summarize_all return dictionary has 2 entries when 2 types have been added")
        summary3 = var_manager.summarize_all(as_json=True)
        self.assertIsInstance(summary3, str,
                              "summarize_all dictionary is returned as a string when as_json is True")


if __name__ == '__main__':
    unittest.main()
