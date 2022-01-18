import os
import unittest
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_json_file import BidsJsonFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.description_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            '../../data/bids/eeg_ds003654s_hed/dataset_description.json')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_constructor(self):
        json1 = BidsJsonFile(Test.description_path, set_contents=False)
        self.assertEqual(json1.suffix, 'dataset_description', "BidsJsonFile should have correct name_suffix")
        self.assertEqual(json1.ext, '.json', "BidsSidecarFile should have correct ext")
        self.assertEqual(len(json1.entities), 0, "BidsSidecarFile should have right number of entities")
        self.assertFalse(json1.contents)

        sidecar2 = BidsJsonFile(Test.sidecar_path, set_contents=True)
        self.assertEqual(sidecar2.suffix, 'events', "BidsSidecarFile should have correct name_suffix")
        self.assertEqual(sidecar2.ext, '.json', "BidsSidecarFile should have correct ext")
        self.assertEqual(len(sidecar2.entities), 1, "BidsSidecarFile should have right number of entities")
        self.assertIsInstance(sidecar2.contents, dict, "BidsSidecarFile should contain a dictionary")


if __name__ == '__main__':
    unittest.main()
