import os
import unittest
import json
import io
import numpy as np
import pandas as pd

from hed.errors import HedFileError
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
        sidecar_dict = {
            "event_code": {
                "HED": {
                    "show": "Sensory-event,Visual-presentation",
                    "respond": "Press",
                    "whatever": "Black",
                    "whatelse": "Purple"
                }
            },
            "defs": {
                "HED": {
                    "defs1": "(Definition/Con1, (Condition-variable/Cond-one)), (Definition/Con2, (Condition-variable/Cond-one))"
                }
            }
        }

        cls.sidecar2 = Sidecar(io.StringIO(json.dumps(sidecar_dict)))
        cls.sidecar = sidecar1
        cls.schema = schema
        cls.def_dict = "(Definition/Def1, (Event))"

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

    def test_no_onset_constructor(self):
        # No onsets --- has an event manager
        tsv = {
            "event_code": ["show", "respond", "show", "respond", "whatever", "show", "whatelse", "respond"],
            "HED": ["Age/100", "n/a", "n/a", "n/a", "Green", "n/a", "Female", "n/a"],
        }

        tab = TabularInput(pd.DataFrame(tsv), sidecar=self.sidecar2)
        eman = EventManager(tab, self.schema)
        self.assertIsNone(eman.onsets)
        self.assertEqual(str(eman.hed_strings[0]), "Age/100,Sensory-event,Visual-presentation")

        # No onsets and an n/a entry
        tsv["event_code"][2] = "n/a"
        tab2 = TabularInput(pd.DataFrame(tsv), sidecar=self.sidecar2)
        eman2 = EventManager(tab2, self.schema)
        self.assertIsNone(eman2.onsets)
        self.assertEqual(str(eman2.hed_strings[0]), "Age/100,Sensory-event,Visual-presentation")
        self.assertFalse(str(eman2.hed_strings[2]))
        self.assertIsNone(eman2.base)
        self.assertIsNone(eman2.context)

    def test_bad_onset_constructor(self):
        tsv = {
            "onset": [0.0, 1.2, 1.2, 3.0, 5, 3.5, 4, 6],
            "duration": [0.5, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"],
            "event_code": ["show", "respond", "show", "respond", "whatever", "show", "whatelse", "respond"],
            "HED": ["Age/100", "n/a", "n/a", "n/a", "Green", "n/a", "Female", "n/a"],
        }

        tab = TabularInput(pd.DataFrame(tsv), sidecar=self.sidecar2)
        with self.assertRaises(HedFileError):
            EventManager(tab, self.schema)

        tsv = {
            "onset": [0.0, 1.2, 1.2, 3.0, "n/a", 3.5, "n/a", 6],
            "duration": [0.5, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"],
            "event_code": ["show", "respond", "show", "respond", "whatever", "show", "whatelse", "respond"],
            "HED": ["Age/100", "n/a", "n/a", "n/a", "Green", "n/a", "Female", "n/a"],
        }
        tab = TabularInput(pd.DataFrame(tsv), sidecar=self.sidecar2)
        with self.assertRaises(HedFileError):
            EventManager(tab, self.schema)

    def test_unfold_no_onset(self):
        tsv = {
            "event_code": ["show", "respond", "show", "respond", "whatever", "show", "whatelse", "respond"],
            "HED": ["Age/100,Condition-variable/Temp", "Def/Con1", "Def/Con2", "n/a", "Green", "n/a", "Female", "n/a"],
        }
        tab = TabularInput(pd.DataFrame(tsv), sidecar=self.sidecar2)
        manager1 = EventManager(tab, self.schema)
        hed1, base1, context1 = manager1.unfold_context()
        hed2, base2, context2 = manager1.unfold_context(remove_types=["Condition-variable"])
        self.assertEqual(hed1[1], "Def/Con1,Press")
        self.assertEqual(hed2[1], "Press")

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

    def test_onset_ordering_mixed(self):
        df = pd.DataFrame({'onset': [1, 2, '3', 3.24, 5],
                           'HED': ['(Duration/4.0 s, (Black))', '(Duration/2 s, (Red))', 'Blue', 'Green', 'Label/1']})
        manager = EventManager(TabularInput(df), self.schema)
        self.assertIsInstance(manager, EventManager)
        hed, base, context = manager.unfold_context()
        self.assertEqual(hed[2], 'Blue')
        self.assertFalse(hed[0])
        self.assertFalse(base[2])
        self.assertFalse(context[0])

    def test_onset_ordering_bad(self):
        df = pd.DataFrame({'onset': [1, 2, '3', 'n/a', 5],
                           'HED': ['(Duration/4.0 s, (Black))', '(Duration/2 s, (Red))', 'Blue', 'n/a', 'Label/1']})
        with self.assertRaises(HedFileError) as ex:
            EventManager(TabularInput(df), self.schema)
            self.assertEqual(ex.args(0), "OnsetsNotOrdered")
        df1 = pd.DataFrame({'onset': [1, 2, 1.4, 6, 5],
                           'HED': ['(Duration/4.0 s, (Black))', '(Duration/2 s, (Red))', 'Blue', 'n/a', 'Label/1']})
        with self.assertRaises(HedFileError) as ex1:
            EventManager(TabularInput(df1), self.schema)
            self.assertEqual(ex1.args(0), "OnsetsNotOrdered")

        df2 = pd.DataFrame({'onset': [1, np.nan, 1.4, 6, 5],
                           'HED': ['(Duration/4.0 s, (Black))', '(Duration/2 s, (Red))', 'Blue', 'n/a', 'Label/1']})
        with self.assertRaises(HedFileError) as ex2:
            EventManager(TabularInput(df2), self.schema)
            self.assertEqual(ex2.args(0), "OnsetsNotOrdered")

    def test_duration_context(self):
        df = pd.DataFrame({'onset': [1, 2, 3, 4, 5],
                           'HED': ['(Duration/5.0 s, (Black))', '(Duration/2 s, (Red))', 'Blue', 'n/a', 'Label/1']})
        manager = EventManager(TabularInput(df), self.schema)
        hed, base, context = manager.unfold_context()
        self.assertTrue(all("Black" in item for item in context[1:]))
        self.assertTrue(all("Red" in item for item in context[2:3]))
        self.assertTrue(all("Black" in item for item in base[0:1]))

    def test_duration_context2(self):
        df = pd.DataFrame({'onset': [1, 2, 3, 4, 5],
                           'HED': ['(Duration/1.0 s, (Black))', '(Duration/2 s, (Red))', 'Blue', 'n/a', 'Label/1']})
        manager = EventManager(TabularInput(df), self.schema)
        hed, base, context = manager.unfold_context()
        self.assertTrue(not any("Black" in item for item in context))
        self.assertTrue(all("Red" in item for item in context[2:3]))
        self.assertTrue(all("Black" in item for item in base[0:1]))

    def test_duration_context_same_onset(self):
        df = pd.DataFrame({'onset': [1, 1, 3, 4, 5],
                           'HED': ['(Duration/3.0 s, (Black))', '(Duration/2 s, (Red))', 'Blue', 'n/a', 'Label/1']})
        manager = EventManager(TabularInput(df), self.schema)
        hed, base, context = manager.unfold_context()
        self.assertTrue(all("Black" in item for item in context[1:3]))
        self.assertTrue(all("Red" in item for item in context[1:2]))
        self.assertTrue(all("Black" in item for item in base[0:1]))
        self.assertTrue(all("Red" in item for item in base[0:1]))


if __name__ == '__main__':
    unittest.main()
