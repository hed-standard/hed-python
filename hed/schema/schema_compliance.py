"""Backward-compatible shim — use ``hed.schema.schema_validation.compliance`` instead."""

from hed.schema.schema_validation.compliance import *  # noqa: F401, F403
from hed.schema.schema_validation.compliance import (  # noqa: F401 — explicit re-exports
    SchemaValidator,
    _IssuesListWithSummary,
    check_compliance,
    CONTENT_SECTIONS,
    DOMAIN_TO_SECTION,
    SECTION_TO_DOMAIN,
)
