import os
import unittest
from hed.models import DefinitionDict

from hed import load_schema_version, HedString
from hed.schema import from_string
from hed.validator import HedValidator
from hed import Sidecar
import io
import json
from hed import HedFileError
from hed.errors import ErrorHandler, get_printable_issue_string
import shutil
from hed import schema
from hed.schema import hed_cache


# To be removed eventually once all errors are being verified.
known_errors = [
    'SIDECAR_INVALID',
    'CHARACTER_INVALID',
    'COMMA_MISSING',
    "DEF_EXPAND_INVALID",
    "DEF_INVALID",
    "DEFINITION_INVALID",
    "NODE_NAME_EMPTY",
    "ONSET_OFFSET_INSET_ERROR",
    "PARENTHESES_MISMATCH",
    "PLACEHOLDER_INVALID",
    "REQUIRED_TAG_MISSING",
    "SIDECAR_INVALID",
    "SIDECAR_KEY_MISSING",
    "STYLE_WARNING",
    "TAG_EMPTY",
    "TAG_EXPRESSION_REPEATED",
    "TAG_EXTENDED",
    "TAG_EXTENSION_INVALID",
    "TAG_GROUP_ERROR",
    "TAG_INVALID",
    "TAG_NOT_UNIQUE",
    "TAG_NAMESPACE_PREFIX_INVALID",
    "TAG_REQUIRES_CHILD",
    "TILDES_UNSUPPORTED",
    "UNITS_INVALID",
    "UNITS_MISSING",
    "VALUE_INVALID",

    "SIDECAR_BRACES_INVALID",
    "SCHEMA_LIBRARY_INVALID",
]

skip_tests = {
    "VERSION_DEPRECATED": "Not applicable",
    "onset-offset-inset-error-duplicated-onset-or-offset": "TBD how we implement this",
    "tag-extension-invalid-bad-node-name": "Part of character invalid checking/didn't get to it yet",
}


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 'hed-specification/tests/json_tests'))
        cls.test_files = [os.path.join(test_dir, f) for f in os.listdir(test_dir)
                          if os.path.isfile(os.path.join(test_dir, f))]
        cls.fail_count = []
        cls.default_sidecar = Sidecar(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_sidecar.json')))

        # this is just to make sure 8.2.0 is in the cache(as you can't find it online yet) and could be cleaned up
        cls.hed_cache_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_errors_cache/')
        base_schema_dir = '../tests/data/schema_tests/merge_tests/'
        cls.saved_cache_folder = hed_cache.HED_CACHE_DIRECTORY
        schema.set_cache_directory(cls.hed_cache_dir)
        cls.full_base_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), base_schema_dir)
        cls.source_schema_path = os.path.join(cls.full_base_folder, "HED8.2.0.xml")
        cls.cache_folder = hed_cache.get_cache_directory()
        cls.schema_path_in_cache = os.path.join(cls.cache_folder, "HED8.2.0.xml")
        shutil.copy(cls.source_schema_path, cls.schema_path_in_cache)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.hed_cache_dir)
        schema.set_cache_directory(cls.saved_cache_folder)

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
                print(f"Skipping {error_code} test because: {skip_tests[error_code]}")
                continue
            name = info.get('name', '')
            if name in skip_tests:
                print(f"Skipping {name} test because: {skip_tests[name]}")
                continue

            description = info['description']
            schema = info['schema']
            check_for_warnings = info.get("warning", False)
            error_handler = ErrorHandler(check_for_warnings)
            if schema:
                schema = load_schema_version(schema)
                definitions = info['definitions']
                def_dict = DefinitionDict(definitions, schema)
                self.assertFalse(def_dict.issues)
            else:
                def_dict = DefinitionDict()
            for section_name, section in info["tests"].items():
                if section_name == "string_tests":
                    self._run_single_string_test(section, schema, def_dict, error_code, description, name, error_handler)
                if section_name == "sidecar_tests":
                    self._run_single_sidecar_test(section, schema, def_dict, error_code, description, name, error_handler)
                if section_name == "event_tests":
                    self._run_single_events_test(section, schema, def_dict, error_code, description, name, error_handler)
                if section_name == "combo_tests":
                    self._run_single_combo_test(section, schema, def_dict, error_code, description, name, error_handler)
                if section_name == "schema_tests":
                    self._run_single_schema_test(section, error_code, description, name, error_handler)

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

    def _run_single_schema_test(self, info, error_code, description,name, error_handler):
        for result, tests in info.items():
            for test in tests:
                schema_string = "\n".join(test)
                try:
                    loaded_schema = from_string(schema_string, file_type=".mediawiki")
                    issues = loaded_schema.check_compliance()
                except HedFileError as e:
                    issues = e.issues
                self.report_result(result, issues, error_code, description, name, test, "schema_tests")

    def test_errors(self):
        for test_file in self.test_files:
            self.run_single_test(test_file)
        print(f"{len(self.fail_count)} tests got an unexpected result")
        print("\n".join(self.fail_count))
        self.assertEqual(len(self.fail_count), 0)

if __name__ == '__main__':
    unittest.main()

