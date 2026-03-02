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

    def test_has_all_checks(self):
        """Summary should contain all 7 top-level checks."""
        issues = self.schema_84.check_compliance()
        summary = issues.compliance_summary
        check_names = [c["name"] for c in summary.check_results]
        expected = [
            "prerelease_version",
            "prologue_epilogue",
            "invalid_characters",
            "attributes",
            "duplicate_names",
            "extras_columns",
            "annotation_attributes",
        ]
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
                f"Attribute '{attr_name}' has {len(ranges_found)} range properties (expected 1): {ranges_found}",
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
        """8.4.0 should pass compliance with only annotation issues from base schema."""
        issues = self.schema.check_compliance()
        # Base 8.4.0 has annotation entries (e.g. ncit:C25499) that are not in ExternalAnnotations
        annotation_codes = {
            "SCHEMA_ANNOTATION_PREFIX_MISSING",
            "SCHEMA_ANNOTATION_EXTERNAL_MISSING",
            "SCHEMA_ANNOTATION_SOURCE_MISSING",
        }
        annotation_issues = [i for i in issues if i["code"] in annotation_codes]
        self.assertEqual(
            len(issues),
            len(annotation_issues),
            f"Unexpected non-annotation issues: {[i for i in issues if i not in annotation_issues]}",
        )

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
        """HED_testlib_4.0.0 should have prerelease + inherited annotation issues."""
        schema_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/schema_tests/test_merge/HED_testlib_4.0.0.mediawiki"
        )
        hed_schema = schema.load_schema(schema_path)
        issues = hed_schema.check_compliance()
        prerelease_issues = [i for i in issues if i["code"] == "SCHEMA_PRERELEASE_VERSION_USED"]
        self.assertEqual(len(prerelease_issues), 1)
        # The inherited annotation issues from base 8.4.0 are also expected
        annotation_codes = {
            "SCHEMA_ANNOTATION_PREFIX_MISSING",
            "SCHEMA_ANNOTATION_EXTERNAL_MISSING",
            "SCHEMA_ANNOTATION_SOURCE_MISSING",
        }
        annotation_issues = [i for i in issues if i["code"] in annotation_codes]
        self.assertEqual(len(issues), len(prerelease_issues) + len(annotation_issues))

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
                    f"{section.section_key.name}/{entry.name} has stale _unknown_attributes: {entry._unknown_attributes}",
                )


class TestExtrasColumnsCompliance(unittest.TestCase):
    """Tests for the check_extras_columns compliance check."""

    @classmethod
    def setUpClass(cls):
        cls.schema_84 = schema.load_schema_version("8.4.0")
        cls.testlib_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../data/schema_tests/test_merge/HED_testlib_4.0.0.mediawiki",
        )
        cls.testlib_schema = schema.load_schema(cls.testlib_path)

    def test_no_missing_values_840(self):
        """8.4.0 extras should have no empty values."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        sv = SchemaValidator(self.schema_84, ErrorHandler())
        issues = sv.check_extras_columns()
        val_issues = [i for i in issues if i["code"] == "SCHEMA_MISSING_EXTRA_VALUE"]
        self.assertEqual(len(val_issues), 0, f"Empty values: {val_issues}")

    def test_no_missing_values_testlib(self):
        """testlib 4.0.0 extras should have no empty values."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        sv = SchemaValidator(self.testlib_schema, ErrorHandler())
        issues = sv.check_extras_columns()
        val_issues = [i for i in issues if i["code"] == "SCHEMA_MISSING_EXTRA_VALUE"]
        self.assertEqual(len(val_issues), 0, f"Empty values: {val_issues}")

    def test_detects_empty_value(self):
        """Should detect empty cells in extras DataFrames."""
        import copy
        import pandas as pd
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler
        from hed.schema.schema_io.df_constants import SOURCES_KEY

        test_schema = copy.copy(self.schema_84)
        test_schema.extras = dict(self.schema_84.extras)
        test_schema.extras[SOURCES_KEY] = pd.DataFrame(
            {
                "source": ["TestSource", ""],
                "link": ["https://example.com", "https://other.com"],
                "description": ["A test source", "Missing source name"],
            }
        )
        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_extras_columns()
        val_issues = [i for i in issues if i["code"] == "SCHEMA_MISSING_EXTRA_VALUE"]
        self.assertGreater(len(val_issues), 0, "Should detect empty source name")

    def test_detects_nan_value(self):
        """Should detect NaN cells in extras DataFrames."""
        import copy
        import pandas as pd
        import numpy as np
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler
        from hed.schema.schema_io.df_constants import PREFIXES_KEY

        test_schema = copy.copy(self.schema_84)
        test_schema.extras = dict(self.schema_84.extras)
        test_schema.extras[PREFIXES_KEY] = pd.DataFrame(
            {
                "prefix": ["test:"],
                "namespace": [np.nan],
                "description": ["A test prefix"],
            }
        )
        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_extras_columns()
        val_issues = [i for i in issues if i["code"] == "SCHEMA_MISSING_EXTRA_VALUE"]
        self.assertEqual(len(val_issues), 1)
        self.assertIn("namespace", val_issues[0]["message"])

    def test_empty_extras_no_issues(self):
        """An empty extras dict should produce no issues."""
        import copy
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        test_schema = copy.copy(self.schema_84)
        test_schema.extras = {}
        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_extras_columns()
        self.assertEqual(len(issues), 0)

    def test_summary_includes_extras_check(self):
        """Compliance summary should include the extras_columns check."""
        issues = self.schema_84.check_compliance()
        check_names = [c["name"] for c in issues.compliance_summary.check_results]
        self.assertIn("extras_columns", check_names)


class TestAnnotationAttributeCompliance(unittest.TestCase):
    """Tests for the check_annotation_attribute_values compliance check."""

    @classmethod
    def setUpClass(cls):
        cls.schema_84 = schema.load_schema_version("8.4.0")
        cls.testlib_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../data/schema_tests/test_merge/HED_testlib_4.0.0.mediawiki",
        )
        cls.testlib_schema = schema.load_schema(cls.testlib_path)

    def test_annotation_check_finds_issues_on_840(self):
        """8.4.0 has annotation entries (ncit:C25499, rdfs:comment) not in ExternalAnnotations."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        sv = SchemaValidator(self.schema_84, ErrorHandler())
        issues = sv.check_annotation_attribute_values()
        self.assertGreater(len(issues), 0, "Should find annotation issues on 8.4.0")
        # Specifically, ncit:C25499 and rdfs:comment should be flagged as missing from ExternalAnnotations
        external_issues = [i for i in issues if i["code"] == "SCHEMA_ANNOTATION_EXTERNAL_MISSING"]
        external_messages = " ".join(i.get("message", "") for i in external_issues)
        self.assertIn("ncit:", external_messages)
        self.assertIn("rdfs:", external_messages)

    def test_annotation_prefix_check(self):
        """Should detect when an annotation prefix is not in Prefixes."""
        import copy
        import pandas as pd
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler
        from hed.schema.schema_io.df_constants import PREFIXES_KEY

        test_schema = copy.copy(self.schema_84)
        test_schema.extras = dict(self.schema_84.extras)
        # Remove all prefixes so nothing is defined
        test_schema.extras[PREFIXES_KEY] = pd.DataFrame(columns=["prefix", "namespace", "description"])
        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_annotation_attribute_values()
        prefix_issues = [i for i in issues if i["code"] == "SCHEMA_ANNOTATION_PREFIX_MISSING"]
        self.assertGreater(len(prefix_issues), 0, "Should detect missing prefix when Prefixes is empty")

    def test_annotation_external_check(self):
        """Should detect when prefix:id is not in ExternalAnnotations."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler

        sv = SchemaValidator(self.schema_84, ErrorHandler())
        issues = sv.check_annotation_attribute_values()
        external_issues = [i for i in issues if i["code"] == "SCHEMA_ANNOTATION_EXTERNAL_MISSING"]
        self.assertGreater(len(external_issues), 0, "8.4.0 Event has ncit:C25499 which is not in ExternalAnnotations")

    def test_valid_annotations_no_issues(self):
        """Annotations with valid prefix:id should produce no issues."""
        import pandas as pd
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler
        from hed.schema.schema_io import df_constants

        # Create a schema where all annotation values are properly defined
        test_schema = schema.load_schema(self.testlib_path)
        test_schema.extras = dict(test_schema.extras)

        # Add ncit:C25499 and rdfs:comment to ExternalAnnotations
        ext_df = test_schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY].copy()
        new_rows = pd.DataFrame(
            {
                "prefix": ["ncit:", "rdfs:"],
                "id": ["C25499", "comment"],
                "iri": ["http://ncit/C25499", "http://rdfs/comment"],
                "description": ["Event NCI concept", "RDF comment property"],
            }
        )
        test_schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY] = pd.concat([ext_df, new_rows], ignore_index=True)

        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_annotation_attribute_values()
        self.assertEqual(len(issues), 0, f"All annotations should be valid but got: {issues}")

    def test_dc_source_check_valid(self):
        """dc:source annotations with valid source names should pass."""
        import pandas as pd
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler
        from hed.schema.schema_io import df_constants
        from hed.schema.hed_schema_constants import HedSectionKey

        test_schema = schema.load_schema(self.testlib_path)
        test_schema.extras = dict(test_schema.extras)

        # Add ncit:C25499 and rdfs:comment to ExternalAnnotations
        ext_df = test_schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY].copy()
        new_rows = pd.DataFrame(
            {
                "prefix": ["ncit:", "rdfs:"],
                "id": ["C25499", "comment"],
                "iri": ["http://ncit/C25499", "http://rdfs/comment"],
                "description": ["Event NCI concept", "RDF comment property"],
            }
        )
        test_schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY] = pd.concat([ext_df, new_rows], ignore_index=True)

        # Set annotation to dc:source Wikipedia is great
        test_entry = test_schema[HedSectionKey.Tags]["Event"]
        test_entry.attributes["annotation"] = "dc:source Wikipedia is great"

        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_annotation_attribute_values()
        source_issues = [i for i in issues if i["code"] == "SCHEMA_ANNOTATION_SOURCE_MISSING"]
        self.assertEqual(len(source_issues), 0, f"Wikipedia is a valid source, should not fail: {source_issues}")

    def test_dc_source_check_invalid(self):
        """dc:source annotations with invalid source names should fail."""
        import pandas as pd
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler
        from hed.schema.schema_io import df_constants
        from hed.schema.hed_schema_constants import HedSectionKey

        test_schema = schema.load_schema(self.testlib_path)
        test_schema.extras = dict(test_schema.extras)

        # Add ncit:C25499 and rdfs:comment to ExternalAnnotations
        ext_df = test_schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY].copy()
        new_rows = pd.DataFrame(
            {
                "prefix": ["ncit:", "rdfs:"],
                "id": ["C25499", "comment"],
                "iri": ["http://ncit/C25499", "http://rdfs/comment"],
                "description": ["Event NCI concept", "RDF comment property"],
            }
        )
        test_schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY] = pd.concat([ext_df, new_rows], ignore_index=True)

        # Set annotation with invalid source
        test_entry = test_schema[HedSectionKey.Tags]["Event"]
        test_entry.attributes["annotation"] = "dc:source NonExistentSource some details"

        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_annotation_attribute_values()
        source_issues = [i for i in issues if i["code"] == "SCHEMA_ANNOTATION_SOURCE_MISSING"]
        self.assertEqual(len(source_issues), 1, f"Should detect invalid source name: {issues}")

    def test_comma_separated_annotations(self):
        """Comma-separated annotation values should each be checked independently."""
        import pandas as pd
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler
        from hed.schema.schema_io import df_constants
        from hed.schema.hed_schema_constants import HedSectionKey

        test_schema = schema.load_schema(self.testlib_path)
        test_schema.extras = dict(test_schema.extras)

        # Add ncit:C25499 and rdfs:comment to ExternalAnnotations
        ext_df = test_schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY].copy()
        new_rows = pd.DataFrame(
            {
                "prefix": ["ncit:", "rdfs:"],
                "id": ["C25499", "comment"],
                "iri": ["http://ncit/C25499", "http://rdfs/comment"],
                "description": ["Event NCI concept", "RDF comment property"],
            }
        )
        test_schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY] = pd.concat([ext_df, new_rows], ignore_index=True)

        # Set two annotations — one valid, one invalid
        test_entry = test_schema[HedSectionKey.Tags]["Event"]
        test_entry.attributes["annotation"] = "dc:source Wikipedia is great,badprefix:unknown"

        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_annotation_attribute_values()
        # badprefix: is not in prefixes, badprefix:unknown not in external annotations
        prefix_issues = [i for i in issues if i["code"] == "SCHEMA_ANNOTATION_PREFIX_MISSING"]
        self.assertGreater(len(prefix_issues), 0, "Should detect invalid prefix in second annotation")

    def test_summary_includes_annotation_check(self):
        """Compliance summary should include the annotation_attributes check."""
        issues = self.schema_84.check_compliance()
        check_names = [c["name"] for c in issues.compliance_summary.check_results]
        self.assertIn("annotation_attributes", check_names)

    def test_annotation_no_colon_detected(self):
        """An annotation value without a colon should be flagged."""
        from hed.schema.schema_validation.compliance import SchemaValidator
        from hed.errors.error_reporter import ErrorHandler
        from hed.schema.hed_schema_constants import HedSectionKey

        test_schema = schema.load_schema(self.testlib_path)
        # Set annotation to a value with no colon
        test_entry = test_schema[HedSectionKey.Tags]["Event"]
        test_entry.attributes["annotation"] = "no_prefix_here"

        sv = SchemaValidator(test_schema, ErrorHandler())
        issues = sv.check_annotation_attribute_values()
        prefix_issues = [i for i in issues if i["code"] == "SCHEMA_ANNOTATION_PREFIX_MISSING"]
        self.assertGreater(len(prefix_issues), 0, "Should detect annotation with no prefix")
