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
            load_schema(os.path.join(FIXTURE_DIR, "HED8.4.0.xml"))
        self.assertFalse(any(issubclass(w.category, DeprecationWarning) for w in caught))


if __name__ == "__main__":
    unittest.main()
