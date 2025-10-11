import os
import unittest
import json
from hed.tools.bids.bids_file import BidsFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        events_file = "../../data/bids_tests/eeg_ds003645s_hed/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv"
        sidecar_file = "../../data/bids_tests/eeg_ds003645s_hed/task-FacePerception_events.json"
        cls.event_path = os.path.realpath(os.path.join(os.path.dirname(__file__), events_file))
        cls.sidecar_path = os.path.realpath(os.path.join(os.path.dirname(__file__), sidecar_file))

    def test_bids_file_constructor(self):
        bids1 = BidsFile(self.event_path)
        self.assertEqual(bids1.suffix, "events", "BidsFile should have correct events suffix")
        self.assertEqual(bids1.ext, ".tsv", "BidsFile should have a .tsv extension")
        self.assertEqual(len(bids1.entity_dict), 3, "BidsFile should have right number of entity_dict")

        bids2 = BidsFile(self.sidecar_path)
        self.assertEqual(bids2.suffix, "events", "BidsFile should have correct events suffix")
        self.assertEqual(bids2.ext, ".json", "BidsFile should have a .json extension")
        self.assertEqual(len(bids2.entity_dict), 1, "BidsFile should have right number of entity_dict")

    def test_get_key(self):
        bids1 = BidsFile(self.event_path)
        key1 = bids1.get_key()
        self.assertEqual(key1, bids1.file_path, "get_key should be file path when no entities")
        key2 = bids1.get_key(("sub", "task"))
        self.assertEqual(key2, "sub-002_task-FacePerception", "get_key should give the correct key with two entities")
        key3 = bids1.get_key(("sub", "ses"))
        self.assertEqual(key3, "sub-002", "get_key should give the correct key when one entity is missing")

    def test_bids_file_str(self):
        bids = BidsFile(self.sidecar_path)
        my_str1 = str(bids)
        self.assertIsInstance(my_str1, str, "BidsFile convert to string should return a string")
        self.assertGreater(len(my_str1), 0, "BidsFile convert to string should return a non-empty string")
        my_str2 = bids.__str__()
        self.assertIsInstance(my_str2, str, "BidsFile __str__ method should return a string")
        self.assertGreater(len(my_str2), 0, "BidsFile __str__ method should return a non-empty string")

    def test_contents(self):
        bids = BidsFile(self.sidecar_path)
        self.assertFalse(bids.contents)
        with open(self.sidecar_path, "r") as fp:
            contents = json.load(fp)
        contents = json.dumps(contents)
        bids.set_contents(content_info=contents)
        self.assertTrue(bids.contents)
        self.assertEqual(len(bids.contents), len(contents))
        new_contents = contents + contents
        bids.set_contents(content_info=new_contents, overwrite=False)
        self.assertEqual(len(contents), len(bids.contents))
        bids.set_contents(content_info=new_contents, overwrite=True)
        self.assertEqual(len(new_contents), len(bids.contents))


if __name__ == "__main__":
    unittest.main()
