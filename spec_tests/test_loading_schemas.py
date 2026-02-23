"""Tests that all schemas in the hed-schemas submodule can be loaded.

Uses hed.scripts.check_schema_loading to verify that every non-deprecated
schema in all 4 formats (XML, MediaWiki, JSON, TSV) loads successfully.
Runs as part of spec_tests via ``python -m unittest discover spec_tests``.
"""

import unittest
from pathlib import Path

from hed.scripts.check_schema_loading import run_loading_check

HED_SCHEMAS_DIR = Path(__file__).parent / "hed-schemas"


@unittest.skipUnless(HED_SCHEMAS_DIR.exists(), "hed-schemas submodule not initialized")
class TestSchemaLoading(unittest.TestCase):
    """Test that all schemas in hed-schemas load without errors."""

    def test_all_released_schemas(self):
        """All released schemas in all formats should load successfully."""
        results = run_loading_check(HED_SCHEMAS_DIR, exclude_prereleases=True)
        self.assertEqual(
            results["failed"],
            0,
            f"{results['failed']} released schema(s) failed to load: " f"{[f['path'] for f in results['failures']]}",
        )
        self.assertGreater(results["total"], 0, "No released schemas found to test")

    def test_all_prerelease_schemas(self):
        """All prerelease schemas in all formats should load successfully."""
        results = run_loading_check(HED_SCHEMAS_DIR, prerelease_only=True)
        self.assertEqual(
            results["failed"],
            0,
            f"{results['failed']} prerelease schema(s) failed to load: " f"{[f['path'] for f in results['failures']]}",
        )
        # Prereleases may or may not exist — no assertGreater here


if __name__ == "__main__":
    unittest.main()
