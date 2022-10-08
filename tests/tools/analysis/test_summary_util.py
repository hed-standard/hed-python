import os
import json
import unittest
from hed.models.hed_string import HedString
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.summary_util import breakout_tags, get_schema_entries, add_tag_list_to_dict


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sidecar_path1 = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')
        cls.schema = load_schema_version(xml_version="8.0.0")
        cls.str1 = f"(Task,Experiment-participant,(See,Face),(Discriminate,(Face, Symmetrical))," \
                   f"(Press,Keyboard-key),Description/Evaluate degree of image symmetry and respond with key" \
                   f"press evaluation.)"
        cls.str2 = f"Sensory-event, (Intended-effect, Cue), (Def/Cross-only, Onset), (Def/Fixation-task, Onset)," \
                   f"(Def/Circle-only, Offset)"
        cls.str_with_def = f"(Definition/First-show-cond, ((Condition-variable/Repetition-type," \
                           f" (Item-count/1, Face), Item-interval/0), " \
                           f"Description/Factor level indicating the first display of this face.))"
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../../data/remodel_tests/tag_summary_template.json5")
        with open(json_path) as fp:
            cls.rules = json.load(fp)

    def test_breakout_tags(self):
        breakout_list = self.rules["Tag-categories"]
        tag_list = ['Sensory-event', 'Experimental-stimulus', 'Def', 'Onset', 'Offset', 'Intended-effect', 'Cue',
                    'Agent-action', 'Participant-response', 'Experiment-structure', 'Indeterminate-action',
                    'Press', 'Keyboard-key', 'Experimental-trial', 'Face', 'Item-interval', 'Image', 'Pathname',
                    'Definition', 'Visual-presentation', 'Foreground-view', 'White', 'Cross', 'Center-of',
                    'Computer-screen', 'Background-view', 'Black', 'Description', 'Hair', 'Grayscale', 'Circle',
                    'Index-finger', 'Left-side-of', 'Experiment-participant', 'Right-side-of',
                    'Condition-variable', 'Famous', 'Unfamiliar', 'Disordered', 'Item-count',
                    'Greater-than-or-equal-to', 'Behavioral-evidence', 'Symmetrical', 'Asymmetrical', 'Task',
                    'See', 'Discriminate', 'Inhibit-blinks', 'Fixate', 'Recording']
        breakout_dict = breakout_tags(self.schema, tag_list, breakout_list)
        self.assertFalse(breakout_dict["leftovers"], "breakout_tags should not have leftovers")
        self.assertEqual(len(breakout_dict["Organizational-property"]), 6,
                         "breakout_tags should have the right number of organizational tags")

    def test_get_schema_entries(self):
        tag1 = 'Red'
        schema_entries1 = get_schema_entries(self.schema, tag1)
        self.assertIsInstance(schema_entries1, list, "get_schema_entries should always return a list for single node")
        self.assertEqual(len(schema_entries1), 8,
                         "get_schema_entries should return a list of the right length for single node")
        self.assertEqual(schema_entries1[0].short_tag_name, tag1,
                         "get_schema_entries should return the right name for the node itself")

        tag2 = 'Definition/Blech'
        schema_entries2 = get_schema_entries(self.schema, tag2)
        self.assertIsInstance(schema_entries2, list, "get_schema_entries should always return a node with value")
        self.assertEqual(len(schema_entries2), 3,
                         "get_schema_entries should return a list of the right length for a node with value")
        self.assertEqual(schema_entries2[0].short_tag_name, "Definition",
                         "get_schema_entries should return the right name for the node itself")

    def test_get_schema_entries_invalid(self):
        tag1 = 'Blech'
        schema_entries1 = get_schema_entries(self.schema, tag1)
        self.assertIsInstance(schema_entries1, list,
                              "get_schema_entries should always return a list for invalid node")
        self.assertEqual(len(schema_entries1), 0,
                         "get_schema_entries should return an empty list for an invalid node")

    def test_add_tag_list_to_dict(self):
        hed1 = HedString(self.str1)
        tag_dict1 = {}
        add_tag_list_to_dict([hed1], tag_dict1, self.schema)
        self.assertIsInstance(tag_dict1, dict, "add_tag_list_to_dict returns a dictionary of tags.")
        self.assertEqual(len(tag_dict1), 9,
                         "add_tag_list_to_dict should have the right number of tags if conversion done after.")

        hed2 = HedString(self.str1)
        hed2.convert_to_canonical_forms(self.schema)
        tag_dict2 = {}
        add_tag_list_to_dict([hed2], tag_dict2)
        self.assertIsInstance(tag_dict2, dict, "add_tag_list_to_dict returns a dictionary of tags.")
        self.assertEqual(len(tag_dict2), 9,
                         "add_tag_list_to_dict should have the right number of tags if conversion done first.")

        tag_dict3 = {}
        add_tag_list_to_dict([HedString(self.str1), HedString(self.str2), HedString(self.str_with_def)],
                             tag_dict3, self.schema)
        self.assertIsInstance(tag_dict3, dict, "add_tag_list_to_dict returns a dictionary of tags.")
        self.assertEqual(len(tag_dict3), 19,
                         "add_tag_list_to_dict should have the right number of tags if conversion done first.")


if __name__ == '__main__':
    unittest.main()
