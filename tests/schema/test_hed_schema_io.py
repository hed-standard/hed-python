import unittest
from unittest.mock import patch

from hed.errors import HedFileError
from hed.errors.error_types import SchemaErrors
from hed.schema import load_schema, HedSchemaGroup, load_schema_version, HedSchema
from hed.schema.hed_schema_io import parse_version_list, _load_schema_version, from_string
from tests.schema.schema_test_helpers import with_temp_file, get_temp_filename

import os
import json
import math
import tempfile
from urllib.error import URLError
from semantic_version import Version
from hed.errors import HedExceptions
from hed.schema import HedKey
from hed.schema import hed_cache
from hed import schema
import shutil


def _assert_valid_sorted_versions(test_case, versions):
    """Assert every entry is a valid semver string and the list is sorted newest-first.

    Deliberately avoids pinning to any specific version number (e.g. "8.2.0") - upstream can
    prune or add versions at any time, and that shouldn't make this assertion fail as long as
    get_available_hed_versions() is still returning well-formed, correctly ordered data.
    """
    test_case.assertTrue(versions, "expected at least one version")
    for version in versions:
        try:
            Version(version)
        except ValueError:
            test_case.fail(f"{version!r} is not a valid semver string")
    test_case.assertEqual(
        versions,
        sorted(versions, key=Version, reverse=True),
        "versions should be sorted newest-first",
    )


# todo: speed up these tests
class TestHedSchema(unittest.TestCase):
    def test_load_schema_invalid_parameters(self):
        bad_filename = "this_is_not_a_real_file.xml"
        with self.assertRaises(HedFileError):
            load_schema(bad_filename)

        bad_filename = "https://github.com/hed-standard/hed-python/bad_url.xml"
        with self.assertRaises(HedFileError):
            load_schema(bad_filename)

    def test_load_schema_name(self):
        schema_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED8.2.0.mediawiki"
        )

        hed_schema = load_schema(schema_path, schema_namespace="testspace", name="Test Name")
        self.assertEqual(hed_schema.schema_namespace, "testspace:")
        self.assertEqual(hed_schema.name, "Test Name")

        hed_schema = load_schema(schema_path, schema_namespace="testspace")
        self.assertEqual(hed_schema.schema_namespace, "testspace:")
        self.assertEqual(hed_schema.name, schema_path)

    def test_load_schema_version(self):
        ver1 = "8.0.0"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version_number, "8.0.0", "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "", "load_schema_version standard schema has no library")
        self.assertEqual(schemas1.name, "8.0.0")
        ver2 = "base:8.0.0"
        schemas2 = load_schema_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertEqual(schemas2.version_number, "8.0.0", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas2._namespace, "base:", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas2.name, "base:8.0.0")
        ver3 = ["base:8.0.0"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertEqual(schemas3.version_number, "8.0.0", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas3._namespace, "base:", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas3.name, "base:8.0.0")

    def test_load_schema_version_merged(self):
        ver4 = ["testlib_2.1.0", "score_2.1.0"]
        schemas3 = load_schema_version(ver4)
        issues = schemas3.check_compliance()
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertTrue(schemas3.version_number, "load_schema_version has the right version with namespace")
        self.assertEqual(schemas3.schema_namespace, "", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas3.name, "testlib_2.1.0,score_2.1.0")
        self.assertEqual(schemas3.version, "testlib_2.1.0,score_2.1.0")
        # Deprecated tag warnings + character issues from SCORE prologue/epilogue
        self.assertEqual(len(issues), 31)

        # Verify this cannot be saved
        with self.assertRaises(HedFileError):
            schemas3.save_as_mediawiki("filename")

    def test_verify_utf8_dupe(self):
        base_dir = os.path.join(os.path.dirname(__file__), "../data/schema_tests")
        schema_path = os.path.join(base_dir, "schema_utf8_dupe.mediawiki")
        schema = load_schema(schema_path)
        issues = schema.check_compliance()
        # This can be 1 or 2, depending on if the "pre-release" warning shows up.
        self.assertTrue(1 <= len(issues) <= 2)

        # Note it finds both of these as a duplicate
        self.assertTrue(schema.get_tag_entry("Wßord"))
        self.assertTrue(schema.get_tag_entry("Wssord"))

    def test_load_schema_version_default_resolves_latest(self):
        """Test that empty version resolves to the highest released standard schema."""
        schema_default = load_schema_version("")
        self.assertIsInstance(schema_default, HedSchema)
        # Should be the highest standard version in the cache
        versions = hed_cache.get_hed_versions(check_prerelease=False)
        self.assertIsInstance(versions, list)
        self.assertEqual(schema_default.version_number, versions[0])

    def test_get_hed_versions_includes_bundled_score(self):
        """Score library is bundled with hedtools and must always be locally available.

        get_hed_versions() reads only the local cache and the schema_data/ bundle shipped
        inside the package — no network call is made.  This test therefore never skips:
        if it fails, a required bundled schema has gone missing.
        """
        versions = hed_cache.get_hed_versions(library_name="score")
        self.assertIsInstance(versions, list)
        self.assertTrue(versions, "score library schemas must always be present in the bundled schema_data")

    def test_get_available_hed_versions_lists_without_downloading(self):
        """get_available_hed_versions() should list real GitHub versions without caching any content."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                versions = hed_cache.get_available_hed_versions()
                if not versions:
                    # get_available_hed_versions() degrades gracefully (returns [] rather than
                    # raising) when GitHub is unreachable or rate-limited. This repo's testing
                    # policy is real network calls, not mocks, so rather than mocking around an
                    # outage, treat "nothing came back" as an environment limitation and skip.
                    self.skipTest("GitHub unreachable or rate-limited in this environment")
                self.assertIsInstance(versions, list)
                _assert_valid_sorted_versions(self, versions)

                versions_all = hed_cache.get_available_hed_versions(library_name="all")
                self.assertIsInstance(versions_all, dict)
                self.assertIn(None, versions_all)
                # Library URLs may be independently rate-limited even when standard-schema URLs
                # succeed.  Only assert score-specific things when the data is actually present;
                # don't skip the whole test — the cache-folder check below is unconditional and
                # must always run.
                score_available = "score" in versions_all
                if score_available:
                    _assert_valid_sorted_versions(self, versions_all["score"])

                versions_with_pre = hed_cache.get_available_hed_versions(check_prerelease=True)
                # Only comparable when the library endpoint was also reachable for the baseline call.
                if score_available:
                    self.assertGreaterEqual(len(versions_with_pre), len(versions))

            # This function only lists what's on GitHub - it should never download or cache
            # actual schema content, unlike cache_xml_versions(). It does write one small
            # listing-metadata file (see test_get_available_hed_versions_caches_result below),
            # so check for the absence of schema files rather than an empty directory.
            cached_files = os.listdir(tmp_dir)
            self.assertTrue(
                all(f == hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME for f in cached_files),
                f"Unexpected files in cache folder: {cached_files}",
            )

    def test_get_available_hed_versions_caches_result(self):
        """A second call within the threshold should reuse the cached listing; force_refresh bypasses it."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                versions = hed_cache.get_available_hed_versions()
                if not versions:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")

                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                self.assertTrue(os.path.exists(cache_filename))
                first_write_time = os.path.getmtime(cache_filename)

                # Within the threshold, a second call should reuse the cache (no new write).
                hed_cache.get_available_hed_versions()
                self.assertEqual(os.path.getmtime(cache_filename), first_write_time)

                # force_refresh=True should bypass the cache and query GitHub again.
                hed_cache.get_available_hed_versions(force_refresh=True)
                self.assertGreaterEqual(os.path.getmtime(cache_filename), first_write_time)

    def test_get_available_hed_versions_conditional_request_after_force_refresh(self):
        """force_refresh should still use a stored ETag and return consistent, correct data.

        This can't assert on which HTTP status GitHub actually returned (304 vs 200) without
        mocking, which this repo's testing policy avoids - real GitHub content could change
        between the two calls, however unlikely in a short test run. What it does verify is that
        force_refresh's conditional revalidation path (see _get_json_with_etag()) round-trips
        correctly against the live API: the second call must return a result at least as
        complete as the first, and the cache must still hold exactly one small metadata file
        rather than a growing pile of one-off cache entries.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                first = hed_cache.get_available_hed_versions(library_name="all")
                if not first:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")

                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                with open(cache_filename, "r") as f:
                    cache_after_first = json.load(f)
                # Every URL that was actually reached should have picked up an ETag to send on
                # the next conditional request - if GitHub stopped returning ETags, this needs
                # attention, so fail loudly rather than silently losing the optimization.
                self.assertTrue(cache_after_first, "expected at least one cached URL entry")

                second = hed_cache.get_available_hed_versions(library_name="all", force_refresh=True)
                self.assertIsInstance(second, dict)
                self.assertIn(None, second)
                # Should be the same or better (e.g. a release landed between the two calls) -
                # never worse, which would indicate the conditional-request path lost data.
                self.assertGreaterEqual(len(second[None]), len(first[None]))

                self.assertEqual(os.listdir(tmp_dir), [hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME])

    def test_get_available_hed_versions_skips_unneeded_urls(self):
        """library_name=None or a specific name should skip fetches whose result is unused.

        Verified by inspecting the on-disk per-URL cache afterward (real network calls, no
        mocks, per this repo's testing policy) - it should only ever contain entries for URLs
        that were actually necessary for the requested library_name, never anything extra.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                standard_only = hed_cache.get_available_hed_versions(library_name=None)
                if not standard_only:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")

                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                with open(cache_filename, "r") as f:
                    cached_urls = set(json.load(f).keys())
                self.assertTrue(
                    all("library_schemas" not in url for url in cached_urls),
                    f"library_name=None should never touch library URLs, but cached: {cached_urls}",
                )

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                score_only = hed_cache.get_available_hed_versions(library_name="score")
                if not score_only:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")

                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                with open(cache_filename, "r") as f:
                    cached_urls = set(json.load(f).keys())
                self.assertTrue(
                    all("standard_schema" not in url for url in cached_urls),
                    f"library_name='score' should never touch standard-schema URLs, but cached: {cached_urls}",
                )
                library_base = hed_cache.LIBRARY_HED_URL
                # Besides the actual per-library content URLs, the cache also legitimately holds
                # two library_schemas/-gate entries that aren't library-content URLs at all: the
                # gate's own commits-endpoint URL, and the plain-string SHA marker recorded under
                # it (see _LIBRARY_HEAD_CACHE_KEY) - neither is scoped to a specific library, so
                # both are expected regardless of which library_name was requested.
                non_library_keys = {library_base, hed_cache.LIBRARY_SCHEMAS_HEAD_URL, hed_cache._LIBRARY_HEAD_CACHE_KEY}
                for url in cached_urls:
                    if url in non_library_keys:
                        continue  # the one unavoidable "list all libraries" call, or a gate entry
                    # Trailing slash matters here - without it, a hypothetical library named
                    # e.g. "scoreboard" would incorrectly pass a plain startswith(".../score").
                    self.assertTrue(
                        url.startswith(library_base + "/score/"),
                        f"Unexpected library URL fetched while only 'score' was requested: {url}",
                    )

    def test_get_available_hed_versions_degrades_on_malformed_response(self):
        """A GitHub response shaped differently than expected should degrade gracefully.

        GitHub's contents API returns a JSON *object* (file metadata) for a path that's a
        file, rather than the *list* every parser in this module expects for a directory.
        Pointing hed_library_urls at a real file's contents URL reproduces exactly the
        "unexpected response shape" Copilot's review flagged as unhandled - using a real,
        live URL rather than mocking a bad response, per this repo's testing policy.
        """
        real_file_url = hed_cache.DEFAULT_HED_LIST_VERSIONS_URL + "/hedxml/HED8.2.0.xml"
        try:
            result = hed_cache.get_available_hed_versions(
                hed_base_urls=(),
                hed_library_urls=(real_file_url,),
                library_name="all",
            )
        except Exception as ex:
            self.fail(f"get_available_hed_versions() should degrade gracefully, not raise: {ex!r}")
        self.assertEqual(result, {})

    def test_get_available_hed_versions_tolerates_corrupted_cache_entry(self):
        """A non-dict per-URL cache entry should degrade to a cache miss, not raise AttributeError.

        Reproduces the exact scenario Copilot's review flagged in _get_json_with_etag(): a
        corrupted cache file, or one written by an older/newer format, could have an entry that
        isn't the expected {"etag", "body", "timestamp"} dict. Hand-writing such an entry for a
        real URL and confirming get_available_hed_versions() still returns real data (rather than
        crashing on cached_entry.get(...)) covers this without mocking any network response.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                corrupted_url = hed_cache.DEFAULT_HED_LIST_VERSIONS_URL + hed_cache.hedxml_suffix
                with open(cache_filename, "w") as f:
                    json.dump({corrupted_url: "not-a-dict-entry"}, f)

                try:
                    versions = hed_cache.get_available_hed_versions()
                except AttributeError as ex:
                    self.fail(f"A corrupted cache entry should degrade to a cache miss, not raise: {ex!r}")

                if not versions:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")
                _assert_valid_sorted_versions(self, versions)

    def test_get_last_commit_sha_returns_a_sha_for_standard_and_library_paths(self):
        """_get_last_commit_sha() should return a real commit SHA for each scoped gate URL."""
        for url in (hed_cache.STANDARD_SCHEMA_HEAD_URL, hed_cache.LIBRARY_SCHEMAS_HEAD_URL):
            sha = hed_cache._get_last_commit_sha(url, {})
            if sha is None:
                self.skipTest("GitHub unreachable or rate-limited in this environment")
            self.assertIsInstance(sha, str)
            self.assertTrue(sha, f"expected a non-empty SHA for {url}")

    def test_get_last_commit_sha_degrades_gracefully_on_bad_path(self):
        """_get_last_commit_sha() should return None, not raise, for a path with no commit history.

        Points at a real repo (hed-standard/hed-schemas) but a path that never existed, rather
        than mocking a bad response, per this repo's testing policy. GitHub's commits-list
        endpoint returns an empty array (not a 404) for such a path.
        """
        bad_url = (
            "https://api.github.com/repos/hed-standard/hed-schemas/commits"
            "?path=this-path-does-not-exist-abc123&per_page=1"
        )
        sha = hed_cache._get_last_commit_sha(bad_url, {})
        self.assertIsNone(sha)

    def test_get_json_with_etag_retries_failed_entry_despite_large_threshold(self):
        """A recorded failure should be retried well before a very large cache_time_threshold
        would otherwise allow, even though a successful entry is legitimately allowed to be
        reused for that long.

        Regression test for a gap flagged in review: get_available_hed_versions()'s
        directory-level gate passes math.inf as the per-folder cache_time_threshold once it
        confirms a directory is unchanged, so that already-fetched, successful entries can be
        reused indefinitely. But a *failed* per-URL entry isn't "known good data" - honoring
        that same infinite threshold for it would mean a transient rate-limit/network error
        gets silently, permanently skipped until the gate happens to see a real change (days or
        weeks later). Uses a real, guaranteed-unreachable address (no mocks, per this repo's
        testing policy) so the "a retry actually happened" assertion reflects a genuine second
        network attempt, not a mocked one - and works regardless of whether GitHub itself is
        reachable in this environment.
        """
        unreachable_url = "http://127.0.0.1:1/this-will-never-respond"
        etag_cache = {}

        with self.assertRaises(URLError):
            hed_cache._get_json_with_etag(unreachable_url, etag_cache, force_refresh=False, cache_time_threshold=0)

        self.assertIn(unreachable_url, etag_cache)
        first_failure_timestamp = etag_cache[unreachable_url]["timestamp"]

        # Simulate the failure having been recorded a while ago - well past
        # AVAILABLE_VERSIONS_TIME_THRESHOLD, but still comfortably inside a "the gate confirmed
        # nothing changed" infinite threshold.
        etag_cache[unreachable_url]["timestamp"] = first_failure_timestamp - (
            hed_cache.AVAILABLE_VERSIONS_TIME_THRESHOLD + 30
        )

        with self.assertRaises(URLError):
            hed_cache._get_json_with_etag(
                unreachable_url, etag_cache, force_refresh=False, cache_time_threshold=math.inf
            )

        # If the large threshold had been honored for this failure, tier 1 would have re-raised
        # immediately from the stale cached entry without touching the network again, and the
        # timestamp would still be the artificially backdated one. Seeing a fresh timestamp
        # proves a real retry happened instead.
        self.assertGreater(etag_cache[unreachable_url]["timestamp"], first_failure_timestamp)

    def test_get_available_hed_versions_skips_crawl_when_standard_schema_unchanged(self):
        """A repeat call should skip the standard-schema crawl once its scoped gate confirms
        nothing changed under standard_schema/ on GitHub - even when force_refresh=True forces
        the gate itself to revalidate.

        Verified by checking that every per-folder URL's stored timestamp is untouched by the
        second call, while relying on real network calls throughout (no mocking, per this
        repo's testing policy) - this assumes hed-schemas genuinely doesn't change mid-test,
        which is exactly the (overwhelmingly common) scenario this gate exists for.

        The gate itself is best-effort: _get_last_commit_sha() can return None (commits endpoint
        unreachable or rate-limited independently of the rest of GitHub's API), in which case
        get_available_hed_versions() falls back to a normal per-folder crawl and can still return
        a non-empty, correct version list without ever recording the gate SHA. That's correct
        behavior, not something this test is meant to catch - so skip rather than fail when the
        gate key never got written.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                first = hed_cache.get_available_hed_versions()
                if not first:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")

                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                with open(cache_filename) as f:
                    cache_after_first = json.load(f)
                if hed_cache._STANDARD_HEAD_CACHE_KEY not in cache_after_first:
                    self.skipTest(
                        "standard-schema gate SHA unavailable this run (commits endpoint unreachable or "
                        "rate-limited); get_available_hed_versions() correctly fell back to a per-folder crawl"
                    )
                gate_keys = {hed_cache._STANDARD_HEAD_CACHE_KEY, hed_cache._LIBRARY_HEAD_CACHE_KEY}
                folder_urls = [
                    url
                    for url in cache_after_first
                    if url not in gate_keys and url != hed_cache.STANDARD_SCHEMA_HEAD_URL
                ]
                self.assertTrue(folder_urls, "expected at least one per-folder URL cached")
                folder_timestamps_before = {url: cache_after_first[url]["timestamp"] for url in folder_urls}

                second = hed_cache.get_available_hed_versions(force_refresh=True)
                self.assertEqual(second, first, "result should be unchanged since nothing on GitHub changed")

                with open(cache_filename) as f:
                    cache_after_second = json.load(f)
                for url in folder_urls:
                    self.assertEqual(
                        cache_after_second[url]["timestamp"],
                        folder_timestamps_before[url],
                        f"{url} should not have been re-checked once the standard-schema gate confirmed "
                        "nothing had changed",
                    )

    def test_get_available_hed_versions_recrawls_when_standard_schema_head_sha_stale(self):
        """A stored standard-schema gate SHA that doesn't match the real one should trigger a
        normal crawl of standard_schema/.

        Hand-writing a deliberately wrong SHA into the cache file (mimicking what a real repo
        change would look like on the next call) - without mocking any network response - and
        confirming get_available_hed_versions() still returns real, complete data rather than
        incorrectly trusting the stale marker, and that the marker gets corrected afterward.

        Refreshing the marker is itself best-effort: _get_last_commit_sha() can return None
        (commits endpoint unreachable or rate-limited independently of the rest of GitHub's
        API), in which case get_available_hed_versions() falls back to a normal per-folder crawl
        and still returns valid data, but deliberately leaves the existing marker untouched
        rather than overwriting it with nothing useful. That's correct behavior, not something
        this test is meant to catch - so skip rather than fail when the marker wasn't refreshed.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                with open(cache_filename, "w") as f:
                    json.dump({hed_cache._STANDARD_HEAD_CACHE_KEY: "not-a-real-sha"}, f)

                versions = hed_cache.get_available_hed_versions()
                if not versions:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")
                _assert_valid_sorted_versions(self, versions)

                with open(cache_filename) as f:
                    cache_after = json.load(f)
                if cache_after[hed_cache._STANDARD_HEAD_CACHE_KEY] == "not-a-real-sha":
                    self.skipTest(
                        "standard-schema gate SHA unavailable this run (commits endpoint unreachable or "
                        "rate-limited); get_available_hed_versions() correctly fell back to a per-folder crawl "
                        "without refreshing the marker"
                    )

    def test_get_available_hed_versions_gates_are_scoped_independently(self):
        """A stale library gate marker should not force a standard-schema recrawl, and vice
        versa - confirming the two gates (standard_schema/ and library_schemas/) are
        independent rather than one shared whole-repo check.

        Both gate SHAs are best-effort: _get_last_commit_sha() can return None (its commits
        endpoint unreachable or rate-limited independently of the rest of GitHub's API), in
        which case get_available_hed_versions() falls back to a normal per-folder crawl for that
        directory and never records the corresponding gate key - correct behavior, but not one
        this test (which specifically manipulates the library gate key) can exercise. Skip
        rather than fail when either key never got written.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                first = hed_cache.get_available_hed_versions(library_name="all")
                if not first:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")

                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                with open(cache_filename) as f:
                    cache_after_first = json.load(f)
                if (
                    hed_cache._STANDARD_HEAD_CACHE_KEY not in cache_after_first
                    or hed_cache._LIBRARY_HEAD_CACHE_KEY not in cache_after_first
                ):
                    self.skipTest(
                        "a gate SHA was unavailable this run (commits endpoint unreachable or rate-limited); "
                        "get_available_hed_versions() correctly fell back to a per-folder crawl"
                    )

                standard_folder_urls = [
                    url for url in cache_after_first if url.startswith(hed_cache.DEFAULT_HED_LIST_VERSIONS_URL)
                ]
                self.assertTrue(standard_folder_urls, "expected at least one standard-schema folder URL cached")
                standard_timestamps_before = {url: cache_after_first[url]["timestamp"] for url in standard_folder_urls}

                # Corrupt only the library gate marker - the standard-schema gate marker is left
                # untouched, so its crawl should still be skipped even though force_refresh=True
                # forces both gates to revalidate against GitHub.
                cache_after_first[hed_cache._LIBRARY_HEAD_CACHE_KEY] = "not-a-real-sha"
                with open(cache_filename, "w") as f:
                    json.dump(cache_after_first, f)

                hed_cache.get_available_hed_versions(library_name="all", force_refresh=True)

                with open(cache_filename) as f:
                    cache_after_second = json.load(f)

                # The SHA gate only fires when the commits endpoint is reachable on the second
                # call.  If it was independently rate-limited, _get_last_commit_sha() returns
                # None, the gate doesn't fire, force_refresh=True causes a genuine re-fetch of
                # the standard-schema folder URLs, and the timestamp assertions below would fail
                # even though the production code is behaving correctly.  Skip in that case.
                sha_entry = cache_after_second.get(hed_cache.STANDARD_SCHEMA_HEAD_URL)
                if not isinstance(sha_entry, dict) or sha_entry.get("body") is None:
                    self.skipTest(
                        "standard-schema commits endpoint was rate-limited on the second call; "
                        "SHA gate couldn't revalidate, so timestamp assertions are not meaningful"
                    )

                for url in standard_folder_urls:
                    self.assertEqual(
                        cache_after_second[url]["timestamp"],
                        standard_timestamps_before[url],
                        f"{url} should not have been re-checked - only the library gate was made stale",
                    )

    def test_get_available_hed_versions_repo_check_interval_limits_gate_frequency(self):
        """A larger repo_check_interval should reduce how often the gate URL itself is hit,
        independently of cache_time_threshold for the per-folder content URLs.

        Verified by checking the on-disk cache after two rapid calls: with a large
        repo_check_interval, the gate URL's own cache entry should not be re-checked on the
        second call (tier-1 reuse). This can't assert anything about GitHub's actual request
        count without mocking, which this repo's testing policy avoids - only the client-side
        effect of not even attempting a network call is checkable here.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(hed_cache, "HED_CACHE_DIRECTORY", tmp_dir):
                first = hed_cache.get_available_hed_versions(repo_check_interval=3600)
                if not first:
                    self.skipTest("GitHub unreachable or rate-limited in this environment")

                cache_filename = os.path.join(tmp_dir, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME)
                with open(cache_filename) as f:
                    cache_after_first = json.load(f)
                gate_entry = cache_after_first.get(hed_cache.STANDARD_SCHEMA_HEAD_URL)
                self.assertIsInstance(gate_entry, dict, "expected the gate URL itself to be cached")
                gate_timestamp_before = gate_entry["timestamp"]

                hed_cache.get_available_hed_versions(repo_check_interval=3600)

                with open(cache_filename) as f:
                    cache_after_second = json.load(f)
                self.assertEqual(
                    cache_after_second[hed_cache.STANDARD_SCHEMA_HEAD_URL]["timestamp"],
                    gate_timestamp_before,
                    "a large repo_check_interval should have skipped re-checking the gate itself",
                )

    def test_load_schema_version_default_no_standard_raises(self):
        """Test that empty version with only library schemas raises HedFileError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Copy only a library schema into the temp directory (no standard schemas)
            src = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../hed/schema/schema_data/HED_score_1.0.0.xml"
            )
            shutil.copy(src, tmp_dir)

            with self.assertRaises(HedFileError) as context:
                load_schema_version("", xml_folder=tmp_dir)
            self.assertEqual(context.exception.args[0], "BAD_PARAMETERS")
            self.assertIn("No version specified", str(context.exception))

    def test_load_and_verify_tags(self):
        # Load 'testlib' by itself
        testlib = load_schema_version("testlib_2.1.0")

        # Load 'score' by itself
        score = load_schema_version("score_2.1.0")

        # Load both 'testlib' and 'score' together
        schemas3 = load_schema_version(["testlib_2.1.0", "score_2.1.0"])

        # Extract the tag names from each library
        testlib_tags = set(testlib.tags.all_names.keys())
        score_tags = set(score.tags.all_names.keys())
        merged_tags = set(schemas3.tags.all_names.keys())

        # Verify that all tags in 'testlib' and 'score' are in the merged library
        for tag in testlib_tags:
            self.assertIn(tag, merged_tags, f"Tag {tag} from testlib is missing in the merged schema.")

        for tag in score_tags:
            self.assertIn(tag, merged_tags, f"Tag {tag} from score is missing in the merged schema.")

        # Negative test cases
        # Ensure merged_tags is not a subset of testlib_tags or score_tags
        self.assertFalse(merged_tags.issubset(testlib_tags), "The merged tags should not be a subset of testlib tags.")
        self.assertFalse(merged_tags.issubset(score_tags), "The merged tags should not be a subset of score tags.")

        # Ensure there are tags that came uniquely from each library
        unique_testlib_tags = testlib_tags - score_tags
        unique_score_tags = score_tags - testlib_tags

        self.assertTrue(
            any(tag in merged_tags for tag in unique_testlib_tags),
            "There should be unique tags from testlib in the merged schema.",
        )
        self.assertTrue(
            any(tag in merged_tags for tag in unique_score_tags),
            "There should be unique tags from score in the merged schema.",
        )

    def test_load_schema_version_libraries(self):
        ver1 = "score_1.0.0"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version_number, "1.0.0", "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no namespace")
        self.assertEqual(
            schemas1.get_formatted_version(),
            '"score_1.0.0"',
            "load_schema_version gives correct version_string with single library no namespace",
        )

        ver2 = "base:score_1.0.0"
        schemas2 = load_schema_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertEqual(schemas2.version_number, "1.0.0", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas2._namespace, "base:", "load_schema_version has the right version with namespace")
        self.assertEqual(
            schemas2.get_formatted_version(),
            '"base:score_1.0.0"',
            "load_schema_version gives correct version_string with single library with namespace",
        )
        self.assertEqual(schemas2.name, "base:score_1.0.0")
        ver3 = ["8.0.0", "sc:score_1.0.0"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchemaGroup, "load_schema_version returns HedSchema version+namespace")
        self.assertIsInstance(schemas3._schemas, dict, "load_schema_version group keeps dictionary of HED versions")
        self.assertEqual(len(schemas3._schemas), 2, "load_schema_version group dictionary is right length")
        self.assertEqual(schemas3.name, "8.0.0,sc:score_1.0.0")
        s = schemas3._schemas[""]
        self.assertEqual(s.version_number, "8.0.0", "load_schema_version has the right version with namespace")
        self.assertEqual(
            schemas3.get_formatted_version(),
            '["8.0.0", "sc:score_1.0.0"]',
            "load_schema_version gives correct version_string with single library with namespace",
        )
        formatted_list = schemas3.get_formatted_version()
        schemas4 = load_schema_version(formatted_list)
        self.assertIsInstance(schemas4, HedSchemaGroup, "load_schema_version returns HedSchema version+namespace")
        self.assertIsInstance(schemas4._schemas, dict, "load_schema_version group keeps dictionary of HED versions")
        self.assertEqual(len(schemas4._schemas), 2, "load_schema_version group dictionary is right length")
        self.assertEqual(
            schemas4.get_formatted_version(),
            '["8.0.0", "sc:score_1.0.0"]',
            "load_schema_version gives correct version_string with multiple prefixes",
        )
        self.assertEqual(schemas4.name, "8.0.0,sc:score_1.0.0")
        s = schemas4._schemas["sc:"]
        self.assertEqual(s.version_number, "1.0.0", "load_schema_version has the right version with namespace")
        with self.assertRaises(KeyError) as context:
            schemas4._schemas["ts:"]
        self.assertEqual(context.exception.args[0], "ts:")

        with self.assertRaises(HedFileError) as context:
            load_schema_version("[Malformed,,json]")

        # Invalid prefix
        with self.assertRaises(HedFileError) as context:
            load_schema_version("sc1:score_1.0.0")

        with self.assertRaises(HedFileError) as context:
            load_schema_version("sc1:")


class TestHedSchemaUnmerged(unittest.TestCase):
    # Verify the HED cache can handle loading unmerged with_standard schemas in case they are ever used
    @classmethod
    def setUpClass(cls):
        hed_cache_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../schema_cache_test_local_unmerged/"
        )
        if os.path.exists(hed_cache_dir) and os.path.isdir(hed_cache_dir):
            shutil.rmtree(hed_cache_dir)
        _load_schema_version.cache_clear()
        cls.hed_cache_dir = hed_cache_dir
        cls.saved_cache_folder = hed_cache.HED_CACHE_DIRECTORY
        schema.set_cache_directory(cls.hed_cache_dir)

        # Copy source as dupe into cache for easily testing dupe detection
        cls.dupe_library_name = "testscoredupe_1.1.0"
        cls.source_library_name = "score_1.1.0"

        for filename in os.listdir(hed_cache.INSTALLED_CACHE_LOCATION):
            final_filename = os.path.join(hed_cache.INSTALLED_CACHE_LOCATION, filename)
            if os.path.isdir(final_filename):
                continue
            loaded_schema = schema.load_schema(final_filename)
            loaded_schema.save_as_xml(os.path.join(cls.hed_cache_dir, filename), save_merged=False)
            if filename == f"HED_{cls.source_library_name}.xml":
                new_filename = f"HED_{cls.dupe_library_name}.xml"
                loaded_schema.save_as_xml(os.path.join(cls.hed_cache_dir, new_filename), save_merged=False)

        # Also copy testlib schemas from spec_tests/hed-schemas if available for testing library merging
        testlib_spec_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../../spec_tests/hed-schemas/library_schemas/testlib"
        )
        if os.path.exists(testlib_spec_path):
            for root, _dirs, files in os.walk(testlib_spec_path):
                for filename in files:
                    if filename.endswith(".xml"):
                        testlib_file = os.path.join(root, filename)
                        try:
                            loaded_schema = schema.load_schema(testlib_file)
                            loaded_schema.save_as_xml(os.path.join(cls.hed_cache_dir, filename), save_merged=False)
                        except Exception:
                            # Skip if there's an issue loading this particular testlib schema
                            pass

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.hed_cache_dir)
        schema.set_cache_directory(cls.saved_cache_folder)
        _load_schema_version.cache_clear()

    def test_load_schema_version(self):
        ver1 = "8.0.0"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version_number, "8.0.0", "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "", "load_schema_version standard schema has no library")
        ver2 = "base:8.0.0"
        schemas2 = load_schema_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertEqual(schemas2.version_number, "8.0.0", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas2._namespace, "base:", "load_schema_version has the right version with namespace")
        ver3 = ["base:8.0.0"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertEqual(schemas3.version_number, "8.0.0", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas3._namespace, "base:", "load_schema_version has the right version with namespace")

    def test_load_schema_version_merged(self):
        ver4 = ["testlib_2.1.0", "score_2.1.0"]
        schemas3 = load_schema_version(ver4)
        issues = schemas3.check_compliance()
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertTrue(schemas3.version_number, "load_schema_version has the right version with namespace")
        self.assertEqual(schemas3._namespace, "", "load_schema_version has the right version with namespace")
        self.assertEqual(len(issues), 31)

    def test_load_schema_version_merged_duplicates(self):
        ver4 = ["score_1.1.0", "testscoredupe_1.1.0"]
        with self.assertRaises(HedFileError) as context:
            load_schema_version(ver4)
        self.assertEqual(len(context.exception.issues), 597)

    def test_load_and_verify_tags(self):
        # Load 'testlib' by itself
        testlib = load_schema_version("testlib_2.1.0")

        # Load 'score' by itself
        score = load_schema_version("score_2.1.0")

        # Load both 'testlib' and 'score' together
        schemas3 = load_schema_version(["testlib_2.1.0", "score_2.1.0"])

        # Extract the tag names from each library
        testlib_tags = set(testlib.tags.all_names.keys())
        score_tags = set(score.tags.all_names.keys())
        merged_tags = set(schemas3.tags.all_names.keys())

        # Verify that all tags in 'testlib' and 'score' are in the merged library
        for tag in testlib_tags:
            self.assertIn(tag, merged_tags, f"Tag {tag} from testlib is missing in the merged schema.")

        for tag in score_tags:
            self.assertIn(tag, merged_tags, f"Tag {tag} from score is missing in the merged schema.")

        # Negative test cases
        # Ensure merged_tags is not a subset of testlib_tags or score_tags
        self.assertFalse(merged_tags.issubset(testlib_tags), "The merged tags should not be a subset of testlib tags.")
        self.assertFalse(merged_tags.issubset(score_tags), "The merged tags should not be a subset of score tags.")

        # Ensure there are tags that came uniquely from each library
        unique_testlib_tags = testlib_tags - score_tags
        unique_score_tags = score_tags - testlib_tags

        self.assertTrue(
            any(tag in merged_tags for tag in unique_testlib_tags),
            "There should be unique tags from testlib in the merged schema.",
        )
        self.assertTrue(
            any(tag in merged_tags for tag in unique_score_tags),
            "There should be unique tags from score in the merged schema.",
        )


class TestHedSchemaMerging(unittest.TestCase):
    # Verify all 5 schemas produce the same results
    base_schema_dir = "../data/schema_tests/merge_tests/"

    @classmethod
    def setUpClass(cls):
        cls.full_base_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.base_schema_dir)

    def _base_merging_test(self, files):
        import filecmp

        loaded_schema = []
        for filename in files:
            loaded_schema.append(load_schema(os.path.join(self.full_base_folder, filename)))
        for save_merged in [True, False]:
            for i in range(len(files) - 1):
                s1 = loaded_schema[i]
                s2 = loaded_schema[i + 1]
                self.assertEqual(s1, s2, "Loaded schemas are not equal.")
                filename1 = get_temp_filename(".xml")
                filename2 = get_temp_filename(".xml")
                try:
                    s1.save_as_xml(filename1, save_merged=save_merged)
                    s2.save_as_xml(filename2, save_merged=save_merged)
                    result = filecmp.cmp(filename1, filename2)

                    # print(i, files[i], s1.filename)
                    # print(files[i+1], s2.filename)
                    self.assertTrue(result, f"Saved xml {files[i]} and {files[i + 1]} are not equal.")
                    reload1 = load_schema(filename1)
                    reload2 = load_schema(filename2)
                    self.assertEqual(reload1, reload2, f"Reloaded xml {files[i]} and {files[i + 1]} are not equal.")
                except Exception as ex:
                    print(ex)
                    self.assertTrue(False)
                finally:
                    os.remove(filename1)
                    os.remove(filename2)

                try:
                    filename1 = get_temp_filename(".mediawiki")
                    filename2 = get_temp_filename(".mediawiki")
                    s1.save_as_mediawiki(filename1, save_merged=save_merged)
                    s2.save_as_mediawiki(filename2, save_merged=save_merged)
                    result = filecmp.cmp(filename1, filename2)
                    self.assertTrue(result, f"Saved wiki {files[i]} and {files[i + 1]} are not equal.")

                    reload1 = load_schema(filename1)
                    reload2 = load_schema(filename2)
                    self.assertEqual(reload1, reload2, f"Reloaded wiki {files[i]} and {files[i + 1]} are not equal.")
                except Exception as ex:
                    print(ex)
                    self.assertTrue(False)
                finally:
                    os.remove(filename1)
                    os.remove(filename2)

                lines1 = s1.get_as_mediawiki_string(save_merged=save_merged)
                lines2 = s2.get_as_mediawiki_string(save_merged=save_merged)
                self.assertEqual(lines1, lines2, f"Mediawiki string {files[i]} and {files[i + 1]} are not equal.")

                lines1 = s1.get_as_xml_string(save_merged=save_merged)
                lines2 = s2.get_as_xml_string(save_merged=save_merged)
                self.assertEqual(lines1, lines2, f"XML string {files[i]} and {files[i + 1]} are not equal.")

    def test_saving_merged(self):
        files = [
            "HED_score_1.1.0.mediawiki",
            "HED_score_unmerged.mediawiki",
            "HED_score_merged.mediawiki",
            "HED_score_merged.xml",
            "HED_score_unmerged.xml",
        ]

        self._base_merging_test(files)

    def test_saving_merged_rooted(self):
        files = ["basic_root.mediawiki", "basic_root.xml"]
        self._base_merging_test(files)

    def test_saving_merged_rooted_sorting(self):
        files = ["sorted_root.mediawiki", "sorted_root_merged.xml"]
        self._base_merging_test(files)

    @with_temp_file(".mediawiki")
    def test_saving_bad_sort(self, filename):
        loaded_schema = load_schema(os.path.join(self.full_base_folder, "bad_sort_test.mediawiki"))
        loaded_schema.save_as_mediawiki(filename)
        reloaded_schema = load_schema(filename)

        self.assertEqual(loaded_schema, reloaded_schema)

    def _base_added_class_tests(self, schema):
        tag_entry = schema.tags["Modulator"]
        self.assertEqual(tag_entry.attributes["suggestedTag"], "Event")

        tag_entry = schema.tags["Sleep-modulator"]
        self.assertEqual(tag_entry.attributes["relatedTag"], "Sensory-event")

        unit_class_entry = schema.unit_classes["weightUnits"]
        unit_entry = unit_class_entry.units["testUnit"]
        self.assertEqual(unit_entry.attributes[HedKey.ConversionFactor], str(100))

        unit_modifier_entry = schema.unit_modifiers["huge"]
        self.assertEqual(unit_modifier_entry.attributes[HedKey.ConversionFactor], "10^100")
        self.assertTrue(unit_modifier_entry.attributes["customElementAttribute"])

        value_class_entry = schema.value_classes["customValueClass"]
        self.assertEqual(value_class_entry.attributes["customAttribute"], "test_attribute_value")

        attribute_entry = schema.attributes["customAttribute"]
        self.assertTrue(attribute_entry.attributes["valueClassProperty"])

        attribute_entry = schema.attributes["customElementAttribute"]
        self.assertTrue(attribute_entry.attributes["elementProperty"])
        self.assertTrue(attribute_entry.attributes["boolProperty"])

        prop_entry = schema.properties["customProperty"]
        self.assertEqual(prop_entry.attributes["inLibrary"], "score")
        self.assertTrue(prop_entry.attributes["customElementAttribute"])

        for section in schema._sections.values():
            self.assertTrue("customElementAttribute" in section.valid_attributes)

        # Only check for non-character-invalid issues (SCORE prologue/epilogue has commas/brackets)
        issues = schema.check_compliance()
        non_char_issues = [i for i in issues if i["code"] != "SCHEMA_CHARACTER_INVALID"]
        self.assertFalse(non_char_issues)

    def test_saving_merged2(self):
        s1 = load_schema(os.path.join(self.full_base_folder, "add_all_types.mediawiki"))
        self._base_added_class_tests(s1)
        for save_merged in [True, False]:
            path1 = get_temp_filename(".xml")
            path2 = get_temp_filename(".mediawiki")
            try:
                s1.save_as_xml(path1, save_merged=save_merged)
                s2 = load_schema(path1)
                self.assertEqual(s1, s2)
                self._base_added_class_tests(s2)

                s1.save_as_mediawiki(path2, save_merged=save_merged)
                s2 = load_schema(path2)
                self.assertEqual(s1, s2)
                self._base_added_class_tests(s2)
            finally:
                os.remove(path1)
                os.remove(path2)

    def test_bad_schemas(self):
        """These should all have one SCHEMA_DUPLICATE_NODE issue"""
        files = [
            load_schema(os.path.join(self.full_base_folder, "issues_tests/overlapping_tags1.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "issues_tests/overlapping_tags2.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "issues_tests/overlapping_tags3.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "issues_tests/overlapping_tags4.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "issues_tests/overlapping_unit_classes.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "issues_tests/overlapping_units.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "issues_tests/HED_dupesubroot_0.0.1.mediawiki")),
        ]
        expected_code = [
            HedExceptions.SCHEMA_LIBRARY_INVALID,
            HedExceptions.SCHEMA_LIBRARY_INVALID,
            HedExceptions.SCHEMA_LIBRARY_INVALID,
            HedExceptions.SCHEMA_LIBRARY_INVALID,
            HedExceptions.SCHEMA_LIBRARY_INVALID,
            HedExceptions.SCHEMA_LIBRARY_INVALID,
            SchemaErrors.SCHEMA_DUPLICATE_NODE,
        ]
        for schema1, expected in zip(files, expected_code, strict=False):
            issues = schema1.check_compliance()
            issue_codes = [i["code"] for i in issues]
            self.assertIn(expected, issue_codes)

    def test_cannot_load_schemas(self):
        files = [
            os.path.join(self.full_base_folder, "issues_tests/HED_badroot_0.0.1.mediawiki"),
            os.path.join(self.full_base_folder, "issues_tests/HED_root_wrong_place_0.0.1.mediawiki"),
            os.path.join(self.full_base_folder, "issues_tests/HED_root_invalid1.mediawiki"),
            os.path.join(self.full_base_folder, "issues_tests/HED_root_invalid2.mediawiki"),
            os.path.join(self.full_base_folder, "issues_tests/HED_root_invalid3.mediawiki"),
        ]
        for file in files:
            with self.assertRaises(HedFileError) as context:
                load_schema(file)
            self.assertEqual(context.exception.code, HedExceptions.SCHEMA_LIBRARY_INVALID)

    def test_rooted_tag_not_in_standard_schema(self):
        # HED_badroot_0.0.1.mediawiki has rooted=AlsoNotRealTag which does not exist in the standard schema.
        # This should raise SCHEMA_LIBRARY_INVALID (not LIBRARY_SCHEMA_INVALID).
        bad_root_file = os.path.join(self.full_base_folder, "issues_tests/HED_badroot_0.0.1.mediawiki")
        with self.assertRaises(HedFileError) as context:
            load_schema(bad_root_file)
        self.assertEqual(context.exception.code, HedExceptions.SCHEMA_LIBRARY_INVALID)
        issue_codes = [issue.get("code") for issue in context.exception.issues]
        self.assertIn(HedExceptions.SCHEMA_LIBRARY_INVALID, issue_codes)

    def test_saving_in_library_wiki(self):
        old_score_schema = load_schema_version("score_1.0.0")

        tag_entry = old_score_schema.get_tag_entry("Modulator")
        self.assertTrue(tag_entry.has_attribute(HedKey.InLibrary))

        schema_string = old_score_schema.get_as_mediawiki_string()
        score_count = schema_string.count("inLibrary=score")
        self.assertEqual(score_count, 0, "InLibrary should not be saved to the file")

        # This should make no difference
        schema_string = old_score_schema.get_as_mediawiki_string(save_merged=True)
        score_count = schema_string.count("inLibrary=score")
        self.assertEqual(score_count, 0, "InLibrary should not be saved to the file")

        score_schema = load_schema_version("score_1.1.0")

        tag_entry = score_schema.get_tag_entry("Modulator")
        self.assertTrue(tag_entry.has_attribute(HedKey.InLibrary))
        schema_string = score_schema.get_as_mediawiki_string(save_merged=False)
        score_count = schema_string.count("inLibrary=score")
        self.assertEqual(score_count, 0, "InLibrary should not be saved to the file")

        schema_string = score_schema.get_as_mediawiki_string(save_merged=True)
        score_count = schema_string.count("inLibrary=score")
        self.assertEqual(score_count, 853, "There should be 853 in library entries in the saved score schema")

    def test_saving_in_library_xml(self):
        old_score_schema = load_schema_version("score_1.0.0")

        tag_entry = old_score_schema.get_tag_entry("Modulator")
        self.assertTrue(tag_entry.has_attribute(HedKey.InLibrary))

        schema_string = old_score_schema.get_as_xml_string()
        score_count = schema_string.count("<name>inLibrary</name>")
        self.assertEqual(score_count, 0, "InLibrary should not be saved to the file")

        # This should make no difference
        schema_string = old_score_schema.get_as_xml_string(save_merged=True)
        score_count = schema_string.count("<name>inLibrary</name>")
        self.assertEqual(score_count, 0, "InLibrary should not be saved to the file")

        score_schema = load_schema_version("score_1.1.0")

        tag_entry = score_schema.get_tag_entry("Modulator")
        self.assertTrue(tag_entry.has_attribute(HedKey.InLibrary))
        schema_string = score_schema.get_as_xml_string(save_merged=False)
        score_count = schema_string.count("<name>inLibrary</name>")
        self.assertEqual(score_count, 0, "InLibrary should not be saved to the file")

        schema_string = score_schema.get_as_xml_string(save_merged=True)
        score_count = schema_string.count("<name>inLibrary</name>")
        # One extra because this also finds the attribute definition, whereas in wiki it's a different format.
        self.assertEqual(score_count, 854, "There should be 854 in library entries in the saved score schema")

    def test_save_merged_raises_when_base_schema_unavailable(self):
        """Test that HedFileError is raised when saving merged output with non-existent base schema."""
        # Create a temporary schema file with a non-existent withStandard version.
        # The schema must be syntactically valid and marked as merged (no unmerged="True")
        # to trigger the save_merged code path in schema2base.
        # This validates the fail-fast behavior: when saving merged output, an exception is raised
        # immediately if the base schema cannot be loaded, preventing silent production of partial output.
        temp_schema_content = """HED version="1.1.0" library="score" withStandard="99.99.99"

'''Prologue'''
Test schema for exception handling.

!# start schema

'''Test-tag'''
* Test-subtag

!# end schema

'''Unit classes'''

'''Unit modifiers'''

'''Value classes'''

'''Schema attributes'''

'''Properties'''

'''Epilogue'''

!# end hed
"""
        temp_schema_file = get_temp_filename(".mediawiki")
        with open(temp_schema_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(temp_schema_content)

        try:
            # Load the schema successfully (it's syntactically valid and marked as merged)
            schema_obj = load_schema(temp_schema_file)

            # Attempting to save the merged schema should raise HedFileError because the base schema
            # version (99.99.99) doesn't exist. The fail-fast design in schema2base.__init__
            # intentionally does NOT wrap the load_schema_version() call in try/except, ensuring
            # this error is raised immediately rather than silently producing an incomplete output.
            with self.assertRaises(HedFileError):
                schema_obj.get_as_mediawiki_string(save_merged=True)
        finally:
            # Clean up the temporary schema file
            if os.path.exists(temp_schema_file):
                os.remove(temp_schema_file)


class TestParseVersionList(unittest.TestCase):
    def test_empty_and_single_library(self):
        """Test that an empty list returns an empty dictionary and a single library is handled correctly."""
        self.assertEqual(parse_version_list([]), {})
        self.assertEqual(parse_version_list(["score"]), {"": "score"})

    def test_multiple_libraries_without_and_with_prefix(self):
        """Test that multiple libraries without a prefix and with the same prefix are handled correctly."""
        self.assertEqual(parse_version_list(["score", "testlib"]), {"": "score,testlib"})
        self.assertEqual(parse_version_list(["test:score", "test:testlib"]), {"test": "test:score,testlib"})

    def test_single_and_multiple_libraries_with_different_prefixes(self):
        """Test a single library with a prefix and multiple libraries with different prefixes are handled correctly."""
        self.assertEqual(parse_version_list(["ol:otherlib"]), {"ol": "ol:otherlib"})
        self.assertEqual(
            parse_version_list(["score", "ol:otherlib", "ul:anotherlib"]),
            {"": "score", "ol": "ol:otherlib", "ul": "ul:anotherlib"},
        )

    def test_duplicate_library_raises_error(self):
        """Test that duplicate libraries raise the correct error."""
        with self.assertRaises(HedFileError):
            parse_version_list(["score", "score"])
        with self.assertRaises(HedFileError):
            parse_version_list(["ol:otherlib", "ol:otherlib"])

    def test_triple_prefixes(self):
        """Test that libraries with triple prefixes are handled correctly."""
        self.assertEqual(
            parse_version_list(["test:score", "ol:otherlib", "test:testlib", "abc:anotherlib"]),
            {"test": "test:score,testlib", "ol": "ol:otherlib", "abc": "abc:anotherlib"},
        )


class TestPrereleaseSchemaLoading(unittest.TestCase):
    """Test that prerelease schemas are always found and loaded correctly.

    Prerelease schemas are now always included in version lookups — there is
    no opt-in flag.  These tests verify that both regular and prerelease
    schemas load successfully from a local xml_folder that mirrors the
    cache layout (regular schemas at the root, prerelease schemas under
    ``prerelease/``).
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.schema_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/")

    def test_load_regular_schema(self):
        """Test that a regular schema loads correctly."""
        schema = load_schema_version("8.2.0", xml_folder=self.schema_dir)
        self.assertIsInstance(schema, HedSchema)
        self.assertEqual(schema.version_number, "8.2.0")

    def test_load_regular_schema_with_namespace(self):
        """Test that a regular schema loads with a namespace prefix."""
        schema = load_schema_version("test:8.2.0", xml_folder=self.schema_dir)
        self.assertIsInstance(schema, HedSchema)
        self.assertEqual(schema._namespace, "test:")
        self.assertEqual(schema.version_number, "8.2.0")

    def test_nonexistent_version_error(self):
        """Test that a nonexistent version raises HedFileError."""
        with self.assertRaises(HedFileError) as context:
            load_schema_version("99.99.99", xml_folder=self.schema_dir)
        self.assertIn("not found", str(context.exception).lower())

    def test_load_prerelease_schema(self):
        """Test loading a schema that exists only in the prerelease directory."""
        schema = load_schema_version("8.3.0", xml_folder=self.schema_dir)
        self.assertIsInstance(schema, HedSchema)
        self.assertEqual(schema.version_number, "8.3.0")
        self.assertIn("event", schema.tags.all_names)

    def test_load_prerelease_library(self):
        """Test loading a prerelease library schema."""
        schema = load_schema_version("testliba_2.1.0", xml_folder=self.schema_dir)
        self.assertIsInstance(schema, HedSchema)
        self.assertEqual(schema.version_number, "2.1.0")
        self.assertEqual(schema.library, "testliba")
        self.assertIn("prerelease-item", schema.tags.all_names)

    def test_mixed_regular_and_prerelease_schemas(self):
        """Test loading a mix of regular and prerelease schemas with different namespaces."""
        schemas = load_schema_version(["base:8.2.0", "test:testlib_2.1.0"], xml_folder=self.schema_dir)
        self.assertIsInstance(schemas, HedSchemaGroup)
        self.assertEqual(len(schemas._schemas), 2)
        self.assertIn("base:", schemas._schemas)
        self.assertIn("test:", schemas._schemas)


class TestLoadSchemaWithPrereleasePartner(unittest.TestCase):
    """Test that withStandard partner resolution works when the standard schema
    exists only in the prerelease subdirectory of the cache.

    Background
    ----------
    A library schema with ``withStandard="X.Y.Z"`` and ``unmerged="True"`` is a *partnered*
    schema: when loaded, the loader automatically calls ``load_schema_version("X.Y.Z")``
    to fetch the standard schema and merge the library's tags on top of it.

    Since prerelease schemas are now always included in version lookups, these tests
    verify that a prerelease standard schema is found and merged correctly without
    any special flag.

    Fixture design
    --------------
    Source files are kept as human-editable MediaWiki so they are easy to update:

      tests/data/schema_tests/prerelease/HED9.9.9.mediawiki
          A minimal standard schema at version 9.9.9 that exists *only* in the
          prerelease subdirectory.

      tests/data/schema_tests/prerelease/HED_testpre_1.0.0.mediawiki
          A minimal library schema with ``library="testpre"``, ``version="1.0.0"``,
          ``withStandard="9.9.9"``, and ``unmerged="True"``.

    Cache isolation
    ---------------
    A temporary directory is used as the cache root with the standard schema only
    in the ``prerelease/`` subdirectory.  ``HED_CACHE_DIRECTORY`` is patched per-test
    and the LRU cache is cleared in setUp/tearDown.
    """

    @classmethod
    def setUpClass(cls):
        """Build the synthetic cache directory used by all tests in this class."""
        fixture_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests")

        cls.lib_schema_path = os.path.join(fixture_dir, "prerelease", "HED_testpre_1.0.0.mediawiki")

        standard_wiki_path = os.path.join(fixture_dir, "prerelease", "HED9.9.9.mediawiki")
        standard_schema = load_schema(standard_wiki_path)
        xml_string = standard_schema.get_as_xml_string()

        cls._tmpdir = tempfile.TemporaryDirectory()
        prerelease_dir = os.path.join(cls._tmpdir.name, "prerelease")
        os.makedirs(prerelease_dir)
        with open(os.path.join(prerelease_dir, "HED9.9.9.xml"), "w") as f:
            f.write(xml_string)

        cls._cache_dir = cls._tmpdir.name

    @classmethod
    def tearDownClass(cls):
        """Remove the temp dir and ensure no patched cache entries remain."""
        _load_schema_version.cache_clear()
        cls._tmpdir.cleanup()

    def setUp(self):
        _load_schema_version.cache_clear()

    def tearDown(self):
        _load_schema_version.cache_clear()

    # ------------------------------------------------------------------
    # load_schema() tests
    # ------------------------------------------------------------------

    def test_load_schema_prerelease_partner(self):
        """load_schema() resolves a withStandard partner in the prerelease subdirectory."""
        with patch.object(hed_cache, "HED_CACHE_DIRECTORY", self._cache_dir):
            result = load_schema(self.lib_schema_path)
        self.assertIsInstance(result, HedSchema)
        self.assertEqual(result.library, "testpre")
        self.assertIn("prerelease-partner-only-item", result.tags.all_names)

    # ------------------------------------------------------------------
    # from_string() tests
    # ------------------------------------------------------------------

    def test_from_string_prerelease_partner(self):
        """from_string() resolves a withStandard partner in the prerelease subdirectory."""
        with open(self.lib_schema_path) as f:
            schema_str = f.read()
        with patch.object(hed_cache, "HED_CACHE_DIRECTORY", self._cache_dir):
            result = from_string(schema_str, schema_format=".mediawiki")
        self.assertIsInstance(result, HedSchema)
        self.assertEqual(result.library, "testpre")
