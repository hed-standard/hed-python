import unittest
import os

from hed.util.def_mapper import DefinitionMapper
from hed.util.hed_schema import HedSchema
from hed.util.def_dict import DefDict

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "HED8.0.0-alpha.1.xml")
        cls.hed_schema = HedSchema(hed_xml_file)
        cls.base_def_mapper = DefinitionMapper(hed_schema=cls.hed_schema)
        cls.def_contents_string = "(Item/TestDef1, Item/TestDef2)"
        cls.basic_def_string = f"(Definition/TestDef, Organizational/TestOrg, {cls.def_contents_string})"
        cls.label_def_string = f"Label-def/TestDef"
        cls.expanded_def_string = f"(Label-exp/TestDef, Organizational/TestOrg, {cls.def_contents_string})"
        cls.basic_hed_string = "Item/BasicTestTag1, Item/BasicTestTag2"
        cls.basic_hed_string_with_def = f"Item/BasicTestTag1, Item/BasicTestTag2, {cls.label_def_string}"

    def test_check_for_definitions(self):
        def_dict = DefDict(hed_schema=self.hed_schema)
        original_def_count = len(def_dict._defs)
        def_dict.check_for_definitions(self.basic_def_string)
        new_def_count = len(def_dict._defs)
        self.assertGreater(new_def_count, original_def_count)

    def test__check_tag_starts_with(self):
        possible_tag_list = ["definition", "informational/definition", "attribute/informational/definition"]

        test_tags = ["Definition/TempTestDef", "Informational/Definition/TempTestDef",
                     "Attribute/Informational/Definition/TempTestDef"]

        for tag in test_tags:
            result = DefinitionMapper._check_tag_starts_with(tag, possible_tag_list)
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()





