import os
import unittest

from hed.models.sidecar import Sidecar
from hed.models.df_util import get_assembled
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
        # self.assertEqual(len(manager1.event_list), len(self.input_data.dataframe))
        # event_count = 0
        # for index, item in enumerate(manager1.event_list):
        #     for event in item:
        #         event_count = event_count + 1
        #         self.assertFalse(event.duration)
        #         self.assertTrue(event.end_index)
        #         self.assertEqual(event.start_index, index)
        #         self.assertEqual(event.start_index, index)
        #         self.assertEqual(event.start_time, manager1.data.dataframe.loc[index, "onset"])
        #         if not event.end_time:
        #             self.assertEqual(event.end_index, len(manager1.data.dataframe))

    # def test_constructor(self):
    #     with self.assertRaises(ValueError) as cont:
    #         HedContextManager(self.test_strings1, None)
    #     self.assertEqual(cont.exception.args[0], "ContextRequiresSchema")

    # def test_iter(self):
    #     hed_strings = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
    #     manager1 = HedContextManager(hed_strings, self.schema)
    #     i = 0
    #     for hed, context in manager1.iter_context():
    #         self.assertEqual(hed, manager1.hed_strings[i])
    #         self.assertEqual(context, manager1.contexts[i])
    #         i = i + 1

    # def test_constructor_from_assembled(self):
    #     hed_strings = get_assembled_strings(self.input_data, hed_schema=self.schema, expand_defs=False)
    #     manager1 = HedContextManager(hed_strings, self.schema)
    #     self.assertEqual(len(manager1.hed_strings), 200,
    #                      "The constructor for assembled strings has expected # of strings")
    #     self.assertEqual(len(manager1.onset_list), 261,
    #                      "The constructor for assembled strings has onset_list of correct length")

    # def test_constructor_unmatched(self):
    #     with self.assertRaises(HedFileError) as context:
    #         HedContextManager(self.test_strings2, self.schema)
    #     self.assertEqual(context.exception.args[0], 'UnmatchedOffset')

    # def test_constructor_multiple_values(self):
    #     manager = HedContextManager(self.test_strings3, self.schema)
    #     self.assertEqual(len(manager.onset_list), 3, "Constructor should have right number of onsets")


if __name__ == '__main__':
    unittest.main()
