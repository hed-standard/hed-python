"""Tests that the JSON schema loader rejects JSON that is not a HED schema (issue #1464)."""

import json
import os
import shutil
import tempfile
import unittest

from hed.errors.exceptions import HedExceptions, HedFileError
from hed.schema import load_schema, load_schema_version
from hed.schema.schema_io.json2schema import SchemaLoaderJSON


class TestJSONNotASchema(unittest.TestCase):
    """JSON that is not a schema raises INVALID_HED_FORMAT, never a misleading header error."""

    # Shaped like the hed-schemas repository manifest schema_versions.json.
    MANIFEST = {
        "generated": "2026-09-17T00:00:00Z",
        "libraries": {"standard": {"released": ["8.4.0"]}},
        "manifest_format_version": 1,
        "repo_commit": "main",
    }

    CASES = {
        "schema_versions.json": (
            MANIFEST,
            "schema_versions.json is not a HED schema JSON file: the root object has no version key "
            "(top-level keys: generated, libraries, manifest_format_version, repo_commit)",
        ),
        "array.json": ([1, 2, 3], "array.json is not a HED schema JSON file: the root is not an object"),
        "string.json": ("abc", "string.json is not a HED schema JSON file: the root is not an object"),
    }

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)

    def test_rejected_as_string(self):
        for name, (data, message) in self.CASES.items():
            with self.subTest(name=name):
                with self.assertRaises(HedFileError) as context:
                    SchemaLoaderJSON.load(schema_as_string=json.dumps(data), name=name)
                self.assertEqual(context.exception.code, HedExceptions.INVALID_HED_FORMAT)
                self.assertEqual(context.exception.message, message)
                self.assertEqual(context.exception.filename, name)

    def test_rejected_as_file(self):
        for name, (data, message) in self.CASES.items():
            with self.subTest(name=name):
                path = os.path.join(self.temp_dir, name)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                with self.assertRaises(HedFileError) as context:
                    load_schema(path)
                self.assertEqual(context.exception.code, HedExceptions.INVALID_HED_FORMAT)
                self.assertEqual(context.exception.message, message.replace(name, path, 1))
                self.assertEqual(context.exception.filename, path)

    def test_empty_object_rejected(self):
        with self.assertRaises(HedFileError) as context:
            SchemaLoaderJSON.load(schema_as_string="{}", name="empty.json")
        self.assertEqual(context.exception.code, HedExceptions.INVALID_HED_FORMAT)
        self.assertIn("(top-level keys: none)", context.exception.message)

    def test_valid_json_schema_still_loads(self):
        expected = load_schema_version("8.4.0")
        path = os.path.join(self.temp_dir, "HED8.4.0.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(expected.get_as_json_string())
        schema = load_schema(path)
        self.assertEqual(schema.version_number, "8.4.0")
        self.assertEqual(schema, expected)


if __name__ == "__main__":
    unittest.main()
