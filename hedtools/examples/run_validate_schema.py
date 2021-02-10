"""
Example of how to validate a given hed schema file.

Functions Demonstrated:
schema_validator.validate_schema - Takes a schema XML filename as input and returns all validation issues found within.
"""
from hed.schema import schema_validator

if __name__ == '__main__':
    # This old schema should produce many issues, including many duplicate terms
    local_hed_xml = "data/HED7.1.1.xml"
    issues = schema_validator.validate_schema(local_hed_xml)
    print(schema_validator.get_printable_issue_string(issues))

    # this should produce fairly minimal issues.
    local_hed_xml = "data/HED8.0.0-alpha.1.xml"
    issues = schema_validator.validate_schema(local_hed_xml)
    print(schema_validator.get_printable_issue_string(issues))
