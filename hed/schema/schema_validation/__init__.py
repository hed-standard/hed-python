"""Schema validation subpackage for HED schema compliance checking.

This package contains all schema validation, compliance checking, and
attribute validation functionality.
"""

from .compliance import check_compliance, SchemaValidator, DOMAIN_TO_SECTION, SECTION_TO_DOMAIN, CONTENT_SECTIONS
from .compliance_summary import ComplianceSummary
from .attribute_validators import (
    attribute_is_deprecated,
    allowed_characters_check,
    conversion_factor,
    in_library_check,
    is_numeric_value,
    item_exists_check,
    tag_exists_base_schema_check,
    tag_is_deprecated_check,
    tag_is_placeholder_check,
    unit_exists,
)
from .hed_id_validator import HedIDValidator
from .validation_util import (
    get_allowed_characters,
    get_allowed_characters_by_name,
    get_problem_indexes,
    schema_version_for_library,
    validate_schema_description_new,
    validate_schema_tag_new,
    validate_schema_term_new,
)
