import os
import unittest
from hed import load_schema_version, Sidecar, TabularInput
from hed.tools import HedContextManager, HedTypeVariable, HedVariableCounts, HedVariableSummary, get_assembled_strings


class Test(unittest.TestCase):

    def setUp(self):
        schema = load_schema_version(xml_version="8.1.0")
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                       'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        hed_strings1 = get_assembled_strings(input_data, hed_schema=schema, expand_defs=False)
        definitions1 = input_data.get_definitions(as_strings=False).gathered_defs
        self.var_type1 = HedTypeVariable(HedContextManager(hed_strings1, schema), schema, definitions1,
                                         variable_type='condition-variable')

    def test_get_summary_one_level(self):
        var_summary1 = HedVariableSummary(variable_type="condition-variable")
        self.assertIsInstance(var_summary1, HedVariableSummary,
                              "Constructor should create a HedVariableSummary")
        summary1 = var_summary1.get_summary(as_json=False)
        self.assertIsInstance(summary1, dict, "get_summary should return a dictionary when empty")
        self.assertFalse(summary1, "get_summary should create a empty dictionary before updates")
        count1 = HedVariableCounts('key-assignment', 'condition-variable')
        var1 = self.var_type1.get_variable('key-assignment')
        count1.update(var1)
        self.assertEqual(0, count1.direct_references, "get_summary")
        self.assertIn('right-sym-cond', count1.level_counts)
        self.assertEqual(200, count1.total_events)
        self.assertEqual(1, count1.level_counts['right-sym-cond']['files'])
        count1.update(var1)
        self.assertEqual(0, count1.direct_references, "get_summary")
        self.assertIn('right-sym-cond', count1.level_counts)
        self.assertEqual(400, count1.total_events)
        self.assertEqual(2, count1.level_counts['right-sym-cond']['files'])

    def test_get_summary_multiple_levels(self):
        var_summary1 = HedVariableSummary(variable_type="condition-variable")
        self.assertIsInstance(var_summary1, HedVariableSummary,
                              "Constructor should create a HedVariableSummary")
        summary1 = var_summary1.get_summary(as_json=False)
        self.assertIsInstance(summary1, dict, "get_summary should return a dictionary when empty")
        self.assertFalse(summary1, "get_summary should create a empty dictionary before updates")
        count1 = HedVariableCounts('face-type', 'condition-variable')
        var1 = self.var_type1.get_variable('face-type')
        count1.update(var1)
        self.assertEqual(0, count1.direct_references, "get_summary")
        self.assertEqual(3, len(count1.level_counts))
        self.assertIn('unfamiliar-face-cond', count1.level_counts)
        self.assertEqual(200, count1.total_events)
        self.assertEqual(52, count1.events)
        self.assertEqual(1, count1.level_counts['unfamiliar-face-cond']['files'])
        count1.update(var1)
        self.assertEqual(0, count1.direct_references, "get_summary")
        self.assertEqual(3, len(count1.level_counts))
        self.assertIn('unfamiliar-face-cond', count1.level_counts)
        self.assertEqual(400, count1.total_events)
        self.assertEqual(104, count1.events)
        self.assertEqual(2, count1.level_counts['unfamiliar-face-cond']['files'])


if __name__ == '__main__':
    unittest.main()
