import unittest
from hed.errors import HedFileError
from hed.schema import load_schema, HedSchemaGroup, load_schema_version, HedSchema


class TestHedSchema(unittest.TestCase):

    def test_load_invalid_schema(self):
        # Handle missing or invalid files.
        invalid_xml_file = "invalidxmlfile.xml"
        hed_schema = None
        try:
            hed_schema = load_schema(invalid_xml_file)
        except HedFileError:
            pass

        self.assertFalse(hed_schema)

        hed_schema = None
        try:
            hed_schema = load_schema(None)
        except HedFileError:
            pass
        self.assertFalse(hed_schema)

        hed_schema = None
        try:
            hed_schema = load_schema("")
        except HedFileError:
            pass
        self.assertFalse(hed_schema)

    def test_load_schema_version_tags(self):
        schema = load_schema_version(xml_version="st:8.0.0")
        schema2 = load_schema_version(xml_version="8.0.0")
        self.assertNotEqual(schema, schema2)
        schema2.set_schema_prefix("st")
        self.assertEqual(schema, schema2)

        score_lib = load_schema_version(xml_version="score_0.0.1")
        self.assertEqual(score_lib._schema_prefix, "")
        self.assertTrue(score_lib.get_tag_entry("Modulators"))

        score_lib = load_schema_version(xml_version="sc:score_0.0.1")
        self.assertEqual(score_lib._schema_prefix, "sc:")
        self.assertTrue(score_lib.get_tag_entry("Modulators", schema_prefix="sc:"))

    def test_load_schema_version(self):
        ver1 = "8.0.0"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version, "8.0.0", "load_schema_version has the right version")
        self.assertEqual(schemas1.library, None, "load_schema_version standard schema has no library")
        ver2 = "base:8.0.0"
        schemas2 = load_schema_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "load_schema_version returns HedSchema version+prefix")
        self.assertEqual(schemas2.version, "8.0.0", "load_schema_version has the right version with prefix")
        self.assertEqual(schemas2._schema_prefix, "base:", "load_schema_version has the right version with prefix")
        ver3 = ["base:8.0.0"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+prefix")
        self.assertEqual(schemas3.version, "8.0.0", "load_schema_version has the right version with prefix")
        self.assertEqual(schemas3._schema_prefix, "base:", "load_schema_version has the right version with prefix")
        ver3 = ["base:"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+prefix")
        self.assertTrue(schemas3.version, "load_schema_version has the right version with prefix")
        self.assertEqual(schemas3._schema_prefix, "base:", "load_schema_version has the right version with prefix")

    def test_load_schema_version_libraries(self):
        ver1 = "score_0.0.1"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version, "0.0.1", "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no prefix")
        self.assertEqual(schemas1.get_formatted_version(), "score_0.0.1",
                         "load_schema_version gives correct version_string with single library no prefix")
        ver1 = "score_"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertTrue(schemas1.version, "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no prefix")
        ver1 = "score"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertTrue(schemas1.version, "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no prefix")

        ver2 = "base:score_0.0.1"
        schemas2 = load_schema_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "load_schema_version returns HedSchema version+prefix")
        self.assertEqual(schemas2.version, "0.0.1", "load_schema_version has the right version with prefix")
        self.assertEqual(schemas2._schema_prefix, "base:", "load_schema_version has the right version with prefix")
        self.assertEqual(schemas2.get_formatted_version(as_string=True), "base:score_0.0.1",
                         "load_schema_version gives correct version_string with single library with prefix")
        ver3 = ["8.0.0", "sc:score_0.0.1"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchemaGroup, "load_schema_version returns HedSchema version+prefix")
        self.assertIsInstance(schemas3._schemas, dict, "load_schema_version group keeps dictionary of hed versions")
        self.assertEqual(len(schemas3._schemas), 2, "load_schema_version group dictionary is right length")
        s = schemas3._schemas[""]
        self.assertEqual(s.version, "8.0.0", "load_schema_version has the right version with prefix")
        self.assertEqual(schemas3.get_formatted_version(as_string=True), '["8.0.0", "sc:score_0.0.1"]',
                         "load_schema_version gives correct version_string with single library with prefix")
        formatted_list = schemas3.get_formatted_version(as_string=False)
        self.assertEqual(len(formatted_list), 2,
                         "load_schema_version gives correct version_string with single library with prefix")
        ver4 = ["ts:8.0.0", "sc:score_0.0.1"]
        schemas4 = load_schema_version(ver4)
        self.assertIsInstance(schemas4, HedSchemaGroup, "load_schema_version returns HedSchema version+prefix")
        self.assertIsInstance(schemas4._schemas, dict, "load_schema_version group keeps dictionary of hed versions")
        self.assertEqual(len(schemas4._schemas), 2, "load_schema_version group dictionary is right length")
        self.assertEqual(schemas4.get_formatted_version(), '["ts:8.0.0", "sc:score_0.0.1"]',
                         "load_schema_version gives correct version_string with multiple prefixes")
        s = schemas4._schemas["ts:"]
        self.assertEqual(s.version, "8.0.0", "load_schema_version has the right version with prefix")
        with self.assertRaises(KeyError) as context:
            schemas4._schemas[""]
        self.assertEqual(context.exception.args[0], '')

    def test_load_schema_version_empty(self):
        schemas = load_schema_version("")
        self.assertIsInstance(schemas, HedSchema, "load_schema_version for empty string returns latest version")
        self.assertTrue(schemas.version, "load_schema_version for empty string has a version")
        self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
        schemas = load_schema_version(None)
        self.assertIsInstance(schemas, HedSchema, "load_schema_version for None returns latest version")
        self.assertTrue(schemas.version, "load_schema_version for empty string has a version")
        self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
        schemas = load_schema_version([""])
        self.assertIsInstance(schemas, HedSchema, "load_schema_version list with blank entry returns latest version")
        self.assertTrue(schemas.version, "load_schema_version for empty string has a version")
        self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
        schemas = load_schema_version([])
        self.assertIsInstance(schemas, HedSchema, "load_schema_version list with blank entry returns latest version")
        self.assertTrue(schemas.version, "load_schema_version for empty string has a version")
        self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")

    def test_schema_load_schema_version_invalid(self):
        with self.assertRaises(HedFileError) as context1:
            load_schema_version("x.0.1")
        self.assertEqual(context1.exception.args[0], 'fileNotFound')

        with self.assertRaises(HedFileError) as context2:
            load_schema_version("base:score_x.0.1")
        self.assertEqual(context2.exception.args[0], 'fileNotFound')

        with self.assertRaises(HedFileError) as context3:
            load_schema_version(["", None])
        self.assertEqual(context3.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context4:
            load_schema_version(["8.0.0", "score_0.0.1"])
        self.assertEqual(context4.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context5:
            load_schema_version(["sc:8.0.0", "sc:score_0.0.1"])
        self.assertEqual(context5.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context6:
            load_schema_version(["", "score_0.0.1"])
        self.assertEqual(context6.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context7:
            load_schema_version(["", "score_"])
        self.assertEqual(context7.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context8:
            load_schema_version(["", "notreallibrary"])
        self.assertEqual(context8.exception.args[0], 'fileNotFound')
