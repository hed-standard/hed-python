import os
import unittest
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_event_file import BidsEventFile
from hed.tools.bids.bids_file import BidsFile
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      '../../data/bids/eeg_ds003654s_hed/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_constructor(self):
        sidecar1 = BidsSidecarFile(Test.sidecar_path, set_contents=False)
        self.assertEqual(sidecar1.suffix, 'events', "BidsSidecarFile should have correct name_suffix")
        self.assertEqual(sidecar1.ext, '.json', "BidsSidecarFile should have correct ext")
        self.assertEqual(len(sidecar1.entities), 1, "BidsSidecarFile should have right number of entities")
        self.assertFalse(sidecar1.contents)

        sidecar2 = BidsSidecarFile(Test.sidecar_path, set_contents=True)
        self.assertEqual(sidecar2.suffix, 'events', "BidsSidecarFile should have correct name_suffix")
        self.assertEqual(sidecar2.ext, '.json', "BidsSidecarFile should have correct ext")
        self.assertEqual(len(sidecar2.entities), 1, "BidsSidecarFile should have right number of entities")
        self.assertIsInstance(sidecar2.contents, Sidecar, "BidsSidecarFile should contain a Sidecar")

    def test_is_sidecar_for(self):
        sidecar1 = BidsSidecarFile(Test.sidecar_path)
        events1 = BidsEventFile(Test.event_path)
        self.assertTrue(sidecar1.is_sidecar_for(events1))

        the_path = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.nfti'
        bids = BidsFile(the_path)
        other = BidsSidecarFile('/d/base/task-overt_run-2_bold.json')
        self.assertTrue(other.is_sidecar_for(bids), "is_a_parent returns true if parent at top level")
        other1 = BidsSidecarFile('/d/base1/task-overt_run-2_bold.json')
        self.assertFalse(other1.is_sidecar_for(bids), "is_a_parent returns false if directories don't match")
        other2 = BidsSidecarFile('/d/base/task-overt_run-3_bold.json')
        self.assertFalse(other2.is_sidecar_for(bids), "is_a_parent returns false if entities don't match")
        other3 = BidsSidecarFile('/d/base/sub-01/sub-01_task-overt_bold.json')
        self.assertTrue(other3.is_sidecar_for(bids), "is_a_parent returns true if entities  match")
        other4 = BidsSidecarFile('/d/base/sub-01/sub-01_task-overt_events.json')
        self.assertFalse(other4.is_sidecar_for(bids), "is_a_parent returns false if suffixes don't match")
        other5 = BidsSidecarFile('/d/base/sub-01/ses-test/func/temp/sub-01_ses-test_task-overt_run-2_bold.json')
        self.assertFalse(other5.is_sidecar_for(bids), "is_a_parent returns false for child even if entities match")


if __name__ == '__main__':
    unittest.main()
