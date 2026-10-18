"""Tests of the reserved-tag rules of reserved_tags.json (specification 3.2.8, Appendix A.6)."""

import io
import json
import os
import unittest

from hed import HedString, Sidecar, TabularInput, load_schema_version, schema
from hed.errors import ErrorSeverity, ValidationErrors
from hed.models import DefinitionDict
from hed.validator import HedValidator
from hed.validator.reserved_checker import ReservedChecker
from hed.validator.spreadsheet_validator import SpreadsheetValidator

DEFINITIONS = ["(Definition/MyDef, (Red))", "(Definition/Other, (Blue))"]


def error_codes(issues):
    """Return the distinct error codes (not warnings) of issues, in order."""
    codes = []
    for issue in issues:
        if issue["severity"] == ErrorSeverity.ERROR and issue["code"] not in codes:
            codes.append(issue["code"])
    return codes


class ReservedTestBase(unittest.TestCase):
    """Validates a string, a sidecar or a timeline file against one schema with MyDef and Other defined."""

    version = "8.4.0"

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version(cls.version)
        cls.def_dict = DefinitionDict(DEFINITIONS, cls.schema)
        assert not cls.def_dict.issues, cls.def_dict.issues

    def string_codes(self, text):
        validator = HedValidator(self.schema, def_dicts=self.def_dict)
        hed_string = HedString(text, self.schema)
        issues = validator.run_basic_checks(hed_string, False)
        if not any(issue["severity"] == ErrorSeverity.ERROR for issue in issues):
            issues += validator.run_full_string_checks(hed_string)
        return error_codes(issues)

    def sidecar_codes(self, sidecar_dict):
        sidecar = Sidecar(io.BytesIO(json.dumps(sidecar_dict).encode("utf-8")))
        return error_codes(sidecar.validate(self.schema, extra_def_dicts=self.def_dict))

    def timeline_codes(self, *hed_cells):
        rows = ["onset\tduration\tHED"] + [f"{i + 1}.0\tn/a\t{cell}" for i, cell in enumerate(hed_cells)]
        tabular = TabularInput(io.BytesIO(("\n".join(rows) + "\n").encode("utf-8")))
        return error_codes(tabular.validate(self.schema, extra_def_dicts=self.def_dict))


class TestReservedCheckerData(unittest.TestCase):
    """The loader reads the published file's two top-level keys."""

    def test_file_is_the_published_reserved_tags_json(self):
        checker = ReservedChecker.get_instance()
        self.assertEqual(os.path.basename(checker.reserved_reqs_path), "reserved_tags.json")
        with open(checker.reserved_reqs_path, encoding="utf-8") as file:
            data = json.load(file)
        self.assertEqual(checker.reserved_map, data["tags"])
        self.assertEqual(checker.value_forms, data["valueForms"])

    def test_derived_sets(self):
        checker = ReservedChecker.get_instance()
        rows = {"Definition", "Delay", "Duration", "Event-context", "Inset", "Offset", "Onset"}
        self.assertEqual(checker.special_names, rows)
        self.assertEqual(checker.no_extension_tags, rows)
        self.assertEqual(checker.require_value_tags, {"Definition", "Delay", "Duration"})
        self.assertEqual(checker.timeline_tags, {"Delay", "Inset", "Offset", "Onset"})
        self.assertEqual(checker.allow_splice_in_group, rows - {"Definition", "Event-context"})
        self.assertEqual(checker.structural_names, rows | {"Def", "Def-expand"})
        self.assertEqual(len(checker.reserved_names), 19)

    def test_timeline_tags_drive_the_banned_list(self):
        self.assertEqual(SpreadsheetValidator.TIMELINE_TAGS, ReservedChecker.get_instance().timeline_tags)


class TestGoverningRow(ReservedTestBase):
    """Delay is secondary beside Onset, Offset, Inset or Duration, whose row then governs (rule 3)."""

    def test_onset_with_delay_takes_zero_or_one_inner_group(self):
        self.assertEqual(self.string_codes("(Onset, Def/MyDef, Delay/2 s)"), [])
        self.assertEqual(self.string_codes("(Onset, Def/MyDef, Delay/2 s, (Blue))"), [])
        self.assertEqual(
            self.string_codes("(Onset, Def/MyDef, Delay/2 s, (Blue), (Green))"), [ValidationErrors.TEMPORAL_TAG_ERROR]
        )

    def test_offset_with_delay_takes_no_inner_group(self):
        self.assertEqual(self.string_codes("(Offset, Def/MyDef, Delay/2 s)"), [])
        self.assertEqual(
            self.string_codes("(Offset, Def/MyDef, Delay/2 s, (Blue))"), [ValidationErrors.TEMPORAL_TAG_ERROR]
        )

    def test_inset_with_delay_takes_zero_or_one_inner_group(self):
        self.assertEqual(self.string_codes("(Inset, Def/MyDef, Delay/2 s)"), [])
        self.assertEqual(self.string_codes("(Inset, Def/MyDef, Delay/2 s, (Blue))"), [])

    def test_duration_with_delay_takes_exactly_one_inner_group(self):
        self.assertEqual(self.string_codes("(Duration/3 s, Delay/2 s, (Red))"), [])
        self.assertEqual(self.string_codes("(Delay/3 s, Duration/2 s)"), [ValidationErrors.TEMPORAL_TAG_ERROR])

    def test_delay_alone_takes_exactly_one_inner_group(self):
        self.assertEqual(self.string_codes("(Delay/2 s, (Red))"), [])
        self.assertEqual(self.string_codes("(Delay/3 s)"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.string_codes("(Delay/3 s, (Red), (Blue))"), [ValidationErrors.TEMPORAL_TAG_ERROR])

    def test_incompatible_tags_are_a_placement_error(self):
        self.assertEqual(self.string_codes("(Offset, Onset, Def/MyDef)"), [ValidationErrors.TAG_GROUP_ERROR])
        self.assertEqual(self.string_codes("(Delay/2 s, Onset, Offset, Def/MyDef)"), [ValidationErrors.TAG_GROUP_ERROR])
        self.assertEqual(self.string_codes("(Onset, Def/MyDef, Duration/3 s)"), [ValidationErrors.TAG_GROUP_ERROR])

    def test_get_governing_tag(self):
        checker = ReservedChecker.get_instance()
        group = HedString("(Delay/2 s, Onset, Def/MyDef)", self.schema).groups()[0]
        governing = checker.get_governing_tag(checker.get_reserved(group))
        self.assertEqual(governing.short_base_tag, "Onset")
        group = HedString("(Offset, Onset, Def/MyDef)", self.schema).groups()[0]
        self.assertIsNone(checker.get_governing_tag(checker.get_reserved(group)))


class TestContentErrorCodes(ReservedTestBase):
    """A content error carries the governing row's ERROR_CODE (rule 6); placement may be TAG_GROUP_ERROR."""

    def test_inner_group_count_uses_the_row_code(self):
        self.assertEqual(self.string_codes("(Onset, Def/MyDef, (Red), (Blue))"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(
            self.sidecar_codes({"defs": {"HED": {"d1": "(Definition/NewDef, (Red), (Blue))"}}}),
            [ValidationErrors.DEFINITION_INVALID],
        )
        self.assertEqual(self.string_codes("(Duration/3 s)"), [ValidationErrors.TEMPORAL_TAG_ERROR])

    def test_missing_or_extra_anchor_uses_the_row_code(self):
        self.assertEqual(self.string_codes("(Onset, (Red))"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.string_codes("(Onset, Def/MyDef, Def/Other)"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.string_codes("(Event-context, Def/MyDef)"), [ValidationErrors.TAG_GROUP_ERROR])

    def test_anchor_forms_are_equivalent(self):
        # Rule 2 and 3.2.8.2: a Def tag and a Def-expand group stand in the same places.
        self.assertEqual(self.string_codes("(Onset, (Def-expand/MyDef, (Red)))"), [])
        self.assertEqual(self.string_codes("(Duration/3 s, Def/MyDef)"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(
            self.string_codes("(Duration/3 s, (Def-expand/MyDef, (Red)))"), [ValidationErrors.TEMPORAL_TAG_ERROR]
        )
        self.assertEqual(self.string_codes("(Duration/3 s, (Def/MyDef))"), [])

    def test_other_top_level_tag_is_a_placement_error(self):
        self.assertEqual(self.string_codes("(Onset, Def/MyDef, Red)"), [ValidationErrors.TAG_GROUP_ERROR])
        self.assertEqual(self.string_codes("(Duration/3 s, Red, (Blue))"), [ValidationErrors.TAG_GROUP_ERROR])

    def test_placement_outside_a_top_level_group_uses_the_row_code(self):
        self.assertEqual(self.string_codes("Onset, Def/MyDef"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.string_codes("(Red, (Onset, Def/MyDef))"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.string_codes("(Red, (Event-context, (Blue)))"), [ValidationErrors.TAG_GROUP_ERROR])


class TestRulesInEveryVersion(ReservedTestBase):
    """Schema 8.1.0 has no tagGroup or topLevelTagGroup on Delay and Duration; the file supplies them (rule 1)."""

    version = "8.1.0"

    def test_placement_comes_from_the_file(self):
        self.assertEqual(self.string_codes("(Red, (Duration/3 s, (Blue)))"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.string_codes("Duration/3 s, Red"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.string_codes("(Duration/3 s, (Blue))"), [])

    def test_group_rules_apply(self):
        self.assertEqual(self.string_codes("(Delay/3 s)"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.string_codes("(Onset, Def/MyDef, Delay/3 s)"), [])

    def test_required_value_comes_from_the_file(self):
        self.assertEqual(self.string_codes("(Duration, (Red))"), [ValidationErrors.TAG_REQUIRES_CHILD])

    def test_delay_and_duration_banned_in_a_definition(self):
        codes = self.sidecar_codes({"defs": {"HED": {"d1": "(Definition/HasDelay, (Delay/2 s, (Red)))"}}})
        self.assertEqual(codes, [ValidationErrors.TEMPORAL_TAG_ERROR])


class TestTagLevelRules(ReservedTestBase):
    """noExtension, '#' as an extension, requireValue and the two-part Definition value."""

    def test_reserved_tag_cannot_be_extended(self):
        self.assertEqual(self.string_codes("(Onset/Blah, Def/MyDef)"), [ValidationErrors.TAG_EXTENSION_INVALID])
        self.assertEqual(self.string_codes("(Event-context/Blah, (Red))"), [ValidationErrors.TAG_EXTENSION_INVALID])
        self.assertEqual(
            self.sidecar_codes({"ev": {"HED": "(Onset/#, Def/MyDef)"}}), [ValidationErrors.TAG_EXTENSION_INVALID]
        )

    def test_placeholder_as_an_extension(self):
        # Red allows extension, but '#' may not be used as one (specification 3.2.5 rule 5).
        self.assertEqual(self.sidecar_codes({"ev": {"HED": "Red/#"}}), [ValidationErrors.PLACEHOLDER_INVALID])
        self.assertEqual(self.sidecar_codes({"ev": {"HED": "Label/#"}}), [])

    def test_ordinary_extension_still_warns(self):
        validator = HedValidator(self.schema, def_dicts=self.def_dict)
        issues = validator.run_basic_checks(HedString("Red/Blah", self.schema), False)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.TAG_EXTENDED])

    def test_definition_second_part_is_only_a_placeholder(self):
        for text in ("(Definition/NewDef/3, (Label/#))", "(Definition/NewDef/#/#, (Label/#))"):
            with self.subTest(text=text):
                codes = self.sidecar_codes({"defs": {"HED": {"d1": text}}})
                self.assertEqual(codes, [ValidationErrors.DEFINITION_INVALID])
        self.assertEqual(self.sidecar_codes({"defs": {"HED": {"d1": "(Definition/NewDef/#, (Label/#))"}}}), [])

    def test_no_splice_in_event_context_or_definition(self):
        other = {"HED": {"x": "(Red)"}}
        self.assertEqual(
            self.sidecar_codes({"ctx": {"HED": {"c1": "(Event-context, {other})"}}, "other": other}),
            [ValidationErrors.TAG_GROUP_ERROR],
        )
        self.assertEqual(
            self.sidecar_codes({"defs": {"HED": {"d1": "(Definition/NewDef, ({other}))"}}, "other": other}),
            [ValidationErrors.DEFINITION_INVALID],
        )
        self.assertEqual(
            self.sidecar_codes({"ctx": {"HED": {"c1": "(Event-context, (Blue)), {other}"}}, "other": other}), []
        )
        self.assertEqual(self.sidecar_codes({"ev": {"HED": {"e1": "(Duration/3 s, {other})"}}, "other": other}), [])


class TestRequiredValue820(ReservedTestBase):
    """Schema 8.2.0 has no requireChild on Delay and Duration; requireValue makes the value mandatory."""

    version = "8.2.0"

    def test_delay_without_a_value(self):
        self.assertEqual(self.timeline_codes("(Delay, (Red))"), [ValidationErrors.TAG_REQUIRES_CHILD])
        self.assertEqual(self.string_codes("(Duration, (Red))"), [ValidationErrors.TAG_REQUIRES_CHILD])
        self.assertEqual(self.timeline_codes("(Delay/2 s, (Red))"), [])


class TestDefaultUnit800(ReservedTestBase):
    """Schema 8.0.0 timeUnits has no conversionFactor: the default unit converts as 1 in every spelling (3.2.8.4)."""

    version = "8.0.0"

    def test_default_unit_converts(self):
        self.assertEqual(self.timeline_codes("(Duration/3 s, (Red))"), [])
        self.assertEqual(self.timeline_codes("(Duration/3, (Red))"), [])
        self.assertEqual(self.timeline_codes("(Delay/3 s, (Blue))"), [])
        self.assertEqual(self.timeline_codes("(Duration/3 second, (Red))"), [])
        self.assertEqual(self.timeline_codes("(Delay/3 seconds, (Blue))"), [])

    def test_other_unit_does_not_convert(self):
        self.assertEqual(self.timeline_codes("(Duration/2 minute, (Red))"), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.timeline_codes("(Duration/300 ms, (Red))"), [ValidationErrors.TEMPORAL_TAG_ERROR])

    def test_value_as_default_unit(self):
        values = {
            text: HedString(text, self.schema).get_all_tags()[0].value_as_default_unit()
            for text in (
                "Duration/3 s",
                "Duration/3",
                "Duration/3 second",
                "Duration/3 seconds",
                "Duration/300 ms",
                "Duration/2 minute",
            )
        }
        self.assertEqual(
            values,
            {
                "Duration/3 s": 3.0,
                "Duration/3": 3.0,
                "Duration/3 second": 3.0,
                "Duration/3 seconds": 3.0,
                "Duration/300 ms": None,
                "Duration/2 minute": None,
            },
        )
        later = load_schema_version("8.1.0")
        self.assertEqual(HedString("Duration/2 minute", later).get_all_tags()[0].value_as_default_unit(), 120.0)

    @staticmethod
    def converted(hed_schema, texts):
        """Return value_as_default_unit() of the single tag of each text."""
        return {text: HedString(text, hed_schema).get_all_tags()[0].value_as_default_unit() for text in texts}

    def test_weight_units_si_default(self):
        """weightUnits (default g, SI): g, gram and grams convert as 1; pound and kg do not."""
        values = self.converted(
            self.schema, ("Weight/3 g", "Weight/3 gram", "Weight/3 grams", "Weight/3 pound", "Weight/3 kg")
        )
        self.assertEqual(
            values,
            {
                "Weight/3 g": 3.0,
                "Weight/3 gram": 3.0,
                "Weight/3 grams": 3.0,
                "Weight/3 pound": None,
                "Weight/3 kg": None,
            },
        )

    def test_speed_units_compound_default(self):
        """speedUnits (default m-per-s, compound): m-per-s and no unit convert as 1; km-per-s does not."""
        values = self.converted(self.schema, ("Speed/3 m-per-s", "Speed/3", "Speed/3 km-per-s"))
        self.assertEqual(values, {"Speed/3 m-per-s": 3.0, "Speed/3": 3.0, "Speed/3 km-per-s": None})

    def test_intensity_units_non_si_default(self):
        """intensityUnits (default dB, not SI): dB converts as 1; the SI units candela and cd do not."""
        # This case exists for the SI guard of HedTag._is_default_unit_without_factors: the Weight cases of
        # test_weight_units_si_default cannot detect the guard being removed, because g is itself SI. No 8.0.0
        # tag uses intensityUnits, so Weight's placeholder is given that class in a copy of the bundled schema.
        path = os.path.join(os.path.dirname(schema.__file__), "schema_data", "HED8.0.0.xml")
        with open(path, encoding="utf-8") as file:
            text = file.read()
        self.assertEqual(text.count("<value>weightUnits</value>"), 1)
        text = text.replace("<value>weightUnits</value>", "<value>intensityUnits</value>")
        intensity_schema = schema.from_string(text, schema_format=".xml")
        values = self.converted(intensity_schema, ("Weight/3 dB", "Weight/3 candela", "Weight/3 cd"))
        self.assertEqual(values, {"Weight/3 dB": 3.0, "Weight/3 candela": None, "Weight/3 cd": None})


class TestTimelineBan(ReservedTestBase):
    """A requiresTimeline tag may not appear in a table without an onset column (rule 4)."""

    def descriptor_codes(self, hed_cell):
        text = f"participant_id\tHED\nsub-01\t{hed_cell}\n"
        tabular = TabularInput(io.BytesIO(text.encode("utf-8")))
        return error_codes(tabular.validate(self.schema, extra_def_dicts=self.def_dict))

    def test_timeline_tags_banned_in_a_descriptor_table(self):
        for text in ("(Onset, Def/MyDef)", "(Offset, Def/MyDef)", "(Inset, Def/MyDef)", "(Delay/3 s, (Red))"):
            with self.subTest(text=text):
                self.assertEqual(self.descriptor_codes(text), [ValidationErrors.TEMPORAL_TAG_ERROR])
        self.assertEqual(self.descriptor_codes("(Duration/3 s, (Red))"), [])


if __name__ == "__main__":
    unittest.main()
