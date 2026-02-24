import unittest
import os

from hed import schema
from hed.schema.schema_validation.compliance import DOMAIN_TO_SECTION, SECTION_TO_DOMAIN, CONTENT_SECTIONS
from hed.schema.schema_validation.compliance_summary import ComplianceSummary
from hed.schema.hed_schema_constants import HedKey, HedSectionKey


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = schema.load_schema_version("8.3.0")

    def test_validate_schema(self):
        schema_path_with_issues = "../data/schema_tests/HED8.0.0t.xml"
        schema_path_with_issues = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_path_with_issues)
        hed_schema = schema.load_schema(schema_path_with_issues)
        issues = hed_schema.check_compliance()
        self.assertTrue(isinstance(issues, list))
        self.assertTrue(len(issues) > 1)


class TestComplianceSummary(unittest.TestCase):
    """Tests for the ComplianceSummary reporting class."""

    @classmethod
    def setUpClass(cls):
        cls.schema_84 = schema.load_schema_version("8.4.0")

    def test_summary_exists_on_issues(self):
        """The returned issues list should carry a compliance_summary attribute."""
        issues = self.schema_84.check_compliance()
        self.assertTrue(hasattr(issues, "compliance_summary"))
        self.assertIsInstance(issues.compliance_summary, ComplianceSummary)

    def test_summary_is_list(self):
        """The returned object should still behave as a plain list."""
        issues = self.schema_84.check_compliance()
        self.assertIsInstance(issues, list)
        _ = len(issues)
        _ = issues + []
        _ = list(issues)

    def test_summary_has_all_checks(self):
        """Summary should contain all 5 top-level checks."""
        issues = self.schema_84.check_compliance()
        summary = issues.compliance_summary
        check_names = [c["name"] for c in summary.check_results]
        expected = ["prerelease_version", "prologue_epilogue", "invalid_characters", "attributes", "duplicate_names"]
        self.assertEqual(check_names, expected)

    def test_summary_descriptions_non_empty(self):
        """Every check should have a non-empty description."""
        issues = self.schema_84.check_compliance()
        for check in issues.compliance_summary.check_results:
            self.assertTrue(check["description"], f"Check '{check['name']}' has no description")

    def test_summary_counts_match_issues(self):
        """Total issue count in summary should match length of the issues list."""
        issues = self.schema_84.check_compliance()
        self.assertEqual(issues.compliance_summary.total_issues, len(issues))

    def test_summary_entries_checked_positive(self):
        """For a real schema, entries_checked should be positive for char and attribute checks."""
        issues = self.schema_84.check_compliance()
        summary = issues.compliance_summary
        for check in summary.check_results:
            if check["name"] in ("invalid_characters", "attributes", "duplicate_names"):
                self.assertGreater(check["entries_checked"], 0, f"Check '{check['name']}' has no entries checked")

    def test_summary_sections_tracked(self):
        """Character and attribute checks should list all 7 schema sections."""
        issues = self.schema_84.check_compliance()
        summary = issues.compliance_summary
        for check in summary.check_results:
            if check["name"] in ("invalid_characters", "attributes"):
                self.assertEqual(len(check["sections_checked"]), 7, f"Check '{check['name']}' should cover 7 sections")

    def test_summary_skipped_deprecated_entries(self):
        """The invalid_characters check should report skipped deprecated entries."""
        issues = self.schema_84.check_compliance()
        char_check = issues.compliance_summary.check_results[2]
        self.assertEqual(char_check["name"], "invalid_characters")
        self.assertGreater(char_check["entries_skipped"], 0, "8.4.0 has deprecated entries that should be skipped")

    def test_summary_sub_checks_present(self):
        """8.3+ schemas should show sub-checks in prologue and char checks."""
        issues = self.schema_84.check_compliance()
        prologue_check = issues.compliance_summary.check_results[1]
        self.assertIn("prologue character validation", prologue_check["sub_checks"])

        char_check = issues.compliance_summary.check_results[2]
        self.assertIn("tag name capitalization", char_check["sub_checks"])

    def test_summary_attribute_sub_checks(self):
        """Attribute check should show domain, range, and semantic sub-checks."""
        issues = self.schema_84.check_compliance()
        attr_check = issues.compliance_summary.check_results[3]
        self.assertEqual(attr_check["name"], "attributes")
        self.assertIn("unknown/invalid attribute detection (domain)", attr_check["sub_checks"])
        self.assertIn("range-based value validation", attr_check["sub_checks"])
        self.assertIn("semantic attribute validation", attr_check["sub_checks"])
        self.assertIn("hedId validation", attr_check["sub_checks"])

    def test_summary_get_summary_string(self):
        """get_summary() should return a non-empty string with expected sections."""
        issues = self.schema_84.check_compliance()
        report = issues.compliance_summary.get_summary()
        self.assertIsInstance(report, str)
        self.assertIn("HED Schema Compliance Report", report)
        self.assertIn("prerelease_version", report)
        self.assertIn("Known gaps", report)

    def test_summary_str(self):
        """__str__ should return a non-verbose summary."""
        issues = self.schema_84.check_compliance()
        report = str(issues.compliance_summary)
        self.assertIsInstance(report, str)
        self.assertIn("HED Schema Compliance Report", report)

    def test_summary_with_issues(self):
        """A schema with known issues should show FAIL in the summary."""
        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED8.0.0t.xml")
        hed_schema = schema.load_schema(schema_path)
        issues = hed_schema.check_compliance()
        summary = issues.compliance_summary
        self.assertGreater(summary.total_issues, 0)
        report = summary.get_summary()
        self.assertIn("FAIL", report)

    def test_summary_schema_metadata(self):
        """Summary should capture schema name and version."""
        issues = self.schema_84.check_compliance()
        summary = issues.compliance_summary
        self.assertEqual(summary.schema_version, "8.4.0")
        self.assertTrue(summary.schema_name)


class TestDomainRangeConstants(unittest.TestCase):
    """Verify the domain/range constant mappings are consistent."""

    def test_domain_to_section_covers_content_sections(self):
        """DOMAIN_TO_SECTION should map all 5 content sections."""
        self.assertEqual(len(DOMAIN_TO_SECTION), 5)
        self.assertEqual(set(DOMAIN_TO_SECTION.values()), CONTENT_SECTIONS)

    def test_section_to_domain_is_reverse(self):
        """SECTION_TO_DOMAIN should be the exact reverse of DOMAIN_TO_SECTION."""
        for domain, section in DOMAIN_TO_SECTION.items():
            self.assertEqual(SECTION_TO_DOMAIN[section], domain)

    def test_content_sections_excludes_attributes_and_properties(self):
        """Content sections should not include Attributes or Properties."""
        self.assertNotIn(HedSectionKey.Attributes, CONTENT_SECTIONS)
        self.assertNotIn(HedSectionKey.Properties, CONTENT_SECTIONS)


class TestDomainRangeValidation(unittest.TestCase):
    """Test that domain and range checking works correctly on real schemas."""

    @classmethod
    def setUpClass(cls):
        cls.schema = schema.load_schema_version("8.4.0")

    def test_all_attributes_have_range(self):
        """Every attribute definition in the schema should have exactly one range property."""
        range_keys = {
            HedKey.BoolRange,
            HedKey.TagRange,
            HedKey.NumericRange,
            HedKey.StringRange,
            HedKey.UnitClassRange,
            HedKey.UnitRange,
            HedKey.ValueClassRange,
        }
        for attr_name, attr_entry in self.schema.attributes.items():
            ranges_found = [r for r in range_keys if attr_entry.has_attribute(r)]
            self.assertEqual(
                len(ranges_found),
                1,
                f"Attribute '{attr_name}' has {len(ranges_found)} range " f"properties (expected 1): {ranges_found}",
            )

    def test_all_attributes_have_domain(self):
        """Every attribute definition should have at least one domain property."""
        domain_keys = set(DOMAIN_TO_SECTION.keys()) | {HedKey.ElementDomain}
        for attr_name, attr_entry in self.schema.attributes.items():
            domains_found = [d for d in domain_keys if attr_entry.has_attribute(d)]
            self.assertGreater(len(domains_found), 0, f"Attribute '{attr_name}' has no domain property")

    def test_range_validator_keys_match_schema(self):
        """The range validator dict should cover all range properties in the schema."""
        from hed.schema.schema_validation.compliance import SchemaValidator

        range_keys_in_validator = set(SchemaValidator._range_validators.keys())
        range_keys = {
            HedKey.BoolRange,
            HedKey.TagRange,
            HedKey.NumericRange,
            HedKey.StringRange,
            HedKey.UnitClassRange,
            HedKey.UnitRange,
            HedKey.ValueClassRange,
        }
        self.assertEqual(range_keys_in_validator, range_keys)

    def test_no_issues_on_840(self):
        """8.4.0 should pass compliance with no issues."""
        issues = self.schema.check_compliance()
        self.assertEqual(len(issues), 0, f"Unexpected issues: {issues[:3]}")

    def test_build_validators_uses_range(self):
        """_build_validators should pull range validators from attribute definitions."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        sv = SchemaValidator(self.schema, ErrorHandler())
        # suggestedTag has tagRange — should include item_exists_check
        validators = sv._build_validators(HedKey.SuggestedTag)
        func_names = [getattr(v, "__name__", None) or getattr(v, "func", lambda: None).__name__ for v in validators]
        self.assertIn("item_exists_check", func_names)

    def test_build_validators_includes_semantic(self):
        """_build_validators should include semantic validators for known attributes."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        sv = SchemaValidator(self.schema, ErrorHandler())
        validators = sv._build_validators(HedKey.TakesValue)
        func_names = [getattr(v, "__name__", None) or getattr(v, "func", lambda: None).__name__ for v in validators]
        self.assertIn("tag_is_placeholder_check", func_names)

    def test_build_validators_includes_hedid(self):
        """_build_validators should include the HedID validator for hedId."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        sv = SchemaValidator(self.schema, ErrorHandler())
        validators = sv._build_validators(HedKey.HedID)
        func_names = [getattr(v, "__name__", None) or getattr(v, "func", lambda: None).__name__ for v in validators]
        self.assertIn("verify_tag_id", func_names)

    def test_build_validators_always_checks_deprecated(self):
        """Every attribute should always get the attribute_is_deprecated check."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        sv = SchemaValidator(self.schema, ErrorHandler())
        for attr_name in list(self.schema.attributes.keys())[:5]:
            validators = sv._build_validators(attr_name)
            func_names = [getattr(v, "__name__", None) for v in validators]
            self.assertIn("attribute_is_deprecated", func_names, f"Attribute '{attr_name}' missing deprecated check")


class TestLibrarySchemaCompliance(unittest.TestCase):
    """Test compliance checking on library/unpartitioned test schemas."""

    def test_testunpart_compliance(self):
        """HED_testunpart_1.0.0 should only have a prerelease warning."""
        schema_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED_testunpart_1.0.0.mediawiki"
        )
        hed_schema = schema.load_schema(schema_path)
        issues = hed_schema.check_compliance()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], "SCHEMA_PRERELEASE_VERSION_USED")

    def test_testlib_compliance(self):
        """HED_testlib_4.0.0 should only have a prerelease warning."""
        schema_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/test_merge/HED_testlib_4.0.0.mediawiki"
        )
        hed_schema = schema.load_schema(schema_path)
        issues = hed_schema.check_compliance()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], "SCHEMA_PRERELEASE_VERSION_USED")

    def test_testunpart_no_unknown_attributes(self):
        """After loading, no entries in testunpart should have stale _unknown_attributes."""
        schema_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/HED_testunpart_1.0.0.mediawiki"
        )
        hed_schema = schema.load_schema(schema_path)
        for section in hed_schema._sections.values():
            for entry in section.all_entries:
                self.assertFalse(
                    entry._unknown_attributes,
                    f"{section.section_key.name}/{entry.name} has stale " f"_unknown_attributes: {entry._unknown_attributes}",
                )
