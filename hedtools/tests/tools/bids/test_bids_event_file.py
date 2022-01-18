import os
import unittest
from hed.models import EventsInput
from hed.tools.bids.bids_event_file import BidsEventFile
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      '../../data/bids_old/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '../../data/bids_old/task-FacePerception_events.json')

    def test_constructor(self):
        events = BidsEventFile(Test.event_path)
        self.assertEqual(events.suffix, 'events', "BidsEventFile should have correct events suffix")
        self.assertEqual(events.ext, '.tsv', "BidsEventFile should have a .tsv extension")
        self.assertEqual(len(events.entities), 3, "BidsEventFile should have right number of entities")
        events_str = str(events)
        self.assertTrue(events_str, "BidsEventFile should have a string representation")

    def test_set_contents(self):
        events = BidsEventFile(Test.event_path)
        self.assertFalse(events.contents, "BidsEventFile should have no contents until set")
        events.set_contents()
        self.assertIsInstance(events.contents, EventsInput,
                              "BidsEventFile should have EventsInput contents after setting")
        events.clear_contents()
        self.assertFalse(events.contents, "BidsEventFile should have no contents after clearing")

    def test_set_sidecars(self):
        events = BidsEventFile(Test.event_path)
        self.assertFalse(events.sidecars, "BidsEventFile should have no sidecars on construction")
        sidecar = BidsSidecarFile(Test.sidecar_path)
        events.set_sidecars(sidecar)
        self.assertIsInstance(events.sidecars, list, "BidsEventFile converts a single sidecar to a list")
        events.set_sidecars([sidecar])
        self.assertIsInstance(events.sidecars, list, "BidsEventFile is a list")
        self.assertEqual(len(events.sidecars), 1, "BidsEventFile has the correct number of sidecars")
        self.assertIsInstance(events.sidecars[0], BidsSidecarFile,
                              "BidsEventFile has sidecars which are of type BidsSidecarFile")

    def test_set_sidecars_empty(self):
        events = BidsEventFile(Test.event_path)
        events.set_sidecars([])
        self.assertIsInstance(events.sidecars, list, "BidsEventFile is a list event when empty")
        self.assertFalse(events.sidecars, "BidsEventFile can have an empty list of sidecars")

        events.set_sidecars(None)
        self.assertIsInstance(events.sidecars, list, "BidsEventFile is a list event when empty")
        self.assertFalse(events.sidecars, "BidsEventFile can have an empty list of sidecars")


if __name__ == '__main__':
    unittest.main()
