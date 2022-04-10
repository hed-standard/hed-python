import unittest
from hed.models.hed_group import HedGroup
from hed.models.hed_string import HedString
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.annotation.summary_entry import SummaryEntry


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version(xml_version="8.0.0")
        cls.str1 = f"(Task,Experiment-participant,(See,Face),(Discriminate,(Face, Symmetrical))," \
                   f"(Press,Keyboard-key),Description/Evaluate degree of image symmetry and respond with key" \
                   f"press evaluation.)"
        cls.str2 = f"Sensory-event, (Intended-effect, Cue), (Def/Cross-only, Onset), (Def/Fixation-task, Onset)," \
                   f"(Def/Circle-only, Offset)"
        cls.str_with_def = f"(Definition/First-show-cond, ((Condition-variable/Repetition-type," \
                           f" (Item-count/1, Face), Item-interval/0), " \
                           f"Description/Factor level indicating the first display of this face.))"
        cls.str_with_defs = f"(Definition/First-show-cond, ((Condition-variable/Repetition-type," \
                            f" (Item-count/1, Face), Item-interval/0), " \
                            f"Description/Factor level indicating the first display of this face.))" \
                            f"(Definition/Immediate-repeat-cond, ((Condition-variable/Repetition-type, " \
                            f"(Item-count/2, Face), Item-interval/1), " \
                            f"Description/Factor level indicating this face was the same as previous one.))" \
                            f"(Definition/Delayed-repeat-cond, (Condition-variable/Repetition-type, " \
                            f"(Item-count/2, Face), (Item-interval, (Greater-than-or-equal-to, Item-interval/5)), " \
                            f"Description/Factor level indicating face was seen 5 to 15 trials ago.))"
        cls.str_with_def_expand = f"(Def-expand/First-show-cond, ((Condition-variable/Repetition-type," \
                                  f" (Item-count/1, Face), Item-interval/0), " \
                                  f"Description/Factor level indicating the first display of this face.))"

    def test_constructor(self):
        hed1 = HedString(self.str1)
        hed1.convert_to_canonical_forms(self.schema)
        entry1 = SummaryEntry("Face-symmetry-evaluation-task", hed1)
        self.assertIsInstance(entry1, SummaryEntry, "SummaryEntry constructor should create an object")
        self.assertEqual(entry1.name, "Face-symmetry-evaluation-task",
                         "SummaryEntry constructor should have the right name")
        self.assertIsInstance(entry1.group, HedGroup, "SummaryEntry constructor group should be a HedGroup")
        self.assertTrue(entry1.tag_dict, "SummaryEntry constructor group should have a tag dictionary until set")
        self.assertTrue('Description' in entry1.tag_dict, "SummaryEntry should not parse values when schema is None")

        entry2 = SummaryEntry("Dummy", HedGroup(""))
        self.assertIsInstance(entry2, SummaryEntry,
                              "SummaryEntry constructor should create an object when contents are empty")
        self.assertEqual(entry2.name, "Dummy",
                         "SummaryEntry constructor should have the right name when contents empty")
        self.assertFalse(entry2.group, "SummaryEntry constructor group should be a None when contents empty")
        self.assertFalse(entry2.tag_dict, "SummaryEntry should not have a tag dictionary when contents empty")

        entry3 = SummaryEntry("NoSchema",  HedString(self.str1))
        self.assertIsInstance(entry3, SummaryEntry,
                              "SummaryEntry constructor should create an object when schema is None")
        self.assertEqual(entry3.name, "NoSchema",
                         "SummaryEntry constructor should have the right name when schema is None")
        self.assertTrue(entry3.group, "SummaryEntry constructor group should be non-empty when schema is None")
        self.assertTrue(entry3.tag_dict, "SummaryEntry should have a tag dictionary when schema is None")
        self.assertFalse('Description' in entry3.tag_dict, "SummaryEntry should not parse values when schema is None")

    def test_extract_anchored_group(self):
        hed1 = HedString(self.str1)
        hed1.convert_to_canonical_forms(self.schema)
        no_entry = SummaryEntry.extract_anchored_group(hed1)
        self.assertFalse(no_entry, "extract_anchored_group should return None if no anchored group")

        hed2 = HedString(self.str_with_def)
        hed2.convert_to_canonical_forms(self.schema)
        groups2 = hed2.groups()
        definition_entry = SummaryEntry.extract_anchored_group(groups2[0])
        self.assertIsInstance(definition_entry, SummaryEntry,
                              "extract_anchored_group should return a SummaryEntry if anchored group")

        hed3 = HedString(self.str_with_def_expand)
        hed3.convert_to_canonical_forms(self.schema)
        groups3 = hed3.groups()
        def_expand_entry = SummaryEntry.extract_anchored_group(groups3[0], "def-expand")
        self.assertIsInstance(def_expand_entry, SummaryEntry,
                              "extract_anchored_group should return a SummaryEntry if definition not the anchor")

        def_expand_entry_case = SummaryEntry.extract_anchored_group(groups3[0], "Def-expand")
        self.assertIsInstance(def_expand_entry_case, SummaryEntry,
                              "extract_anchored_group should return a SummaryEntry anchor and is not case sensitive")

    def test_extract_anchored_groups(self):
        hed1 = HedString(self.str1)
        hed1.convert_to_canonical_forms(self.schema)
        entry_dict1 = {}
        hed1_tags = SummaryEntry.separate_anchored_groups(hed1, entry_dict1, anchor_name="definition")
        self.assertIsInstance(hed1_tags, list, "separate_anchored_groups returns a list when no anchor")
        self.assertEqual(len(hed1_tags), 1, "separate_anchored_groups returns a list of right length when no anchor")
        self.assertFalse(entry_dict1, "separate_anchored_groups returns an empty dictionary if no anchored groups")

        hed2 = HedString(self.str2)
        hed2.convert_to_canonical_forms(self.schema)
        entry_dict2 = {}
        hed2_tags = SummaryEntry.separate_anchored_groups(hed2, entry_dict2, anchor_name="definition")
        self.assertIsInstance(hed2_tags, list, "separate_anchored_groups returns a list when no anchor and tags")
        self.assertEqual(len(hed2_tags), 5,
                         "separate_anchored_groups returns a list of right length when no anchor and tags")

        hed3 = HedString(self.str_with_defs)
        hed3.convert_to_canonical_forms(self.schema)
        entry_dict3 = {}
        hed3_tags = SummaryEntry.separate_anchored_groups(hed3, entry_dict3, anchor_name="definition")
        self.assertIsInstance(hed3_tags, list,
                              "separate_anchored_groups returns a list when multiple definitions no tags")
        self.assertEqual(len(hed3_tags), 0,
                         "separate_anchored_groups returns a list of right length when no anchor and tags")
        self.assertEqual(len(entry_dict3), 3,
                         "separate_anchored_groups returns a anchor dictionary of right length when definitions")


if __name__ == '__main__':
    unittest.main()
