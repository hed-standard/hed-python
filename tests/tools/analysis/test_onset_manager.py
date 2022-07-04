import os
import unittest
from hed import HedString, load_schema_version
from hed.errors import HedFileError
from hed.tools import OnsetGroup, OnsetManager


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        cls.test_strings1 = [HedString('Sensory-event,(Def/Cond1,(Red, Blue),Onset),(Def/Cond2,Onset),Green,Yellow',
                                      hed_schema=schema),
                             HedString('(Def/Cond1, Offset)', hed_schema=schema),
                             HedString('White, Black', hed_schema=schema),
                             HedString('', hed_schema=schema)]
        cls.test_strings2 = [HedString('(Def/Cond3, Offset)', hed_schema=schema)]
        cls.sidecar_path1 = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')
        cls.schema = schema

    def test_constructor(self):
        manager1 = OnsetManager(self.test_strings1, self.schema)
        self.assertIsInstance(manager1, OnsetManager, "The constructor should create an OnsetManager")
        self.assertEqual(len(manager1.hed_strings), 4, "The constructor should have the right number of strings")
        self.assertEqual(len(manager1.onset_list), 2, "The constructor should have right length onset list")
        self.assertIsInstance(manager1.hed_strings[1], HedString, "Constructor hed string should be a hedstring")
        self.assertFalse(manager1.hed_strings[1].children, "When no tags list HedString is empty")

    def test_constructor_unmatched(self):
        with self.assertRaises(HedFileError):
            OnsetManager(self.test_strings2, self.schema)


if __name__ == '__main__':
    unittest.main()
