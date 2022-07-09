import os
import unittest
from hed import HedString, HedTag, load_schema_version, Sidecar, TabularInput
from hed.models import DefinitionEntry
from hed.tools import DefinitionManager


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        cls.test_strings1 = [HedString('Sensory-event,(Def/Cond1,(Red, Blue),Onset),(Def/Cond2,Onset),Green,Yellow',
                                       hed_schema=schema),
                             HedString('(Def/Cond1, Offset)', hed_schema=schema),
                             HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast',
                                       hed_schema=schema),
                             HedString('', hed_schema=schema),
                             HedString('(Def/Cond2, Onset)', hed_schema=schema),
                             HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
                             HedString('Arm, Leg, Condition-variable/Fast', hed_schema=schema)]

        # def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=schema)
        # def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=schema)
        # def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
        #                  hed_schema=schema)
        # def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=schema)
        # cls.definitions1 = {'cond1': DefinitionEntry('Cond1', def1, False, None),
        #                     'cond2': DefinitionEntry('Cond2', def2, False, None),
        #                     'cond3': DefinitionEntry('Cond3', def3, True, None),
        #                     'cond4': DefinitionEntry('Cond4', def4, False, None)}

        def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=schema)
        def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=schema)
        def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
                         hed_schema=schema)
        def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=schema)
        def5 = HedString('(Condition-variable/Lumber, Apple, Banana)', hed_schema=schema)
        def6 = HedString('(Condition-variable/Lumber, Label/#, Apple, Banana)', hed_schema=schema)
        cls.definitions1 = {'Cond1': DefinitionEntry('Cond1', def1, False, None),
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

    def test_constructor(self):
        def_man = DefinitionManager(self.definitions1, self.schema)
        self.assertIsInstance(def_man, DefinitionManager,
                              "Constructor should create a DefinitionManager directly from a dict")
        self.assertEqual(len(def_man.variable_map), 6, "Constructor condition_map should have the right length")
        self.assertEqual(len(def_man.variable_map), len(def_man.definitions),
                         "Constructor condition_map should be the same length as the definitions dictionary")

    def test_constructor_from_tabular_input(self):
        definitions = self.input_data.get_definitions(as_strings=False)
        def_man = DefinitionManager(definitions, self.schema)
        self.assertIsInstance(def_man, DefinitionManager,
                              "Constructor should create a DefinitionManager from a tabular input")
        self.assertEqual(len(def_man.variable_map), 17, "Constructor condition_map should have the right length")
        self.assertEqual(len(def_man.variable_map), len(def_man.definitions),
                         "Constructor condition_map should be the same length as the definitions dictionary")

    def test_get_vars(self):
        def_man = DefinitionManager(self.definitions1, self.schema)
        item1 = HedString(f"Sensory-event,((Red,Blue)),", self.schema)
        vars1 = def_man.get_vars(item1)
        self.assertFalse(vars1, "get_vars should return None if no condition variables")
        item2 = HedString(f"Sensory-event,(Def/Cond1,(Red,Blue,Condition-variable/Trouble))", self.schema)
        vars2 = def_man.get_vars(item2)
        self.assertEqual(len(vars2), 1, "get_vars should return correct number of condition variables")
        item3 = HedString(f"Sensory-event,(Def/Cond1,(Red,Blue,Condition-variable/Trouble)),"
                          f"(Def/Cond2),Green,Yellow,Def/Cond5, Def/Cond6/4", self.schema)
        vars3 = def_man.get_vars(item3)
        self.assertEqual(len(vars3), 5, "get_vars should return multiple condition variables")

    def test_get_def_names(self):
        def_man = DefinitionManager(self.definitions1, self.schema)
        a = def_man.get_def_names(HedTag('Def/Cond3/4', hed_schema=self.schema))
        self.assertEqual(len(a), 1, "get_def_names returns 1 item if single tag")
        self.assertEqual(a[0], 'cond3', "get_def_names returns the correct item if single tag")
        b = def_man.get_def_names(HedTag('Def/Cond3/4', hed_schema=self.schema), no_value=False)
        self.assertEqual(len(b), 1, "get_def_names returns 1 item if single tag")
        self.assertEqual(b[0], 'cond3/4', "get_def_names returns the correct item if single tag")
        c = def_man.get_def_names(HedString('(Def/Cond3/5,(Red, Blue))', hed_schema=self.schema))
        self.assertEqual(len(c), 1, "get_def_names returns 1 item if single group def")
        self.assertEqual(c[0], 'cond3', "get_def_names returns the correct item if single group def")
        d = def_man.get_def_names(HedString('(Def/Cond3/6,(Red, Blue, Def/Cond1), Def/Cond2)', hed_schema=self.schema),
                                  no_value=False)
        self.assertEqual(len(d), 3, "get_def_names returns right number of items if multiple defs")
        self.assertEqual(d[0], 'cond3/6', "get_def_names returns the correct item if multiple def")
        e = def_man.get_def_names(HedString('((Red, Blue, (Green), Black))'))
        self.assertFalse(e, "get_def_names returns no items if no defs")

    def test_split_name(self):
        name1, val1 = DefinitionManager.split_name('')
        self.assertIsNone(name1, "split_name should return None split name for empty name")
        self.assertIsNone(val1, "split_name should return None split value for empty name")
        name2, val2 = DefinitionManager.split_name('lumber')
        self.assertEqual(name2, 'lumber', 'split_name should return name if no split value')
        self.assertEqual(val2, '', 'split_name should return empty string if no split value')
        name3, val3 = DefinitionManager.split_name('Lumber/5.23', lowercase=False)
        self.assertEqual(name3, 'Lumber', 'split_name should return name if split value')
        self.assertEqual(val3, '5.23', 'split_name should return value as string if split value')
        name4, val4 = DefinitionManager.split_name('Lumber/5.23')
        self.assertEqual(name4, 'lumber', 'split_name should return name if split value')
        self.assertEqual(val4, '5.23', 'split_name should return value as string if split value')


if __name__ == '__main__':
    unittest.main()
