import os
import unittest
from hed.models.tabular_input import TabularInput
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile
from hed.tools.bids.bids_tabular_file import BidsTabularFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        event_path = "../../data/remodel_tests/sub-001_task-AuditoryVisualShift_run-01_events.tsv"
        cls.event_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), event_path)

        hed_col_path = "../../data/remodel_tests/sub-002withHed_task-FacePerception_run-1_events.tsv"
        cls.event_path_hed_col = os.path.join(os.path.dirname(os.path.realpath(__file__)), hed_col_path)

        sidecar_path = "../../data/remodel_tests/task-AuditoryVisualShift_events.json"
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), sidecar_path)

    def test_constructor(self):
        events = BidsTabularFile(self.event_path)
        self.assertEqual(events.suffix, "events", "BidsTabularFile should have correct events suffix.")
        self.assertEqual(events.ext, ".tsv", "BidsTabularFile should have a .tsv extension.")
        self.assertEqual(len(events.entity_dict), 3, "BidsTabularFile should have right number of entity_dict.")
        events_str = str(events)
        self.assertTrue(events_str, "BidsTabularFile should have a string representation.")
        self.assertFalse(events.sidecar, "BidsTabularFile does not have a sidecar unless set.")

    def test_set_contents_no_sidecar(self):
        events = BidsTabularFile(self.event_path)
        self.assertFalse(events.contents, "BidsTabularFile should have no contents until set.")
        events.set_contents()
        self.assertIsInstance(
            events.contents, TabularInput, "BidsTabularFile should have TabularInput contents after setting."
        )
        self.assertFalse(events.has_hed, "set_contents indicate HED if no sidecar and no HED columns.")
        events.clear_contents()
        self.assertIsNone(events.contents, "BidsTabularFile should have no contents after clearing.")

    def test_set_contents_with_sidecar(self):
        events = BidsTabularFile(self.event_path)
        sidecar = BidsSidecarFile(self.sidecar_path)
        self.assertFalse(sidecar.contents, "BidsSidecar does not have contents until set.")
        self.assertFalse(sidecar.has_hed, "The sidecar has HED")
        sidecar.set_contents()
        self.assertIsInstance(sidecar.contents, Sidecar, "The sidecar has contents after setting")
        events.sidecar = sidecar.contents
        self.assertFalse(events.has_hed, "The events file does not have HED until contents set.")
        events.set_contents()
        self.assertIsInstance(events.contents, TabularInput, "BidsTabularFile the right contents after setting")
        self.assertTrue(events.has_hed, "The events file has HED after contents are set.")

    def test_set_contents_with_hed_col(self):
        events = BidsTabularFile(self.event_path_hed_col)
        self.assertFalse(events.has_hed, "The events file does not have HED until contents set.")
        events.set_contents()
        self.assertIsInstance(events.contents, TabularInput, "BidsTabularFile the right contents after setting")
        self.assertTrue(events.has_hed, "The events file has HED after contents are set if HED column no sidecar.")


if __name__ == "__main__":
    unittest.main()
