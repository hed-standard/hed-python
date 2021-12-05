"""
Example of how to validate a given hed schema file.

Functions Demonstrated:
hed_schema.check_compliance - Checks if a HedSchema object is hed3 compatible.
"""

from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_file import load_schema

if __name__ == '__main__':
    # This old schema should produce many issues, including many duplicate terms
    local_hed_xml = "../data/schema_data/HED7.2.0.xml"
    hed_schema = load_schema(local_hed_xml)
    issues = hed_schema.check_compliance()
    print(get_printable_issue_string(issues))

    # this should produce fairly minimal issues.
    local_hed_xml = "../data/HED8.0.0.xml"
    issues = hed_schema.check_compliance()
    print(get_printable_issue_string(issues))
