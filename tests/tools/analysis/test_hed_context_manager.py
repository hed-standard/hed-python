import os
import unittest
from hed.errors.exceptions import HedFileError
from hed.models.hed_group import HedGroup
from hed.models.hed_string import HedString
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.analysis.analysis_util import get_assembled_strings


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
                             HedString('(Def/Cond3/1.3, Onset)', hed_schema=schema),
                             HedString('Arm, Leg', hed_schema=schema)]
        cls.test_strings2 = [HedString('(Def/Cond3/2, Offset)', hed_schema=schema)]
        cls.test_strings3 = [HedString(f"Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
                                       hed_schema=schema),
                             HedString("Yellow", hed_schema=schema),
                             HedString("Def/Cond2, (Def/Cond6/4, Onset)", hed_schema=schema),
                             HedString("Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)", hed_schema=schema),
                             HedString("Def/Cond2, Def/Cond6/4", hed_schema=schema)]

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids_tests/eeg_ds003654s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.schema = schema

    def test_constructor(self):
        manager1 = HedContextManager(self.test_strings1)
        self.assertIsInstance(manager1, HedContextManager, "The constructor should create an HedContextManager")
        self.assertEqual(len(manager1.hed_strings), 7, "The constructor should have the right number of strings")
        self.assertEqual(len(manager1.onset_list), 4, "The constructor should have right length onset list")
        self.assertIsInstance(manager1.hed_strings[1], HedString, "Constructor hed string should be a hedstring")
        self.assertFalse(manager1.hed_strings[1].children, "When no tags list HedString is empty")
        context = manager1.contexts
        self.assertIsInstance(context, list, "The constructor event contexts should be a list")
        self.assertIsInstance(context[1][0], HedGroup, "The constructor event contexts has a correct element")

    def test_constructor_from_assembled(self):
        hed_strings = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
        manager1 = HedContextManager(hed_strings)
        self.assertEqual(len(manager1.hed_strings), 200,
                         "The constructor for assembled strings has expected # of strings")
        self.assertEqual(len(manager1.onset_list), 261,
                         "The constructor for assembled strings has onset_list of correct length")

    def test_constructor_unmatched(self):
        with self.assertRaises(HedFileError):
            HedContextManager(self.test_strings2)

    def test_constructor_multiple_values(self):
        manager = HedContextManager(self.test_strings3)
        self.assertEqual(len(manager.onset_list), 3, "Constructor should have right number of onsets")


if __name__ == '__main__':
    unittest.main()
