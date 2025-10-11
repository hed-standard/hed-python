import os
import unittest
import urllib.error

from hed.models import DefinitionDict

from hed import load_schema_version, HedString
from hed.schema import from_string
from hed.validator import HedValidator
from hed import Sidecar
import io
import json
from hed import HedFileError
from hed.errors import ErrorHandler, get_printable_issue_string, SchemaWarnings


skip_tests = {
    # "tag-extension-invalid-bad-node-name": "Part of character invalid checking/didn't get to it yet",
    # "curly-braces-has-no-hed": "Need to fix issue #1006",
    # "character-invalid-non-printing appears": "Need to recheck how this is verified for textClass",
    "invalid-character-name-value-class-deprecated": "Removing support for 8.2.0 or earlier name classes"
}

class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 'hed-specification/tests/json_tests'))
        cls.test_dir = test_dir
        cls.fail_count = []

        # Check if the required directory exists
        if not os.path.exists(test_dir):
            cls.test_files = []
            cls.skip_tests = True
            # Only print warning if not in CI environment to avoid interference
            if not os.environ.get('GITHUB_ACTIONS'):
                print(f"WARNING: Test directory not found: {test_dir}")
                print("To run spec error tests, copy hed-specification repository content to spec_tests/hed-specification/")
        else:
            cls.test_files = [os.path.join(test_dir, f) for f in os.listdir(test_dir)
                              if os.path.isfile(os.path.join(test_dir, f))]
            cls.skip_tests = False

        cls.default_sidecar = Sidecar(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    'test_sidecar.json')))

    @classmethod
    def tearDownClass(cls):
        pass

    def run_single_test(self, test_file, test_name=None, test_type=None):
        with open(test_file, "r") as fp:
            test_info = json.load(fp)
        for info in test_info:
            error_code = info['error_code']
            all_codes = [error_code] + info.get('alt_codes', [])
            if error_code in skip_tests:
                print(f"Skipping {error_code} test because: {skip_tests[error_code]}")
                continue
            name = info.get('name', '')
            if name in skip_tests:
                print(f"Skipping {name} test because: {skip_tests[name]}")
                continue
            if test_name is not None and name != test_name:
                print(f"Skipping {name} test because it is not the one specified")
                continue
            description = info['description']
            schema = info['schema']
            check_for_warnings = info.get("warning", False)
            error_handler = ErrorHandler(check_for_warnings)
            if schema:
                try:
                    schema = load_schema_version(schema)
                except HedFileError as e:
                    issues = e.issues
                    if not issues:
                        issues += [{"code": e.code,
                                    "message": e.message}]
                    self.report_result("fails", issues, error_code, all_codes, description, name, "dummy", "Schema")
                    # self.fail_count.append(name)
                    continue
                definitions = info.get('definitions', None)
                def_dict = DefinitionDict(definitions, schema)
                self.assertFalse(def_dict.issues)

            else:
                def_dict = DefinitionDict()
            for section_name, section in info["tests"].items():
                if test_type is not None and test_type != section_name:
                    continue
                if section_name == "string_tests":
                    self._run_single_string_test(section, schema, def_dict, error_code, all_codes,
                                                 description, name, error_handler)
                if section_name == "sidecar_tests":
                    self._run_single_sidecar_test(section, schema, def_dict, error_code, all_codes,
                                                  description, name, error_handler)
                if section_name == "event_tests":
                    self._run_single_events_test(section, schema, def_dict, error_code, all_codes,
                                                 description, name, error_handler)
                if section_name == "combo_tests":
                    self._run_single_combo_test(section, schema, def_dict, error_code, all_codes,
                                                description, name, error_handler)
                if section_name == "schema_tests":
                    self._run_single_schema_test(section, error_code, all_codes, description, name, error_handler)

    def report_result(self, expected_result, issues, error_code, all_codes, description, name, test, test_type):
        # Filter out pre-release warnings, we don't care about them.
        issues = [issue for issue in issues if issue["code"] != SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED]
        if expected_result == "fails":
            if not issues:
                print(f"{error_code}: {description}")
                print(f"Passed '{test_type}' (which should fail) '{name}': {test}")
                print(get_printable_issue_string(issues))
                self.fail_count.append(name)
            else:
                if any(issue['code'] in all_codes for issue in issues):
                    return
                print(f"{error_code}: {description} all codes:[{str(all_codes)}]")
                print(f"Failed '{test_type}' (unexpected errors found) '{name}': {test}")
                print(get_printable_issue_string(issues))
                self.fail_count.append(name)
        else:
            if issues:
                print(f"{error_code}: {description}")
                print(f"Failed '{test_type}' test '{name}': {test}")
                print(get_printable_issue_string(issues))
                self.fail_count.append(name)

    def _run_single_string_test(self, info, schema, def_dict, error_code, all_codes, description, name, error_handler):
        string_validator = HedValidator(hed_schema=schema, def_dicts=def_dict)
        for result, tests in info.items():
            for test in tests:
                test_string = HedString(test, schema)

                issues = string_validator.run_basic_checks(test_string, False)
                issues += string_validator.run_full_string_checks(test_string)
                error_handler.add_context_and_filter(issues)
                self.report_result(result, issues, error_code, all_codes, description, name, test, "string_test")

    def _run_single_sidecar_test(self, info, schema, def_dict, error_code, all_codes, description, name, error_handler):
        for result, tests in info.items():
            for test in tests:
                buffer = io.BytesIO(json.dumps(test).encode("utf-8"))
                sidecar = Sidecar(buffer)
                issues = sidecar.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                self.report_result(result, issues, error_code, all_codes, description, name, test, "sidecar_test")

    def _run_single_events_test(self, info, schema, def_dict, error_code, all_codes, description, name, error_handler):
        from hed import TabularInput
        for result, tests in info.items():
            for test in tests:
                string = ""
                for row in test:
                    if not isinstance(row, list):
                        print(f"Improper grouping in test: {error_code}:{name}")
                        print("This is probably a missing set of square brackets.")
                        break
                    string += "\t".join(str(x) for x in row) + "\n"

                if not string:
                    print(F"Invalid blank events found in test: {error_code}:{name}")
                    continue
                file_obj = io.BytesIO(string.encode("utf-8"))

                file = TabularInput(file_obj, sidecar=self.default_sidecar)
                issues = file.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                self.report_result(result, issues, error_code, all_codes, description, name, test, "events_test")

    def _run_single_combo_test(self, info, schema, def_dict, error_code, all_codes, description, name, error_handler):
        from hed import TabularInput
        for result, tests in info.items():
            for test in tests:
                sidecar_test = test['sidecar']
                default_dict = self.default_sidecar.loaded_dict
                for key, value in default_dict.items():
                    sidecar_test.setdefault(key, value)

                buffer = io.BytesIO(json.dumps(sidecar_test).encode("utf-8"))
                sidecar = Sidecar(buffer)
                issues = sidecar.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                string = ""
                try:
                    for row in test['events']:
                        if not isinstance(row, list):
                            print(f"Improper grouping in test: {error_code}:{name}")
                            print(f"Improper data for test {name}: {test}")
                            print("This is probably a missing set of square brackets.")
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
                    print("This is probably a missing set of square brackets.")
                    continue
                issues += file.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                self.report_result(result, issues, error_code, all_codes, description, name, test, "combo_tests")

    def _run_single_schema_test(self, info, error_code, all_codes, description, name, error_handler):
        for result, tests in info.items():
            for test in tests:
                schema_string = "\n".join(test)
                issues = []
                try:
                    loaded_schema = from_string(schema_string, schema_format=".mediawiki")
                    issues = loaded_schema.check_compliance()
                except HedFileError as e:
                    issues = e.issues
                    if not issues:
                        issues += [{"code": e.code,
                                   "message": e.message}]
                except urllib.error.HTTPError:
                    issues += [{"code": "Http_error",
                                "message": "HTTP error in testing, probably due to rate limiting for local testing."}]
                self.report_result(result, issues, error_code, all_codes, description, name, test, "schema_tests")

    def test_errors(self):
        if hasattr(self, 'skip_tests') and self.skip_tests:
            self.skipTest("hed-specification directory not found. Copy submodule content to run this test.")

        count = 1
        for test_file in self.test_files:
            self.run_single_test(test_file)
            count = count + 1

        print(f"{len(self.fail_count)} tests got an unexpected result")
        print("\n".join(self.fail_count))
        self.assertEqual(len(self.fail_count), 0)

    # def test_debug(self):
    #     test_file = os.path.realpath('./temp7.json')
    #     test_name = None
    #     test_type = None
    #     self.run_single_test(test_file, test_name, test_type)


if __name__ == '__main__':
    unittest.main()
