import io
import json
import os
import unittest

from hed import schema
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ErrorContext, SidecarErrors
from hed.models import Sidecar
from hed.validator.sidecar_validator import SidecarValidator


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")
        cls.base_data_dir = base_data_dir
        cls.hed_schema = schema.load_schema_version("8.0.0")
        cls._refs_json_filename = os.path.join(base_data_dir, "sidecar_tests/basic_refs_test.json")
        cls._bad_refs_json_filename = os.path.join(base_data_dir, "sidecar_tests/bad_refs_test2.json")
        cls._malformed_refs_json_filename = os.path.join(base_data_dir, "sidecar_tests/malformed_refs_test.json")
        cls._multiple_category_refs = os.path.join(base_data_dir, "sidecar_tests/multiple_category_refs.json")

    def test_basic_refs(self):
        sidecar = Sidecar(self._refs_json_filename)
        issues = sidecar.validate(self.hed_schema)

        self.assertEqual(len(issues), 0)
        refs = sidecar.get_column_refs()
        self.assertEqual(len(refs), 2)

    def test_multicategory_refs(self):
        sidecar = Sidecar(self._multiple_category_refs)
        issues = sidecar.validate(self.hed_schema)

        # 3 issues are expected for repeated tags from stacking lines
        self.assertEqual(len(issues), 2)
        refs = sidecar.get_column_refs()
        self.assertEqual(len(refs), 2)

    def test_bad_refs(self):
        sidecar = Sidecar(self._bad_refs_json_filename)
        issues = sidecar.validate(self.hed_schema)

        self.assertEqual(len(issues), 2)

    def test_malformed_refs(self):
        sidecar = Sidecar(self._malformed_refs_json_filename)
        issues = sidecar.validate(self.hed_schema)

        self.assertEqual(len(issues), 4)

    def test_padded_keys(self):
        # A padded top-level key is SIDECAR_INVALID with or without a "HED" entry; an inner blank is fine.
        sidecar = Sidecar(
            io.StringIO(
                json.dumps(
                    {
                        "trial ": {"HED": {"go": "Event"}},
                        "\tresponse": {"Description": "No HED here."},
                        "trial type": {"HED": {"go": "Event"}},
                    }
                )
            )
        )
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual([issue["code"] for issue in issues], ["SIDECAR_INVALID"] * 2)
        self.assertEqual([issue[ErrorContext.SIDECAR_COLUMN_NAME] for issue in issues], ["trial ", "\tresponse"])
        self.assertIn("'trial '", issues[0]["message"])

    def test_unpadded_keys_pass(self):
        sidecar = Sidecar(io.StringIO(json.dumps({"trial type": {"HED": {"go": "Event"}}, "trial\u00a0": {}})))
        self.assertEqual(sidecar.validate(self.hed_schema), [])

    def test_padded_categorical_keys(self):
        # A key under HED in a categorical entry with leading or trailing whitespace is SIDECAR_INVALID.
        for key in ("go ", " go", "go\t"):
            with self.subTest(key=key):
                sidecar = Sidecar(io.StringIO(json.dumps({"trial": {"HED": {key: "Event", "stop": "Event"}}})))
                issues = sidecar.validate(self.hed_schema)
                self.assertEqual([issue["code"] for issue in issues], ["SIDECAR_INVALID"])
                self.assertEqual(issues[0][ErrorContext.SIDECAR_KEY_NAME], key)
                self.assertIn(repr(key), issues[0]["message"])

    def test_unpadded_categorical_keys_pass(self):
        # An inner blank and a no-break space are not padding; Levels keys are not checked.
        data = {
            "trial": {"HED": {"go now": "Event", "stop\u00a0": "Event"}},
            "response": {"Levels": {"left ": "Left hand"}, "HED": {"left": "Event"}},
        }
        self.assertEqual(Sidecar(io.StringIO(json.dumps(data))).validate(self.hed_schema), [])

    def test_malformed_braces(self):
        hed_strings = [
            "column2}, Event, Action",
            "{column, Event, Action",
            "This is a {malformed {input string}} with extra {opening brackets",
            "{Event{Action}}",
            "Event, Action}",
        ]
        error_counts = [1, 1, 3, 2, 1]

        for string, error_count in zip(hed_strings, error_counts, strict=False):
            issues = SidecarValidator._find_non_matching_braces(string)

            self.assertEqual(len(issues), error_count)

    def test_bad_structure_na(self):
        sidecar_with_na_json = """
{
  "column3": {
       "HED": {
         "cat1": "Event",
         "n/a": "Description/invalid category name"
       }
   }
}
"""
        sidecar = Sidecar(io.StringIO(sidecar_with_na_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 1)

    def test_bad_structure_HED_in_ignored(self):
        sidecar_with_na_json = """
    {
      "column3": {
           "other": {
             "HED": "Event",
             "n/a": "Description/invalid category name"
           }
       },
       "HED": {
       },
       "OtherBad": {
           "subbad": ["thing1", "HED", "Other"]
       }
    }
    """
        sidecar = Sidecar(io.StringIO(sidecar_with_na_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 2)

    def test_bad_pound_signs(self):
        sidecar_json = """
    {
      "columnCat": {
           "HED": {
             "cat1": "Event",
             "cat2": "Weight/# g"
           }
       },
       "columnVal": {
            "HED": "Description/Invalid"
       },
       "columnVal2": {
            "HED": "Description/#, Weight/# g"
       }
    }
    """
        sidecar = Sidecar(io.StringIO(sidecar_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 3)

    def test_missing_hed(self):
        sidecar_with_hed_missing = """
        {
            "event_code": {
                "HED": {
                    "face": "Statistical-accuracy/0.677, {response}"
                }
            },
            "response": "Label/#",
            "other": "Description"
        }
    """
        sidecar = Sidecar(io.StringIO(sidecar_with_hed_missing))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), 1)

    def test_invalid_list(self):
        sidecar_json = """
        {
          "columnInvalidList": {
               "HED": ["This", "should", "be", "a", "dictionary", "not", "a", "list"]
           }
        }
        """
        self.run_test(sidecar_json, expected_number_of_issues=1)

    def test_invalid_number(self):
        sidecar_json = """
        {
          "columnInvalidNumber": {
               "HED": 12345
           }
        }
        """
        self.run_test(sidecar_json, expected_number_of_issues=1)

    def test_invalid_boolean(self):
        sidecar_json = """
        {
          "columnInvalidBoolean": {
               "HED": true
           }
        }
        """
        self.run_test(sidecar_json, expected_number_of_issues=1)

    def test_mixed_category(self):
        sidecar_json = """
        {
          "columnMixedCategory": {
               "HED": {
                 "cat1": "Event",
                 "cat2": ["Invalid", "data", "type"]
               }
           }
        }
        """
        self.run_test(sidecar_json, expected_number_of_issues=1)

    def run_test(self, sidecar_json, expected_number_of_issues):
        sidecar = Sidecar(io.StringIO(sidecar_json))
        issues = sidecar.validate(self.hed_schema)
        self.assertEqual(len(issues), expected_number_of_issues)

    def test_validate_without_name_adds_no_filename_context(self):
        """With no name, the validator adds no FILE_NAME context and leaves the caller's context intact."""
        sidecar = Sidecar(io.StringIO('{"event_code": {"HED": {"a": "Event", "b": "InvalidTagXYZ"}}}'))
        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.TABLE_NAME, "trials")

        issues = SidecarValidator(self.hed_schema).validate(sidecar, error_handler=error_handler)

        self.assertGreater(len(issues), 0)
        for issue in issues:
            self.assertNotIn("ec_filename", issue)
            self.assertEqual(issue.get("ec_table_name"), "trials")
        self.assertEqual(error_handler.error_context, [(ErrorContext.TABLE_NAME, "trials")])

    def test_validate_with_name_keeps_filename_context(self):
        """With a name, every issue carries it as ec_filename, as before."""
        sidecar = Sidecar(io.StringIO('{"event_code": {"HED": {"a": "Event", "b": "InvalidTagXYZ"}}}'))
        error_handler = ErrorHandler()

        issues = SidecarValidator(self.hed_schema).validate(sidecar, name="events.json", error_handler=error_handler)

        self.assertGreater(len(issues), 0)
        self.assertTrue(all(issue.get("ec_filename") == "events.json" for issue in issues))
        self.assertEqual(error_handler.error_context, [])

    def test_validate_pops_context_on_structure_error(self):
        """The early return on a reference error must not leave the FILE_NAME context on the stack."""
        sidecar = Sidecar(io.StringIO('{"event_code": {"HED": {"a": "Event, {missing_column}"}}}'))
        error_handler = ErrorHandler()

        issues = SidecarValidator(self.hed_schema).validate(sidecar, name="events.json", error_handler=error_handler)

        self.assertIn(SidecarErrors.SIDECAR_BRACES_INVALID, {issue["code"] for issue in issues})
        self.assertEqual(error_handler.error_context, [])
