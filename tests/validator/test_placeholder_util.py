import unittest

from hed import load_schema_version
from hed.models import DefinitionDict
from hed.validator.util import placeholder_tag


class TestPlaceholderTag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.4.0")
        cls.definitions = DefinitionDict(
            ["(Definition/Acc/#, (Acceleration/# m-per-s^2, Red))", "(Definition/Plain, (Blue))"], cls.schema
        )

    def test_unit_class_template(self):
        tag = placeholder_tag("Distance/# m", self.schema)
        self.assertEqual(str(tag), "Distance/# m")
        self.assertTrue(tag.is_unit_class_tag())

    def test_value_class_template_among_other_tags(self):
        tag = placeholder_tag("Sensory-event, (Label/#, Red), {response}", self.schema)
        self.assertEqual(tag.short_base_tag, "Label")
        self.assertEqual(tag.extension, "#")

    def test_def_template_returns_the_placeholder_inside_the_definition(self):
        tag = placeholder_tag("Def/Acc/#, Green", self.schema, self.definitions)
        self.assertEqual(tag.short_base_tag, "Acceleration")
        self.assertEqual(str(tag), "Acceleration/# m-per-s^2")

    def test_def_template_without_definitions_is_none(self):
        self.assertIsNone(placeholder_tag("Def/Acc/#", self.schema))
        self.assertIsNone(placeholder_tag("Def/Unknown/#", self.schema, self.definitions))

    def test_def_template_of_a_definition_that_takes_no_value_is_none(self):
        self.assertIsNone(placeholder_tag("Def/Plain/#", self.schema, self.definitions))

    def test_template_without_placeholder_is_none(self):
        self.assertIsNone(placeholder_tag("Sensory-event, Red", self.schema))


if __name__ == "__main__":
    unittest.main()
