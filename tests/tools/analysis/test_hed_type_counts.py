import os
import unittest
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.tools.analysis.hed_type_values import HedTypeValues
from hed.tools.analysis.hed_type_counts import HedTypeCount, HedTypeCounts
from hed.models.df_util import get_assembled


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
        input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        hed_strings1, definitions1 = get_assembled(input_data, sidecar1, schema, extra_def_dicts=None,
                                                   join_columns=True, shrink_defs=True, expand_defs=False)
        cls.var_type1 = HedTypeValues(HedContextManager(hed_strings1, schema), definitions1, 'run-01',
                                      type_tag='condition-variable')

    def test_type_count_one_level(self):
        type_counts1 = HedTypeCounts('Dummy', "condition-variable")
        self.assertIsInstance(type_counts1, HedTypeCounts, "Constructor should create a HedTypeCounts")
        count1 = HedTypeCount('key-assignment', 'condition-variable', 'run-01')
        self.assertEqual(0, count1.direct_references, "get_summary")
        var1 = self.var_type1.get_type_value_factors('key-assignment')
        count1.update(var1.get_summary(), 'run-1')
        self.assertEqual(0, count1.direct_references, "get_summary")
        self.assertIn('right-sym-cond', count1.level_counts)
        self.assertEqual(200, count1.total_events)
        self.assertEqual(1, count1.level_counts['right-sym-cond']['files'])
        count1.update(var1.get_summary(), 'run-2')
        self.assertEqual(0, count1.direct_references, "get_summary")
        self.assertIn('right-sym-cond', count1.level_counts)
        self.assertEqual(400, count1.total_events)
        self.assertEqual(2, count1.level_counts['right-sym-cond']['files'])

    def test_get_summary_multiple_levels(self):
        counts = HedTypeCounts('Dummy', "condition-variable")
        self.assertIsInstance(counts, HedTypeCounts, "Constructor should create a HedTypeCounts")
        counts.update_summary(self.var_type1.get_summary(), self.var_type1.total_events, 'run-1')
        type_dict = counts.type_dict
        self.assertEqual(len(type_dict), 3)
        self.assertIn('face-type', type_dict)
        face_type = type_dict['face-type']
        self.assertEqual(face_type.total_events, 200)
        self.assertEqual(face_type.events, 52)
        self.assertEqual(len(face_type.files), 1)
        counts.update_summary(self.var_type1.get_summary(), self.var_type1.total_events, 'run-2')
        type_dict = counts.type_dict
        self.assertEqual(len(type_dict), 3)
        self.assertIn('face-type', type_dict)
        face_type = type_dict['face-type']
        self.assertEqual(face_type.total_events, 400)
        self.assertEqual(face_type.events, 104)
        self.assertEqual(len(face_type.files), 2)
        counts.add_descriptions(self.var_type1.definitions)
        self.assertTrue(face_type.level_counts['famous-face-cond']['description'])


if __name__ == '__main__':
    unittest.main()
