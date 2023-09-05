import os
import unittest

from hed.models.sidecar import Sidecar, HedString
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.event_manager import EventManager


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

    def test_constructor(self):
        manager1 = EventManager(self.input_data, self.schema)
        self.assertIsInstance(manager1.event_list, list)
        self.assertEqual(len(manager1.event_list), len(self.input_data.dataframe))
        self.assertEqual(len(manager1.event_list[0]), 2)
        self.assertIsInstance(manager1.hed_strings, list)
        self.assertEqual(len(manager1.hed_strings), len(self.input_data.dataframe))
        self.assertEqual(len(manager1.event_list), len(self.input_data.dataframe))
        event_count = 0
        for index, item in enumerate(manager1.event_list):
            for event in item:
                event_count = event_count + 1
                self.assertTrue(event.end_index)
                self.assertEqual(event.start_index, index)
                self.assertEqual(event.start_index, index)
                self.assertEqual(event.start_time, float(manager1.input_data.dataframe.loc[index, "onset"]))
                if not event.end_time:
                    self.assertEqual(event.end_index, len(manager1.input_data.dataframe))

    def test_unfold_context_no_remove(self):
        manager1 = EventManager(self.input_data, self.schema)
        hed, base, context = manager1.unfold_context()
        for index in range(len(manager1.onsets)):
            self.assertIsInstance(hed[index], str)
            self.assertIsInstance(base[index], str)

    def test_unfold_context_remove(self):
        manager1 = EventManager(self.input_data, self.schema)
        hed, base, context = manager1.unfold_context(remove_types=['Condition-variable', 'Task'])
        for index in range(len(manager1.onsets)):
            self.assertIsInstance(hed[index], str)
            self.assertIsInstance(base[index], str)
        # ToDo  finish tests

    def test_str_list_to_hed(self):
        manager = EventManager(self.input_data, self.schema)
        hed_obj1 = manager.str_list_to_hed(['', '', ''])
        self.assertFalse(hed_obj1)
        hed, base, context = manager.unfold_context()

        hed_obj2 = manager.str_list_to_hed([hed[1], base[1], '(Event-context, (' + context[1] + '))'])
        self.assertIsInstance(hed_obj2, HedString)
        self.assertEqual(9, len(hed_obj2.children))
        hed3, base3, context3 = manager.unfold_context(remove_types=['Condition-variable', 'Task'])
        hed_obj3 = manager.str_list_to_hed([hed3[1], base3[1], '(Event-context, (' + context3[1] + '))'])
        self.assertIsInstance(hed_obj3, HedString)
        self.assertEqual(5, len(hed_obj3.children))

    def test_get_type_defs(self):
        manager1 = EventManager(self.input_data, self.schema)
        def_names = manager1.get_type_defs(["Condition-variable", "task"])
        self.assertIsInstance(def_names, list)
        self.assertEqual(11, len(def_names))


if __name__ == '__main__':
    unittest.main()
