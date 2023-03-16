import os
import unittest
from hed.errors.exceptions import HedFileError
from hed.models.hed_string import HedString
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.analysis.hed_context_manager import HedContextManager
from hed.models.df_util import get_assembled


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = load_schema_version(xml_version="8.1.0")
        cls.test_strings1 = [HedString('Sensory-event,(Def/Cond1,(Red, Blue),Onset),(Def/Cond2,Onset),Green,Yellow',
                                       hed_schema=schema),
                             HedString('(Def/Cond1, Offset)', hed_schema=schema),
                             HedString('White, Black', hed_schema=schema),
                             HedString('', hed_schema=schema),
                             HedString('(Def/Cond2, Onset)', hed_schema=schema),
                             HedString('(Def/Cond3/1.3, Onset)', hed_schema=schema),
                             HedString('Arm, Leg', hed_schema=schema)]
        cls.test_strings2 = [HedString('(Def/Cond3/2, Offset)', hed_schema=schema)]
        cls.test_strings3 = [HedString("Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
                                       hed_schema=schema),
                             HedString("Yellow", hed_schema=schema),
                             HedString("Def/Cond2, (Def/Cond6/4, Onset)", hed_schema=schema),
                             HedString("Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)", hed_schema=schema),
                             HedString("Def/Cond2, Def/Cond6/4", hed_schema=schema)]

        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids_tests/eeg_ds003645s_hed'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.sidecar1 = sidecar1
        cls.schema = schema

    # def test_onset_group(self):
    #     str1 = '(Def/Temper, (Label/help))'
    #     str1_obj = HedString(str1)
    #     grp1 = str1_obj.chilren()[0]
    #     on_grp1 = OnsetGroup('this_group', x, 1)
    #     self.assertIsInstance(grp1.contents, str)
    #     self.assertEqual(grp1.contents, '(Def/Temper,(Label/help))')
    #     str1_obj = HedString(str1)
    #     grp2 =
    #     self.assertIsInstance(grp2.contents, str)
    #     self.assertEqual(grp2.contents, str1)
    #
    #     y = HedGroup(str1)
    #     grp3 = OnsetGroup('this_group', y, 0)
    #     self.assertIsInstance(grp3.contents, str)
    #     self.assertEqual(grp3.contents, str1)
    #     grp4 = OnsetGroup('this_group', x, 0, 10)
    #     self.assertIsInstance(grp4.contents, str)
    #     self.assertEqual(grp4.contents, str1)

    def test_constructor(self):
        manager1 = HedContextManager(self.test_strings1, self.schema)
        self.assertIsInstance(manager1, HedContextManager, "The constructor should create an HedContextManager")
        self.assertEqual(len(manager1.hed_strings), 7, "The constructor should have the right number of strings")
        self.assertEqual(len(manager1.onset_list), 4, "The constructor should have right length onset list")
        self.assertIsInstance(manager1.hed_strings[1], HedString, "Constructor hed string should be a hedstring")
        self.assertFalse(manager1.hed_strings[1].children, "When no tags list HedString is empty")
        context = manager1.contexts
        self.assertIsInstance(context, list, "The constructor event contexts should be a list")
        self.assertIsInstance(context[1], HedString, "The constructor event contexts has a correct element")

    def test_constructor1(self):
        with self.assertRaises(ValueError) as cont:
            HedContextManager(self.test_strings1, None)
        self.assertEqual(cont.exception.args[0], "ContextRequiresSchema")

    def test_iter(self):
        hed_strings, _ = get_assembled(self.input_data, self.sidecar1, self.schema, extra_def_dicts=None,
                                       join_columns=True, shrink_defs=True, expand_defs=False)
        manager1 = HedContextManager(hed_strings, self.schema)
        i = 0
        for hed, context in manager1.iter_context():
            self.assertEqual(hed, manager1.hed_strings[i])
            self.assertEqual(context, manager1.contexts[i])
            i = i + 1

    def test_constructor_from_assembled(self):
        hed_strings, _ = get_assembled(self.input_data, self.sidecar1, self.schema, extra_def_dicts=None,
                                       join_columns=True, shrink_defs=True, expand_defs=False)
        manager1 = HedContextManager(hed_strings, self.schema)
        self.assertEqual(len(manager1.hed_strings), 200,
                         "The constructor for assembled strings has expected # of strings")
        self.assertEqual(len(manager1.onset_list), 261,
                         "The constructor for assembled strings has onset_list of correct length")

    def test_constructor_unmatched(self):
        with self.assertRaises(HedFileError) as context:
            HedContextManager(self.test_strings2, self.schema)
        self.assertEqual(context.exception.args[0], 'UnmatchedOffset')

    def test_constructor_multiple_values(self):
        manager = HedContextManager(self.test_strings3, self.schema)
        self.assertEqual(len(manager.onset_list), 3, "Constructor should have right number of onsets")


if __name__ == '__main__':
    unittest.main()
