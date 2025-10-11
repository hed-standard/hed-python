import os
import unittest
from hed.models import DefinitionDict
from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.tools.analysis.hed_type_defs import HedTypeDefs
from hed.schema.hed_schema_io import load_schema_version


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        defs = [
            HedString("(Definition/Cond1, (Condition-variable/Var1, Circle, Square))", hed_schema=schema),
            HedString(
                "(Definition/Cond2, (condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere))", hed_schema=schema
            ),
            HedString("(Definition/Cond3/#, (Condition-variable/Var3, Label/#, Ellipse, Cross))", hed_schema=schema),
            HedString("(Definition/Cond4, (Condition-variable, Rectangle, Triangle))", hed_schema=schema),
            HedString("(Definition/Cond5, (Condition-variable/Lumber, Action, Sensory-presentation))", hed_schema=schema),
            HedString("(Definition/Cond6/#, (Condition-variable/Lumber, Label/#, Agent, Move))", hed_schema=schema),
        ]
        def_dict = DefinitionDict()
        for value in defs:
            def_dict.check_for_definitions(value)

        cls.test_strings1 = [
            "Sensory-event,(Def/Cond1,(Elbow, Hip, Condition-variable/Trouble),Onset)",
            "(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4",
            "(Def/Cond1, Offset)",
            "White, Black, Condition-variable/Wonder, Condition-variable/Fast",
            "",
            "(Def/Cond2, Onset)",
            "(Def/Cond3/4.3, Onset)",
            "Upper-arm, Head, Condition-variable/Fast",
        ]
        cls.definitions1 = def_dict
        bids_root_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_hed")
        )
        events_path = os.path.realpath(
            os.path.join(bids_root_path, "sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv")
        )
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, "task-FacePerception_events.json"))
        sidecar1 = Sidecar(sidecar_path, name="face_sub1_json")
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.schema = schema
        cls.sidecar1 = sidecar1

    def test_constructor(self):
        def_man = HedTypeDefs(self.definitions1)
        self.assertIsInstance(def_man, HedTypeDefs, "Constructor should create a HedTypeDefinitions directly from a dict")
        self.assertEqual(len(def_man.def_map), 6, "Constructor condition_map should have the right length")
        self.assertEqual(
            len(def_man.def_map),
            len(def_man.definitions),
            "Constructor condition_map should be the same length as the type_defs dictionary",
        )

    def test_constructor_from_sidecar(self):
        definitions = self.sidecar1.get_def_dict(self.schema)
        def_man = HedTypeDefs(definitions)
        self.assertIsInstance(def_man, HedTypeDefs, "Constructor should create a HedTypeDefinitions from a tabular input")
        self.assertEqual(len(def_man.def_map), 8, "Constructor condition_map should have the right length")
        self.assertEqual(len(def_man.definitions), len(definitions))
        defs = def_man.type_def_names
        self.assertIsInstance(defs, list)
        self.assertEqual(len(defs), 8)

    def test_constructor_from_tabular(self):
        def_dict = self.input_data.get_def_dict(self.schema)
        def_man = HedTypeDefs(def_dict, type_tag="Condition-variable")
        self.assertIsInstance(def_man, HedTypeDefs)
        self.assertEqual(len(def_man.def_map), 8)
        self.assertEqual(len(def_man.type_map), 3)
        self.assertEqual(len(def_man.type_def_names), 8)

    def test_get_type_values_tabular(self):
        def_dict = self.input_data.get_def_dict(self.schema)
        def_man = HedTypeDefs(def_dict, type_tag="Condition-variable")
        test_str = HedString("Sensory-event, Def/Right-sym-cond", self.schema)
        values1 = def_man.get_type_values(test_str)
        self.assertIsInstance(values1, list)
        self.assertEqual(1, len(values1))

    def test_get_type_values(self):
        def_man = HedTypeDefs(self.definitions1)
        item1 = HedString("Sensory-event,((Red,Blue)),", self.schema)
        vars1 = def_man.get_type_values(item1)
        self.assertFalse(vars1, "get_type_values should return None if no condition type_variables")
        item2 = HedString("Sensory-event,(Def/Cond1,(Red,Blue,Condition-variable/Trouble))", self.schema)
        vars2 = def_man.get_type_values(item2)
        self.assertEqual(1, len(vars2), "get_type_values should return correct number of condition type_variables")
        item3 = HedString(
            "Sensory-event,(Def/Cond1,(Red,Blue,Condition-variable/Trouble)),"
            + "(Def/Cond2),Green,Yellow,Def/Cond5, Def/Cond6/4, Description/Tell me",
            self.schema,
        )
        vars3 = def_man.get_type_values(item3)
        self.assertEqual(len(vars3), 5, "get_type_values should return multiple condition type_variables")

    def test_extract_def_names(self):
        def_man = HedTypeDefs(self.definitions1)
        a = def_man.extract_def_names(HedTag("Def/Cond3/4", hed_schema=self.schema))
        self.assertEqual(len(a), 1, "get_def_names returns 1 item if single tag")
        self.assertEqual(a[0], "cond3", "get_def_names returns the correct item if single tag")
        b = def_man.extract_def_names(HedTag("Def/Cond3/4", hed_schema=self.schema), no_value=False)
        self.assertEqual(len(b), 1, "get_def_names returns 1 item if single tag")
        self.assertEqual(b[0], "cond3/4", "get_def_names returns the correct item if single tag")
        c = def_man.extract_def_names(HedString("(Def/Cond3/5,(Red, Blue))", hed_schema=self.schema))
        self.assertEqual(len(c), 1, "get_def_names returns 1 item if single group def")
        self.assertEqual(c[0], "cond3", "get_def_names returns the correct item if single group def")
        d = def_man.extract_def_names(
            HedString("(Def/Cond3/6,(Red, Blue, Def/Cond1), Def/Cond2)", hed_schema=self.schema), no_value=False
        )
        self.assertEqual(len(d), 3, "get_def_names returns right number of items if multiple defs")
        self.assertEqual(d[0], "cond3/6", "get_def_names returns the correct item if multiple def")
        e = def_man.extract_def_names(HedString("((Red, Blue, (Green), Black))", hed_schema=self.schema))
        self.assertFalse(e, "get_def_names returns no items if no defs")

    def test_split_name(self):
        name1, val1 = HedTypeDefs.split_name("")
        self.assertIsNone(name1, "split_name should return None split name for empty name")
        self.assertIsNone(val1, "split_name should return None split value for empty name")
        name2, val2 = HedTypeDefs.split_name("lumber")
        self.assertEqual(name2, "lumber", "split_name should return name if no split value")
        self.assertEqual(val2, "", "split_name should return empty string if no split value")
        name3, val3 = HedTypeDefs.split_name("Lumber/5.23", lowercase=False)
        self.assertEqual(name3, "Lumber", "split_name should return name if split value")
        self.assertEqual(val3, "5.23", "split_name should return value as string if split value")
        name4, val4 = HedTypeDefs.split_name("Lumber/5.23")
        self.assertEqual(name4, "lumber", "split_name should return name if split value")
        self.assertEqual(val4, "5.23", "split_name should return value as string if split value")


if __name__ == "__main__":
    unittest.main()
