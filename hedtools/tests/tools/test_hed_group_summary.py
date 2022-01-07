import unittest
import json
from hed.models.sidecar import Sidecar
from hed.schema.hed_schema_file import load_schema

from hed.tools.hed_group_summary import HedGroupSummary


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp = ""

    def test_hed_group_summary_constructor(self):
        hed_url_path = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml'
        hed_schema = load_schema(hed_url_path=hed_url_path)
        the_path = '../data/bids/task-FacePerception_events.json'
        sidecar = Sidecar(the_path)
        x = sidecar._column_data['hed_def_conds'].def_dict._defs
        y = x['scrambled-face-cond']
        test_summary = HedGroupSummary(y.contents, hed_schema, name=y.name, keep_all_values=True)
        self.assertEqual(test_summary.name, 'scrambled-face-cond', 'HedGroupSummary has the right name')
        self.assertEqual(len(test_summary.tag_dict), 5, 'HedGroupSummary has the right number of tags')

    def test_hed_group_summary_str(self):
        hed_url_path = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml'
        hed_schema = load_schema(hed_url_path=hed_url_path)
        the_path = '../data/bids/task-FacePerception_events.json'
        sidecar = Sidecar(the_path)
        x = sidecar._column_data['hed_def_conds'].def_dict._defs
        y = x['scrambled-face-cond']
        test_summary = HedGroupSummary(y.contents, hed_schema, name=y.name, keep_all_values=True)
        self.assertTrue(str(test_summary).startswith('Scrambled-face-cond'), 'HedGroupSummary has a string method')
        print(f"{str(test_summary)}")


if __name__ == '__main__':
    unittest.main()
