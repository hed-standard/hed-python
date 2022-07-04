import os
import unittest
from hed import HedString, load_schema_version, Sidecar, TabularInput
from hed.models import HedGroup
from hed.errors import HedFileError
from hed.tools import OnsetGroup, OnsetManager, get_assembled_strings


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        cls.test_strings1 = [HedString('Sensory-event,(Def/Cond1,(Red, Blue),Onset),(Def/Cond2,Onset),Green,Yellow',
                                      hed_schema=schema),
                             HedString('(Def/Cond1, Offset)', hed_schema=schema),
                             HedString('White, Black', hed_schema=schema),
                             HedString('', hed_schema=schema),
                             HedString('(Def/Cond2, Onset)', hed_schema=schema),
                             HedString('(Def/Cond3, Onset)', hed_schema=schema),
                             HedString('Arm, Leg', hed_schema=schema)]
        cls.test_strings2 = [HedString('(Def/Cond3, Offset)', hed_schema=schema)]

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.schema = schema

    def test_constructor(self):
        manager1 = OnsetManager(self.test_strings1, self.schema)
        self.assertIsInstance(manager1, OnsetManager, "The constructor should create an OnsetManager")
        self.assertEqual(len(manager1.hed_strings), 7, "The constructor should have the right number of strings")
        self.assertEqual(len(manager1.onset_list), 4, "The constructor should have right length onset list")
        self.assertIsInstance(manager1.hed_strings[1], HedString, "Constructor hed string should be a hedstring")
        self.assertFalse(manager1.hed_strings[1].children, "When no tags list HedString is empty")
        context = manager1.event_contexts
        self.assertIsInstance(context, list, "The constructor event contexts should be a list")
        self.assertIsInstance(context[1][0], HedGroup, "The constructor event contexts has a correct element")

    def test_constructor_from_assembled(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        manager1 = OnsetManager(hed_strings, self.schema)
        self.assertEqual(len(manager1.hed_strings), 200,
                         "The constructor for assembled strings has expected # of strings")
        self.assertEqual(len(manager1.onset_list), 261,
                         "The constructor for assembled strings has onset_list of correct length")

    def test_constructor_unmatched(self):
        with self.assertRaises(HedFileError):
            OnsetManager(self.test_strings2, self.schema)


if __name__ == '__main__':
    unittest.main()
