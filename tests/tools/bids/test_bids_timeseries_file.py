import os
import unittest
from hed.tools.bids.bids_timeseries_file import BidsTimeseriesFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_path = \
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         '../../data/bids/eeg_ds003654s_hed/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_constructor(self):
        events = BidsTimeseriesFile(self.event_path)
        self.assertEqual(events.suffix, 'events', "BidsTimeseriesFile should have correct events suffix")
        self.assertEqual(events.ext, '.tsv', "BidsTimeseriesFile should have a .tsv extension")
        self.assertEqual(len(events.entity_dict), 3, "BidsTimeseriesFile should have right number of entity_dict")
        events_str = str(events)
        self.assertTrue(events_str, "BidsTimeseriesFile should have a string representation")

    def test_set_contents(self):
        events = BidsTimeseriesFile(self.event_path)
        self.assertFalse(events.contents, "BidsTimeseriesFile should have no contents until set")


if __name__ == '__main__':
    unittest.main()
