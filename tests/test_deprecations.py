"""Registry of deprecated items and the major release that removes each one.

Every deprecated item in hedtools is listed in SCHEDULED_REMOVALS with a check that tells whether
it still exists. The first test fails as soon as the package's major version reaches an item's
removal release while the item is still present, so a scheduled removal cannot be forgotten. The
other tests keep the registry honest (the items exist before their removal) and confirm that the
deprecated schema= parameter still warns.

The 2.0.0 removals are tracked in https://github.com/hed-standard/hed-python/issues/1391.
"""

import inspect
import os
import re
import unittest
import warnings

import hed
from hed.errors.error_types import SchemaAttributeErrors
from hed.schema import load_schema
from hed.schema.hed_schema_io import from_string
from hed.schema.schema_io.base2schema import SchemaLoader
from hed.tools.util import data_util
from hed.validator import SpreadsheetValidator
from hed.validator.util import UnitValueValidator
from tests.schema.schema_test_helpers import bundled_standard_path

FIXTURE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "data/schema_tests/merge_group_tests"))


def _has_parameter(func, name):
    return name in inspect.signature(func).parameters


# (what, still_exists, major version that removes it)
SCHEDULED_REMOVALS = [
    ("schema= parameter of hed.schema.load_schema", lambda: _has_parameter(load_schema, "schema"), 2),
    ("schema= parameter of hed.schema.from_string", lambda: _has_parameter(from_string, "schema"), 2),
    (
        "appending branch (schema= parameter) of SchemaLoader.__init__ and SchemaLoader.load",
        lambda: _has_parameter(SchemaLoader.__init__, "schema") or _has_parameter(SchemaLoader.load, "schema"),
        2,
    ),
    (
        "SchemaAttributeErrors.SCHEMA_MISSING_EXTRA_VALUE alias of SCHEMA_MISSING_EXTRA",
        lambda: hasattr(SchemaAttributeErrors, "SCHEMA_MISSING_EXTRA_VALUE"),
        2,
    ),
    (
        "def_dicts= parameter of SpreadsheetValidator.validate",
        lambda: _has_parameter(SpreadsheetValidator.validate, "def_dicts"),
        2,
    ),
    (
        "value_validators= parameter of UnitValueValidator.__init__ (no-op since the date-time cleanup)",
        lambda: _has_parameter(UnitValueValidator.__init__, "value_validators"),
        2,
    ),
    (
        "hed.tools.util.data_util.delete_rows_by_column (replaced by remove_rows_by_value)",
        lambda: hasattr(data_util, "delete_rows_by_column"),
        2,
    ),
]


def _major_version():
    """Return the major version of the installed hedtools, or None if it cannot be determined."""
    match = re.match(r"(\d+)\.", getattr(hed, "__version__", "") or "")
    return int(match.group(1)) if match else None


class TestScheduledRemovals(unittest.TestCase):
    def test_items_are_removed_in_their_release(self):
        major = _major_version()
        if major is None:
            self.skipTest("hedtools version unknown")
        overdue = [
            what for what, still_exists, remove_in in SCHEDULED_REMOVALS if major >= remove_in and still_exists()
        ]
        self.assertEqual(overdue, [], f"Scheduled removals still present in {hed.__version__}: {overdue}")

    def test_registry_matches_the_code(self):
        major = _major_version()
        if major is None:
            self.skipTest("hedtools version unknown")
        stale = [
            what for what, still_exists, remove_in in SCHEDULED_REMOVALS if major < remove_in and not still_exists()
        ]
        self.assertEqual(stale, [], f"Registry lists items that no longer exist; remove them: {stale}")


class TestSchemaParameterDeprecation(unittest.TestCase):
    def test_schema_parameter_warns_and_still_works(self):
        base = load_schema(os.path.join(FIXTURE_DIR, "HED_testconflict_2.0.0.xml"), xml_folder=FIXTURE_DIR)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            appended = load_schema(os.path.join(FIXTURE_DIR, "HED_testclash_1.0.0.xml"), schema=base)
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))
        self.assertIsNotNone(appended.get_tag_entry("Clash-one"))
        self.assertIsNotNone(appended.get_tag_entry("Object-one"))

    def test_no_warning_without_schema_parameter(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            load_schema(bundled_standard_path("8.4.0"))
        self.assertFalse(any(issubclass(w.category, DeprecationWarning) for w in caught))


class TestDefDictsParameterDeprecation(unittest.TestCase):
    """SpreadsheetValidator.validate(data, def_dicts=...) was the signature before the staged validator."""

    @classmethod
    def setUpClass(cls):
        import pandas as pd

        from hed.models import TabularInput
        from hed.schema import load_schema_version

        cls.schema = load_schema_version("8.4.0")
        cls.definitions = "(Definition/MyDef, (Event))"
        cls.events = TabularInput(pd.DataFrame({"onset": [1.0, 2.0], "HED": ["(Onset, Def/MyDef)", "Red"]}))

    def test_def_dicts_keyword_warns_and_still_works(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            issues = SpreadsheetValidator(self.schema).validate(self.events, def_dicts=self.definitions)
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))
        self.assertEqual(issues, [])

    def test_definitions_in_the_sidecar_position_raise(self):
        with self.assertRaises(TypeError):
            SpreadsheetValidator(self.schema).validate(self.events, self.definitions)

    def test_no_warning_with_extra_def_dicts(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            issues = SpreadsheetValidator(self.schema).validate(self.events, extra_def_dicts=self.definitions)
        self.assertFalse(any(issubclass(w.category, DeprecationWarning) for w in caught))
        self.assertEqual(issues, [])


class TestValueValidatorsParameterDeprecation(unittest.TestCase):
    """UnitValueValidator(value_validators=...) injected per-class functions that validation never called."""

    def test_value_validators_keyword_warns_and_is_ignored(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            validator = UnitValueValidator(value_validators={"dateTimeClass": lambda value: False})
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))
        self.assertTrue(validator._char_validator.is_valid_value("2026-09-30T09:55:00", "dateTimeClass"))

    def test_no_warning_without_value_validators(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            UnitValueValidator(modern_allowed_char_rules=True)
        self.assertFalse(any(issubclass(w.category, DeprecationWarning) for w in caught))


class TestDeleteRowsByColumnDeprecation(unittest.TestCase):
    """delete_rows_by_column deleted rows in place, which pandas 3.1 deprecates; remove_rows_by_value returns a copy."""

    def test_warns_names_replacement_and_still_deletes_in_place(self):
        import pandas as pd

        df = pd.DataFrame({"a": ["x", "n/a", "y"], "b": ["1", "2", "n/a"]})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = data_util.delete_rows_by_column(df, "n/a")
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(len(deprecations), 1, [str(w.message) for w in deprecations])
        self.assertIn("remove_rows_by_value", str(deprecations[0].message))
        self.assertIn("2.0.0", str(deprecations[0].message))
        self.assertIsNone(result)
        self.assertListEqual(list(df.index), [0])


if __name__ == "__main__":
    unittest.main()
