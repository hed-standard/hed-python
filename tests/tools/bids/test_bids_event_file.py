import os
import unittest
from hed.models import EventsInput
from hed.tools.bids.bids_event_file import BidsEventFile
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_path = \
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         '../../data/bids/eeg_ds003654s_hed/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_constructor(self):
        events = BidsEventFile(Test.event_path)
        self.assertEqual(events.suffix, 'events', "BidsEventFile should have correct events suffix")
        self.assertEqual(events.ext, '.tsv', "BidsEventFile should have a .tsv extension")
        self.assertEqual(len(events.entity_dict), 3, "BidsEventFile should have right number of entity_dict")
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
        self.assertFalse(events.bids_sidecar, "BidsEventFile should not have a sidecar on construction")
        sidecar = BidsSidecarFile(Test.sidecar_path)
        events.set_sidecars(sidecar)
        self.assertIsInstance(events.bids_sidecars, list, "BidsEventFile converts a single sidecar to a list")
        events.set_sidecars([sidecar])
        self.assertIsInstance(events.bids_sidecars, list, "BidsEventFile is a list")
        self.assertEqual(len(events.bids_sidecars), 1, "BidsEventFile has the correct number of sidecars")
        self.assertIsInstance(events.bids_sidecars[0], BidsSidecarFile,
                              "BidsEventFile has sidecars which are of type BidsSidecarFile")

    def test_set_sidecars_empty(self):
        events = BidsEventFile(Test.event_path)
        events.set_sidecars([])
        self.assertIsInstance(events.bids_sidecars, list, "BidsEventFile is a list event when empty")
        self.assertFalse(events.bids_sidecars, "BidsEventFile can have an empty list of sidecars")

        events.set_sidecars(None)
        self.assertIsInstance(events.bids_sidecars, list, "BidsEventFile is a list event when empty")
        self.assertFalse(events.bids_sidecars, "BidsEventFile can have an empty list of sidecars")


if __name__ == '__main__':
    unittest.main()
