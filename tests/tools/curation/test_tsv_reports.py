import unittest
import os
from io import StringIO
from unittest import mock

from hed.errors.exceptions import HedFileError
from hed.tools import BidsTabularDictionary, HedLogger, report_diffs
from hed.util import get_file_list


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bids_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         '../../data/bids/eeg_ds003654s_hed')
        cls.file_list = get_file_list(cls.bids_base_dir, name_suffix="_events",
                                      extensions=['.tsv'], exclude_dirs=['stimuli'])

    def test_report_tsv_diffs(self):
        dict1 = BidsTabularDictionary("Bids1", self.file_list, entities=('sub', 'run'))
        dict2 = BidsTabularDictionary("Bids2", self.file_list, entities=('sub', 'run'))
        logger = HedLogger()
        self.assertEqual(6, len(dict1.key_list),
                         "BidsTabularDictionary should have correct number of entries when key okay")
        self.assertFalse(logger.log, "report_diffs the logger is empty before report is called")
        with mock.patch('sys.stdout', new=StringIO()) as fake_out1:
            self.assertIsInstance(fake_out1, StringIO, "Mock creates a StringIO")
            report_diffs(dict1, dict2, logger)
        self.assertTrue(logger.log, "report_diffs the logger is empty before report is called")


if __name__ == '__main__':
    unittest.main()
