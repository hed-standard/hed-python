import os
import unittest
from hed.errors.exceptions import HedFileError
from hed.models.tabular_input import TabularInput
from hed.tools.bids.bids_file import BidsFile
from hed.tools.bids.bids_tabular_file import BidsTabularFile
from hed.tools.bids.bids_tabular_dictionary import BidsTabularDictionary
from hed.tools.util.io_util import get_file_list
from hed.tools.util.hed_logger import HedLogger


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bids_base = os.path.realpath(os.path.join(os.path.dirname(__file__), '../../data/bids_tests/eeg_ds003645s_hed'))
        cls.json = os.path.realpath(os.path.join(bids_base, 'task-FacePerception_events.json'))
        cls.bids_base_dir = bids_base
        cls.file_list = get_file_list(bids_base, name_suffix="_events", extensions=['.tsv'], exclude_dirs=['stimuli'])

    def test_constructor_valid(self):
        dict1 = BidsTabularDictionary("Tsv Name", self.file_list, entities=('sub', 'run'))
        self.assertEqual(6, len(dict1.key_list), "BidsTabularDictionary has correct number of entries when key okay")

    def test_constructor_invalid(self):
        with self.assertRaises(HedFileError) as context:
            BidsTabularDictionary("Tsv name", self.file_list, entities=('sub',))
        self.assertEqual(context.exception.args[0], 'NonUniqueFileKeys')

    def test_count_diffs_same(self):
        dict1 = BidsTabularDictionary("Tsv Name1", self.file_list, entities=('sub', 'run'))
        self.assertEqual(6, len(dict1.key_list), "BidsTabularDictionary has correct number of entries when key okay.")
        dict2 = BidsTabularDictionary("Tsv Name2", self.file_list, entities=('sub', 'run'))
        self.assertEqual(6, len(dict2.key_list), "BidsTabularDictionary has correct number of entries when key okay.")
        diff_list1 = dict1.count_diffs(dict2)
        self.assertFalse(diff_list1, "count_diffs has no differences when dictionaries same.")
        diff_list2 = dict2.count_diffs(dict1)
        self.assertFalse(diff_list2, "count_diffs has no differences when dictionaries same regardless of order.")

    def test_count_diffs_diff(self):
        dict1 = BidsTabularDictionary("Tsv Name1", self.file_list[:-1], entities=('sub', 'run'))
        self.assertEqual(5, len(dict1.key_list),
                         "BidsTabularDictionary has correct number of entries when key okay.")
        dict2 = BidsTabularDictionary("Tsv Name2", self.file_list[2:], entities=('sub', 'run'))
        self.assertEqual(4, len(dict2.key_list),
                         "BidsTabularDictionary has correct number of entries when key okay.")
        diff_list1 = dict1.count_diffs(dict2)
        self.assertTrue(diff_list1, "count_diffs has differences when keys are missing.")
        self.assertEqual(len(diff_list1), 2, "count_diffs has differences when  ")
        diff_list2 = dict2.count_diffs(dict1)
        self.assertTrue(diff_list2, "count_diffs has no differences when dictionaries same regardless of order.")
        self.assertEqual(len(diff_list2), 1, "count_diffs has differences when other self keys are missing")

    def test_set_tsv_info(self):
        dict1 = BidsTabularDictionary("Tsv Name1", sorted(self.file_list)[:-1], entities=('sub', 'run'))
        info1 = dict1.get_info('sub-002_run-1')
        self.assertIsInstance(info1, dict)
        info2 = dict1.get_info('sub-002_run-1')
        self.assertIsInstance(info2, dict)
        self.assertEqual(info1["row_count"], 200)
        self.assertEqual(info2["row_count"], 200)
        info3 = dict1.get_info('sub-001_run-1')
        self.assertIsInstance(info3, dict)
        self.assertIsNone(info3["row_count"])

    def test_create_split_dict(self):
        dict1 = BidsTabularDictionary("My name", self.file_list, entities=('sub', 'run'))
        dist1_split, leftovers = dict1.split_by_entity('run')
        self.assertIsInstance(dist1_split, dict, "split_by_entity returns a dictionary")
        self.assertEqual(3, len(dist1_split), 'split_by_entity should return the correct number of items')
        for value in dist1_split.values():
            self.assertIsInstance(value, BidsTabularDictionary,
                                  "split_by_entity dict has BidsTabularDictionary objects")
        self.assertFalse(leftovers, "split_by_entity leftovers are empty")

    def test_correct_file_bad_file(self):
        input_data = TabularInput(self.file_list[0])
        with self.assertRaises(HedFileError) as context:
            BidsTabularDictionary._correct_file(input_data)
        self.assertEqual(context.exception.code, 'BadArgument')

    def test_correct_file_bids_file(self):
        bids_file = BidsFile(self.file_list[0])
        self.assertIsInstance(bids_file, BidsFile)
        self.assertNotIsInstance(bids_file, BidsTabularFile)
        new_file = BidsTabularDictionary._correct_file(bids_file)
        self.assertIsInstance(new_file, BidsTabularFile)

    def test_make_new(self):
        dict1 = BidsTabularDictionary("My name", self.file_list, entities=('sub', 'run'))
        dict2 = dict1.make_new("My new", self.file_list[:-1])
        self.assertIsInstance(dict1, BidsTabularDictionary)
        self.assertIsInstance(dict2, BidsTabularDictionary)
        self.assertEqual(len(dict1.file_dict), 6)
        self.assertEqual(len(dict2.file_dict), 5)

    def test_report_diffs_no_divs(self):
        dict1 = BidsTabularDictionary("Bids1", self.file_list, entities=('sub', 'run'))
        dict2 = BidsTabularDictionary("Bids2", self.file_list, entities=('sub', 'run'))
        logger = HedLogger()
        self.assertEqual(6, len(dict1.key_list), "BidsTabularDictionary has correct number of entries")
        self.assertEqual(6, len(dict2.key_list), "BidsTabularDictionary has correct number of entries")
        self.assertFalse(logger.log, "report_diffs the logger is empty before report is called")
        output1 = dict1.report_diffs(dict2, logger)
        self.assertTrue(output1, "report_diffs reports even if no differences")
        self.assertTrue(logger.log, "report_diffs the logger is not empty after report called")

    def test_report_diffs_diff_keys(self):
        dict1 = BidsTabularDictionary("Bids1", self.file_list[:-1], entities=('sub', 'run'))
        dict2 = BidsTabularDictionary("Bids2", self.file_list[1:], entities=('sub', 'run'))
        logger = HedLogger()
        self.assertEqual(5, len(dict1.key_list), "BidsTabularDictionary has correct number of entries")
        self.assertEqual(5, len(dict2.key_list), "BidsTabularDictionary has correct number of entries")
        self.assertFalse(logger.log, "report_diffs the logger is empty before report is called")
        dict1.report_diffs(dict2, logger)
        output = dict1.report_diffs(dict2, logger)
        self.assertTrue(output, "report_diffs has differences")
        self.assertTrue(logger.log, "report_diffs the logger is empty before report is called")

    def test_report_diffs_diff_rows(self):
        dict1 = BidsTabularDictionary("Bids1", self.file_list[0:1], entities=('sub', 'run'))
        dict2 = BidsTabularDictionary("Bids2", self.file_list[0:1], entities=('sub', 'run'))
        dict1.set_tsv_info()
        dict2.set_tsv_info()
        dict2.rowcount_dict["sub-002_run-1"] = 100
        logger = HedLogger()
        self.assertEqual(1, len(dict1.key_list), "BidsTabularDictionary has correct number of entries")
        self.assertEqual(1, len(dict2.key_list), "BidsTabularDictionary has correct number of entries")
        self.assertFalse(logger.log, "report_diffs the logger is empty before report is called")
        dict1.report_diffs(dict2, logger)
        output = dict1.report_diffs(dict2, logger)
        self.assertTrue(output, "report_diffs has differences")
        self.assertTrue(logger.log, "report_diffs the logger is empty before report is called")

    def test_with_tabular_summary(self):
        from hed.tools.analysis.tabular_summary import TabularSummary
        bids_root_path = os.path.realpath('../../data/bids_tests/eeg_ds003645s_hed')
        name = 'eeg_ds003645s_hed'
        exclude_dirs = ['stimuli']
        entities = ('sub', 'run')
        skip_columns = ["onset", "duration", "sample", "stim_file", "trial", "response_time"]

        # Construct the file dictionary for the BIDS event files
        event_files = get_file_list(bids_root_path, extensions=[".tsv"], name_suffix="_events",
                                    exclude_dirs=exclude_dirs)
        bids_tab = BidsTabularDictionary(name, event_files, entities=entities)

        # Create a summary of the original BIDS events file content
        bids_dicts_all, bids_dicts = TabularSummary.make_combined_dicts(bids_tab.file_dict, skip_cols=skip_columns)
        self.assertIsInstance(bids_dicts, dict)
        self.assertEqual(len(bids_dicts), len(event_files))


if __name__ == '__main__':
    unittest.main()
