import unittest
from hed.tools.bids_file import BidsFile
from hed.tools.bids_sidecar_file import BidsSidecarFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp = ""

    def test_bids_sidecar_file_constructor(self):
        the_path = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.json'
        bids = BidsSidecarFile(the_path, set_contents=False)
        self.assertEqual(bids.suffix, 'bold', "BidsFile should have correct name_suffix")
        self.assertEqual(bids.ext, '.json', "BidsFile should have correct ext")
        self.assertEqual(len(bids.entities), 4, "BidsFile should have right number of entities")
        self.assertFalse(bids.contents)

    def test_is_sidecar_for(self):
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
