import os
import unittest
from hed.schema.hed_schema_file import load_schema
from hed.tools.bids.bids_event_files import BidsEventFiles
from hed.validator.hed_validator import HedValidator


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/bids_old')
        cls.event_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      '../../data/bids_old/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '../../data/bids_old/task-FacePerception_events.tsv')

    def test_constructor(self):
        events = BidsEventFiles(Test.root_path)
        self.assertIsInstance(events, BidsEventFiles, "BidsEventFiles should create an BidsEventFiles instance")
        self.assertIsInstance(events.events_dict, dict, "BidsEventFiles should have an event files dictionary")
        self.assertEqual(len(events.events_dict), 2, "BidsEventFiles event files dictionary should have 2 entries")
        self.assertIsInstance(events.sidecar_dict, dict, "BidsEventFiles should have sidecar files dictionary")
        self.assertEqual(len(events.sidecar_dict), 1, "BidsEventFiles event files dictionary should have 1 entry")
        self.assertIsInstance(events.sidecar_dir_dict, dict, "BidsEventFiles should have sidecar directory dictionary")

    def test_validator(self):
        events = BidsEventFiles(Test.root_path)
        hed_schema = load_schema(
            hed_url_path='https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml')
        validator = HedValidator(hed_schema=hed_schema)
        validation_issues = events.validate(validators=[validator], check_for_warnings=False)
        self.assertFalse(validation_issues, "BidsEventFiles should have no validation errors")
        validation_issues = events.validate(validators=[validator], check_for_warnings=True)
        self.assertTrue(validation_issues, "BidsEventFiles should have validation warnings")
        self.assertEqual(len(validation_issues), 2,
                         "BidsEventFiles should have 2 validation warnings for missing columns")


if __name__ == '__main__':
    unittest.main()
