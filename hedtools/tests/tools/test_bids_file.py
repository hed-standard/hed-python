import unittest
from hed.tools.bids_file import BidsFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp = ""

    def test_bids_file_constructor(self):
        the_path = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.json'
        bids = BidsFile(the_path)
        self.assertEqual(bids.suffix, 'bold', "BidsFile should have correct name_suffix")
        self.assertEqual(bids.ext, '.json', "BidsFile should have correct ext")
        self.assertEqual(len(bids.entities), 4, "BidsFile should have right number of entities")


if __name__ == '__main__':
    unittest.main()
