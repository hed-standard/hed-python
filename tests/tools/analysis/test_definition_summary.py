import os
import unittest
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_json = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                     '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_constructor(self):
        sidecar1 = BidsSidecarFile(self.test_json)
        self.assertEqual(sidecar1.suffix, 'events', "BidsSidecarFile should have correct name_suffix")
        self.assertEqual(sidecar1.ext, '.json', "BidsSidecarFile should have correct ext")
        self.assertEqual(len(sidecar1.entity_dict), 1, "BidsSidecarFile should have right number of entity_dict")
        self.assertFalse(sidecar1.contents, "BidsSidecarFile should not have contents on construction.")
        sidecar1.set_contents()
        self.assertIsInstance(sidecar1.contents, Sidecar, "BidsSidecarFile should contain a Sidecar after set_contents")


if __name__ == '__main__':
    unittest.main()
