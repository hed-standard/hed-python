import contextlib
import copy
import io
import os
import shutil
import tempfile
import unittest

from hed import load_schema, load_schema_version
from hed.errors import HedFileError
from hed.schema import HedKey
from hed.scripts.add_hed_ids import main
from hed.scripts.schema_script_util import get_prerelease_path

SCHEMA_TESTS = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests")


class TestAddHedIds(unittest.TestCase):
    """hed_add_ids on a hed-schemas style checkout, built in a temporary folder."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="hed_add_ids_")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _prerelease(self, library, version):
        folder = os.path.join(self.repo, "library_schemas", library, "prerelease")
        os.makedirs(folder)
        return os.path.join(folder, f"HED_{library}_{version}")

    def test_missing_tsv_set_fails(self):
        # A prerelease with only the mediawiki: the TSV set that carries the ids is absent.
        basename = self._prerelease("score", "1.1.0")
        shutil.copy(os.path.join(SCHEMA_TESTS, "merge_tests", "HED_score_unmerged.mediawiki"), basename + ".mediawiki")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([self.repo, "score", "1.1.0"])
        self.assertEqual(result, 1)
        expected = get_prerelease_path(self.repo, "score", "1.1.0")
        self.assertIn(expected, output.getvalue())
        self.assertIn("hed_update_schemas", output.getvalue())

    def test_empty_tsv_folder_fails(self):
        # The hedtsv/<name> folder exists but holds no TSV files: still no TSV set.
        basename = self._prerelease("score", "1.1.0")
        shutil.copy(os.path.join(SCHEMA_TESTS, "merge_tests", "HED_score_unmerged.mediawiki"), basename + ".mediawiki")
        os.makedirs(get_prerelease_path(self.repo, "score", "1.1.0"))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([self.repo, "score", "1.1.0"])
        self.assertEqual(result, 1)
        self.assertIn("No prerelease TSV set", output.getvalue())

    def test_unregistered_library_raises(self):
        # testlocal has no id_range in hed-schemas library_data.json, so no id can be assigned.
        schema = load_schema(os.path.join(SCHEMA_TESTS, "HED_testlocal_2.1.0.xml"))
        basename = self._prerelease("testlocal", "2.1.0")
        schema.save_as_mediawiki(basename + ".mediawiki")
        schema.save_as_dataframes(os.path.join(os.path.dirname(basename), "hedtsv", os.path.basename(basename)))
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(HedFileError) as context:
            main([self.repo, "testlocal", "2.1.0"])
        self.assertIn("library_data.json", context.exception.message)
        self.assertIn("testlocal", context.exception.message)

    def test_assigns_ids_to_registered_library(self):
        # score is registered (range 40000-59999). Strip the ids from score 2.1.0's own tags and let the
        # tool put them back: each must land in the tag sub-range, unique, and a second run is a no-op.
        schema = copy.deepcopy(load_schema_version("score_2.1.0"))  # the loader caches; never mutate it
        stripped = []
        for entry in schema.tags.all_entries:
            if entry.has_attribute(HedKey.InLibrary) and entry.attributes.pop(HedKey.HedID, None):
                stripped.append(entry.name)
        self.assertTrue(stripped)
        basename = self._prerelease("score", "2.1.0")
        schema.save_as_mediawiki(basename + ".mediawiki")
        schema.save_as_dataframes(os.path.join(os.path.dirname(basename), "hedtsv", os.path.basename(basename)))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([self.repo, "score", "2.1.0"]), 0)

        reloaded = load_schema(basename + ".xml")
        ids = [int(reloaded.tags[name].attributes[HedKey.HedID].removeprefix("HED_")) for name in stripped]
        self.assertTrue(all(42001 <= i <= 59999 for i in ids), ids[:5])
        self.assertEqual(len(ids), len(set(ids)))
        # Idempotent: a second run changes nothing.
        with open(basename + ".xml", encoding="utf-8") as fp:
            before = fp.read()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([self.repo, "score", "2.1.0"]), 0)
        with open(basename + ".xml", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), before)

    def test_arg_list_and_schema_name_case(self):
        # The hedpy wrapper passes an argument list; the schema name is matched case-insensitively.
        basename = self._prerelease("score", "1.1.0")
        shutil.copy(os.path.join(SCHEMA_TESTS, "merge_tests", "HED_score_unmerged.mediawiki"), basename + ".mediawiki")
        with contextlib.redirect_stdout(io.StringIO()):
            result = main([self.repo, "SCORE", "1.1.0"])
        self.assertEqual(result, 1)  # still the missing TSV set, reached through the lowercased path


if __name__ == "__main__":
    unittest.main()
