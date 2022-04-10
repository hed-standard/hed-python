import os
import unittest
from hed.errors import HedFileError
from hed.tools import BidsJsonFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.description_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                            '../../data/bids/eeg_ds003654s_hed/dataset_description.json')
        cls.json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                     '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_constructor(self):
        json1 = BidsJsonFile(Test.json_path, set_contents=False)
        self.assertEqual(json1.suffix, 'events', "BidsJsonFile should have correct suffix")
        self.assertEqual(json1.ext, '.json', "BidsJsonFile should have correct ext")
        self.assertEqual(len(json1.entity_dict), 1, "BidsJsonFile should have right size entity_dict")
        self.assertFalse(json1.contents)

        sidecar2 = BidsJsonFile(Test.json_path, set_contents=True)
        self.assertEqual(sidecar2.suffix, 'events', "BidsJsonFile should have correct name_suffix")
        self.assertEqual(sidecar2.ext, '.json', "BidsJsonFile should have correct ext")
        self.assertEqual(len(sidecar2.entity_dict), 1, "BidsJsonFile should have right number of entity_dict")
        self.assertIsInstance(sidecar2.contents, dict, "BidsJsonFile should contain a dictionary")

    def test_bad_constructor(self):

        try:
            json1 = BidsJsonFile(Test.description_path, set_contents=True)
        except HedFileError:
            pass
        except Exception:
            self.fail("BidsJsonFile threw the wrong exception when filename invalid")
        else:
            self.fail("BidsJsonFile should have thrown a HedFileError when duplicate key")

    def test_bids_json_file_str(self):
        json_file1 = BidsJsonFile(Test.json_path)
        self.assertTrue(str(json_file1), "BidsJsonFile should have a string representation")
        json_file2 = BidsJsonFile(Test.json_path, set_contents=True)
        self.assertTrue(str(json_file2), "BidsJsonFile should have a string representation")
        self.assertGreater(len(str(json_file2)), len(str(json_file1)),
                           "BidsJsonFile with contents should have a longer string representation than without")

    def test_bids_json_file_set_contents(self):
        json_file = BidsJsonFile(Test.json_path)
        self.assertFalse(json_file.contents, "BidsJsonFile should have no contents until set")
        json_file.set_contents()
        self.assertIsInstance(json_file.contents, dict, "BidsJsonFile should have dict contents after setting")
        json_file.clear_contents()
        self.assertFalse(json_file.contents, "BidsJsonFile should have no contents after clearing")


if __name__ == '__main__':
    unittest.main()
