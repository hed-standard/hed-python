import os
import unittest
from hed.models.hed_group import HedGroup
from hed.models.hed_string import HedString
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.summaries.definition_summary import DefinitionEntry


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sidecar_path1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_constructor(self):
        def_str1 = f"(Task,Experiment-participant,(See,Face),(Discriminate,(Face, Symmetrical))," \
            f"(Press,Keyboard-key),Description/Evaluate degree of image symmetry and respond with key" \
            f"press evaluation.)"
        def_entry1 = DefinitionEntry("Face-symmetry-evaluation-task", HedString(def_str1))
        self.assertIsInstance(def_entry1, DefinitionEntry, "DefinitionEntry constructor should create an object")
        self.assertEqual(def_entry1.name, "Face-symmetry-evaluation-task",
                         "DefinitionEntry constructor should have the right definition name")
        self.assertIsInstance(def_entry1.group, HedGroup,
                              "DefinitionEntry constructor group should be a HedGroup")
        self.assertFalse(def_entry1.tag_dict,
                         "DefinitionEntry constructor group should not have a tag dictionary until set")
        def_entry2 = DefinitionEntry("Dummy", None)
        self.assertIsInstance(def_entry2, DefinitionEntry, "DefinitionEntry constructor should create an object")
        self.assertEqual(def_entry2.name, "Dummy",
                         "DefinitionEntry constructor should have the right definition name when no group")
        self.assertFalse(def_entry2.group,
                         "DefinitionEntry constructor group should be a None when no group")
        self.assertFalse(def_entry2.tag_dict,
                         "DefinitionEntry constructor dictionary should not have a tag dictionary until set")

    def test_set_tag_dict(self):
        schema = load_schema_version(xml_version_number="8.0.0")
        def_str1 = f"(Task,Experiment-participant,(See,Face),(Discriminate,(Face, Symmetrical))," \
            f"(Press,Keyboard-key),Description/Evaluate degree of image symmetry and respond with key" \
            f"press evaluation.)"
        def_entry1 = DefinitionEntry("Face-symmetry-evaluation-task", HedString(def_str1))
        self.assertFalse(def_entry1.tag_dict,
                         "DefinitionEntry dictionary should not have a tag dictionary until set")
        def_entry1.set_tag_dict(hed_schema=schema)

        self.assertTrue(def_entry1.tag_dict,
                        "DefinitionEntry dictionary should have a tag dictionary after setting")
        self.assertEqual(len(def_entry1.tag_dict), 9,
                         "DefinitionEntry dictionary should have a tag dictionary with the right number of elements")


if __name__ == '__main__':
    unittest.main()
