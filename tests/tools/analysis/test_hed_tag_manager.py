import os
import unittest
from pandas import DataFrame
from hed.models import DefinitionDict
from hed.models.hed_string import HedString
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_tag_manager import HedTagManager


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.2.0")
        # Set up the definition dictionary
        defs = [
            HedString("(Definition/Cond1, (Condition-variable/Var1, Circle, Square))", hed_schema=schema),
            HedString(
                "(Definition/Cond2, (condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere))", hed_schema=schema
            ),
            HedString("(Definition/Cond3/#, (Condition-variable/Var3, Label/#, Ellipse, Cross))", hed_schema=schema),
            HedString("(Definition/Cond4, (Condition-variable, Apple, Banana))", hed_schema=schema),
            HedString("(Definition/Cond5, (Condition-variable/Lumber, Apple, Banana))", hed_schema=schema),
            HedString("(Definition/Cond6/#, (Condition-variable/Lumber, Label/#, Apple, Banana))", hed_schema=schema),
        ]
        def_dict = DefinitionDict()
        for value in defs:
            def_dict.check_for_definitions(value)

        test_strings1 = [
            "Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset)",
            "(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4",
            "(Def/Cond1, Offset)",
            "White, Black, Condition-variable/Wonder, Condition-variable/Fast",
            "",
            "(Def/Cond2, Onset)",
            "(Def/Cond3/4.3, Onset)",
            "Arm, Leg, Condition-variable/Fast",
        ]
        test_onsets1 = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        df1 = DataFrame(test_onsets1, columns=["onset"])
        df1["HED"] = test_strings1
        input_data1 = TabularInput(df1)
        cls.event_man1 = EventManager(input_data1, schema, extra_defs=def_dict)
        test_strings2 = [
            "Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
            "Yellow",
            "Def/Cond2, (Def/Cond6/4, Onset)",
            "Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)",
            "Def/Cond2, Def/Cond6/4",
        ]
        test_onsets2 = [0.0, 1.0, 2.0, 3.0, 4.0]
        df2 = DataFrame(test_onsets2, columns=["onset"])
        df2["HED"] = test_strings2
        input_data2 = TabularInput(df2)
        cls.event_man2 = EventManager(input_data2, schema, extra_defs=def_dict)
        test_strings3 = ["(Def/Cond3, Offset)"]
        test_onsets3 = [0.0]
        df3 = DataFrame(test_onsets3, columns=["onset"])
        df3["HED"] = test_strings3
        cls.input_data3 = TabularInput(df3)
        bids_root_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_hed")
        )
        events_path = os.path.realpath(
            os.path.join(bids_root_path, "sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv")
        )
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, "task-FacePerception_events.json"))
        cls.input_data = TabularInput(events_path, sidecar_path)
        cls.schema = schema
        cls.def_dict = def_dict

    def test_constructor_from_tabular_input(self):
        event_man = EventManager(self.input_data, self.schema)
        tag_man1 = HedTagManager(EventManager(self.input_data, self.schema))
        self.assertIsInstance(tag_man1, HedTagManager)
        hed_objs1a = tag_man1.get_hed_objs(include_context=False, replace_defs=False)
        self.assertNotIn("Event-context", str(hed_objs1a[1]))
        self.assertIn("Def", str(hed_objs1a[1]))
        self.assertNotIn("Condition-variable", str(hed_objs1a[1]))
        hed_objs1b = tag_man1.get_hed_objs(include_context=True, replace_defs=False)
        self.assertIn("Event-context", str(hed_objs1b[1]))
        self.assertIn("Def", str(hed_objs1b[1]))
        self.assertNotIn("Condition-variable", str(hed_objs1b[1]))
        hed_objs1c = tag_man1.get_hed_objs(include_context=False, replace_defs=True)
        self.assertNotIn("Event-context", str(hed_objs1c[1]))
        self.assertNotIn("Def", str(hed_objs1c[1]))
        self.assertIn("Condition-variable", str(hed_objs1c[1]))
        hed_objs1d = tag_man1.get_hed_objs(include_context=True, replace_defs=True)
        self.assertIn("Event-context", str(hed_objs1d[1]))
        self.assertNotIn("Def", str(hed_objs1d[1]))
        self.assertIn("Condition-variable", str(hed_objs1d[1]))
        tag_man2 = HedTagManager(event_man, remove_types=["Condition-variable", "Task"])
        hed_objs2a = tag_man2.get_hed_objs(include_context=False, replace_defs=False)
        self.assertNotIn("Condition-variable", str(hed_objs2a[1]))
        hed_objs2b = tag_man2.get_hed_objs(include_context=True, replace_defs=False)
        self.assertNotIn("Condition-variable", str(hed_objs2b[1]))
        hed_objs2c = tag_man2.get_hed_objs(include_context=False, replace_defs=True)
        self.assertNotIn("Condition-variable", str(hed_objs2c[1]))
        hed_objs2d = tag_man2.get_hed_objs(include_context=True, replace_defs=True)
        self.assertNotIn("Condition-variable", str(hed_objs2d[1]))
        self.assertIsInstance(tag_man2, HedTagManager)
        self.assertIsInstance(tag_man2, HedTagManager)

    def test_get_hed_objs(self):
        tag_man = HedTagManager(EventManager(self.input_data, self.schema))
        self.assertIsInstance(tag_man, HedTagManager)
        hed_objs = tag_man.get_hed_objs()
        self.assertIsInstance(hed_objs, list)
        self.assertEqual(len(hed_objs), len(tag_man.event_manager.onsets))

    def test_get_hed_obj_empty_string(self):
        """Test that get_hed_obj returns None for empty or None input."""
        tag_man = HedTagManager(EventManager(self.input_data, self.schema))
        result1 = tag_man.get_hed_obj("")
        self.assertIsNone(result1, "get_hed_obj should return None for empty string")
        result2 = tag_man.get_hed_obj(None)
        self.assertIsNone(result2, "get_hed_obj should return None for None")

    def test_get_hed_obj_basic(self):
        """Test basic functionality of get_hed_obj without removing types."""
        tag_man = HedTagManager(EventManager(self.input_data, self.schema))
        hed_str = "Red, Blue, (Green, Yellow)"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=False)
        self.assertIsNotNone(hed_obj)
        from hed.models.hed_string import HedString
        self.assertIsInstance(hed_obj, HedString)
        self.assertIn("Red", str(hed_obj))
        self.assertIn("Blue", str(hed_obj))
        self.assertIn("Green", str(hed_obj))

    def test_get_hed_obj_remove_types_simple(self):
        """Test that remove_types=True removes specified type tags."""
        tag_man = HedTagManager(EventManager(self.input_data, self.schema), remove_types=["Condition-variable"])
        hed_str = "Red, Condition-variable/TestVar, Blue"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True)
        self.assertNotIn("Condition-variable", str(hed_obj))
        self.assertIn("Red", str(hed_obj))
        self.assertIn("Blue", str(hed_obj))

    def test_get_hed_obj_remove_types_multiple_instances(self):
        """Test removing multiple instances of the same type tag."""
        tag_man = HedTagManager(EventManager(self.input_data, self.schema), remove_types=["Condition-variable"])
        hed_str = "Condition-variable/Var1, Red, Condition-variable/Var2, Blue, Condition-variable/Var3"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True)
        self.assertNotIn("Condition-variable", str(hed_obj))
        self.assertNotIn("Var1", str(hed_obj))
        self.assertNotIn("Var2", str(hed_obj))
        self.assertNotIn("Var3", str(hed_obj))
        self.assertIn("Red", str(hed_obj))
        self.assertIn("Blue", str(hed_obj))

    def test_get_hed_obj_remove_types_nested_groups(self):
        """Test removing type tags from nested groups."""
        tag_man = HedTagManager(EventManager(self.input_data, self.schema), remove_types=["Condition-variable"])
        hed_str = "Red, (Blue, (Condition-variable/TestVar, Green, (Yellow, Condition-variable/Nested)))"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True, remove_group=False)
        self.assertNotIn("Condition-variable", str(hed_obj))
        self.assertNotIn("TestVar", str(hed_obj))
        self.assertNotIn("Nested", str(hed_obj))
        # Other tags should remain
        self.assertIn("Red", str(hed_obj))
        self.assertIn("Blue", str(hed_obj))
        self.assertIn("Green", str(hed_obj))
        self.assertIn("Yellow", str(hed_obj))

    def test_get_hed_obj_remove_group_with_nested_groups(self):
        """Test that remove_group=True removes entire groups even when nested."""
        tag_man = HedTagManager(EventManager(self.input_data, self.schema), remove_types=["Condition-variable"])
        hed_str = "Red, (Condition-variable/TestVar, Green, Yellow), Blue"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True, remove_group=True)
        self.assertNotIn("Condition-variable", str(hed_obj))
        self.assertNotIn("Green", str(hed_obj))
        self.assertNotIn("Yellow", str(hed_obj))
        self.assertIn("Red", str(hed_obj))
        self.assertIn("Blue", str(hed_obj))

    def test_get_hed_obj_remove_multiple_type_tags(self):
        """Test removing multiple different type tags in complex structure."""
        tag_man = HedTagManager(
            EventManager(self.input_data, self.schema), 
            remove_types=["Condition-variable", "Task"]
        )
        hed_str = "Red, (Condition-variable/Var1, Blue), Task/Memory, (Green, Task/Visual, Yellow)"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True, remove_group=False)
        self.assertNotIn("Condition-variable", str(hed_obj))
        self.assertNotIn("Task", str(hed_obj))
        self.assertIn("Red", str(hed_obj))
        self.assertIn("Blue", str(hed_obj))
        self.assertIn("Green", str(hed_obj))
        self.assertIn("Yellow", str(hed_obj))

    def test_get_hed_obj_remove_multiple_types_with_remove_group(self):
        """Test removing multiple type tags with remove_group=True."""
        tag_man = HedTagManager(
            EventManager(self.input_data, self.schema), 
            remove_types=["Condition-variable", "Task"]
        )
        hed_str = "Red, (Condition-variable/Var1, Blue), Task/Memory, (Green, Task/Visual, Yellow)"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True, remove_group=True)
        self.assertNotIn("Condition-variable", str(hed_obj))
        self.assertNotIn("Task", str(hed_obj))
        self.assertNotIn("Blue", str(hed_obj))  # Group with Condition-variable removed
        self.assertNotIn("Green", str(hed_obj))  # Group with Task removed
        self.assertNotIn("Yellow", str(hed_obj))  # Group with Task removed
        self.assertIn("Red", str(hed_obj))

    def test_get_hed_obj_remove_types_mixed_with_definitions(self):
        """Test removing type tags while preserving definitions in complex structure."""
        tag_man = HedTagManager(self.event_man1, remove_types=["Condition-variable"])
        hed_str = "Def/Cond1, (Red, Condition-variable/External), Blue, Condition-variable/Another"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True)
        self.assertIn("Def/Cond1", str(hed_obj))
        self.assertNotIn("Condition-variable/External", str(hed_obj))
        self.assertNotIn("Condition-variable/Another", str(hed_obj))
        self.assertIn("Red", str(hed_obj))
        self.assertIn("Blue", str(hed_obj))

    def test_get_hed_obj_remove_types_all_content_removed(self):
        """Test when all content consists of removable type tags."""
        tag_man = HedTagManager(EventManager(self.input_data, self.schema), remove_types=["Condition-variable"])
        hed_str = "Condition-variable/Var1, Condition-variable/Var2"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True)
        # Should have an empty or minimal string
        self.assertNotIn("Condition-variable", str(hed_obj))
        self.assertNotIn("Var1", str(hed_obj))
        self.assertNotIn("Var2", str(hed_obj))

    def test_get_hed_obj_no_remove_types_specified(self):
        """Test that remove_types=True has no effect when manager has no remove_types."""
        tag_man = HedTagManager(EventManager(self.input_data, self.schema))
        hed_str = "Red, Condition-variable/TestVar, Blue"
        hed_obj = tag_man.get_hed_obj(hed_str, remove_types=True)
        # Since no remove_types were specified in the manager, nothing should be removed
        self.assertIn("Condition-variable", str(hed_obj))
        self.assertIn("Red", str(hed_obj))
        self.assertIn("Blue", str(hed_obj))


if __name__ == "__main__":
    unittest.main()
