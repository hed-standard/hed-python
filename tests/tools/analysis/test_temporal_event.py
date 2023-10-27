import os
import unittest

from hed.schema.hed_schema_io import load_schema_version
from hed.models import HedString, HedGroup, Sidecar, TabularInput
from hed.tools.analysis.temporal_event import TemporalEvent
from hed.tools.analysis.event_manager import EventManager


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids_tests/eeg_ds003645s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.events_path = events_path
        cls.sidecar = sidecar1
        cls.schema = schema

    def test_constructor_no_group(self):
        test1 = HedString("(Onset, def/blech)", hed_schema=self.schema)
        groups = test1.find_top_level_tags(["onset"], include_groups=1)
        te = TemporalEvent(groups[0], 3, 4.5)
        self.assertEqual(te.start_index, 3)
        self.assertEqual(te.start_time, 4.5)
        self.assertEqual(te.anchor, 'Def/blech')
        self.assertFalse(te.internal_group)

    def test_constructor_group(self):
        test1 = HedString("(Onset, (Label/Apple, Blue), Def/Blech/54.3)", hed_schema=self.schema)
        groups = test1.find_top_level_tags(["onset"], include_groups=1)
        te = TemporalEvent(groups[0], 3, 4.5)
        self.assertEqual(te.start_index, 3)
        self.assertEqual(te.start_time, 4.5)
        self.assertTrue(te.internal_group)
        self.assertEqual(te.anchor, 'Def/Blech/54.3')
        self.assertIsInstance(te.internal_group, HedGroup)

    def test_constructor_on_files(self):
        manager1 = EventManager(self.input_data, self.schema)
        event_list = manager1.event_list
        for events in event_list:
            if not events:
                continue
            for event in events:
                self.assertIsInstance(event, TemporalEvent)
                self.assertGreaterEqual(event.start_index, 0)
                self.assertGreaterEqual(event.start_time, 0)
                self.assertGreater(event.end_index, event.start_index)


if __name__ == '__main__':
    unittest.main()
