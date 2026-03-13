"""Schema compliance checking for HED schemas.

This module is designed for HED 8.3+ schemas, which carry full domain and
range metadata on their attributes. It can be run on any loaded schema, but
schemas earlier than 8.3 will produce extensive known compliance errors
because they lack the attribute metadata that 8.3 introduced.

The checker validates domain constraints, range constraints, and semantic
rules for all entries in a schema. The schema's own Attributes and
Properties sections define which attributes are valid for each section
(domain) and what type of value each attribute takes (range). This checker
is data-driven by that metadata rather than hard-coding parallel validator
dictionaries.
"""

from functools import partial

import pandas as pd
from semantic_version import Version

from hed.errors.error_reporter import ErrorHandler, sort_issues
from hed.errors.error_types import (
    ErrorContext,
    ErrorSeverity,
    SchemaAttributeErrors,
    SchemaErrors,
    SchemaWarnings,
)
from hed.schema import hed_cache
from hed.schema.schema_validation import attribute_validators
from hed.schema.hed_schema import HedSchema, HedKey, HedSectionKey
from hed.schema.schema_io import df_constants
from hed.schema.schema_validation.hed_id_validator import HedIDValidator
from hed.schema.schema_validation.compliance_summary import ComplianceSummary
from hed.schema.schema_validation.validation_util import (
    get_allowed_characters_by_name,
    get_problem_indexes,
    validate_schema_description,
    validate_schema_tag,
    validate_schema_term,
)

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def check_compliance(hed_schema, check_for_warnings=True, name=None, error_handler=None):
    """Check a HED schema for compliance.

    Parameters:
        hed_schema (HedSchema): HedSchema object to check for hed3 compliance.
        check_for_warnings (bool): If True, check for formatting issues like
            invalid characters, capitalization, etc.
        name (str): If present, will use as filename for context.
        error_handler (ErrorHandler or None): Used to report errors.
            Uses a default one if none passed in.

    Returns:
        list: A list of all warnings and errors found. Each issue is a dict.
            The returned list has an additional ``compliance_summary``
            attribute (ComplianceSummary) providing a structured report.

    Raises:
        ValueError: If *hed_schema* is not a ``HedSchema`` instance.
    """
    if not isinstance(hed_schema, HedSchema):
        raise ValueError("To check compliance of a HedGroupSchema, call self.check_compliance on the schema itself.")

    error_handler = error_handler or ErrorHandler(check_for_warnings)
    validator = SchemaValidator(hed_schema, error_handler)
    issues = []

    name = name or hed_schema.filename
    error_handler.push_error_context(ErrorContext.FILE_NAME, name)

    issues += validator.check_if_prerelease_version()
    issues += validator.check_prologue_epilogue()
    issues += validator.check_invalid_characters()
    issues += validator.check_attributes()
    issues += validator.check_duplicate_names()
    issues += validator.check_duplicate_hed_ids()
    issues += validator.check_extras_columns()
    issues += validator.check_annotation_attribute_values()

    error_handler.pop_error_context()
    issues = sort_issues(issues)
    return _IssuesListWithSummary(issues, validator.summary)


class _IssuesListWithSummary(list):
    """A list subclass that carries a ``compliance_summary`` attribute."""

    def __init__(self, issues, summary):
        super().__init__(issues)
        self.compliance_summary = summary


# ---------------------------------------------------------------------------
# Constants — domain / range mappings
# ---------------------------------------------------------------------------

#: Map from domain property name to the HedSectionKey it gates.
DOMAIN_TO_SECTION = {
    HedKey.TagDomain: HedSectionKey.Tags,
    HedKey.UnitClassDomain: HedSectionKey.UnitClasses,
    HedKey.UnitDomain: HedSectionKey.Units,
    HedKey.UnitModifierDomain: HedSectionKey.UnitModifiers,
    HedKey.ValueClassDomain: HedSectionKey.ValueClasses,
}

#: Reverse map — section to domain property name.
SECTION_TO_DOMAIN = {v: k for k, v in DOMAIN_TO_SECTION.items()}

#: The five primary content sections.
CONTENT_SECTIONS = frozenset(DOMAIN_TO_SECTION.values())


# ---------------------------------------------------------------------------
# Validator class
# ---------------------------------------------------------------------------


class SchemaValidator:
    """Validates a loaded HedSchema for compliance.

    The five content sections (Tags, UnitClasses, Units, UnitModifiers,
    ValueClasses) are validated using range and domain metadata that the
    schema itself provides in its Attributes and Properties sections.

    Typical usage is through :func:`check_compliance`.
    """

    # -- Range validators ---------------------------------------------------
    # Each range property maps to zero or more validator functions with the
    # signature:  validator(hed_schema, tag_entry, attribute_name) -> list[dict]
    _range_validators = {
        HedKey.BoolRange: [],  # bool attributes are present/absent — no value check
        HedKey.TagRange: [
            partial(attribute_validators.item_exists_check, section_key=HedSectionKey.Tags),
        ],
        HedKey.NumericRange: [
            attribute_validators.is_numeric_value,
        ],
        HedKey.StringRange: [],  # free-form string — no structural validation
        HedKey.UnitClassRange: [
            partial(attribute_validators.item_exists_check, section_key=HedSectionKey.UnitClasses),
        ],
        HedKey.UnitRange: [
            attribute_validators.unit_exists,
        ],
        HedKey.ValueClassRange: [
            partial(attribute_validators.item_exists_check, section_key=HedSectionKey.ValueClasses),
        ],
    }

    # -- Semantic validators ------------------------------------------------
    # Extra checks for specific attributes, beyond what range covers.
    _semantic_validators = {
        HedKey.TakesValue: [attribute_validators.tag_is_placeholder_check],
        HedKey.UnitClass: [attribute_validators.tag_is_placeholder_check],
        HedKey.ValueClass: [attribute_validators.tag_is_placeholder_check],
        HedKey.DeprecatedFrom: [attribute_validators.tag_is_deprecated_check],
        HedKey.ConversionFactor: [attribute_validators.conversion_factor],
        HedKey.AllowedCharacter: [attribute_validators.allowed_characters_check],
        HedKey.InLibrary: [attribute_validators.in_library_check],
    }

    # -----------------------------------------------------------------------
    # Construction
    # -----------------------------------------------------------------------

    def __init__(self, hed_schema, error_handler):
        self.hed_schema = hed_schema
        self.error_handler = error_handler
        self._id_validator = HedIDValidator(hed_schema)
        self.summary = ComplianceSummary(
            schema_name=hed_schema.filename or "",
            schema_version=hed_schema.version_number,
        )

    # -----------------------------------------------------------------------
    # Top-level checks
    # -----------------------------------------------------------------------

    def check_if_prerelease_version(self):
        """Warn if this schema version is newer than all known released versions."""
        self.summary.start_check(
            "prerelease_version",
            "Check if schema version is newer than all known released versions.",
        )
        issues = []
        libraries = self.hed_schema.library.split(",")
        versions = self.hed_schema.version_number.split(",")
        for library, version in zip(libraries, versions, strict=False):
            all_known = hed_cache.get_hed_versions(library_name=library)
            if not all_known or Version(all_known[0]) < Version(version):
                issues += ErrorHandler.format_error(
                    SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED,
                    version,
                    all_known,
                )

        if self.hed_schema.with_standard:
            all_known = hed_cache.get_hed_versions()
            if not all_known or Version(all_known[0]) < Version(self.hed_schema.with_standard):
                issues += ErrorHandler.format_error(
                    SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED,
                    self.hed_schema.with_standard,
                    all_known,
                )
        self.error_handler.add_context_and_filter(issues)
        self.summary.record_issues(len(issues))
        return issues

    def check_prologue_epilogue(self):
        """Validate characters in the prologue and epilogue."""
        self.summary.start_check(
            "prologue_epilogue",
            "Validate characters in prologue and epilogue text.",
        )
        self.summary.add_sub_check("prologue character validation")
        self.summary.add_sub_check("epilogue character validation")
        issues = []
        char_set = get_allowed_characters_by_name(["text", "newline"])
        for label, text in [("Prologue", self.hed_schema.prologue), ("Epilogue", self.hed_schema.epilogue)]:
            for _, index in get_problem_indexes(text, char_set):
                issues += ErrorHandler.format_error(
                    SchemaWarnings.SCHEMA_PROLOGUE_CHARACTER_INVALID,
                    char_index=index,
                    source_string=text,
                    section_name=label,
                )
        self.error_handler.add_context_and_filter(issues)
        self.summary.record_issues(len(issues))
        return issues

    def check_invalid_characters(self):
        """Validate characters in entry names and descriptions."""
        self.summary.start_check(
            "invalid_characters",
            "Validate characters in entry names and descriptions.",
        )
        self.summary.add_sub_check("tag name capitalization")
        self.summary.add_sub_check("term/name character validation")
        self.summary.add_sub_check("description character validation")

        issues = []
        for section_key in HedSectionKey:
            checked = 0
            skipped = 0
            self.error_handler.push_error_context(ErrorContext.SCHEMA_SECTION, str(section_key))
            for entry in self.hed_schema[section_key].values():
                if entry.has_attribute(HedKey.DeprecatedFrom):
                    skipped += 1
                    continue
                checked += 1
                self.error_handler.push_error_context(ErrorContext.SCHEMA_TAG, str(entry))
                validator = validate_schema_tag if section_key == HedSectionKey.Tags else validate_schema_term
                new_issues = validator(entry) + validate_schema_description(entry)
                self.error_handler.add_context_and_filter(new_issues)
                issues += new_issues
                self.error_handler.pop_error_context()
            self.summary.record_section(section_key, checked, skipped)
            self.error_handler.pop_error_context()

        self.summary.record_issues(len(issues))
        return issues

    # -----------------------------------------------------------------------
    # Attribute checking — the core domain + range logic
    # -----------------------------------------------------------------------

    def check_attributes(self):
        """Validate every attribute on every entry in every section.

        For each attribute this performs three layers of checking:

        1. **Domain** — the attribute is valid for the entry's section.
           Any attribute not in the section's ``valid_attributes`` was
           already flagged as ``_unknown_attributes`` during loading;
           those are reported here.
        2. **Range** — the attribute value matches the range type declared
           on the attribute's own definition (boolRange, tagRange, etc.).
        3. **Semantic** — extra attribute-specific rules (e.g. takesValue
           requires a placeholder entry, deprecatedFrom version must exist).
        """
        self.summary.start_check(
            "attributes",
            "Validate attribute domains, ranges, and semantic constraints.",
        )
        self.summary.add_sub_check("unknown/invalid attribute detection (domain)")
        self.summary.add_sub_check("deprecated attribute usage")
        self.summary.add_sub_check("range-based value validation")
        self.summary.add_sub_check("semantic attribute validation")
        self.summary.add_sub_check("hedId validation")

        issues = []
        for section_key in HedSectionKey:
            entry_count = 0
            self.error_handler.push_error_context(ErrorContext.SCHEMA_SECTION, str(section_key))
            for entry in self.hed_schema[section_key].values():
                entry_count += 1
                self.error_handler.push_error_context(ErrorContext.SCHEMA_TAG, entry.name)
                issues += self._check_entry_attributes(entry)
                self.error_handler.pop_error_context()
            self.summary.record_section(section_key, entry_count)
            self.error_handler.pop_error_context()

        self.summary.record_issues(len(issues))
        return issues

    def check_duplicate_hed_ids(self):
        """Check for duplicate hedId values across all schema sections."""
        self.summary.start_check(
            "duplicate_hed_ids",
            "Check for duplicate hedId values within or across schema sections.",
        )
        issues = []
        seen_ids: dict[str, tuple[str, str]] = {}  # maps hedId string → (first tag name, section key)
        for section_key in HedSectionKey:
            section = self.hed_schema[section_key]
            self.summary.record_section(section_key, len(section))
            for entry in section.values():
                hed_id = entry.attributes.get(HedKey.HedID)
                if not hed_id:
                    continue
                if hed_id in seen_ids:
                    first_tag_name, first_section_key = seen_ids[hed_id]
                    self.error_handler.push_error_context(ErrorContext.SCHEMA_SECTION, str(section_key))
                    self.error_handler.push_error_context(ErrorContext.SCHEMA_TAG, entry.name)
                    issues += self.error_handler.format_error_with_context(
                        SchemaAttributeErrors.SCHEMA_HED_ID_INVALID,
                        entry.name,
                        new_id=hed_id,
                        duplicate_tag=first_tag_name,
                        duplicate_tag_section=first_section_key,
                    )
                    self.error_handler.pop_error_context()
                    self.error_handler.pop_error_context()
                else:
                    seen_ids[hed_id] = (entry.name, section_key.value)
        self.summary.record_issues(len(issues))
        return issues

    def check_duplicate_names(self):
        """Check for duplicate entry names across library merges."""
        self.summary.start_check(
            "duplicate_names",
            "Check for duplicate entry names within or across library merges.",
        )
        issues = []
        for section_key in HedSectionKey:
            self.summary.record_section(section_key, len(self.hed_schema[section_key]))
            for name, dups in self.hed_schema[section_key].duplicate_names.items():
                libraries = {e.has_attribute(HedKey.InLibrary) for e in dups}
                code = (
                    SchemaErrors.SCHEMA_DUPLICATE_FROM_LIBRARY
                    if len(libraries) == 2
                    else SchemaErrors.SCHEMA_DUPLICATE_NODE
                )
                issues += self.error_handler.format_error_with_context(
                    code,
                    name,
                    duplicate_tag_list=[e.name for e in dups],
                    section=section_key,
                )
        self.summary.record_issues(len(issues))
        return issues

    def check_extras_columns(self):
        """Validate that all extras DataFrames have non-empty values in required columns.

        For each extras section (Sources, Prefixes, ExternalAnnotations), checks
        that every cell in the required columns defined in
        ``df_constants.extras_column_dict`` has a non-empty value.

        Note:
            Missing columns are automatically added with empty strings during
            schema loading (see ``base2schema.fix_extra``), so only value
            presence needs to be checked here.
        """
        self.summary.start_check(
            "extras_columns",
            "Validate extras sections have non-empty values in required columns.",
        )
        self.summary.add_sub_check("non-empty cell values")

        issues = []
        extras = getattr(self.hed_schema, "extras", {}) or {}
        for section_name, required_cols in df_constants.extras_column_dict.items():
            df = extras.get(section_name)
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                # Empty extras are fine — nothing to validate
                continue

            rows_checked = len(df)
            self.summary.record_section(section_name, rows_checked)

            for col in required_cols:
                if col not in df.columns:
                    continue
                mask = df[col].isna() | df[col].astype(str).str.strip().eq("")
                for row_idx in mask[mask].index:
                    issues += ErrorHandler.format_error(
                        SchemaAttributeErrors.SCHEMA_MISSING_EXTRA_VALUE,
                        section_name=section_name,
                        column_name=col,
                        row_index=row_idx,
                    )

        self.error_handler.add_context_and_filter(issues)
        self.summary.record_issues(len(issues))
        return issues

    def check_annotation_attribute_values(self):
        """Validate that annotation attribute values reference valid prefixes, external annotations, and sources.

        For each entry that has an ``annotation`` attribute, checks that:

        1. The value starts with ``prefix:id`` where ``prefix:`` is defined in
           the Prefixes extras section and ``prefix:`` + ``id`` is a row in the
           ExternalAnnotations extras section.
        2. If the annotation references ``dc:source``, the remaining text after
           ``dc:source `` must start with a name from the Sources extras section.
        """
        self.summary.start_check(
            "annotation_attributes",
            "Validate annotation attribute values reference defined prefixes, external annotations, and sources.",
        )
        self.summary.add_sub_check("prefix defined in Prefixes")
        self.summary.add_sub_check("prefix:id in ExternalAnnotations")
        self.summary.add_sub_check("dc:source references valid Sources entry")

        issues = []

        # Build lookup sets from extras
        extras = getattr(self.hed_schema, "extras", {}) or {}
        defined_prefixes = self._get_extras_column_values(extras, df_constants.PREFIXES_KEY, df_constants.prefix)
        external_pairs = self._get_external_annotation_pairs(extras)
        defined_sources = self._get_extras_column_values(extras, df_constants.SOURCES_KEY, df_constants.source)

        # Scan all entries in all sections for the "annotation" attribute
        entries_checked = 0
        for section_key in HedSectionKey:
            self.error_handler.push_error_context(ErrorContext.SCHEMA_SECTION, str(section_key))
            for entry in self.hed_schema[section_key].values():
                annotation_value = entry.attributes.get("annotation")
                if not annotation_value:
                    continue
                entries_checked += 1
                self.error_handler.push_error_context(ErrorContext.SCHEMA_TAG, entry.name)
                # Annotation values can be comma-separated (multiple annotations)
                for single_annotation in annotation_value.split(","):
                    single_annotation = single_annotation.strip()
                    if single_annotation:
                        issues += self._validate_annotation_value(
                            entry, single_annotation, defined_prefixes, external_pairs, defined_sources
                        )
                self.error_handler.pop_error_context()
            self.error_handler.pop_error_context()

        self.summary.record_section("annotation_entries", entries_checked)
        self.summary.record_issues(len(issues))
        return issues

    # -----------------------------------------------------------------------
    # Private helpers — extras / annotation validation
    # -----------------------------------------------------------------------

    @staticmethod
    def _get_extras_column_values(extras, section_key, column_name):
        """Return the set of values in a column of an extras DataFrame.

        Parameters:
            extras (dict): The schema extras dictionary.
            section_key (str): Key into the extras dict (e.g. "Prefixes").
            column_name (str): The column whose values to collect.

        Returns:
            set: The set of non-empty string values in that column.
        """
        df = extras.get(section_key)
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return set()
        if column_name not in df.columns:
            return set()
        return {str(v).strip() for v in df[column_name] if pd.notna(v) and str(v).strip()}

    @staticmethod
    def _get_external_annotation_pairs(extras):
        """Return a set of (prefix, id) tuples from the ExternalAnnotations DataFrame.

        Parameters:
            extras (dict): The schema extras dictionary.

        Returns:
            set: Set of (prefix_str, id_str) tuples.
        """
        df = extras.get(df_constants.EXTERNAL_ANNOTATION_KEY)
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return set()
        pairs = set()
        if df_constants.prefix in df.columns and df_constants.id in df.columns:
            for _, row in df.iterrows():
                p = str(row[df_constants.prefix]).strip() if pd.notna(row[df_constants.prefix]) else ""
                i = str(row[df_constants.id]).strip() if pd.notna(row[df_constants.id]) else ""
                if p and i:
                    pairs.add((p, i))
        return pairs

    def _validate_annotation_value(self, entry, annotation_value, defined_prefixes, external_pairs, defined_sources):
        """Validate a single annotation attribute value.

        Parameters:
            entry: The schema entry with the annotation attribute.
            annotation_value (str): The annotation value string.
            defined_prefixes (set): Valid prefixes from the Prefixes section.
            external_pairs (set): Valid (prefix, id) pairs from ExternalAnnotations.
            defined_sources (set): Valid source names from the Sources section.

        Returns:
            list: A list of issue dicts.
        """
        issues = []
        tag_name = entry.name

        # Parse prefix:id from the annotation value
        # Expected format: "prefix:id rest_of_text" e.g. "dc:source Beniczky ea 2017 Table 2."
        colon_pos = annotation_value.find(":")
        if colon_pos < 1:
            # No colon found — cannot parse prefix:id
            issues += self.error_handler.format_error_with_context(
                SchemaAttributeErrors.SCHEMA_ANNOTATION_PREFIX_MISSING,
                tag_name,
                annotation_value=annotation_value,
                prefix="(none)",
            )
            return issues

        ann_prefix = annotation_value[: colon_pos + 1]  # e.g. "dc:"
        remainder = annotation_value[colon_pos + 1 :]  # e.g. "source Beniczky ea 2017 Table 2."

        # Split remainder into id and rest — id is the first whitespace-delimited token
        parts = remainder.split(None, 1)  # split on whitespace, max 1 split
        ann_id = parts[0] if parts else remainder  # e.g. "source"
        rest_text = parts[1] if len(parts) > 1 else ""  # e.g. "Beniczky ea 2017 Table 2."

        # Check 1: prefix must be in Prefixes
        if ann_prefix not in defined_prefixes:
            issues += self.error_handler.format_error_with_context(
                SchemaAttributeErrors.SCHEMA_ANNOTATION_PREFIX_MISSING,
                tag_name,
                annotation_value=annotation_value,
                prefix=ann_prefix,
            )

        # Check 2: prefix:id must be in ExternalAnnotations
        if (ann_prefix, ann_id) not in external_pairs:
            issues += self.error_handler.format_error_with_context(
                SchemaAttributeErrors.SCHEMA_ANNOTATION_EXTERNAL_MISSING,
                tag_name,
                annotation_value=annotation_value,
                prefix=ann_prefix,
                annotation_id=ann_id,
            )

        # Check 3: If dc:source, the rest_text must start with a defined source name
        if ann_prefix == "dc:" and ann_id == "source":
            rest_text_stripped = rest_text.strip() if rest_text else ""
            if not rest_text_stripped or not any(rest_text_stripped.startswith(src) for src in defined_sources):
                issues += self.error_handler.format_error_with_context(
                    SchemaAttributeErrors.SCHEMA_ANNOTATION_SOURCE_MISSING,
                    tag_name,
                    annotation_value=annotation_value,
                    source_text=rest_text_stripped,
                )

        for issue in issues:
            issue["severity"] = ErrorSeverity.WARNING
        return issues

    # -----------------------------------------------------------------------
    # Private helpers — attribute validation
    # -----------------------------------------------------------------------

    def _check_entry_attributes(self, entry):
        """Run domain, range, and semantic checks on a single schema entry."""
        issues = []
        # 1. Domain check — report unknown attributes
        issues += self._check_unknown_attributes(entry)
        # 2–4. Per-attribute range + semantic + deprecated checks
        for attribute_name in entry.attributes:
            validators = self._build_validators(attribute_name)
            issues += self._run_validators(entry, attribute_name, validators)
        return issues

    def _check_unknown_attributes(self, entry):
        """Report attributes that are not valid for this entry's section."""
        issues = []
        if entry._unknown_attributes:
            for attr in entry._unknown_attributes:
                issues += self.error_handler.format_error_with_context(
                    SchemaAttributeErrors.SCHEMA_ATTRIBUTE_INVALID,
                    attr,
                    source_tag=entry.name,
                )
        return issues

    def _build_validators(self, attribute_name):
        """Assemble the validator list for *attribute_name*.

        Combines (in order):
        - deprecated-attribute check (always)
        - range validators (from the attribute's definition)
        - semantic validators (hard-coded extras for specific attributes)
        - hedId validator (if attribute is hedId)
        """
        validators = [attribute_validators.attribute_is_deprecated]

        # Range validators — look up the attribute definition to find its range
        attr_entry = self.hed_schema.get_tag_entry(attribute_name, HedSectionKey.Attributes)
        if attr_entry:
            for range_key, range_funcs in self._range_validators.items():
                if attr_entry.has_attribute(range_key):
                    validators.extend(range_funcs)

        # Semantic validators
        validators.extend(self._semantic_validators.get(attribute_name, []))

        # HedID validator
        if attribute_name == HedKey.HedID:
            validators.append(self._id_validator.verify_tag_id)

        return validators

    def _run_validators(self, entry, attribute_name, validators):
        """Run a list of validators for one attribute on one entry."""
        issues = []
        for validator in validators:
            self.error_handler.push_error_context(ErrorContext.SCHEMA_ATTRIBUTE, attribute_name)
            new_issues = validator(self.hed_schema, entry, attribute_name)
            self.error_handler.add_context_and_filter(new_issues)
            issues += new_issues
            self.error_handler.pop_error_context()
        return issues
