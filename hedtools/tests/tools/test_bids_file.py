import unittest
from hed.tools.bids_file import BIDSFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp = ""

    def test_bids_file_constructor(self):
        the_path = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.json'
        bids = BIDSFile(the_path)
        self.assertEqual(bids.suffix, 'bold', "BIDSFile should have correct name_suffix")
        self.assertEqual(bids.ext, '.json', "BIDSFile should have correct ext")
        self.assertEqual(len(bids.entities), 4, "BIDSFile should have right number of entities")

    def test_is_parent(self):
        the_path = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.nfti'
        bids = BIDSFile(the_path)
        other = BIDSFile('/d/base/task-overt_run-2_bold.json')
        self.assertTrue(other.is_parent(bids), "is_a_parent returns true if parent at top level")
        other1 = BIDSFile('/d/base1/task-overt_run-2_bold.json')
        self.assertFalse(other1.is_parent(bids), "is_a_parent returns false if directories don't match")
        other2 = BIDSFile('/d/base/task-overt_run-3_bold.json')
        self.assertFalse(other2.is_parent(bids), "is_a_parent returns false if entities don't match")
        other3 = BIDSFile('/d/base/sub-01/sub-01_task-overt_bold.json')
        self.assertTrue(other3.is_parent(bids), "is_a_parent returns true if entities  match")
        other4 = BIDSFile('/d/base/sub-01/sub-01_task-overt_events.json')
        self.assertFalse(other4.is_parent(bids), "is_a_parent returns false if suffixes don't match")

if __name__ == '__main__':
    unittest.main()
