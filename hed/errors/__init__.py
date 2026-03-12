"""Error handling module for HED."""

from .error_reporter import (
    ErrorHandler,
    separate_issues,
    get_printable_issue_string,
    get_printable_issue_string_html,
    check_for_any_errors,
    sort_issues,
    iter_errors,
)
from .error_types import (
    DefinitionErrors,
    TemporalErrors,
    SchemaErrors,
    SchemaWarnings,
    SchemaAttributeErrors,
    SidecarErrors,
    ValidationErrors,
    ColumnErrors,
    TagQualityErrors,
)
from .error_types import ErrorContext, ErrorSeverity
from .exceptions import HedExceptions, HedFileError, HedQueryError
