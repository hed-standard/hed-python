import unittest
import copy

from hed.schema import schema_attribute_validators, HedSectionKey
from hed import load_schema_version


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = load_schema_version("8.2.0")

    def test_util_placeholder(self):
        tag_entry = self.hed_schema.tags["Event"]
        attribute_name = "unitClass"
        self.assertTrue(schema_attribute_validators.tag_is_placeholder_check(self.hed_schema, tag_entry, attribute_name))
        attribute_name = "unitClass"
        tag_entry = self.hed_schema.tags["Age/#"]
        self.assertFalse(schema_attribute_validators.tag_is_placeholder_check(self.hed_schema, tag_entry, attribute_name))

    def test_util_suggested(self):
        tag_entry = self.hed_schema.tags["Event/Sensory-event"]
        attribute_name = "suggestedTag"
        self.assertFalse(schema_attribute_validators.item_exists_check(self.hed_schema, tag_entry, attribute_name, HedSectionKey.Tags))
        tag_entry = self.hed_schema.tags["Property"]
        self.assertFalse(schema_attribute_validators.item_exists_check(self.hed_schema, tag_entry, attribute_name, HedSectionKey.Tags))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["suggestedTag"] = "InvalidSuggestedTag"
        self.assertTrue(schema_attribute_validators.item_exists_check(self.hed_schema, tag_entry, attribute_name, HedSectionKey.Tags))

    def test_util_rooted(self):
        tag_entry = self.hed_schema.tags["Event"]
        attribute_name = "rooted"
        self.assertFalse(schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = self.hed_schema.tags["Property"]
        self.assertFalse(schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["rooted"] = "Event"
        self.assertFalse(schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["rooted"] = "NotRealTag"
        self.assertTrue(schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))

    def test_unit_class_exists(self):
        tag_entry = self.hed_schema.tags["Weight/#"]
        attribute_name = "unitClass"
        self.assertFalse(schema_attribute_validators.item_exists_check(self.hed_schema, tag_entry, attribute_name, HedSectionKey.UnitClasses))

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["unitClass"] = "fakeClass"
        self.assertTrue(schema_attribute_validators.item_exists_check(self.hed_schema, tag_entry, attribute_name, HedSectionKey.UnitClasses))

    def test_value_class_exists(self):
        tag_entry = self.hed_schema.tags["Weight/#"]
        attribute_name = "valueClass"
        self.assertFalse(schema_attribute_validators.item_exists_check(self.hed_schema, tag_entry, attribute_name, HedSectionKey.ValueClasses))

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["valueClass"] = "fakeClass"
        self.assertTrue(schema_attribute_validators.item_exists_check(self.hed_schema, tag_entry, attribute_name, HedSectionKey.ValueClasses))

    def test_unit_exists(self):
        tag_entry = self.hed_schema.unit_classes["accelerationUnits"]
        attribute_name = "defaultUnits"
        self.assertFalse(schema_attribute_validators.unit_exists(self.hed_schema, tag_entry, attribute_name))

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["defaultUnits"] = "bad_unit"
        self.assertTrue(schema_attribute_validators.unit_exists(self.hed_schema, tag_entry, attribute_name))

    def test_deprecatedFrom(self):
        tag_entry = self.hed_schema.tags["Event/Measurement-event"]
        attribute_name = "deprecatedFrom"
        self.assertFalse(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["deprecatedFrom"] = "200.3.0"
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes["deprecatedFrom"] = "invalid"
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes["deprecatedFrom"] = "1"
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes["deprecatedFrom"] = "8.0.0"
        self.assertFalse(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes["deprecatedFrom"] = "8.2.0"
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))
        del tag_entry.attributes["deprecatedFrom"]

        unit_class_entry = copy.deepcopy(self.hed_schema.unit_classes["temperatureUnits"])
        # This should raise an issue because it assumes the attribute is set
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry, attribute_name))
        unit_class_entry.attributes["deprecatedFrom"] = "8.1.0"
        unit_class_entry.units['degree Celsius'].attributes["deprecatedFrom"] = "8.1.0"
        # Still a warning for oC
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry, attribute_name))
        unit_class_entry.units['oC'].attributes["deprecatedFrom"] = "8.1.0"
        self.assertFalse(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry, attribute_name))
        # this is still fine, as we are validating the child has deprecated from, not it's value
        unit_class_entry.units['oC'].attributes["deprecatedFrom"] = "8.2.0"
        self.assertFalse(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry, attribute_name))

        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry.units['oC'], attribute_name))

    def test_conversionFactor(self):
        tag_entry = self.hed_schema.unit_classes["accelerationUnits"].units["m-per-s^2"]
        attribute_name = "conversionFactor"
        self.assertFalse(schema_attribute_validators.conversion_factor(self.hed_schema, tag_entry, attribute_name))

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes[attribute_name] = "-1.0"
        self.assertTrue(schema_attribute_validators.conversion_factor(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes[attribute_name] = "10^3"
        self.assertFalse(schema_attribute_validators.conversion_factor(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes[attribute_name] = None
        self.assertTrue(schema_attribute_validators.conversion_factor(self.hed_schema, tag_entry, attribute_name))

    def test_conversionFactor_modifier(self):
        tag_entry = self.hed_schema.unit_classes["magneticFieldUnits"].units["tesla"]
        attribute_name = "conversionFactor"
        self.assertFalse(schema_attribute_validators.conversion_factor(self.hed_schema, tag_entry, attribute_name))

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes[attribute_name] = "-1.0"
        self.assertTrue(schema_attribute_validators.conversion_factor(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes[attribute_name] = "10^3"
        self.assertFalse(schema_attribute_validators.conversion_factor(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes[attribute_name] = None
        self.assertTrue(schema_attribute_validators.conversion_factor(self.hed_schema, tag_entry, attribute_name))

    def test_allowed_characters_check(self):
        tag_entry = self.hed_schema.value_classes["dateTimeClass"]
        attribute_name = "allowedCharacter"
        valid_attributes = {"letters", "blank", "digits", "alphanumeric", ":", "$", "a"}
        self.assertFalse(schema_attribute_validators.allowed_characters_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry = copy.deepcopy(tag_entry)
        for attribute in valid_attributes:
            tag_entry.attributes[attribute_name] = attribute
            self.assertFalse(schema_attribute_validators.allowed_characters_check(self.hed_schema, tag_entry, attribute_name))

        invalid_attributes = {"lettersdd", "notaword", ":a"}
        for attribute in invalid_attributes:
            tag_entry.attributes[attribute_name] = attribute
            self.assertTrue(schema_attribute_validators.allowed_characters_check(self.hed_schema, tag_entry, attribute_name))

    def test_in_library_check(self):
        score = load_schema_version("score_1.1.0")
        tag_entry = score.tags["Modulator"]
        attribute_name = "inLibrary"
        self.assertFalse(schema_attribute_validators.in_library_check(score, tag_entry, attribute_name))

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes[attribute_name] = "invalid"
        self.assertTrue(schema_attribute_validators.in_library_check(score, tag_entry, attribute_name))

        tag_entry.attributes[attribute_name] = ""
        self.assertTrue(schema_attribute_validators.in_library_check(score, tag_entry, attribute_name))