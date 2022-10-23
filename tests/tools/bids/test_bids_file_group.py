import os
import unittest
from hed.schema.hed_schema_io import load_schema
from hed.tools.analysis.tabular_summary import TabularSummary
from hed.tools.bids.bids_file_group import BidsFileGroup
from hed.validator.hed_validator import HedValidator

# TODO: Add test when exclude directories have files of the type needed (such as JSON in code directory).


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                      '../../data/bids_tests/eeg_ds003654s_hed'))
        file_name = 'eeg/sub-002_task-FacePerception_run-1_events.tsv'
        cls.event_path = \
            os.path.realpath(os.path.join(os.path.dirname(__file__),
                                          '../../data/bids_tests/eeg_ds003654s_hed/sub-002', file_name))
        events_file = '../../data/bids_tests/eeg_ds003654s_hed/task-FacePerception_events.tsv'
        cls.sidecar_path = os.path.realpath(os.path.join(os.path.dirname(__file__), events_file))

    def test_constructor(self):
        events = BidsFileGroup(self.root_path)
        self.assertIsInstance(events, BidsFileGroup, "BidsFileGroup should create an BidsFileGroup instance")
        self.assertIsInstance(events.datafile_dict, dict, "BidsFileGroup should have an event files dictionary")
        self.assertEqual(len(events.datafile_dict), 6, "BidsFileGroup event files dictionary should have 2 entries")
        self.assertIsInstance(events.sidecar_dict, dict, "BidsFileGroup should have sidecar files dictionary")
        self.assertEqual(len(events.sidecar_dict), 1, "BidsFileGroup event files dictionary should have 1 entry")
        self.assertIsInstance(events.sidecar_dir_dict, dict, "BidsFileGroup should have sidecar directory dictionary")

    def test_validator(self):
        events = BidsFileGroup(self.root_path)
        hed_schema = \
            load_schema('https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml')
        validator = HedValidator(hed_schema)
        validation_issues = events.validate_datafiles(hed_ops=[validator], check_for_warnings=False)
        self.assertFalse(validation_issues, "BidsFileGroup should have no validation errors")
        validation_issues = events.validate_datafiles(hed_ops=[validator], check_for_warnings=True)
        self.assertTrue(validation_issues, "BidsFileGroup should have validation warnings")
        self.assertEqual(len(validation_issues), 6,
                         "BidsFileGroup should have 2 validation warnings for missing columns")

    def test_summarize(self):
        events = BidsFileGroup(self.root_path)
        info = events.summarize()
        self.assertIsInstance(info, TabularSummary, "summarize returns a TabularSummary")
        self.assertEqual(len(info.categorical_info), 10, "summarize info has entries with all columns if non-skipped")
        info2 = events.summarize(skip_cols=['onset', 'sample'])
        self.assertEqual(len(info2.categorical_info), len(info.categorical_info)-2,
                         "summarize info has two less entries if two columns are skipped")


if __name__ == '__main__':
    unittest.main()
