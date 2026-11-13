import io
import json
import os
import unittest

from hed import schema
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ErrorContext, SidecarErrors
from hed.models import Sidecar, TabularInput
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

        # Two combinations (go with go2, stop with go2) repeat Azure; the repeat is reported once.
        self.assertEqual(len(issues), 1)
        refs = sidecar.get_column_refs()
        self.assertEqual(len(refs), 2)

    def test_bad_refs(self):
        sidecar = Sidecar(self._bad_refs_json_filename)
        issues = sidecar.validate(self.hed_schema)

        self.assertEqual(len(issues), 2)

    def test_malformed_refs(self):
        sidecar = Sidecar(self._malformed_refs_json_filename)
        issues = sidecar.validate(self.hed_schema)

        # The {Property/...} reference is an unknown column (any character but a brace may name one), which
        # also makes column1 a reference column that column2 and column4 reference: 3 more issues.
        self.assertEqual(len(issues), 7)

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


class TestSidecarFalseNegatives(unittest.TestCase):
    """Sidecar errors that hedtools 1.3.0 did not report (HED 8.4.0)."""

    @classmethod
    def setUpClass(cls):
        cls.hed_schema = schema.load_schema_version("8.4.0")

    def codes(self, sidecar_dict):
        sidecar = Sidecar(io.StringIO(json.dumps(sidecar_dict)))
        return [issue["code"] for issue in sidecar.validate(self.hed_schema)]

    def test_brace_name_with_period_unknown(self):
        self.assertIn("SIDECAR_BRACES_INVALID", self.codes({"cond": {"HED": {"a": "Red, {my.col}"}}}))

    def test_brace_name_with_period_known(self):
        sidecar = {"cond": {"HED": {"a": "Red, {my.col}"}}, "my.col": {"HED": {"b": "Blue"}}}
        self.assertEqual(self.codes(sidecar), [])
        self.assertEqual(Sidecar(io.StringIO(json.dumps(sidecar))).get_column_refs(), ["my.col"])

    def test_brace_name_with_hash_assembled(self):
        # The value fills the template's placeholder only, not a "#" in a referenced column name.
        sidecar = Sidecar(
            io.StringIO(json.dumps({"val": {"HED": "Label/#, {col#1}"}, "col#1": {"HED": {"x": "Blue"}}}))
        )
        tsv = io.StringIO("onset\tval\tcol#1\n1.0\t3\tx\n")
        tabular = TabularInput(tsv, sidecar=sidecar)
        self.assertEqual(tabular.validate(self.hed_schema), [])
        self.assertEqual([str(hed) for hed in tabular.series_a], ["Label/3, Blue"])

    def test_brace_name_with_delimiter_not_a_reference(self):
        # A reference must parse as one tag (specification 3.2.9.3 rule 8), so a name holding a comma or a
        # parenthesis is never a reference, even when such a column is annotated.
        for name in ["a,b", "a(b)"]:
            with self.subTest(name=name):
                sidecar = {"cond": {"HED": {"a": "Red, {" + name + "}"}}, name: {"HED": {"b": "Blue"}}}
                self.assertTrue(self.codes(sidecar))
                self.assertEqual(Sidecar(io.StringIO(json.dumps(sidecar))).get_column_refs(), [])

    def test_every_categorical_substitution_checked(self):
        sidecar = {"event_code": {"HED": {"face": "(Red, {color})"}}, "color": {"HED": {"warm": "Red", "cool": "Blue"}}}
        self.assertEqual(self.codes(sidecar), ["TAG_EXPRESSION_REPEATED"])

    def test_definition_beside_tags(self):
        cases = [
            {"cond": {"HED": {"a": "(Definition/MyDef, (Red)), Blue"}}},
            {"val": {"HED": "(Definition/MyDef, (Red)), Label/#"}},
            {"val": {"HED": "(Definition/MyDef, (Red)), Label/#, Age/#"}},
        ]
        for sidecar in cases:
            with self.subTest(sidecar=sidecar):
                self.assertEqual(self.codes(sidecar), ["DEFINITION_INVALID"])

    def test_definitions_alone_valid(self):
        cases = [
            {"defs": {"HED": {"a": "(Definition/MyDef, (Red))", "b": "(Definition/Other, (Blue))"}}},
            {"defs": {"HED": "(Definition/MyDef, (Red)), (Definition/Other/#, (Label/#))"}},
        ]
        for sidecar in cases:
            with self.subTest(sidecar=sidecar):
                self.assertEqual(self.codes(sidecar), [])

    def test_nested_hed_key(self):
        cases = [
            {"cond": {"HED": {"a": "Red"}, "Levels": {"a": "x", "HED": "Blue"}}},
            {"cond": {"HED": {"a": "Red"}, "extra": {"inner": {"HED": "Blue"}}}},
            {"val": {"HED": "Label/#", "extra": {"HED": "Blue"}}},
        ]
        for sidecar in cases:
            with self.subTest(sidecar=sidecar):
                self.assertEqual(self.codes(sidecar), ["SIDECAR_INVALID"])


class TestRemovalSubstitution(unittest.TestCase):
    """A removed reference (its column n/a or blank) is a substitution for the repeat check only (HED 8.4.0).

    Specification 3.2.9.3 rule 10 and its explanation: for TAG_EXPRESSION_REPEATED the annotation with a
    reference removed (rule 3) is one of the substitutions, for every reference; for {HED} it is the only one.
    """

    COLOR = {"HED": {"warm": "Blue", "cool": "Green"}}

    @classmethod
    def setUpClass(cls):
        cls.hed_schema = schema.load_schema_version("8.4.0")

    def issues(self, sidecar_dict):
        return Sidecar(io.StringIO(json.dumps(sidecar_dict))).validate(self.hed_schema)

    def codes(self, sidecar_dict):
        return [issue["code"] for issue in self.issues(sidecar_dict)]

    def test_hed_reference_removed_repeats(self):
        sidecar = {"event_code": {"HED": {"face": "(Red, {HED}), (Red)"}}}
        self.assertEqual(self.codes(sidecar), ["TAG_EXPRESSION_REPEATED"])

    def test_categorical_reference_removed_repeats(self):
        sidecar = {"event_code": {"HED": {"face": "(Red, {color}), (Red)"}}, "color": self.COLOR}
        self.assertEqual(self.codes(sidecar), ["TAG_EXPRESSION_REPEATED"])

    def test_value_reference_removed_repeats(self):
        sidecar = {"event_code": {"HED": {"face": "(Red, {rt}), (Red)"}}, "rt": {"HED": "Label/#"}}
        self.assertEqual(self.codes(sidecar), ["TAG_EXPRESSION_REPEATED"])

    def test_hed_reference_alone_in_group(self):
        self.assertEqual(self.codes({"event_code": {"HED": {"face": "Red, ({HED})"}}}), [])

    def test_hed_reference_removed_no_repeat(self):
        self.assertEqual(self.codes({"event_code": {"HED": {"face": "(Red, {HED}), (Blue)"}}}), [])

    def test_categorical_reference_removed_no_repeat(self):
        sidecar = {"event_code": {"HED": {"face": "(Red, {color}), (Yellow)"}}, "color": self.COLOR}
        self.assertEqual(self.codes(sidecar), [])

    def test_duration_group_rule_not_checked_with_removal(self):
        # Removing {stim_desc} leaves (Duration/# s) without its inner group; the row with n/a fails when
        # assembled, not the sidecar.
        sidecar = {"dur": {"HED": "(Duration/# s, {stim_desc})"}, "stim_desc": {"HED": {"a": "(Red)", "b": "(Blue)"}}}
        self.assertEqual(self.codes(sidecar), [])

    def test_duration_group_rule_not_checked_for_hed_reference(self):
        self.assertEqual(self.codes({"dur": {"HED": "(Duration/# s, {HED})"}}), [])

    def test_categorical_substitution_repeat_kept(self):
        sidecar = {"event_code": {"HED": {"face": "(Red, {color})"}}, "color": {"HED": {"warm": "Red", "cool": "Blue"}}}
        self.assertEqual(self.codes(sidecar), ["TAG_EXPRESSION_REPEATED"])

    def test_removal_reports_only_repeats(self):
        # Each removal leaves a group that breaks another rule ((Duration/# s) with no inner group, a lone
        # (Onset)); only the repeat is reported.
        cases = [
            {"dur": {"HED": "(Duration/# s, {HED}), (Red, {HED}), (Red)"}},
            {"event_code": {"HED": {"face": "(Onset, {HED}), (Red, {HED}), (Red)"}}},
            {
                "dur": {"HED": "(Duration/# s, {stim_desc}), (Red, {stim_desc}), (Red)"},
                "stim_desc": {"HED": {"a": "(Blue)", "b": "(Green)"}},
            },
        ]
        for sidecar in cases:
            with self.subTest(sidecar=sidecar):
                self.assertEqual(self.codes(sidecar), ["TAG_EXPRESSION_REPEATED"])

    def test_repeat_reported_once(self):
        # Every combination finds these repeats; each is reported once.
        cases = [
            ({"event_code": {"HED": {"face": "Red, Red, {color}"}}, "color": self.COLOR}, 1),
            ({"event_code": {"HED": {"face": "(Red, {color}), (Red, {HED})"}}, "color": self.COLOR}, 1),
            (
                {
                    "event_code": {"HED": {"face": "(Red, {color}, {rt}), (Red)"}},
                    "color": self.COLOR,
                    "rt": {"HED": "Label/#"},
                },
                1,
            ),
        ]
        for sidecar, count in cases:
            with self.subTest(sidecar=sidecar):
                self.assertEqual(self.codes(sidecar), ["TAG_EXPRESSION_REPEATED"] * count)
