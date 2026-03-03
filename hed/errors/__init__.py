"""Error handling module for HED."""

from .error_reporter import (
    ErrorHandler,
    separate_issues,
    get_printable_issue_string,
    sort_issues,
    iter_errors,
)
from .error_types import (
    DefinitionErrors,
    TemporalErrors,
    SchemaErrors,
    SchemaWarnings,
    SidecarErrors,
    ValidationErrors,
    ColumnErrors,
)
from .error_types import ErrorContext, ErrorSeverity
from .exceptions import HedExceptions, HedFileError
