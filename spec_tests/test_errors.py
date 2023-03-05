import os
import json
import unittest
from hed.models import DefinitionDict, DefMapper, OnsetMapper
from hed.models.hed_ops import apply_ops
from hed import load_schema_version
from hed import HedValidator
from hed import Sidecar
import io
import json


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 'hed-specification/docs/source/_static/data/error_tests'))
        cls.test_files = [os.path.join(test_dir, f) for f in os.listdir(test_dir)
                          if os.path.isfile(os.path.join(test_dir, f))]
        cls.fail_count = 0
        cls.default_sidecar = Sidecar(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_sidecar.json')))


    def run_single_test(self, test_file):
        with open(test_file, "r") as fp:
            test_info = json.load(fp)
        for info in test_info:
            error_code = info['error_code']
            if error_code == "VERSION_DEPRECATED":
                print("Skipping VERSION_DEPRECATED test")
                continue
            name = info.get('name', '')
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
            for section_name, section in info["tests"].items():
                if section_name == "string_tests":
                    self._run_single_string_test(section, validator, def_mapper,
                                                 onset_mapper, error_code, description, name)
                elif section_name == "sidecar_tests":
                    self._run_single_sidecar_test(section, validator, def_mapper, onset_mapper, error_code, description,
                                                  name)
                elif section_name == "event_tests":
                    self._run_single_events_test(section, validator, def_mapper, onset_mapper, error_code, description,
                                                name)

    def _run_single_string_test(self, info, validator, def_mapper, onset_mapper, error_code, description,
                               name):
        for result, tests in info.items():
            for test in tests:
                modified_test, issues = apply_ops(test, [validator, def_mapper, onset_mapper], check_for_warnings=True,
                                                  expand_defs=True)
                if modified_test and modified_test != test:
                    _, def_expand_issues = apply_ops(modified_test, validator, check_for_warnings=True)
                    issues += def_expand_issues
                if result == "fails":
                    if not issues:
                        print(f"{error_code}: {description}")
                        print(f"Passed this test(that should fail) '{name}': {test}")
                        print(issues)
                        self.fail_count += 1
                else:
                    if issues:
                        print(f"{error_code}: {description}")
                        print(f"Failed this test {name}: {test}")
                        print(issues)

                        self.fail_count += 1

    def _run_single_sidecar_test(self, info, validator, def_mapper, onset_mapper, error_code, description,
                               name):
        for result, tests in info.items():

            for test in tests:
                # Well this is a disaster
                buffer = io.BytesIO(json.dumps(test).encode("utf-8"))
                sidecar = Sidecar(buffer)
                issues = sidecar.validate_entries([validator, def_mapper, onset_mapper], check_for_warnings=True)
                if result == "fails":
                    if not issues:
                        print(f"{error_code}: {description}")
                        print(f"Passed this test(that should fail) '{name}': {test}")
                        print(issues)
                        self.fail_count += 1
                else:
                    if issues:
                        print(f"{error_code}: {description}")
                        print(f"Failed this test {name}: {test}")
                        print(issues)

                        self.fail_count += 1

    def _run_single_events_test(self, info, validator, def_mapper, onset_mapper, error_code, description,
                               name):
        from hed import TabularInput
        for result, tests in info.items():

            for test in tests:
                string = ""
                for row in test:
                    if not isinstance(row, list):
                        print(f"Improper grouping in test: {error_code}:{name}")
                        print(f"This is probably a missing set of square brackets.")
                        break
                    string += "\t".join(str(x) for x in row) + "\n"

                if not string:
                    print(F"Invalid blank events found in test: {error_code}:{name}")
                    continue
                file_obj = io.BytesIO(string.encode("utf-8"))

                file = TabularInput(file_obj, sidecar=self.default_sidecar)
                issues = file.validate_file([validator, def_mapper, onset_mapper], check_for_warnings=True)
                if result == "fails":
                    if not issues:
                        print(f"{error_code}: {description}")
                        print(f"Passed this test(that should fail) '{name}': {test}")
                        print(issues)
                        self.fail_count += 1
                else:
                    if issues:
                        print(f"{error_code}: {description}")
                        print(f"Failed this test {name}: {test}")
                        print(issues)

                        self.fail_count += 1

    def test_summary(self):
        for test_file in self.test_files:
            self.run_single_test(test_file)
        print(f"{self.fail_count} tests got an unexpected result")
        self.assertEqual(self.fail_count, 0)

if __name__ == '__main__':
    unittest.main()
