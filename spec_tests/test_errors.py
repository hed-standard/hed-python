import os
import unittest
from hed.models import DefinitionDict

from hed import load_schema_version, HedString
from hed.validator import HedValidator
from hed import Sidecar
import io
import json
from hed import HedFileError
from hed.errors import ErrorHandler, get_printable_issue_string


known_errors = [
    'SIDECAR_INVALID',
    'CHARACTER_INVALID',
    'COMMA_MISSING',
    "DEF_EXPAND_INVALID",
    "DEF_INVALID",
]

skip_tests = ["VERSION_DEPRECATED", "CHARACTER_INVALID", "STYLE_WARNING"]


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 'hed-specification/docs/source/_static/data/error_tests'))
        cls.test_files = [os.path.join(test_dir, f) for f in os.listdir(test_dir)
                          if os.path.isfile(os.path.join(test_dir, f))]
        cls.fail_count = []
        cls.default_sidecar = Sidecar(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_sidecar.json')))

    def run_single_test(self, test_file):
        with open(test_file, "r") as fp:
            test_info = json.load(fp)
        for info in test_info:
            error_code = info['error_code']
            verify_code = False
            if error_code in known_errors:
                verify_code = True

            # To be deprecated once we add this to all tests
            self._verify_code = verify_code
            if error_code in skip_tests:
                print(f"Skipping {error_code} test")
                continue
            name = info.get('name', '')
            description = info['description']
            schema = info['schema']
            check_for_warnings = info.get("warning", False)
            error_handler = ErrorHandler(check_for_warnings)
            if schema:
                schema = load_schema_version(schema)
            else:
                raise ValueError("Tests always require a schema now")
            definitions = info['definitions']
            def_dict = DefinitionDict(definitions, schema)
            self.assertFalse(def_dict.issues)
            for section_name, section in info["tests"].items():
                if section_name == "string_tests":
                    self._run_single_string_test(section, schema, def_dict, error_code, description, name, error_handler)
                if section_name == "sidecar_tests":
                    self._run_single_sidecar_test(section, schema, def_dict, error_code, description, name, error_handler)
                if section_name == "event_tests":
                    self._run_single_events_test(section, schema, def_dict, error_code, description, name, error_handler)
                if section_name == "combo_tests":
                    self._run_single_combo_test(section, schema, def_dict, error_code, description, name, error_handler)

    def report_result(self, expected_result, issues, error_code, description, name, test, test_type):
        if expected_result == "fails":
            if not issues:
                print(f"{error_code}: {description}")
                print(f"Passed '{test_type}' (which should fail) '{name}': {test}")
                print(get_printable_issue_string(issues))
                self.fail_count.append(name)
            elif self._verify_code:
                if any(issue['code'] == error_code for issue in issues):
                    return
                print(f"{error_code}: {description}")
                print(f"Failed '{test_type}' (unexpected errors found) '{name}': {test}")
                print(get_printable_issue_string(issues))
                self.fail_count.append(name)
        else:
            if issues:
                print(f"{error_code}: {description}")
                print(f"Failed '{test_type}' test '{name}': {test}")
                print(get_printable_issue_string(issues))
                self.fail_count.append(name)

    def _run_single_string_test(self, info, schema, def_dict, error_code, description, name, error_handler):
        string_validator = HedValidator(hed_schema=schema, def_dicts=def_dict, run_full_onset_checks=False)
        for result, tests in info.items():
            for test in tests:
                test_string = HedString(test, schema)

                issues = string_validator.run_basic_checks(test_string, False)
                issues += string_validator.run_full_string_checks(test_string)
                error_handler.add_context_and_filter(issues)
                self.report_result(result, issues, error_code, description, name, test, "string_test")

    def _run_single_sidecar_test(self, info, schema, def_dict, error_code, description, name, error_handler):
        for result, tests in info.items():
            for test in tests:
                buffer = io.BytesIO(json.dumps(test).encode("utf-8"))
                sidecar = Sidecar(buffer)
                issues = sidecar.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                self.report_result(result, issues, error_code, description, name, test, "sidecar_test")

    def _run_single_events_test(self, info, schema, def_dict, error_code, description,name, error_handler):
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
                issues = file.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                self.report_result(result, issues, error_code, description, name, test, "events_test")

    def _run_single_combo_test(self, info, schema, def_dict, error_code, description,name, error_handler):
        from hed import TabularInput
        for result, tests in info.items():
            for test in tests:
                buffer = io.BytesIO(json.dumps(test['sidecar']).encode("utf-8"))
                sidecar = Sidecar(buffer)
                sidecar.loaded_dict.update(self.default_sidecar.loaded_dict)
                issues = sidecar.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                string = ""
                try:
                    for row in test['events']:
                        if not isinstance(row, list):
                            print(f"Improper grouping in test: {error_code}:{name}")
                            print(f"Improper data for test {name}: {test}")
                            print(f"This is probably a missing set of square brackets.")
                            break
                        string += "\t".join(str(x) for x in row) + "\n"

                    if not string:
                        print(F"Invalid blank events found in test: {error_code}:{name}")
                        continue
                    file_obj = io.BytesIO(string.encode("utf-8"))

                    file = TabularInput(file_obj, sidecar=sidecar)
                except HedFileError:
                    print(f"{error_code}: {description}")
                    print(f"Improper data for test {name}: {test}")
                    print(f"This is probably a missing set of square brackets.")
                    continue
                issues += file.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                self.report_result(result, issues, error_code, description, name, test, "combo_tests")

    def test_errors(self):
        for test_file in self.test_files:
            self.run_single_test(test_file)
        print(f"{len(self.fail_count)} tests got an unexpected result")
        print("\n".join(self.fail_count))
        self.assertEqual(len(self.fail_count), 0)

if __name__ == '__main__':
    unittest.main()

