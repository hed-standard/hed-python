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
        test_dir = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "hed-specification/tests/json_tests")
        )
        cls.test_dir = test_dir
        cls.fail_count = []

        # Check if the required directory exists
        if not os.path.exists(test_dir):
            cls.test_files = []
            cls.skip_tests = True
            # Only print warning if not in CI environment to avoid interference
            if not os.environ.get("GITHUB_ACTIONS"):
                print(f"WARNING: Test directory not found: {test_dir}")
                print("To run spec error tests, copy hed-specification repository content to spec_tests/hed-specification/")
        else:
            # Get all .json files except backup files
            cls.test_files = [
                os.path.join(test_dir, f)
                for f in os.listdir(test_dir)
                if os.path.isfile(os.path.join(test_dir, f)) and f.endswith(".json") and not f.endswith(".backup")
            ]
            cls.skip_tests = False

        cls.default_sidecar = Sidecar(
            os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_sidecar.json"))
        )

    @classmethod
    def tearDownClass(cls):
        pass

    def run_single_test(self, test_file, test_name=None, test_type=None):
        with open(test_file, "r") as fp:
            test_info = json.load(fp)

        file_basename = os.path.basename(test_file)

        for info in test_info:
            error_code = info["error_code"]
            all_codes = [error_code] + info.get("alt_codes", [])
            if error_code in skip_tests:
                print(f"  ⊘ Skipping {error_code} test: {skip_tests[error_code]}")
                continue
            name = info.get("name", "")
            if name in skip_tests:
                print(f"  ⊘ Skipping '{name}' test: {skip_tests[name]}")
                continue
            if test_name is not None and name != test_name:
                continue

            description = info["description"]
            schema = info["schema"]
            check_for_warnings = info.get("warning", False)
            error_handler = ErrorHandler(check_for_warnings)

            if schema:
                try:
                    schema = load_schema_version(schema)
                except HedFileError as e:
                    issues = e.issues
                    if not issues:
                        issues += [{"code": e.code, "message": e.message}]
                    self.report_result("fails", issues, error_code, all_codes, description, name, "dummy", "Schema")
                    continue
                except Exception as e:
                    print(f"\n⚠️  Error loading schema for test '{name}' in {file_basename}")
                    print(f"   Schema: {schema}")
                    print(f"   Error: {str(e)}")
                    continue

                definitions = info.get("definitions", None)
                def_dict = DefinitionDict(definitions, schema)
                if def_dict.issues:
                    print(f"\n⚠️  Definition issues in test '{name}' in {file_basename}")
                    print(f"   Definitions: {definitions}")
                    print(f"   Issues: {get_printable_issue_string(def_dict.issues)}")
                self.assertFalse(def_dict.issues)

            else:
                def_dict = DefinitionDict()

            for section_name, section in info["tests"].items():
                if test_type is not None and test_type != section_name:
                    continue
                if section_name == "string_tests":
                    self._run_single_string_test(
                        section, schema, def_dict, error_code, all_codes, description, name, error_handler
                    )
                if section_name == "sidecar_tests":
                    self._run_single_sidecar_test(
                        section, schema, def_dict, error_code, all_codes, description, name, error_handler
                    )
                if section_name == "event_tests":
                    self._run_single_events_test(
                        section, schema, def_dict, error_code, all_codes, description, name, error_handler
                    )
                if section_name == "combo_tests":
                    self._run_single_combo_test(
                        section, schema, def_dict, error_code, all_codes, description, name, error_handler
                    )
                if section_name == "schema_tests":
                    self._run_single_schema_test(section, error_code, all_codes, description, name, error_handler)

    def report_result(self, expected_result, issues, error_code, all_codes, description, name, test, test_type):
        # Filter out pre-release warnings, we don't care about them.
        issues = [issue for issue in issues if issue["code"] != SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED]

        if expected_result == "fails":
            if not issues:
                # Test should have failed but passed - this is a problem
                print("\n" + "=" * 80)
                print(f"❌ TEST FAILURE: Test passed but should have failed")
                print("=" * 80)
                print(f"Error Code:    {error_code}")
                print(f"Test Name:     {name}")
                print(f"Test Type:     {test_type}")
                print(f"Description:   {description}")
                print(f"Expected Error Codes: {all_codes}")
                print(f"\nTest Data:\n{self._format_test_data(test)}")
                print(f"\nResult: Test produced NO errors (expected one of: {all_codes})")
                print("=" * 80 + "\n")
                self.fail_count.append(name)
            else:
                # Test failed as expected, check if it's the right error code
                if any(issue["code"] in all_codes for issue in issues):
                    return  # Correct error code found, test passes

                # Wrong error code
                print("\n" + "=" * 80)
                print(f"❌ TEST FAILURE: Wrong error code returned")
                print("=" * 80)
                print(f"Error Code:    {error_code}")
                print(f"Test Name:     {name}")
                print(f"Test Type:     {test_type}")
                print(f"Description:   {description}")
                print(f"Expected Error Codes: {all_codes}")
                print(f"\nTest Data:\n{self._format_test_data(test)}")
                print(f"\nActual Error Codes Found:")
                for issue in issues:
                    print(f"  - {issue['code']}")
                print(f"\nDetailed Issues:")
                print(get_printable_issue_string(issues))
                print("=" * 80 + "\n")
                self.fail_count.append(name)
        else:
            # Test should pass
            if issues:
                print("\n" + "=" * 80)
                print(f"❌ TEST FAILURE: Test failed but should have passed")
                print("=" * 80)
                print(f"Error Code:    {error_code}")
                print(f"Test Name:     {name}")
                print(f"Test Type:     {test_type}")
                print(f"Description:   {description}")
                print(f"\nTest Data:\n{self._format_test_data(test)}")
                print(f"\nUnexpected Issues Found:")
                print(get_printable_issue_string(issues))
                print("=" * 80 + "\n")
                self.fail_count.append(name)

    def _format_test_data(self, test):
        """Format test data for readable output"""
        if isinstance(test, str):
            return f"  {test}"
        elif isinstance(test, dict):
            return json.dumps(test, indent=2)
        elif isinstance(test, list):
            if len(test) > 0 and isinstance(test[0], str):
                # Schema test - format as multiline
                return "\n".join(f"  {line}" for line in test)
            else:
                # Event test or other list
                return json.dumps(test, indent=2)
        else:
            return str(test)

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
                    print(f"Invalid blank events found in test: {error_code}:{name}")
                    continue
                file_obj = io.BytesIO(string.encode("utf-8"))

                file = TabularInput(file_obj, sidecar=self.default_sidecar)
                issues = file.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                self.report_result(result, issues, error_code, all_codes, description, name, test, "events_test")

    def _run_single_combo_test(self, info, schema, def_dict, error_code, all_codes, description, name, error_handler):
        from hed import TabularInput

        for result, tests in info.items():
            for test in tests:
                sidecar_test = test["sidecar"]
                default_dict = self.default_sidecar.loaded_dict
                for key, value in default_dict.items():
                    sidecar_test.setdefault(key, value)

                buffer = io.BytesIO(json.dumps(sidecar_test).encode("utf-8"))
                sidecar = Sidecar(buffer)
                issues = sidecar.validate(hed_schema=schema, extra_def_dicts=def_dict, error_handler=error_handler)
                string = ""
                try:
                    for row in test["events"]:
                        if not isinstance(row, list):
                            print(f"Improper grouping in test: {error_code}:{name}")
                            print(f"Improper data for test {name}: {test}")
                            print("This is probably a missing set of square brackets.")
                            break
                        string += "\t".join(str(x) for x in row) + "\n"

                    if not string:
                        print(f"Invalid blank events found in test: {error_code}:{name}")
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
                        issues += [{"code": e.code, "message": e.message}]
                except urllib.error.HTTPError:
                    issues += [
                        {
                            "code": "Http_error",
                            "message": "HTTP error in testing, probably due to rate limiting for local testing.",
                        }
                    ]
                self.report_result(result, issues, error_code, all_codes, description, name, test, "schema_tests")

    def test_errors(self):
        if hasattr(self, "skip_tests") and self.skip_tests:
            self.skipTest("hed-specification directory not found. Copy submodule content to run this test.")

        print("\n" + "=" * 80)
        print("Running HED Specification Error Tests")
        print("=" * 80)

        count = 1
        for test_file in self.test_files:
            filename = os.path.basename(test_file)
            print(f"Processing {count}/{len(self.test_files)}: {filename}")
            self.run_single_test(test_file)
            count = count + 1

        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        if len(self.fail_count) == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ {len(self.fail_count)} test(s) failed:")
            for i, failed_test in enumerate(self.fail_count, 1):
                print(f"  {i}. {failed_test}")
        print("=" * 80 + "\n")

        self.assertEqual(len(self.fail_count), 0, f"\n{len(self.fail_count)} test(s) failed. See detailed output above.")

    # def test_debug(self):
    #     test_file = os.path.realpath('./temp7.json')
    #     test_name = None
    #     test_type = None
    #     self.run_single_test(test_file, test_name, test_type)


if __name__ == "__main__":
    unittest.main()
