import os
import io
import unittest
from unittest.mock import patch
from hed.scripts.validate_bids import get_parser, validate_dataset, main


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_root = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                      '../data/bids_tests/eeg_ds003645s_hed_demo'))

    def test_main_bids(self):
        arg_list = [self.data_root,  '-x', 'derivatives', 'stimuli' ]
        with patch('sys.stdout', new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_warnings(self):
        arg_list = [self.data_root,  '-x', 'derivatives', 'stimuli', '-w', '-p', '-s' ]
        with patch('sys.stdout', new=io.StringIO()) as fp:
            main(arg_list)
            self.assertTrue(fp.getvalue())

if __name__ == '__main__':
    unittest.main()
