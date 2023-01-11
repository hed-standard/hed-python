# import os
# import unittest
# from hed import HedString, load_schema_version, Sidecar, TabularInput
# from hed.models import DefinitionEntry
# # from hed.tools.analysis.hed_filters import RemoveTagsFilter
#
#
# class Test(unittest.TestCase):
#     CONST = 3
#     # @classmethod
#     # def setUpClass(cls):
#     #     curation_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/remodeling')
#     #     bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
#     #                                       '../../data/bids_tests/eeg_ds003654s_hed'))
#     #     schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
#     #                                    '../../data/schema_tests/HED8.0.0.xml'))
#     #     schema = load_schema_version(xml_version="8.1.0")
#     #     cls.test_strings1 = [HedString(f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset),"
#     #                                    f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4, Def/Other",
#     #                                    hed_schema=schema),
#     #                          HedString('(Def/Cond1, Offset)', hed_schema=schema),
#     #                          HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast',
#     #                                    hed_schema=schema),
#     #                          HedString('', hed_schema=schema),
#     #                          HedString('(Def/Cond2, Onset), Def/Other, ', hed_schema=schema),
#     #                          HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
#     #                          HedString('Arm, Leg, Condition-variable/Fast', hed_schema=schema)]
#     #     cls.test_strings2 = [HedString(f"Def/Cond2, (Def/Cond6/4, Onset), (Def/Cond6/7.8, Onset), Def/Cond6/Alpha",
#     #                                    hed_schema=schema),
#     #                          HedString("Yellow", hed_schema=schema),
#     #                          HedString("Def/Cond2, (Def/Cond6/4, Onset)", hed_schema=schema),
#     #                          HedString("Def/Cond2, Def/Cond6/5.2 (Def/Cond6/7.8, Offset)", hed_schema=schema),
#     #                          HedString("Def/Cond2, Def/Cond6/4", hed_schema=schema)]
#     #
#     #     def1 = HedString('(Condition-variable/Var1, Circle, Square)', hed_schema=schema)
#     #     def2 = HedString('(condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere)', hed_schema=schema)
#     #     def3 = HedString('(Organizational-property/Condition-variable/Var3, Physical-length/#, Ellipse, Cross)',
#     #                      hed_schema=schema)
#     #     def4 = HedString('(Condition-variable, Apple, Banana)', hed_schema=schema)
#     #     def5 = HedString('(Condition-variable/Lumber, Apple, Banana)', hed_schema=schema)
#     #     def6 = HedString('(Condition-variable/Lumber, Label/#, Apple, Banana)', hed_schema=schema)
#     #     def7 = HedString('(Label/#, Apple, Banana)', hed_schema=schema)
#     #     cls.defs = {'Cond1': DefinitionEntry('Cond1', def1, False, None),
#     #                 'Cond2': DefinitionEntry('Cond2', def2, False, None),
#     #                 'Cond3': DefinitionEntry('Cond3', def3, True, None),
#     #                 'Cond4': DefinitionEntry('Cond4', def4, False, None),
#     #                 'Cond5': DefinitionEntry('Cond5', def5, False, None),
#     #                 'Cond6': DefinitionEntry('Cond6', def6, True, None),
#     #                 'Other': DefinitionEntry('Other', def7, False, None)
#     #                 }
#     #
#     #     cls.dlist = \
#     #         ['(Definition/Cond1, (Condition-variable/Var1, Circle, Square))',
#     #          '(Definition/Cond2, (condition-variable/Var2, Condition-variable/Apple, Triangle, Sphere))',
#     #          '(Definition/Cond3, (Organizational-property/Condition-variable/Var3, Physical-length/#,
#     #          Ellipse, Cross))',
#     #          '(Definition/Cond4, (Condition-variable, Apple, Banana))',
#     #          '(Definition/Cond5, (Condition-variable/Lumber, Apple, Banana))',
#     #          '(Definition/Cond6, (Condition-variable/Lumber, Label/#, Apple, Banana))',
#     #          '(Definition/Cond6, (Label/#, Apple, Banana))']
#     #
#     #     cls.string1 = f"Sensory-event,(Def/Cond1,(Red, Blue, Condition-variable/Trouble),Onset)," + \
#     #                   f"(Def/Cond2,Onset),Green,Yellow, Def/Cond5, Def/Cond6/4, Def/Other"
#     #     bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
#     #                                       '../../data/bids_tests/eeg_ds003654s_hed'))
#     #     events_path = os.path.realpath(os.path.join(bids_root_path,
#     #                                                 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
#     #     sidecar_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
#     #     sidecar1 = Sidecar(sidecar_path, name='face_sub1_json')
#     #     cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
#     #     cls.hed_schema = schema
#     #
#     # def test_remove_tags_filter(self):
#     #     filter1 = RemoveTagsFilter(["Definition"], remove_option="all")
#     #     definitions = (',').join(self.dlist)
#     #     hed1 = HedString(definitions, hed_schema=self.hed_schema)
#     #     self.assertTrue(hed1.children, "remove_tags_filter test string before is not empty")
#     #     filter1.remove_tags(hed1)
#     #     self.assertFalse(hed1.children, "remove_tags_filter test after is empty")
#     #
#
#
# if __name__ == '__main__':
#     unittest.main()
