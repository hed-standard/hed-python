import os
import unittest
from hed import HedString, load_schema_version, Sidecar, TabularInput
from hed.models import DefinitionEntry
from hed.tools import HedContextManager, HedTypeVariable, HedVariableSummary, get_assembled_strings


class Test(unittest.TestCase):

    def setUp(self):
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                       'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        self.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        schema = load_schema_version(xml_version="8.1.0")
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                       'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        hed_strings1 = get_assembled_strings(input_data, hed_schema=schema, expand_defs=False)
        definitions = self.input_data.get_definitions(as_strings=False).gathered_defs
        self.var_type1 = HedTypeVariable(HedContextManager(hed_strings1, schema), schema, definitions,
                                         variable_type='condition-variable')

    def test_get_summary(self):
        var_summary1 = HedVariableSummary(variable_type="condition-variable")
        self.assertIsInstance(var_summary1, HedVariableSummary,
                              "Constructor should create a HedVariableSummary")
        summary1 = var_summary1.get_summary(as_json=False)
        self.assertIsInstance(summary1, dict, "get_summary should return a dictionary when empty")
        self.assertFalse(summary1, "get_summary should create a empty dictionary before updates")
        var_summary1.update_summary(self.var_type1)
        summary2 = var_summary1.get_summary(as_json=False)
        self.assertEqual(len(summary2), 3)
        self.assertEqual(summary2['repetition-type']['number_type_events'], 52)
        var_summary1.update_summary(self.var_type1)
        summary3 = var_summary1.get_summary(as_json=False)
        self.assertEqual(len(summary3), 3)
        self.assertEqual(summary3['repetition-type']['number_type_events'], 104)


if __name__ == '__main__':
    unittest.main()
