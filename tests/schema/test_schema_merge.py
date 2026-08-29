"""Tests for combining partnered library schemas with their standard partner (schema_io.schema_merge)."""

import os
import shutil
import tempfile
import unittest

from hed import schema
from hed.errors import HedExceptions, HedFileError
from hed.schema import HedKey, hed_cache, load_schema, load_schema_version
from hed.schema.hed_schema_io import _load_schema_version
from hed.schema.schema_io.schema_merge import resolve_group
from hed.schema.schema_io.xml2schema import SchemaLoaderXML

FIXTURE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/schema_tests/merge_group_tests"))


class TestSingleLibraryMerge(unittest.TestCase):
    """An unmerged partnered library loads as library-only, then merges with one copy of its partner."""

    @classmethod
    def setUpClass(cls):
        # Point the cache at an empty folder so every partner must come from xml_folder (hermetic).
        cls.saved_cache_folder = hed_cache.HED_CACHE_DIRECTORY
        cls.empty_cache = tempfile.mkdtemp()
        schema.set_cache_directory(cls.empty_cache)
        _load_schema_version.cache_clear()
        cls.unmerged_path = os.path.join(FIXTURE_DIR, "HED_testconflict_2.0.0.xml")

    @classmethod
    def tearDownClass(cls):
        schema.set_cache_directory(cls.saved_cache_folder)
        _load_schema_version.cache_clear()
        shutil.rmtree(cls.empty_cache, ignore_errors=True)

    def test_loader_returns_library_only_schema(self):
        library_only = SchemaLoaderXML.load(self.unmerged_path)
        self.assertEqual(library_only.header_attributes.get("unmerged"), "True")
        self.assertEqual(library_only.with_standard, "8.5.0")
        self.assertFalse(library_only.merged)
        # Only the library's own elements, all stamped, rooted tag still at the root.
        self.assertLess(len(library_only.tags.all_entries), 30)
        self.assertTrue(all(HedKey.InLibrary in e.attributes for e in library_only.tags.all_entries))
        rooted = library_only.tags.get("Rooted-tag")
        self.assertEqual(rooted.long_tag_name, "Rooted-tag")
        self.assertEqual(rooted.attributes.get(HedKey.Rooted), "Event")
        self.assertIsNone(library_only.tags.get("Red"))

    def test_load_schema_combines_with_partner(self):
        loaded = load_schema(self.unmerged_path, xml_folder=FIXTURE_DIR)
        self.assertNotIn("unmerged", loaded.header_attributes)
        self.assertEqual(
            loaded.header_attributes, {"version": "2.0.0", "library": "testconflict", "withStandard": "8.5.0"}
        )
        self.assertTrue(loaded.merged)
        self.assertEqual(loaded.version, "testconflict_2.0.0")
        self.assertTrue(loaded.can_save())
        self.assertFalse(loaded.has_duplicates())
        # Standard content present, library content placed and stamped.
        self.assertIsNotNone(loaded.get_tag_entry("Red"))
        rooted = loaded.get_tag_entry("Event/Rooted-tag")
        self.assertEqual(rooted.attributes[HedKey.InLibrary], "testconflict")
        self.assertIs(rooted.parent, loaded.get_tag_entry("Event"))
        self.assertEqual(set(rooted.children), {"Rooted-one", "Rooted-two"})
        self.assertIsNotNone(loaded.get_tag_entry("Event/Rooted-tag/Rooted-one/Deep-one"))
        measure = loaded.get_tag_entry("Measure-tag")
        self.assertIsNotNone(measure.takes_value_child_entry)
        self.assertEqual(measure.takes_value_child_entry.attributes[HedKey.InLibrary], "testconflict")
        self.assertEqual(loaded.tags.get("Nested-item").long_tag_name, "Anchor-item/Nested-item")
        self.assertIn("testconflict 2.0.0 partners with", loaded.prologue)

    def test_unmerged_load_equals_merged_file_load(self):
        loaded = load_schema(self.unmerged_path, xml_folder=FIXTURE_DIR)
        merged_path = os.path.join(self.empty_cache, "HED_testconflict_2.0.0_merged.xml")
        loaded.save_as_xml(merged_path, save_merged=True)
        reloaded = load_schema(merged_path)
        self.assertTrue(reloaded.merged)
        self.assertEqual(loaded, reloaded)
        self.assertEqual(
            [e.long_tag_name for e in loaded.tags.all_entries if HedKey.InLibrary in e.attributes],
            [e.long_tag_name for e in reloaded.tags.all_entries if HedKey.InLibrary in e.attributes],
        )

    def test_load_schema_version_from_unmerged_folder(self):
        by_version = load_schema_version("testconflict_2.0.0", xml_folder=FIXTURE_DIR)
        by_path = load_schema(self.unmerged_path, xml_folder=FIXTURE_DIR)
        self.assertEqual(by_version, by_path)
        prefixed = load_schema_version("sc:testconflict_2.0.0", xml_folder=FIXTURE_DIR)
        self.assertEqual(prefixed.schema_namespace, "sc:")
        self.assertIsNotNone(prefixed.get_tag_entry("sc:Event/Rooted-tag", schema_namespace="sc:"))

    def test_partner_falls_back_to_cache(self):
        # xml_folder holds only the library; the partner is found in the (redirected) cache.
        library_only_dir = tempfile.mkdtemp()
        try:
            shutil.copy(self.unmerged_path, library_only_dir)
            shutil.copy(os.path.join(FIXTURE_DIR, "HED8.5.0.xml"), self.empty_cache)
            _load_schema_version.cache_clear()
            loaded = load_schema_version("testconflict_2.0.0", xml_folder=library_only_dir)
            self.assertIsNotNone(loaded.get_tag_entry("Event/Rooted-tag"))
        finally:
            os.remove(os.path.join(self.empty_cache, "HED8.5.0.xml"))
            _load_schema_version.cache_clear()
            shutil.rmtree(library_only_dir, ignore_errors=True)

    def test_partner_unavailable_is_library_invalid(self):
        # A partner version that exists nowhere (folder, cache, or GitHub) must surface as
        # SCHEMA_LIBRARY_INVALID, the code single-file loading has always used for this.
        library_only_dir = tempfile.mkdtemp()
        try:
            with open(self.unmerged_path, encoding="utf-8") as fp:
                text = fp.read().replace('withStandard="8.5.0"', 'withStandard="1.2.3"', 1)
            bad_partner_path = os.path.join(library_only_dir, "HED_testconflict_2.0.0.xml")
            with open(bad_partner_path, "w", encoding="utf-8") as fp:
                fp.write(text)
            with self.assertRaises(HedFileError) as context:
                load_schema(bad_partner_path, xml_folder=library_only_dir)
            self.assertEqual(context.exception.code, HedExceptions.SCHEMA_LIBRARY_INVALID)
            self.assertIn("1.2.3", context.exception.message)
        finally:
            shutil.rmtree(library_only_dir, ignore_errors=True)


class TestUnpartneredAndStandardUnchanged(unittest.TestCase):
    """Files without a partner are returned exactly as the loader produced them."""

    def test_unpartnered_library(self):
        loaded = load_schema(os.path.join(FIXTURE_DIR, "HED_testconflict_1.1.0.xml"))
        self.assertEqual(loaded.with_standard, "")
        self.assertEqual(loaded.library, "testconflict")
        self.assertIsNone(loaded.get_tag_entry("Red"))

    def test_standard_schema(self):
        loaded = load_schema(os.path.join(FIXTURE_DIR, "HED8.4.0.xml"))
        self.assertEqual(loaded.version, "8.4.0")
        self.assertIsNotNone(loaded.get_tag_entry("Red"))


class TestMergeGroups(unittest.TestCase):
    """Merge groups per spec 3.1.2.4, against the hed-tests libraries (unmerged form, hermetic folder)."""

    @classmethod
    def setUpClass(cls):
        cls.saved_cache_folder = hed_cache.HED_CACHE_DIRECTORY
        cls.empty_cache = tempfile.mkdtemp()
        schema.set_cache_directory(cls.empty_cache)
        _load_schema_version.cache_clear()

    @classmethod
    def tearDownClass(cls):
        schema.set_cache_directory(cls.saved_cache_folder)
        _load_schema_version.cache_clear()
        shutil.rmtree(cls.empty_cache, ignore_errors=True)

    def _load(self, versions):
        return load_schema_version(versions, xml_folder=FIXTURE_DIR)

    def _assert_fails(self, versions, code=HedExceptions.SCHEMA_LOAD_FAILED, mentions=()):
        with self.assertRaises(HedFileError) as context:
            self._load(versions)
        self.assertEqual(context.exception.code, code, context.exception.message)
        for text in mentions:
            self.assertIn(text, context.exception.message)
        return context.exception

    # Merge group rules
    def test_three_libraries_same_partner_load_in_any_order(self):
        forward = self._load(["testconflict_2.1.0", "testclash_1.0.0", "testminimal_2.1.0"])
        reverse = self._load(["testminimal_2.1.0", "testclash_1.0.0", "testconflict_2.1.0"])
        # Same vocabulary either way; only the header lists the libraries in listed order.
        self.assertEqual(forward._sections, reverse._sections)
        self.assertEqual(reverse.header_attributes["library"], "testminimal,testclash,testconflict")
        self.assertEqual(forward.header_attributes["version"], "2.1.0,1.0.0,2.1.0")
        self.assertEqual(forward.header_attributes["library"], "testconflict,testclash,testminimal")
        self.assertEqual(forward.with_standard, "8.5.0")
        self.assertTrue(forward.merged)
        self.assertFalse(forward.can_save())
        self.assertFalse(forward.has_duplicates())
        for tag in ("Red", "Object-one", "Clash-one", "Mini-one"):
            self.assertIsNotNone(forward.get_tag_entry(tag), tag)
        self.assertIn("testconflict 2.1.0", forward.prologue)

    def test_duplicate_version_ignored(self):
        twice = self._load(["testconflict_2.0.0", "testconflict_2.0.0"])
        self.assertEqual(twice, self._load(["testconflict_2.0.0"]))

    def test_two_versions_of_one_library_fail(self):
        self._assert_fails(["testconflict_2.0.0", "testconflict_2.1.0"], mentions=["testconflict", "2.0.0", "2.1.0"])
        self._assert_fails(["testconflict_2.1.0", "testconflict_2.1.1"])
        self._assert_fails(["8.4.0", "8.5.0"], mentions=["standard schema"])

    def test_namespaces_resolve_independently(self):
        group = self._load(["8.4.0", "sc:testconflict_2.1.0", "ts:testminimal_1.0.0"])
        self.assertEqual(sorted(group.valid_prefixes), ["", "sc:", "ts:"])
        self.assertIsNotNone(group.get_tag_entry("sc:Object-one", schema_namespace="sc:"))
        group2 = self._load(["8.5.0", "sc:8.4.0"])
        self.assertEqual(len(group2.valid_prefixes), 2)

    def test_rules_apply_inside_each_namespace(self):
        self._assert_fails(["8.5.0", "sc:testconflict_2.0.0", "sc:testminimal_2.0.0"], mentions=["8.4.0", "8.5.0"])

    # Standard partner rules
    def test_matching_standard_adds_nothing(self):
        alone = self._load(["testconflict_2.0.0"])
        self.assertEqual(self._load(["8.5.0", "testconflict_2.0.0"]), alone)
        self.assertEqual(self._load(["testconflict_2.0.0", "8.5.0"]), alone)

    def test_mismatching_standard_fails(self):
        self._assert_fails(["8.4.0", "testconflict_2.0.0"], mentions=["8.4.0", "8.5.0"])
        self._assert_fails(["testconflict_2.0.0", "8.4.0"])

    def test_different_partners_fail(self):
        self._assert_fails(["testconflict_2.0.0", "testminimal_2.0.0"], mentions=["different partners"])

    # Unpartnered rules
    def test_unpartnered_must_be_alone(self):
        self._assert_fails(["8.5.0", "testconflict_1.1.0"], mentions=["Unpartnered"])
        self._assert_fails(["ts:testconflict_1.1.2", "ts:testminimal_1.0.0"], mentions=["Unpartnered"])
        alone = self._load(["ts:testminimal_1.0.0"])
        self.assertEqual(alone.schema_namespace, "ts:")
        self.assertIsNone(alone.get_tag_entry("ts:Red", schema_namespace="ts:"))

    def test_missing_version_is_file_not_found(self):
        self._assert_fails(["8.5.0", "testconflict_99.0.0"], code=HedExceptions.FILE_NOT_FOUND)

    # Element compatibility
    def test_identical_shared_element_merges_with_both_libraries(self):
        merged = self._load(["testconflict_2.0.0", "testclash_1.0.0"])
        shared = merged.get_tag_entry("Shared-item")
        self.assertEqual(shared.attributes[HedKey.InLibrary], "testconflict,testclash")
        self.assertEqual(len([e for e in merged.tags.all_entries if e.short_tag_name == "Shared-item"]), 1)
        self.assertFalse(merged.has_duplicates())
        codes = {issue["code"] for issue in merged.check_compliance()}
        self.assertNotIn("SCHEMA_IN_LIBRARY_INVALID", codes)

    def test_element_conflicts_fail_with_the_element_named(self):
        cases = {
            "testclash_2.0.0": ("Attribute-item", "attributes differ"),
            "testclash_3.0.0": ("Description-item", "description differs"),
            "testclash_4.0.0": ("Nested-item", "ancestor path differs"),
            "testclash_5.0.0": ("Placeholder-item", "'#' child"),
            "testclash_6.0.0": ("Rooted-tag", "ancestor path differs"),
            "testclash_7.0.0": ("Rooted-tag", "ancestor path differs"),
            "testclash_9.0.0": ("Rooted-one", "description differs"),
            "testclash_12.0.0": ("Deep-one", "description differs"),
        }
        for clash, (element, reason) in cases.items():
            with self.subTest(clash=clash):
                error = self._assert_fails(["testconflict_2.0.0", clash])
                self.assertTrue(error.issues, "issues list should name the element")
                self.assertIn(element, error.issues[0]["message"])
                self.assertIn(reason, error.issues[0]["message"])
                # Order independence of the outcome
                self._assert_fails([clash, "testconflict_2.0.0"])

    def test_shared_hierarchy_with_different_children(self):
        merged = self._load(["testconflict_2.0.0", "testclash_8.0.0"])
        rooted = merged.get_tag_entry("Event/Rooted-tag")
        self.assertEqual(rooted.attributes[HedKey.InLibrary], "testconflict,testclash")
        self.assertEqual(set(rooted.children), {"Rooted-one", "Rooted-two", "Rooted-three"})
        self.assertEqual(rooted.children["Rooted-one"].attributes[HedKey.InLibrary], "testconflict,testclash")
        self.assertEqual(set(rooted.children["Rooted-one"].children), {"Deep-one"})
        disjoint = self._load(["testconflict_2.0.0", "testclash_10.0.0"])
        self.assertEqual(
            set(disjoint.get_tag_entry("Event/Rooted-tag").children), {"Rooted-one", "Rooted-two", "Rooted-four"}
        )
        grandchildren = self._load(["testconflict_2.0.0", "testclash_11.0.0"])
        self.assertEqual(
            set(grandchildren.get_tag_entry("Event/Rooted-tag/Rooted-one").children), {"Deep-one", "Deep-two"}
        )

    # Load order
    def test_merged_member_is_the_base(self):
        # Save one library in merged form; a group containing it must build on that file rather
        # than on a separate copy of the standard.
        folder = tempfile.mkdtemp()
        try:
            merged_path = os.path.join(folder, "HED_testconflict_2.0.0.xml")
            self._load(["testconflict_2.0.0"]).save_as_xml(merged_path, save_merged=True)
            shutil.copy(os.path.join(FIXTURE_DIR, "HED_testclash_8.0.0.xml"), folder)
            loaders = [
                SchemaLoaderXML(os.path.join(folder, "HED_testclash_8.0.0.xml")),
                SchemaLoaderXML(merged_path),
            ]
            spec = resolve_group(loaders)
            self.assertEqual(spec.partner, "8.5.0")
            self.assertIs(spec.base, loaders[1])
            self.assertEqual([m.schema.library for m in spec.members], ["testclash", "testconflict"])
            _load_schema_version.cache_clear()
            from_folder = load_schema_version(["testclash_8.0.0", "testconflict_2.0.0"], xml_folder=folder)
            from_fixtures = self._load(["testclash_8.0.0", "testconflict_2.0.0"])
            self.assertEqual(from_folder, from_fixtures)
            # The standard was never needed from the cache or the folder: no HED8.5.0.xml exists in either.
            self.assertFalse(os.path.exists(os.path.join(folder, "HED8.5.0.xml")))
        finally:
            _load_schema_version.cache_clear()
            shutil.rmtree(folder, ignore_errors=True)

    def test_prepass_fails_before_parsing_bodies(self):
        loaders = [
            SchemaLoaderXML(os.path.join(FIXTURE_DIR, "HED_testconflict_2.0.0.xml")),
            SchemaLoaderXML(os.path.join(FIXTURE_DIR, "HED_testminimal_2.0.0.xml")),
        ]
        with self.assertRaises(HedFileError) as context:
            resolve_group(loaders, name="group")
        self.assertEqual(context.exception.code, HedExceptions.SCHEMA_LOAD_FAILED)
        self.assertEqual(len(context.exception.issues), 1)
        # Nothing was parsed: the loaders still hold only their headers.
        for loader in loaders:
            self.assertEqual(len(loader.schema.tags.all_entries), 0)


if __name__ == "__main__":
    unittest.main()
