import unittest
import os

from hed import schema


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = schema.load_schema_version("8.1.0")

    def test_validate_schema(self):
        schema_path_with_issues = "../data/schema_tests/HED8.0.0t.xml"
        schema_path_with_issues = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_path_with_issues)
        hed_schema = schema.load_schema(schema_path_with_issues)
        issues = hed_schema.check_compliance()
        self.assertTrue(isinstance(issues, list))
        self.assertTrue(len(issues) > 1)

    def test_validate_schema_deprecated(self):
        hed_schema = schema.load_schema_version("score_1.1.0")
        issues = hed_schema.check_compliance()
        self.assertTrue(isinstance(issues, list))
        self.assertTrue(len(issues) > 1)
