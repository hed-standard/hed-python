from hed import load_schema_version
from hed.models.hed_tag import HedTag
from hed.schema import HedKey, from_string
from tests.schema import util_create_schemas
from tests.validator.test_tag_validator_base import TestHedBase

# Load the schema once, globally
hed_schema_global = load_schema_version("8.4.0")


class TestValidatorUtilityFunctions(TestHedBase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = hed_schema_global

    def test_if_tag_exists(self):
        valid_tag1 = HedTag("Left-handed", hed_schema=self.hed_schema)
        hash1 = hash(valid_tag1)
        hash2 = hash(valid_tag1)
        self.assertEqual(hash1, hash2)
        valid_tag2 = HedTag("Geometric-object", hed_schema=self.hed_schema)
        valid_tag3 = HedTag("duration/#", hed_schema=self.hed_schema)
        invalid_tag1 = HedTag("something", hed_schema=self.hed_schema)
        invalid_tag2 = HedTag("Participant/nothing", hed_schema=self.hed_schema)
        invalid_tag3 = HedTag("participant/#", hed_schema=self.hed_schema)
        valid_tag1_results = valid_tag1.tag_exists_in_schema()
        valid_tag2_results = valid_tag2.tag_exists_in_schema()
        valid_tag3_results = valid_tag3.tag_exists_in_schema()
        invalid_tag1_results = invalid_tag1.tag_exists_in_schema()
        invalid_tag2_results = invalid_tag2.tag_exists_in_schema()
        invalid_tag3_results = invalid_tag3.tag_exists_in_schema()

        self.assertEqual(valid_tag1_results, True)
        self.assertEqual(valid_tag2_results, True)
        self.assertEqual(valid_tag3_results, True)
        self.assertEqual(invalid_tag1_results, False)
        self.assertEqual(invalid_tag2_results, False)
        self.assertEqual(invalid_tag3_results, False)


class TestSchemaUtilityFunctions(TestHedBase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = hed_schema_global

    def test_correctly_determine_tag_takes_value(self):
        value_tag1 = HedTag("Distance/35 px", hed_schema=self.hed_schema)
        value_tag2 = HedTag("id/35", hed_schema=self.hed_schema)
        value_tag3 = HedTag("duration/#", hed_schema=self.hed_schema)
        no_value_tag1 = HedTag("something", hed_schema=self.hed_schema)
        no_value_tag2 = HedTag("attribute/color/black", hed_schema=self.hed_schema)
        no_value_tag3 = HedTag("participant/#", hed_schema=self.hed_schema)
        value_tag1_result = value_tag1.is_takes_value_tag()
        value_tag2_result = value_tag2.is_takes_value_tag()
        value_tag3_result = value_tag3.is_takes_value_tag()
        no_value_tag1_result = no_value_tag1.is_takes_value_tag()
        no_value_tag2_result = no_value_tag2.is_takes_value_tag()
        no_value_tag3_result = no_value_tag3.is_takes_value_tag()
        self.assertEqual(value_tag1_result, True)
        self.assertEqual(value_tag2_result, True)
        self.assertEqual(value_tag3_result, True)
        self.assertEqual(no_value_tag1_result, False)
        self.assertEqual(no_value_tag2_result, False)
        self.assertEqual(no_value_tag3_result, False)

    def test_should_determine_default_unit(self):
        unit_class_tag1 = HedTag("duration/35 ms", hed_schema=self.hed_schema)
        # unit_class_tag2 = HedTag('participant/effect/cognitive/reward/11 dollars',
        #                          schema=self.schema)
        no_unit_class_tag = HedTag("RGB-red/0.5", hed_schema=self.hed_schema)
        no_value_tag = HedTag("Black", hed_schema=self.hed_schema)
        unit_class_tag1_result = unit_class_tag1.default_unit
        # unit_class_tag2_result = unit_class_tag2.default_unit
        no_unit_class_tag_result = no_unit_class_tag.default_unit
        no_value_tag_result = no_value_tag.default_unit
        self.assertEqual(unit_class_tag1_result.name, "s")
        # self.assertEqual(unit_class_tag2_result, '$')
        self.assertEqual(no_unit_class_tag_result, None)
        self.assertEqual(no_value_tag_result, None)

    def test_correctly_determine_tag_unit_classes(self):
        unit_class_tag1 = HedTag("distance/35 px", hed_schema=self.hed_schema)
        # Todo: Make a schema with a currency unit to test this
        # unit_class_tag2 = HedTag('reward/$10.55', schema=self.schema)
        unit_class_tag3 = HedTag("duration/#", hed_schema=self.hed_schema)
        no_unit_class_tag = HedTag("RGB-red/0.5", hed_schema=self.hed_schema)
        unit_class_tag1_result = list(unit_class_tag1.unit_classes.keys())
        # unit_class_tag2_result = list(unit_class_tag2.get_tag_unit_class_units())
        unit_class_tag3_result = list(unit_class_tag3.unit_classes.keys())
        no_unit_class_tag_result = list(no_unit_class_tag.unit_classes.keys())
        self.assertCountEqual(unit_class_tag1_result, ["physicalLengthUnits"])
        # self.assertCountEqual(unit_class_tag2_result, ['currency'])
        self.assertCountEqual(unit_class_tag3_result, ["timeUnits"])
        self.assertEqual(no_unit_class_tag_result, [])

    def test_determine_tags_legal_units(self):
        unit_class_tag1 = HedTag("distance/35 px", hed_schema=self.hed_schema)
        # todo: add this back in when we have a currency unit or make a test for one.
        # unit_class_tag2 = HedTag('reward/$10.55', schema=self.schema)
        no_unit_class_tag = HedTag("RGB-red/0.5", hed_schema=self.hed_schema)
        unit_class_tag1_result = unit_class_tag1.get_tag_unit_class_units()
        # unit_class_tag2_result = unit_class_tag2.get_tag_unit_class_units()
        no_unit_class_tag_result = no_unit_class_tag.get_tag_unit_class_units()
        self.assertCountEqual(
            sorted(unit_class_tag1_result),
            sorted(
                [
                    "inch",
                    "m",
                    "foot",
                    "metre",
                    "meter",
                    "mile",
                ]
            ),
        )
        self.assertEqual(no_unit_class_tag_result, [])

    def test_strip_off_units_from_value(self):
        volume_string_no_space = HedTag("Volume/100m^3", hed_schema=self.hed_schema)
        volume_string = HedTag("Volume/100 m^3", hed_schema=self.hed_schema)
        prefixed_volume_string = HedTag("Volume/100 cm^3", hed_schema=self.hed_schema)
        invalid_volume_string = HedTag("Volume/200 cm", hed_schema=self.hed_schema)
        invalid_distance_string = HedTag("Distance/200 M", hed_schema=self.hed_schema)
        volume_units = {"volume": self.hed_schema.unit_classes["volumeUnits"]}
        distance_units = {"distance": self.hed_schema.unit_classes["physicalLengthUnits"]}
        stripped_volume_string, _, _ = HedTag._get_tag_units_portion(volume_string.extension, volume_units)
        stripped_volume_string_no_space, _, _ = HedTag._get_tag_units_portion(
            volume_string_no_space.extension, volume_units
        )
        stripped_prefixed_volume_string, _, _ = HedTag._get_tag_units_portion(
            prefixed_volume_string.extension, volume_units
        )
        stripped_invalid_volume_string, units_invalid, unit_entry_invalid = HedTag._get_tag_units_portion(
            invalid_volume_string.extension, volume_units
        )
        stripped_invalid_distance_string, dist_invalid_units, dist_invalid_entry = HedTag._get_tag_units_portion(
            invalid_distance_string.extension, distance_units
        )
        self.assertEqual(stripped_volume_string, "100")
        self.assertEqual(stripped_volume_string_no_space, "100m^3")
        self.assertEqual(stripped_prefixed_volume_string, "100")
        self.assertEqual(stripped_invalid_volume_string, "200")
        self.assertEqual(units_invalid, "cm")
        self.assertEqual(unit_entry_invalid, None)
        self.assertEqual(stripped_invalid_distance_string, "200")
        self.assertEqual(dist_invalid_units, "M")
        self.assertEqual(dist_invalid_entry, None)

    def test_determine_allows_extensions(self):
        extension_tag1 = HedTag("boat", hed_schema=self.hed_schema)
        no_extension_tag1 = HedTag("duration/22 s", hed_schema=self.hed_schema)
        no_extension_tag2 = HedTag("id/45", hed_schema=self.hed_schema)
        no_extension_tag3 = HedTag("RGB-red/0.5", hed_schema=self.hed_schema)
        extension_tag1_result = extension_tag1.has_attribute(HedKey.ExtensionAllowed)
        no_extension_tag1_result = no_extension_tag1.has_attribute(HedKey.ExtensionAllowed)
        no_extension_tag2_result = no_extension_tag2.has_attribute(HedKey.ExtensionAllowed)
        no_extension_tag3_result = no_extension_tag3.has_attribute(HedKey.ExtensionAllowed)
        self.assertEqual(extension_tag1_result, True)
        self.assertEqual(no_extension_tag1_result, False)
        self.assertEqual(no_extension_tag2_result, False)
        self.assertEqual(no_extension_tag3_result, False)

    def test_get_as_default_units(self):
        tag = HedTag("Duration/300 ms", hed_schema=self.hed_schema)
        self.assertAlmostEqual(0.3, tag.value_as_default_unit())

        tag2 = HedTag("Duration/300", hed_schema=self.hed_schema)
        self.assertAlmostEqual(300, tag2.value_as_default_unit())

        tag3 = HedTag("Duration/300 m", hed_schema=self.hed_schema)
        self.assertEqual(None, tag3.value_as_default_unit())

        tag4 = HedTag("IntensityTakesValue/300", hed_schema=util_create_schemas.load_schema_intensity())
        self.assertEqual(300, tag4.value_as_default_unit())

        # cd has no conversionFactor, so no conversion is possible: None, not the raw number.
        tag5 = HedTag("IntensityTakesValue/300 cd", hed_schema=util_create_schemas.load_schema_intensity())
        self.assertEqual(None, tag5.value_as_default_unit())

    def test_value_as_default_unit_no_conversion_factor(self):
        # month and year are the factor-less units of timeUnits in 8.4.0 (spec item 1: no factor, no conversion).
        self.assertIsNone(HedTag("Duration/3 month", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertIsNone(HedTag("Duration/1 year", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertAlmostEqual(180, HedTag("Duration/3 minutes", hed_schema=self.hed_schema).value_as_default_unit())

    def test_value_as_default_unit_invalid_value_or_case(self):
        # A wrongly cased unit is invalid (previously this raised TypeError from float(None)).
        self.assertIsNone(HedTag("Length/3 Feet", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertAlmostEqual(0.9144, HedTag("Length/3 feet", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertIsNone(HedTag("Duration/3 MS", hed_schema=self.hed_schema).value_as_default_unit())
        # A non-numeric value cannot be converted either (previously ValueError).
        self.assertIsNone(HedTag("Duration/abc s", hed_schema=self.hed_schema).value_as_default_unit())

    def test_unit_matching_is_case_sensitive(self):
        # Names as listed, optionally pluralized; symbols exactly; modifiers exactly. Nothing case-folds.
        length_units = self.hed_schema.unit_classes["physicalLengthUnits"]
        self.assertIsNotNone(length_units.get_derivative_unit_entry("feet"))
        self.assertIsNotNone(length_units.get_derivative_unit_entry("foot"))
        self.assertIsNotNone(length_units.get_derivative_unit_entry("m"))
        self.assertIsNotNone(length_units.get_derivative_unit_entry("km"))
        self.assertIsNone(length_units.get_derivative_unit_entry("Feet"))
        self.assertIsNone(length_units.get_derivative_unit_entry("FOOT"))
        self.assertIsNone(length_units.get_derivative_unit_entry("M"))
        self.assertIsNone(length_units.get_derivative_unit_entry("KM"))
        time_units = self.hed_schema.unit_classes["timeUnits"]
        self.assertIsNotNone(time_units.get_derivative_unit_entry("milliseconds"))
        self.assertIsNotNone(time_units.get_derivative_unit_entry("ms"))
        self.assertIsNone(time_units.get_derivative_unit_entry("Milliseconds"))
        self.assertIsNone(time_units.get_derivative_unit_entry("Seconds"))
        self.assertIsNone(time_units.get_derivative_unit_entry("MS"))
        volt_units = self.hed_schema.unit_classes["electricPotentialUnits"]
        self.assertIsNotNone(volt_units.get_derivative_unit_entry("uV"))
        self.assertIsNone(volt_units.get_derivative_unit_entry("UV"))

    def test_default_unit_derived_form(self):
        # defaultUnits may be a derived form (mV here); the entry of the unit it derives from is returned.
        schema = util_create_schemas.load_schema_derived_default()
        tag = HedTag("VoltageTakesValue/3 V", hed_schema=schema)
        default_unit = tag.default_unit
        self.assertIsNotNone(default_unit)
        self.assertEqual(default_unit.name, "V")
        # An explicitly listed default still returns its own entry.
        duration_default = HedTag("Duration/3 s", hed_schema=self.hed_schema).default_unit
        self.assertEqual(duration_default.name, "s")
        # Conversion goes to the derived default: the listed unit's factor is against that default (1 V = 1000 mV).
        self.assertAlmostEqual(3000.0, HedTag("VoltageTakesValue/3 V", hed_schema=schema).value_as_default_unit())
        self.assertAlmostEqual(3.0, HedTag("VoltageTakesValue/3 mV", hed_schema=schema).value_as_default_unit())
        self.assertAlmostEqual(3.0, HedTag("VoltageTakesValue/3", hed_schema=schema).value_as_default_unit())

    def test_any_units_placeholder(self):
        # unitClass=anyUnits: the placeholder resolves a unit against every unit class of the schema.
        schema = util_create_schemas.load_schema_any_units()
        placeholder = schema.tags["Quantity/#"]
        self.assertEqual(placeholder.attributes["unitClass"], "anyUnits")
        self.assertNotIn("anyUnits", placeholder.unit_classes)
        self.assertIn("timeUnits", placeholder.unit_classes)
        self.assertIn("physicalLengthUnits", placeholder.unit_classes)
        # Conversion goes to the default of the class the unit belongs to.
        self.assertAlmostEqual(0.5, HedTag("Quantity/500 ms", hed_schema=schema).value_as_default_unit())
        self.assertAlmostEqual(3000.0, HedTag("Quantity/3 km", hed_schema=schema).value_as_default_unit())
        self.assertAlmostEqual(3.0, HedTag("Quantity/3 dB", hed_schema=schema).value_as_default_unit())
        self.assertIsNotNone(HedTag("Quantity/3 cm-per-us", hed_schema=schema).value_as_default_unit())
        # Listed wins over derived: dB is the decibel of intensityUnits, not d + B of memorySizeUnits.
        _, _, entry = HedTag._get_tag_units_portion("3 dB", placeholder.unit_classes)
        self.assertEqual(entry.unit_class_entry.name, "intensityUnits")
        _, _, entry = HedTag._get_tag_units_portion("3 dam", placeholder.unit_classes)
        self.assertEqual(entry.name, "m")
        # No unit: a plain number with no default unit.
        self.assertIsNone(HedTag("Quantity/7", hed_schema=schema).default_unit)
        self.assertEqual(7.0, HedTag("Quantity/7", hed_schema=schema).value_as_default_unit())
        # Invalid strings stay invalid.
        for bad in ("Quantity/3 foo", "Quantity/3 MS", "Quantity/3 kmm-per-s", "Quantity/3 Feet"):
            self.assertIsNone(HedTag(bad, hed_schema=schema).value_as_default_unit(), bad)

    def test_any_units_with_derived_default_class(self):
        # A class whose default is a derived form (mQ) converts through the listed unit's factor (1 Q = 1000 mQ).
        schema = util_create_schemas.load_schema_any_units(
            (
                "* qUnits <nowiki>{defaultUnits=mQ}</nowiki>",
                "** Q <nowiki>{SIUnit, unitSymbol, conversionFactor=1000}</nowiki>",
            )
        )
        self.assertAlmostEqual(3000.0, HedTag("Quantity/3 Q", hed_schema=schema).value_as_default_unit())
        self.assertAlmostEqual(3.0, HedTag("Quantity/3 mQ", hed_schema=schema).value_as_default_unit())
        self.assertAlmostEqual(3e6, HedTag("Quantity/3 kQ", hed_schema=schema).value_as_default_unit())

    def test_any_units_has_no_default_even_with_one_class(self):
        # A standalone schema with anyUnits and exactly one real class: the placeholder still has no default unit.
        lines = [
            'HED version="1.0.0"',
            "'''Prologue'''",
            "!# start schema",
            "'''Quantity'''",
            "* # {takesValue, unitClass=anyUnits}",
            "'''Duration'''",
            "* # {takesValue, unitClass=timeUnits}",
            "!# end schema",
            "'''Unit classes'''",
            "* anyUnits",
            "* timeUnits {defaultUnits=s}",
            "** s {SIUnit, unitSymbol, conversionFactor=1.0}",
            "'''Unit modifiers'''",
            "* m {SIUnitSymbolModifier, conversionFactor=0.001}",
            "'''Value classes'''",
            "'''Schema attributes'''",
            "* takesValue {tagProperty}",
            "* unitClass {tagProperty}",
            "* defaultUnits {unitClassProperty}",
            "* SIUnit {unitProperty}",
            "* unitSymbol {unitProperty}",
            "* conversionFactor {unitProperty, unitModifierProperty}",
            "* SIUnitSymbolModifier {unitModifierProperty}",
            "'''Properties'''",
            "* tagProperty",
            "* unitClassProperty",
            "* unitProperty",
            "* unitModifierProperty",
            "'''Epilogue'''",
            "!# end hed",
        ]
        schema = from_string("\n".join(lines), schema_format=".mediawiki")
        self.assertEqual(list(schema.tags["Quantity/#"].unit_classes), ["timeUnits"])
        self.assertIsNone(HedTag("Quantity/7", hed_schema=schema).default_unit)
        self.assertEqual(7.0, HedTag("Quantity/7", hed_schema=schema).value_as_default_unit())
        self.assertAlmostEqual(0.003, HedTag("Quantity/3 ms", hed_schema=schema).value_as_default_unit())
        self.assertEqual("s", HedTag("Duration/7", hed_schema=schema).default_unit.name)

    def test_compound_unit_conversion_factors(self):
        # A compound SI unit takes one modifier per component; the exponent applies to the prefixed component
        # and denominator exponents are negative (spec item 4). Exact values here use only modifiers whose
        # factor 8.4.0 spells exactly (k, c, m); mega and up, micro and down are written 10e6 / 10e-6 there.
        self.assertAlmostEqual(3000.0, HedTag("Speed/3 km-per-s", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertAlmostEqual(3000.0, HedTag("Speed/3 m-per-ms", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertAlmostEqual(0.03, HedTag("Speed/3 cm-per-s", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertAlmostEqual(2e-9, HedTag("Volume/2 mm^3", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertAlmostEqual(2e-6, HedTag("Volume/2 cm^3", hed_schema=self.hed_schema).value_as_default_unit())
        # cm-per-ms^2 = 0.01 * (0.001)^-2 = 1e4 m-per-s^2
        self.assertAlmostEqual(
            1e4, HedTag("Acceleration/1 cm-per-ms^2", hed_schema=self.hed_schema).value_as_default_unit()
        )
        self.assertAlmostEqual(
            0.002, HedTag("Acceleration/2 mm-per-s^2", hed_schema=self.hed_schema).value_as_default_unit()
        )
        # Micro: the factor is whatever the schema lists for the "u" modifier (10e-6 in 8.4.0, 1e-6 in 8.5.0).
        micro = float(self.hed_schema.unit_modifiers["u"].attributes["conversionFactor"])
        self.assertAlmostEqual(
            3 * micro, HedTag("Speed/3 um-per-s", hed_schema=self.hed_schema).value_as_default_unit()
        )
        self.assertAlmostEqual(
            3 * 0.01 / micro, HedTag("Speed/3 cm-per-us", hed_schema=self.hed_schema).value_as_default_unit()
        )
        # Two modifiers on one component, a wrongly cased or misspelled component: invalid, so no conversion.
        self.assertIsNone(HedTag("Speed/3 kmm-per-s", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertIsNone(HedTag("Speed/3 m-per-S", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertIsNone(HedTag("Speed/3 m-per-sec", hed_schema=self.hed_schema).value_as_default_unit())
        # A compound unit without SIUnit (m-per-s^3 in 8.4.0) accepts no modifiers at all.
        self.assertAlmostEqual(2.0, HedTag("Jerk-rate/2 m-per-s^3", hed_schema=self.hed_schema).value_as_default_unit())
        self.assertIsNone(HedTag("Jerk-rate/2 mm-per-s^3", hed_schema=self.hed_schema).value_as_default_unit())

    def test_compound_unit_derivative_entries(self):
        # Every accepted surface form of a compound unit maps back to the listed unit entry.
        speed_units = self.hed_schema.unit_classes["speedUnits"]
        for units in ("m-per-s", "km-per-s", "cm-per-us", "m-per-ks", "um-per-ns"):
            self.assertEqual("m-per-s", speed_units.get_derivative_unit_entry(units).name, units)
        for units in ("kmm-per-s", "m-per-S", "m-per-sec", "M-per-s", "m-per-s^2", "km-per-h", "-per-s", "m-per-"):
            self.assertIsNone(speed_units.get_derivative_unit_entry(units), units)
        volume_units = self.hed_schema.unit_classes["volumeUnits"]
        self.assertEqual("m^3", volume_units.get_derivative_unit_entry("mm^3").name)
        self.assertIsNone(volume_units.get_derivative_unit_entry("m^3^3"))
        self.assertIsNone(volume_units.get_derivative_unit_entry("mm3"))
        # 20 symbol modifiers plus the unmodified form per component: 21 forms for m^3, 21^2 for m-per-s.
        self.assertEqual(21, len(self.hed_schema.units["m^3"].derivative_units))
        self.assertEqual(441, len(self.hed_schema.units["m-per-s"].derivative_units))
