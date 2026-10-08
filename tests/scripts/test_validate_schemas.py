import contextlib
import copy
import io
import os
import shutil
import tempfile
import unittest

from hed import load_schema, load_schema_version
from hed.schema import HedKey, HedSectionKey
from hed.scripts.schema_script_util import missing_hed_ids
from hed.scripts.validate_schemas import main


class TestRequireIds(unittest.TestCase):
    """hed_validate_schemas --require-ids: a release candidate must carry a hedId on every element."""

    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.mkdtemp(prefix="hed_validate_")
        cls.released = os.path.join(cls.folder, "HED8.4.0.mediawiki")
        schema = copy.deepcopy(load_schema_version("8.4.0"))  # load_schema_version caches; never mutate it
        schema.save_as_mediawiki(cls.released)

        # The same schema with one new tag and one unit stripped of their ids.
        cls.candidate = os.path.join(cls.folder, "HED8.4.1.mediawiki")
        new_entry = schema._create_tag_entry("Tag-without-id", HedSectionKey.Tags)
        schema._add_tag_to_dict("Tag-without-id", new_entry, HedSectionKey.Tags)
        del schema.units["month"].attributes[HedKey.HedID]
        schema.save_as_mediawiki(cls.candidate)
        cls.candidate_json = os.path.join(cls.folder, "HED8.4.1.json")
        schema.save_as_json(cls.candidate_json)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder, ignore_errors=True)

    def test_missing_hed_ids(self):
        self.assertEqual(missing_hed_ids(load_schema_version("8.4.0")), [])
        missing = missing_hed_ids(load_schema(self.candidate))
        self.assertEqual(sorted(missing), ["tags: Tag-without-id", "units: month"])

    def test_released_schema_passes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([self.released, "--require-ids"]), 0)

    def test_candidate_without_ids_fails_only_when_required(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([self.candidate]), 0)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main([self.candidate, "--require-ids"]), 1)
        self.assertIn("2 schema element(s) have no hedId", output.getvalue())
        self.assertIn("tags: Tag-without-id", output.getvalue())
        self.assertIn("units: month", output.getvalue())

    def test_json_input_is_checked(self):
        # A .json path used to be ignored by the file grouping, so --require-ids passed without looking.
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main([self.candidate_json, "--require-ids"]), 1)
        self.assertIn("2 schema element(s) have no hedId", output.getvalue())
        self.assertNotIn("Ignoring file", output.getvalue())


if __name__ == "__main__":
    unittest.main()
