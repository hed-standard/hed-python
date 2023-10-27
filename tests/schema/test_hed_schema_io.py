import unittest

from hed.errors import HedFileError
from hed.errors.error_types import SchemaErrors
from hed.schema import load_schema, HedSchemaGroup, load_schema_version, HedSchema
import os
from hed.errors import HedExceptions
from hed.schema import HedKey


# todo: speed up these tests
class TestHedSchema(unittest.TestCase):

    # def test_load_invalid_schema(self):
    #     # Handle missing or invalid files.
    #     invalid_xml_file = "invalidxmlfile.xml"
    #     hed_schema = None
    #     try:
    #         hed_schema = load_schema(invalid_xml_file)
    #     except HedFileError:
    #         pass
    #
    #     self.assertFalse(hed_schema)
    #
    #     hed_schema = None
    #     try:
    #         hed_schema = load_schema(None)
    #     except HedFileError:
    #         pass
    #     self.assertFalse(hed_schema)
    #
    #     hed_schema = None
    #     try:
    #         hed_schema = load_schema("")
    #     except HedFileError:
    #         pass
    #     self.assertFalse(hed_schema)
    #
    # def test_load_schema_version_tags(self):
    #     schema = load_schema_version(xml_version="st:8.0.0")
    #     schema2 = load_schema_version(xml_version="8.0.0")
    #     self.assertNotEqual(schema, schema2)
    #     schema2.set_schema_prefix("st")
    #     self.assertEqual(schema, schema2)
    #
    #     score_lib = load_schema_version(xml_version="score_1.0.0")
    #     self.assertEqual(score_lib._namespace, "")
    #     self.assertTrue(score_lib.get_tag_entry("Modulator"))
    #
    #     score_lib = load_schema_version(xml_version="sc:score_1.0.0")
    #     self.assertEqual(score_lib._namespace, "sc:")
    #     self.assertTrue(score_lib.get_tag_entry("Modulator", schema_namespace="sc:"))

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
        ver3 = ["base:"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertTrue(schemas3.version_number, "load_schema_version has the right version with namespace")
        self.assertEqual(schemas3._namespace, "base:", "load_schema_version has the right version with namespace")

    def test_load_schema_version_libraries(self):
        ver1 = "score_1.0.0"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version_number, "1.0.0", "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no namespace")
        self.assertEqual(schemas1.get_formatted_version(), '"score_1.0.0"',
                         "load_schema_version gives correct version_string with single library no namespace")
        ver1 = "score_"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertTrue(schemas1.version_number, "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no namespace")
        ver1 = "score"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertTrue(schemas1.version_number, "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no namespace")

        ver2 = "base:score_1.0.0"
        schemas2 = load_schema_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "load_schema_version returns HedSchema version+namespace")
        self.assertEqual(schemas2.version_number, "1.0.0", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas2._namespace, "base:", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas2.get_formatted_version(), '"base:score_1.0.0"',
                         "load_schema_version gives correct version_string with single library with namespace")
        ver3 = ["8.0.0", "sc:score_1.0.0"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchemaGroup, "load_schema_version returns HedSchema version+namespace")
        self.assertIsInstance(schemas3._schemas, dict, "load_schema_version group keeps dictionary of hed versions")
        self.assertEqual(len(schemas3._schemas), 2, "load_schema_version group dictionary is right length")
        s = schemas3._schemas[""]
        self.assertEqual(s.version_number, "8.0.0", "load_schema_version has the right version with namespace")
        self.assertEqual(schemas3.get_formatted_version(), '["8.0.0", "sc:score_1.0.0"]',
                         "load_schema_version gives correct version_string with single library with namespace")
        formatted_list = schemas3.get_formatted_version()
        schemas4 = load_schema_version(formatted_list)
        self.assertIsInstance(schemas4, HedSchemaGroup, "load_schema_version returns HedSchema version+namespace")
        self.assertIsInstance(schemas4._schemas, dict, "load_schema_version group keeps dictionary of hed versions")
        self.assertEqual(len(schemas4._schemas), 2, "load_schema_version group dictionary is right length")
        self.assertEqual(schemas4.get_formatted_version(), '["8.0.0", "sc:score_1.0.0"]',
                         "load_schema_version gives correct version_string with multiple prefixes")
        s = schemas4._schemas["sc:"]
        self.assertEqual(s.version_number, "1.0.0", "load_schema_version has the right version with namespace")
        with self.assertRaises(KeyError) as context:
            schemas4._schemas["ts:"]
        self.assertEqual(context.exception.args[0], 'ts:')

        with self.assertRaises(HedFileError) as context:
            load_schema_version("[Malformed,,json]")

        # Invalid prefix
        with self.assertRaises(HedFileError) as context:
            load_schema_version("sc1:score_1.0.0")

        with self.assertRaises(HedFileError) as context:
            load_schema_version("sc1:")
    # def test_load_schema_version_empty(self):
    #     schemas = load_schema_version("")
    #     self.assertIsInstance(schemas, HedSchema, "load_schema_version for empty string returns latest version")
    #     self.assertTrue(schemas.version_number, "load_schema_version for empty string has a version")
    #     self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
    #     schemas = load_schema_version(None)
    #     self.assertIsInstance(schemas, HedSchema, "load_schema_version for None returns latest version")
    #     self.assertTrue(schemas.version_number, "load_schema_version for empty string has a version")
    #     self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
    #     schemas = load_schema_version([""])
    #     self.assertIsInstance(schemas, HedSchema, "load_schema_version list with blank entry returns latest version")
    #     self.assertTrue(schemas.version_number, "load_schema_version for empty string has a version")
    #     self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
    #     schemas = load_schema_version([])
    #     self.assertIsInstance(schemas, HedSchema, "load_schema_version list with blank entry returns latest version")
    #     self.assertTrue(schemas.version_number, "load_schema_version for empty string has a version")
    #     self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")


class TestHedSchemaMerging(unittest.TestCase):
    # Verify all 5 schemas produce the same results
    base_schema_dir = '../data/schema_tests/merge_tests/'

    @classmethod
    def setUpClass(cls):
        cls.full_base_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.base_schema_dir)

    def _base_merging_test(self, files):
        import filecmp
        path1 = ""
        path2 = ""
        for save_merged in [True, False]:
            for i in range(len(files) - 1):
                s1 = files[i]
                s2 = files[i + 1]
                self.assertEqual(s1, s2)
                try:
                    path1 = s1.save_as_xml(save_merged=save_merged)
                    path2 = s2.save_as_xml(save_merged=save_merged)
                    result = filecmp.cmp(path1, path2)
                    # print(s1.filename)
                    # print(s2.filename)
                    self.assertTrue(result)
                    reload1 = load_schema(path1)
                    reload2 = load_schema(path2)
                    self.assertEqual(reload1, reload2)
                except Exception:
                    self.assertTrue(False)
                finally:
                    os.remove(path1)
                    os.remove(path2)

                try:
                    path1 = s1.save_as_mediawiki(save_merged=save_merged)
                    path2 = s2.save_as_mediawiki(save_merged=save_merged)
                    result = filecmp.cmp(path1, path2)
                    self.assertTrue(result)

                    reload1 = load_schema(path1)
                    reload2 = load_schema(path2)
                    self.assertEqual(reload1, reload2)
                except Exception:
                    self.assertTrue(False)
                finally:
                    os.remove(path1)
                    os.remove(path2)

                lines1 = s1.get_as_mediawiki_string(save_merged=save_merged)
                lines2 = s2.get_as_mediawiki_string(save_merged=save_merged)
                self.assertEqual(lines1, lines2)

                lines1 = s1.get_as_xml_string(save_merged=save_merged)
                lines2 = s2.get_as_xml_string(save_merged=save_merged)
                self.assertEqual(lines1, lines2)

    def test_saving_merged(self):
        files = [
            load_schema(os.path.join(self.full_base_folder, "HED_score_1.1.0.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "HED_score_lib_tags.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "HED_score_merged.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "HED_score_merged.xml")),
            load_schema(os.path.join(self.full_base_folder, "HED_score_lib_tags.xml"))
        ]

        self._base_merging_test(files)

    def test_saving_merged_rooted(self):
        files = [
            load_schema(os.path.join(self.full_base_folder, "basic_root.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "basic_root.xml")),
        ]

        self._base_merging_test(files)

    def test_saving_merged_rooted_sorting(self):
        files = [
            load_schema(os.path.join(self.full_base_folder, "sorted_root.mediawiki")),
            load_schema(os.path.join(self.full_base_folder, "sorted_root_merged.xml")),
        ]

        self._base_merging_test(files)

    def test_saving_bad_sort(self):
        loaded_schema = load_schema(os.path.join(self.full_base_folder, "bad_sort_test.mediawiki"))
        filename = loaded_schema.save_as_mediawiki()
        try:
            reloaded_schema = load_schema(filename)
        finally:
            os.remove(filename)

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

        self.assertFalse(schema.check_compliance())

    def test_saving_merged2(self):
        s1 = load_schema(os.path.join(self.full_base_folder, "add_all_types.mediawiki"))
        self._base_added_class_tests(s1)
        path1 = ""
        path2 = ""
        for save_merged in [True, False]:
            try:
                path1 = s1.save_as_xml(save_merged=save_merged)
                s2 = load_schema(path1)
                self.assertEqual(s1, s2)
                self._base_added_class_tests(s2)

                path2 = s1.save_as_mediawiki(save_merged=save_merged)
                s2 = load_schema(path1)
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
            load_schema(os.path.join(self.full_base_folder, "issues_tests/HED_dupesubroot_0.0.1.mediawiki"))
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
        for schema, expected_code in zip(files, expected_code):
            # print(schema.filename)
            issues = schema.check_compliance()
            # for issue in issues:
            #     print(str(issue))
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]["code"], expected_code)

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
