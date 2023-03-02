import os
import json
import unittest
from hed.models import DefinitionDict, DefMapper, OnsetMapper
from hed.models.hed_ops import apply_ops
from hed import load_schema_version
from hed import HedValidator


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 '../../hed-specification/docs/source/_static/data/error_tests'))
        cls.test_files = [os.path.join(test_dir, f) for f in os.listdir(test_dir)
                          if os.path.isfile(os.path.join(test_dir, f))]
        cls.fail_count = 0

    def run_single_test(self, test_file):
        with open(test_file, "r") as fp:
            test_info = json.load(fp)
        for info in test_info:
            error_code = info['error_code']
            if error_code == "VERSION_DEPRECATED":
                print("Skipping VERSION_DEPRECATED test")
                continue
            description = info['description']
            schema = info['schema']
            if schema:
                schema = load_schema_version(schema)
            else:
                schema = None
            definitions = info['definitions']
            def_dict = DefinitionDict()
            _, issues = apply_ops(definitions, [schema, def_dict])
            self.assertFalse(issues)
            validator = HedValidator(schema)
            def_mapper = DefMapper(def_dict)
            onset_mapper = OnsetMapper(def_mapper)
            for section_name in info["tests"]:
                if section_name == "string_tests":
                    for result, tests in info["tests"]["string_tests"].items():
                        for test in tests:
                            modified_test, issues = apply_ops(test, [validator, def_mapper, onset_mapper], check_for_warnings=True, expand_defs=True)
                            if modified_test and modified_test != test:
                                _, def_expand_issues = apply_ops(modified_test, validator, check_for_warnings=True)
                                issues += def_expand_issues
                            if result == "fails":
                                if not issues:
                                    print(f"{error_code}: {description}")
                                    print(f"Passed this test(that should fail): {test}")
                                    print(issues)
                                    self.fail_count += 1
                            else:
                                if issues:
                                    print(f"{error_code}: {description}")
                                    print(f"Failed this test: {test}")
                                    print(issues)
                                    self.fail_count += 1



    def test_summary(self):
        for test_file in self.test_files:
            self.run_single_test(test_file)
        self.assertEqual(self.fail_count, 0)

if __name__ == '__main__':
    unittest.main()
