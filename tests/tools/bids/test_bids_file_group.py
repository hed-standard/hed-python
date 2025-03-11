import os
import unittest
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.tabular_summary import TabularSummary
from hed.tools.bids.bids_file_group import BidsFileGroup
from hed.tools.util import io_util
from hed.errors.error_reporter import ErrorHandler

# TODO: Add test when exclude directories have files of the type needed (such as JSON in code directory).


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root_path = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                      '../../data/bids_tests/eeg_ds003645s_hed'))
        exclude_dirs = ['sourcedata', 'derivatives', 'code', 'stimuli']
        file_name = 'eeg/sub-002_task-FacePerception_run-1_events.tsv'
        cls.file_paths = io_util.get_file_list(root_path, extensions=['.tsv', '.json'],
                                               exclude_dirs=exclude_dirs, name_suffix=['_events'])
        cls.root_path = root_path
        cls.exclude_dirs = exclude_dirs
        cls.event_path = \
            os.path.realpath(os.path.join(os.path.dirname(__file__),
                                          '../../data/bids_tests/eeg_ds003645s_hed/sub-002', file_name))
        events_file = '../../data/bids_tests/eeg_ds003645s_hed/task-FacePerception_events.tsv'
        cls.sidecar_path = os.path.realpath(os.path.join(os.path.dirname(__file__), events_file))

    def test_constructor(self):
        events = BidsFileGroup(self.root_path, self.file_paths, 'events')
        self.assertIsInstance(events, BidsFileGroup, "BidsFileGroup should create an BidsFileGroup instance")
        self.assertIsInstance(events.datafile_dict, dict, "BidsFileGroup should have an event files dictionary")
        self.assertEqual(len(events.datafile_dict), 6, "BidsFileGroup event files dictionary should have 2 entries")
        self.assertIsInstance(events.sidecar_dict, dict, "BidsFileGroup should have sidecar files dictionary")
        self.assertEqual(len(events.sidecar_dict), 1, "BidsFileGroup event files dictionary should have 1 entry")
        self.assertIsInstance(events.sidecar_dir_dict, dict, "BidsFileGroup should have sidecar directory dictionary")
        empty_stuff = BidsFileGroup(self.root_path, [], 'events')
        self.assertIsInstance(events, BidsFileGroup, "BidsFileGroup should create an BidsFileGroup instance")

    def test_create_file_group(self):
        events = BidsFileGroup.create_file_group(self.root_path, self.file_paths, 'events')
        self.assertIsInstance(events, BidsFileGroup, "BidsFileGroup should create an BidsFileGroup instance")
        self.assertIsInstance(events.datafile_dict, dict, "BidsFileGroup should have an event files dictionary")
        self.assertEqual(len(events.datafile_dict), 6, "BidsFileGroup event files dictionary should have 2 entries")
        self.assertIsInstance(events.sidecar_dict, dict, "BidsFileGroup should have sidecar files dictionary")
        self.assertEqual(len(events.sidecar_dict), 1, "BidsFileGroup event files dictionary should have 1 entry")
        self.assertIsInstance(events.sidecar_dir_dict, dict, "BidsFileGroup should have sidecar directory dictionary")
        empty_stuff = BidsFileGroup.create_file_group(self.root_path, [], 'events')
        self.assertIsNone(empty_stuff, "create_file_group with empty list should return None")

    def test_validator(self):
        events = BidsFileGroup(self.root_path, self.file_paths, 'events')
        hed_schema = load_schema_version("8.3.0")
        validation_issues = events.validate_datafiles(hed_schema)
        self.assertFalse(validation_issues, "BidsFileGroup should have no validation errors")
        validation_issues = events.validate_datafiles(hed_schema, error_handler=ErrorHandler(check_for_warnings=True))
        self.assertTrue(validation_issues, "BidsFileGroup should have validation warnings")
        self.assertEqual(len(validation_issues), 6,
                         "BidsFileGroup should have 2 validation warnings for missing columns")

    def test_summarize(self):
        events = BidsFileGroup(self.root_path, self.file_paths, 'events')
        info = events.summarize()
        self.assertIsInstance(info, TabularSummary, "get_summary returns a TabularSummary")
        self.assertEqual(len(info.categorical_info), 10, "get_summary info has entries with all columns if non-skipped")
        info2 = events.summarize(skip_cols=['onset', 'sample'])
        self.assertEqual(len(info2.categorical_info), len(info.categorical_info)-2,
                         "get_summary info has two less entries if two columns are skipped")


if __name__ == '__main__':
    unittest.main()
