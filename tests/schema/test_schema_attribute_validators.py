import copy
import unittest

from hed import load_schema_version
from hed.errors import ErrorHandler
from hed.models import HedString
from hed.schema import HedSectionKey, from_string
from hed.schema.schema_validation import attribute_validators as schema_attribute_validators
from hed.validator import HedValidator
from tests.schema import util_create_schemas


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = load_schema_version("8.2.0")

    def test_util_placeholder(self):
        tag_entry = self.hed_schema.tags["Event"]
        attribute_name = "unitClass"
        self.assertTrue(
            schema_attribute_validators.tag_is_placeholder_check(self.hed_schema, tag_entry, attribute_name)
        )
        attribute_name = "unitClass"
        tag_entry = self.hed_schema.tags["Age/#"]
        self.assertFalse(
            schema_attribute_validators.tag_is_placeholder_check(self.hed_schema, tag_entry, attribute_name)
        )

    def test_util_suggested(self):
        tag_entry = self.hed_schema.tags["Event/Sensory-event"]
        attribute_name = "suggestedTag"
        self.assertFalse(
            schema_attribute_validators.item_exists_check(
                self.hed_schema, tag_entry, attribute_name, HedSectionKey.Tags
            )
        )
        tag_entry = self.hed_schema.tags["Property"]
        self.assertFalse(
            schema_attribute_validators.item_exists_check(
                self.hed_schema, tag_entry, attribute_name, HedSectionKey.Tags
            )
        )
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["suggestedTag"] = "InvalidSuggestedTag"
        self.assertTrue(
            schema_attribute_validators.item_exists_check(
                self.hed_schema, tag_entry, attribute_name, HedSectionKey.Tags
            )
        )

    def test_util_rooted(self):
        tag_entry = self.hed_schema.tags["Event"]
        attribute_name = "rooted"
        self.assertFalse(
            schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name)
        )
        tag_entry = self.hed_schema.tags["Property"]
        self.assertFalse(
            schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name)
        )
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["rooted"] = "Event"
        self.assertFalse(
            schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name)
        )
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["rooted"] = "NotRealTag"
        self.assertTrue(
            schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name)
        )

    def test_unit_class_exists(self):
        tag_entry = self.hed_schema.tags["Weight/#"]
        attribute_name = "unitClass"
        self.assertFalse(
            schema_attribute_validators.item_exists_check(
                self.hed_schema, tag_entry, attribute_name, HedSectionKey.UnitClasses
            )
        )

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["unitClass"] = "fakeClass"
        self.assertTrue(
            schema_attribute_validators.item_exists_check(
                self.hed_schema, tag_entry, attribute_name, HedSectionKey.UnitClasses
            )
        )

    def test_value_class_exists(self):
        tag_entry = self.hed_schema.tags["Weight/#"]
        attribute_name = "valueClass"
        self.assertFalse(
            schema_attribute_validators.item_exists_check(
                self.hed_schema, tag_entry, attribute_name, HedSectionKey.ValueClasses
            )
        )

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["valueClass"] = "fakeClass"
        self.assertTrue(
            schema_attribute_validators.item_exists_check(
                self.hed_schema, tag_entry, attribute_name, HedSectionKey.ValueClasses
            )
        )

    def test_unit_exists(self):
        tag_entry = self.hed_schema.unit_classes["accelerationUnits"]
        attribute_name = "defaultUnits"
        self.assertFalse(schema_attribute_validators.unit_exists(self.hed_schema, tag_entry, attribute_name))

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["defaultUnits"] = "bad_unit"
        self.assertTrue(schema_attribute_validators.unit_exists(self.hed_schema, tag_entry, attribute_name))

    def test_unit_exists_derived_default(self):
        # HED 8.5.0 lets defaultUnits be a derived form (mV of a listed V); an unlisted unit still fails.
        schema = util_create_schemas.load_schema_derived_default()
        unit_class = schema.unit_classes["testVoltageUnits"]
        self.assertEqual(unit_class.attributes["defaultUnits"], "mV")
        self.assertEqual(schema_attribute_validators.unit_exists(schema, unit_class, "defaultUnits"), [])

        for bad_default in ("mX", "mv", "kmV", "millivolts"):
            unit_class = copy.deepcopy(unit_class)
            unit_class.attributes["defaultUnits"] = bad_default
            issues = schema_attribute_validators.unit_exists(schema, unit_class, "defaultUnits")
            self.assertEqual(len(issues), 1, bad_default)
            self.assertEqual(issues[0]["code"], "SCHEMA_ATTRIBUTE_VALUE_INVALID", bad_default)
            self.assertIn(f"invalid defaultUnit '{bad_default}'", issues[0]["message"], bad_default)

    def test_single_unit_class_check(self):
        # A placeholder has at most one unit class (spec 4.0.0, 3.1.4.4).
        tag_entry = self.hed_schema.tags["Duration/#"]
        self.assertEqual(tag_entry.attributes["unitClass"], "timeUnits")
        self.assertEqual(
            schema_attribute_validators.single_unit_class_check(self.hed_schema, tag_entry, "unitClass"), []
        )

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["unitClass"] = "timeUnits,physicalLengthUnits"
        issues = schema_attribute_validators.single_unit_class_check(self.hed_schema, tag_entry, "unitClass")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], "SCHEMA_ATTRIBUTE_VALUE_INVALID")
        self.assertIn("more than one unit class", issues[0]["message"])

    def test_multiple_unit_classes_reported_by_compliance(self):
        # End to end through check_compliance on an unmerged library, the shape hed-tests uses.
        lines = [
            'HED version="1.0.0" library="score" withStandard="8.4.0" unmerged="True"',
            "'''Prologue'''",
            "!# start schema",
            "'''Tag-with-two-classes'''",
            "* # {unitClass=%s}",
            "!# end schema",
            "'''Unit classes'''",
            "'''Unit modifiers'''",
            "'''Value classes'''",
            "'''Schema attributes'''",
            "'''Properties'''",
            "'''Epilogue'''",
            "!# end hed",
        ]
        bad = from_string("\n".join(lines) % "timeUnits, unitClass=physicalLengthUnits", schema_format=".mediawiki")
        codes = [issue["code"] for issue in bad.check_compliance()]
        self.assertIn("SCHEMA_ATTRIBUTE_VALUE_INVALID", codes)
        good = from_string("\n".join(lines) % "physicalLengthUnits", schema_format=".mediawiki")
        codes = [issue["code"] for issue in good.check_compliance()]
        self.assertNotIn("SCHEMA_ATTRIBUTE_VALUE_INVALID", codes)

    def test_unit_class_requires_numeric_check(self):
        # Spec 4.0.0, 3.1.4.4: a placeholder with a unit class must have valueClass=numericClass. The check is
        # gated to standard schemas >= 8.5.0 (8.3.0 has Sampling-rate/# with a unit class and no value class).
        lines = [
            'HED version="1.0.0" library="score" withStandard="%s" unmerged="True"',
            "'''Prologue'''",
            "!# start schema",
            "'''Tag-with-units'''",
            "* # {%s}",
            "!# end schema",
            "'''Unit classes'''",
            "'''Unit modifiers'''",
            "'''Value classes'''",
            "'''Schema attributes'''",
            "'''Properties'''",
            "'''Epilogue'''",
            "!# end hed",
        ]

        def codes(standard, attributes):
            schema = from_string("\n".join(lines) % (standard, attributes), schema_format=".mediawiki")
            return [
                issue["message"]
                for issue in schema.check_compliance()
                if issue["code"] == "SCHEMA_ATTRIBUTE_VALUE_INVALID"
            ]

        self.assertEqual(codes("8.5.0", "unitClass=timeUnits, valueClass=numericClass"), [])
        text_issues = codes("8.5.0", "unitClass=timeUnits, valueClass=textClass")
        self.assertEqual(len(text_issues), 1)
        self.assertIn("valueClass 'textClass'", text_issues[0])
        none_issues = codes("8.5.0", "unitClass=timeUnits")
        self.assertEqual(len(none_issues), 1)
        self.assertIn("no valueClass", none_issues[0])
        # Partnered with 8.4.0: not checked.
        self.assertEqual(codes("8.4.0", "unitClass=timeUnits, valueClass=textClass"), [])
        # Released 8.3.0 itself is not flagged for Sampling-rate/#.
        old = load_schema_version("8.3.0")
        self.assertEqual(old.tags["Sampling-rate/#"].attributes.get("valueClass"), None)
        self.assertEqual(
            [issue for issue in old.check_compliance() if "must have valueClass=numericClass" in issue["message"]], []
        )

    def test_any_units_validation(self):
        schema = util_create_schemas.load_schema_any_units()
        validator = HedValidator(schema)

        def codes(text):
            return [issue["code"] for issue in validator.validate(HedString(text, schema), allow_placeholders=False)]

        for good in (
            "Quantity/3 ms",
            "Quantity/3 cm-per-us",
            "Quantity/3 dB",
            "Quantity/2 kV",
            "Quantity/5 dollars",
            "Quantity/7",
        ):
            self.assertEqual(codes(good), [], good)
        for bad in ("Quantity/3 foo", "Quantity/3 MS", "Quantity/3 kmm-per-s"):
            self.assertIn("UNITS_INVALID", codes(bad), bad)

    def test_any_units_compliance(self):
        def compliance_codes(schema):
            return [
                issue["code"]
                for issue in schema.check_compliance(error_handler=ErrorHandler(False))
                if "ANNOTATION" not in issue["code"]
            ]

        clean = util_create_schemas.load_schema_any_units()
        self.assertNotIn("SCHEMA_ATTRIBUTE_INVALID", compliance_codes(clean))
        self.assertNotIn("SCHEMA_DUPLICATE_NODE", compliance_codes(clean))

        with_unit = util_create_schemas.load_schema_any_units(("** foo <nowiki>{conversionFactor=1.0}</nowiki>",))
        issues = with_unit.check_compliance(error_handler=ErrorHandler(False))
        messages = [issue["message"] for issue in issues if issue["code"] == "SCHEMA_ATTRIBUTE_INVALID"]
        self.assertEqual(len(messages), 1)
        self.assertIn("must not list units", messages[0])

        with_default = util_create_schemas.load_schema_any_units(any_units_attributes="{defaultUnits=s}")
        issues = with_default.check_compliance(error_handler=ErrorHandler(False))
        messages = [issue["message"] for issue in issues if issue["code"] == "SCHEMA_ATTRIBUTE_INVALID"]
        self.assertEqual(len(messages), 1)
        self.assertIn("must not have defaultUnits", messages[0])

        # One unit entry shared by two classes (as the JSON loader can produce) is a listing collision that
        # check_duplicate_names cannot see; the derived forms of that one unit are not reported a second time.
        shared = util_create_schemas.load_schema_any_units(
            (
                "* qUnits <nowiki>{defaultUnits=Q}</nowiki>",
                "** Q <nowiki>{SIUnit, unitSymbol, conversionFactor=1.0}</nowiki>",
            )
        )
        shared.unit_classes["timeUnits"].units["Q"] = shared.unit_classes["qUnits"].units["Q"]
        messages = [
            issue["message"]
            for issue in shared.check_compliance(error_handler=ErrorHandler(False))
            if issue["code"] == "SCHEMA_DUPLICATE_NODE"
        ]
        self.assertEqual(len(messages), 1, messages)
        self.assertIn("Unit 'Q' is listed by more than one unit class (qUnits, timeUnits)", messages[0])

        # A derived form shared by two classes and listed by neither: daQ is da + Q and also d + aQ.
        collision = util_create_schemas.load_schema_any_units(
            (
                "* qUnits <nowiki>{defaultUnits=Q}</nowiki>",
                "** Q <nowiki>{SIUnit, unitSymbol, conversionFactor=1.0}</nowiki>",
                "* aqUnits <nowiki>{defaultUnits=aQ}</nowiki>",
                "** aQ <nowiki>{SIUnit, unitSymbol, conversionFactor=1.0}</nowiki>",
            )
        )
        issues = collision.check_compliance(error_handler=ErrorHandler(False))
        messages = [issue["message"] for issue in issues if issue["code"] == "SCHEMA_DUPLICATE_NODE"]
        self.assertTrue(any("'daQ'" in message for message in messages), messages)
        # Released 8.3.0: dB is listed in intensityUnits, so its derivation in memorySizeUnits is not an error.
        self.assertNotIn("SCHEMA_DUPLICATE_NODE", compliance_codes(load_schema_version("8.3.0")))

    def test_unit_class_checks_skip_non_placeholders(self):
        # unitClass on a non-placeholder is the existing SCHEMA_NON_PLACEHOLDER_HAS_CLASS warning, nothing more.
        lines = [
            'HED version="1.0.0" library="score" withStandard="8.5.0" unmerged="True"',
            "'''Prologue'''",
            "!# start schema",
            "'''Not-a-placeholder''' {unitClass=timeUnits, unitClass=physicalLengthUnits}",
            "!# end schema",
            "'''Unit classes'''",
            "'''Unit modifiers'''",
            "'''Value classes'''",
            "'''Schema attributes'''",
            "'''Properties'''",
            "'''Epilogue'''",
            "!# end hed",
        ]
        schema = from_string("\n".join(lines), schema_format=".mediawiki")
        issues = [issue for issue in schema.check_compliance() if issue["code"] == "SCHEMA_ATTRIBUTE_VALUE_INVALID"]
        self.assertEqual(len(issues), 1, issues)
        self.assertIn("Only placeholder nodes", issues[0]["message"])
        for own_message in ("more than one unit class", "must have valueClass=numericClass"):
            self.assertNotIn(own_message, issues[0]["message"])

    def test_deprecatedFrom(self):
        tag_entry = self.hed_schema.tags["Event/Measurement-event"]
        attribute_name = "deprecatedFrom"
        self.assertFalse(
            schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name)
        )

        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["deprecatedFrom"] = "200.3.0"
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes["deprecatedFrom"] = "invalid"
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes["deprecatedFrom"] = "1"
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))

        tag_entry.attributes["deprecatedFrom"] = "8.0.0"
        self.assertFalse(
            schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name)
        )

        # deprecatedFrom equal to current version is valid (deprecating in current release)
        tag_entry.attributes["deprecatedFrom"] = "8.2.0"
        self.assertFalse(
            schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name)
        )

        # deprecatedFrom in the future is invalid
        tag_entry.attributes["deprecatedFrom"] = "8.3.0"
        self.assertTrue(schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, tag_entry, attribute_name))
        del tag_entry.attributes["deprecatedFrom"]

        unit_class_entry = copy.deepcopy(self.hed_schema.unit_classes["temperatureUnits"])
        # This should raise an issue because it assumes the attribute is set
        self.assertTrue(
            schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry, attribute_name)
        )
        unit_class_entry.attributes["deprecatedFrom"] = "8.1.0"
        unit_class_entry.units["degree Celsius"].attributes["deprecatedFrom"] = "8.1.0"
        # Still a warning for oC
        self.assertTrue(
            schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry, attribute_name)
        )
        unit_class_entry.units["oC"].attributes["deprecatedFrom"] = "8.1.0"
        self.assertFalse(
            schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry, attribute_name)
        )
        # this is still fine, as we are validating the child has deprecated from, not it's value
        unit_class_entry.units["oC"].attributes["deprecatedFrom"] = "8.2.0"
        self.assertFalse(
            schema_attribute_validators.tag_is_deprecated_check(self.hed_schema, unit_class_entry, attribute_name)
        )

        # deprecatedFrom=8.2.0 on oC is valid (current version)
        self.assertFalse(
            schema_attribute_validators.tag_is_deprecated_check(
                self.hed_schema, unit_class_entry.units["oC"], attribute_name
            )
        )

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
        self.assertFalse(
            schema_attribute_validators.allowed_characters_check(self.hed_schema, tag_entry, attribute_name)
        )

        tag_entry = copy.deepcopy(tag_entry)
        for attribute in valid_attributes:
            tag_entry.attributes[attribute_name] = attribute
            self.assertFalse(
                schema_attribute_validators.allowed_characters_check(self.hed_schema, tag_entry, attribute_name)
            )

        invalid_attributes = {"lettersdd", "notaword", ":a"}
        for attribute in invalid_attributes:
            tag_entry.attributes[attribute_name] = attribute
            self.assertTrue(
                schema_attribute_validators.allowed_characters_check(self.hed_schema, tag_entry, attribute_name)
            )

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
