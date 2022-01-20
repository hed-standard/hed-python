import os
import unittest
from hed.models.sidecar import Sidecar
from hed.schema import load_schema

from hed.tools.summaries.hed_group_summary import HedGroupSummary


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bids_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json')

    def test_hed_group_summary_constructor(self):
        hed_url_path = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml'
        hed_schema = load_schema(hed_url_path)
        sidecar = Sidecar(self.bids_path)
        x = sidecar._column_data['hed_def_conds'].def_dict._defs
        y = x['scrambled-face-cond']
        test_summary = HedGroupSummary(y.contents, hed_schema, name=y.name, keep_all_values=True)
        self.assertEqual(test_summary.name, 'Scrambled-face-cond', 'HedGroupSummary has the right name')
        self.assertEqual(len(test_summary.tag_dict), 5, 'HedGroupSummary has the right number of tags')

    def test_hed_group_summary_str(self):
        hed_url_path = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml'
        hed_schema = load_schema(hed_url_path)

        sidecar = Sidecar(self.bids_path)
        x = sidecar._column_data['hed_def_conds'].def_dict._defs
        y = x['scrambled-face-cond']
        test_summary = HedGroupSummary(y.contents, hed_schema, name=y.name, keep_all_values=True)
        self.assertTrue(str(test_summary).startswith('Scrambled-face-cond'), 'HedGroupSummary has a string method')


if __name__ == '__main__':
    unittest.main()
