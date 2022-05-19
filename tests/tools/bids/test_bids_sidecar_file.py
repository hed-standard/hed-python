import os
import unittest
from hed.errors import HedFileError
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_tabular_file import BidsTabularFile
from hed.tools.bids.bids_file import BidsFile
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.description_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                            '../../data/bids/eeg_ds003654s_hed/dataset_description.json')
        cls.event_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                      '../../data/bids/eeg_ds003654s_hed/sub-002/'
                                      'eeg/sub-002_task-FacePerception_run-1_events.tsv')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_constructor(self):
        sidecar1 = BidsSidecarFile(Test.sidecar_path)
        self.assertEqual(sidecar1.suffix, 'events', "BidsSidecarFile should have correct name_suffix")
        self.assertEqual(sidecar1.ext, '.json', "BidsSidecarFile should have correct ext")
        self.assertEqual(len(sidecar1.entity_dict), 1, "BidsSidecarFile should have right number of entity_dict")
        self.assertFalse(sidecar1.contents)

    def test_bad_constructor(self):

        try:
            json1 = BidsSidecarFile(Test.description_path)
        except HedFileError:
            pass
        except Exception:
            self.fail("BidsSidecarFile threw the wrong exception when filename invalid")
        else:
            self.fail("BidsSidecarFile should have thrown a HedFileError when duplicate key")

    def test_bids_sidecar_file_str(self):
        sidecar1 = BidsSidecarFile(Test.sidecar_path)
        self.assertTrue(str(sidecar1), "BidsSidecarFile should have a string representation")
        sidecar2 = BidsSidecarFile(Test.sidecar_path)
        self.assertTrue(str(sidecar2), "BidsSidecarFile should have a string representation")

    def test_bids_sidecar_file_set_contents(self):
        sidecar1 = BidsSidecarFile(Test.sidecar_path)
        self.assertFalse(sidecar1.contents, "BidsSidecarFile should have no contents until set")
        sidecar1.set_contents()
        self.assertIsInstance(sidecar1.contents, Sidecar, "BidsSidecarFile should have dict contents after setting")
        sidecar1.clear_contents()
        self.assertFalse(sidecar1.contents, "BidsSidecarFile should have no contents after clearing")

    def test_is_sidecar_for(self):
        sidecar1 = BidsSidecarFile(Test.sidecar_path)
        events1 = BidsTabularFile(Test.event_path)
        self.assertTrue(sidecar1.is_sidecar_for(events1))

        the_path = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.nfti'
        bids = BidsFile(the_path)
        other = BidsSidecarFile('/d/base/task-overt_run-2_bold.json')
        self.assertTrue(other.is_sidecar_for(bids), "is_a_parent returns true if parent at top level")
        other1 = BidsSidecarFile('/d/base1/task-overt_run-2_bold.json')
        self.assertFalse(other1.is_sidecar_for(bids), "is_a_parent returns false if directories don't match")
        other2 = BidsSidecarFile('/d/base/task-overt_run-3_bold.json')
        self.assertFalse(other2.is_sidecar_for(bids), "is_a_parent returns false if entity_dict don't match")
        other3 = BidsSidecarFile('/d/base/sub-01/sub-01_task-overt_bold.json')
        self.assertTrue(other3.is_sidecar_for(bids), "is_a_parent returns true if entity_dict  match")
        other4 = BidsSidecarFile('/d/base/sub-01/sub-01_task-overt_events.json')
        self.assertFalse(other4.is_sidecar_for(bids), "is_a_parent returns false if suffixes don't match")
        other5 = BidsSidecarFile('/d/base/sub-01/ses-test/func/temp/sub-01_ses-test_task-overt_run-2_bold.json')
        self.assertFalse(other5.is_sidecar_for(bids), "is_a_parent returns false for child even if entity_dict match")


if __name__ == '__main__':
    unittest.main()
