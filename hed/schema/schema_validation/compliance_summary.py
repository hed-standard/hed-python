"""Summary report for HED schema compliance checking."""

from hed.schema.hed_schema_constants import HedSectionKey

# Section display names for readable output
_SECTION_DISPLAY_NAMES = {
    HedSectionKey.Tags: "Tags",
    HedSectionKey.UnitClasses: "Unit Classes",
    HedSectionKey.Units: "Units",
    HedSectionKey.UnitModifiers: "Unit Modifiers",
    HedSectionKey.ValueClasses: "Value Classes",
    HedSectionKey.Attributes: "Attributes",
    HedSectionKey.Properties: "Properties",
}


class ComplianceSummary:
    """Tracks what was checked during schema compliance validation and the results.

    This provides a structured report of all checks performed, how many entries
    were examined, and how many issues were found per check category.

    Use ``get_summary()`` for a human-readable text report, or access
    ``check_results`` directly for programmatic use.
    """

    def __init__(self, schema_name="", schema_version=""):
        """Initialize a ComplianceSummary.

        Parameters:
            schema_name (str): Display name for the schema being checked.
            schema_version (str): The schema version string.
        """
        self.schema_name = schema_name
        self.schema_version = schema_version
        self.check_results = []
        self._current_check = None

    def start_check(self, check_name, description=""):
        """Begin tracking a new compliance check.

        Parameters:
            check_name (str): Short identifier for the check (e.g. "prerelease_version").
            description (str): Human-readable description of what this check validates.
        """
        self._current_check = {
            "name": check_name,
            "description": description,
            "sections_checked": {},
            "entries_checked": 0,
            "entries_skipped": 0,
            "issue_count": 0,
            "sub_checks": [],
        }
        self.check_results.append(self._current_check)

    def record_section(self, section_key, entries_checked, entries_skipped=0):
        """Record that a section was examined during the current check.

        Parameters:
            section_key (HedSectionKey or str): The section that was checked.
            entries_checked (int): Number of entries examined in this section.
            entries_skipped (int): Number of entries skipped (e.g. deprecated).
        """
        if self._current_check is None:
            return
        key = str(section_key)
        self._current_check["sections_checked"][key] = {
            "entries_checked": entries_checked,
            "entries_skipped": entries_skipped,
        }
        self._current_check["entries_checked"] += entries_checked
        self._current_check["entries_skipped"] += entries_skipped

    def add_sub_check(self, sub_check_name):
        """Record a named sub-check within the current check.

        Parameters:
            sub_check_name (str): Name of the sub-check (e.g. an attribute validator name).
        """
        if self._current_check is None:
            return
        if sub_check_name not in self._current_check["sub_checks"]:
            self._current_check["sub_checks"].append(sub_check_name)

    def record_issues(self, issue_count):
        """Record issues found during the current check.

        Parameters:
            issue_count (int): Number of issues found.
        """
        if self._current_check is None:
            return
        self._current_check["issue_count"] += issue_count

    @property
    def total_issues(self):
        """Return total issues across all checks.

        Returns:
            int: Total number of issues found.
        """
        return sum(c["issue_count"] for c in self.check_results)

    @property
    def total_entries_checked(self):
        """Return total entries checked across all checks.

        Returns:
            int: Total number of entries examined.
        """
        return sum(c["entries_checked"] for c in self.check_results)

    def get_summary(self, verbose=True):
        """Return a human-readable summary of all compliance checks.

        Parameters:
            verbose (bool): If True, include per-section breakdowns and sub-check lists.

        Returns:
            str: Formatted multi-line summary report.
        """
        lines = []
        lines.append("=" * 70)
        lines.append("HED Schema Compliance Report")
        lines.append("=" * 70)
        if self.schema_name:
            lines.append(f"Schema: {self.schema_name}")
        if self.schema_version:
            lines.append(f"Version: {self.schema_version}")
        lines.append(f"Total issues found: {self.total_issues}")
        lines.append("")

        for i, check in enumerate(self.check_results, 1):
            status = "PASS" if check["issue_count"] == 0 else f"FAIL ({check['issue_count']} issues)"
            lines.append(f"{i}. [{status}] {check['name']}")
            if check["description"]:
                lines.append(f"   {check['description']}")

            if verbose:
                if check["entries_checked"] > 0 or check["entries_skipped"] > 0:
                    parts = [f"{check['entries_checked']} entries checked"]
                    if check["entries_skipped"] > 0:
                        parts.append(f"{check['entries_skipped']} skipped")
                    lines.append(f"   ({', '.join(parts)})")

                if check["sections_checked"] and verbose:
                    for section_str, info in check["sections_checked"].items():
                        display_name = section_str
                        # Try to get a nice display name
                        for sk, dn in _SECTION_DISPLAY_NAMES.items():
                            if str(sk) == section_str:
                                display_name = dn
                                break
                        skip_note = f", {info['entries_skipped']} skipped" if info["entries_skipped"] else ""
                        lines.append(f"     - {display_name}: {info['entries_checked']} checked{skip_note}")

                if check["sub_checks"]:
                    lines.append("   Sub-checks performed:")
                    for sc in check["sub_checks"]:
                        lines.append(f"     - {sc}")
            lines.append("")

        # Summary of what is NOT checked
        lines.append("-" * 70)
        lines.append("Known gaps (not currently checked):")
        lines.append("  - BoolRange attribute validation")
        lines.append("  - Missing descriptions on entries")
        lines.append("  - SuggestedTag/RelatedTag existence (8.3+ schemas)")
        lines.append("  - Unit class must have at least one unit")
        lines.append("  - DefaultUnits must be in the tag's own unit classes")
        lines.append("  - HedID uniqueness across entries")
        lines.append("  - HedID completeness (all entries should have IDs)")
        lines.append("  - Attributes must have exactly one range type")
        lines.append("  - Attributes must have at least one domain")
        lines.append("  - Reserved tag semantics")
        lines.append("  - Prologue/epilogue existence for released schemas")
        lines.append("  - StringRange value validation")
        lines.append("=" * 70)
        return "\n".join(lines)

    def __str__(self):
        return self.get_summary(verbose=False)
