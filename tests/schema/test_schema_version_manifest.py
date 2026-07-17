"""Unit tests for hed.schema.schema_version_manifest (manifest parsing fast path).

These are pure parsing tests over an in-memory manifest fixture - no network, no real schema files.
The live fetch path (manifest -> hed_cache.get_available_hed_versions / _download_schema_version) is
exercised by the existing schema-cache spec tests.
"""

import unittest

from hed.schema import schema_version_manifest as manifest


SAMPLE_MANIFEST = {
    "manifest_format_version": 1,
    "generated": "2026-07-16T00:00:00+00:00",
    "repo_commit": "abc123def456",
    "libraries": {
        "": {
            "released": [
                {"version": "8.4.0", "file": "standard_schema/hedxml/HED8.4.0.xml", "sha": "sha840", "date": "d"},
                {"version": "8.3.0", "file": "standard_schema/hedxml/HED8.3.0.xml", "sha": "sha830", "date": "d"},
            ],
            "prerelease": [
                {"version": "8.5.0", "file": "standard_schema/prerelease/HED8.5.0.xml", "sha": "sha850", "date": "d"},
            ],
            "deprecated": [
                # 8.3.5 is deliberately "mid-range" (between released 8.3.0 and 8.4.0) so the tests
                # cover a deprecated version that falls inside the released range, not just below it.
                {
                    "version": "8.3.5",
                    "file": "standard_schema/hedxml/deprecated/HED8.3.5.xml",
                    "sha": "sha835",
                    "date": "d",
                },
                {
                    "version": "7.2.0",
                    "file": "standard_schema/hedxml/deprecated/HED7.2.0.xml",
                    "sha": "sha720",
                    "date": "d",
                },
            ],
        },
        "score": {
            "released": [
                {
                    "version": "2.1.0",
                    "file": "library_schemas/score/hedxml/HED_score_2.1.0.xml",
                    "sha": "shasc",
                    "date": "d",
                },
            ],
            "prerelease": [],
            "deprecated": [
                # A deprecated *library* version, to confirm deprecated exclusion is not standard-only.
                {
                    "version": "2.0.0",
                    "file": "library_schemas/score/hedxml/deprecated/HED_score_2.0.0.xml",
                    "sha": "shascd",
                    "date": "d",
                },
            ],
        },
        "mouse": {  # prerelease only - no released versions
            "released": [],
            "prerelease": [
                {
                    "version": "1.0.0",
                    "file": "library_schemas/mouse/prerelease/HED_mouse_1.0.0.xml",
                    "sha": "shamo",
                    "date": "d",
                },
            ],
            "deprecated": [],
        },
    },
}


class TestIsSupported(unittest.TestCase):
    def test_supported(self):
        self.assertTrue(manifest.is_supported(SAMPLE_MANIFEST))

    def test_unsupported_format_version(self):
        self.assertFalse(manifest.is_supported({"manifest_format_version": 2, "libraries": {}}))

    def test_non_dict(self):
        self.assertFalse(manifest.is_supported(None))
        self.assertFalse(manifest.is_supported([]))
        self.assertFalse(manifest.is_supported("not a manifest"))


class TestAvailableVersions(unittest.TestCase):
    def test_standard_default_excludes_prerelease_and_deprecated(self):
        # Also proves the mid-range deprecated version (8.3.5) is excluded from the listing.
        self.assertEqual(manifest.available_versions(SAMPLE_MANIFEST), ["8.4.0", "8.3.0"])

    def test_standard_with_prerelease_newest_first(self):
        self.assertEqual(
            manifest.available_versions(SAMPLE_MANIFEST, None, check_prerelease=True),
            ["8.5.0", "8.4.0", "8.3.0"],
        )

    def test_specific_library(self):
        # score has a deprecated 2.0.0; it must not appear in the released listing.
        self.assertEqual(manifest.available_versions(SAMPLE_MANIFEST, "score"), ["2.1.0"])

    def test_all_maps_standard_to_none_and_omits_empty(self):
        result = manifest.available_versions(SAMPLE_MANIFEST, "all")
        self.assertEqual(result[None], ["8.4.0", "8.3.0"])
        self.assertEqual(result["score"], ["2.1.0"])
        # mouse has no released versions and check_prerelease is False -> omitted entirely.
        self.assertNotIn("mouse", result)

    def test_all_with_prerelease_includes_prerelease_only_library(self):
        result = manifest.available_versions(SAMPLE_MANIFEST, "all", check_prerelease=True)
        self.assertEqual(result["mouse"], ["1.0.0"])
        self.assertIn(None, result)

    def test_unknown_library_returns_empty(self):
        self.assertEqual(manifest.available_versions(SAMPLE_MANIFEST, "nosuch"), [])


class TestFindVersionInfo(unittest.TestCase):
    def test_released_pins_to_repo_commit(self):
        info = manifest.find_version_info(SAMPLE_MANIFEST, "8.4.0", None)
        self.assertEqual(
            info,
            (
                "sha840",
                "https://raw.githubusercontent.com/hed-standard/hed-schemas/"
                "abc123def456/standard_schema/hedxml/HED8.4.0.xml",
                False,
            ),
        )

    def test_prerelease_flag_true(self):
        info = manifest.find_version_info(SAMPLE_MANIFEST, "8.5.0", None)
        self.assertIsNotNone(info)
        self.assertTrue(info[2])

    def test_library_version(self):
        info = manifest.find_version_info(SAMPLE_MANIFEST, "2.1.0", "score")
        self.assertEqual(info[0], "shasc")
        self.assertTrue(info[1].endswith("library_schemas/score/hedxml/HED_score_2.1.0.xml"))
        self.assertFalse(info[2])

    def test_ref_override(self):
        info = manifest.find_version_info(SAMPLE_MANIFEST, "8.4.0", None, ref="main")
        self.assertIn("/main/", info[1])

    def test_missing_version_returns_none(self):
        self.assertIsNone(manifest.find_version_info(SAMPLE_MANIFEST, "9.9.9", None))
        self.assertIsNone(manifest.find_version_info(SAMPLE_MANIFEST, "1.0.0", "nosuch"))

    def test_deprecated_versions_are_not_loadable(self):
        # Deprecated schemas are display-only (for the static schema browser); the download/load
        # path must never surface them - for the standard schema or any library, and regardless of
        # where the version falls in the range (below the released range, or in the middle of it).
        self.assertIsNone(manifest.find_version_info(SAMPLE_MANIFEST, "8.3.5", None))  # mid-range standard
        self.assertIsNone(manifest.find_version_info(SAMPLE_MANIFEST, "7.2.0", None))  # old standard
        self.assertIsNone(manifest.find_version_info(SAMPLE_MANIFEST, "2.0.0", "score"))  # deprecated library


class TestRawUrl(unittest.TestCase):
    def test_raw_url_for(self):
        self.assertEqual(
            manifest.raw_url_for("standard_schema/hedxml/HED8.4.0.xml", "deadbeef"),
            "https://raw.githubusercontent.com/hed-standard/hed-schemas/deadbeef/standard_schema/hedxml/HED8.4.0.xml",
        )


if __name__ == "__main__":
    unittest.main()
