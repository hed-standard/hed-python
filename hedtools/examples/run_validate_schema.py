"""
Example of how to validate a given hed schema file.

Functions Demonstrated:
hed_schema.check_compliance - Checks if a HedSchema object is hed3 compatible.
"""

import hed

if __name__ == '__main__':
    # This old schema should produce many issues, including many duplicate terms
    local_hed_xml = "data/HED7.1.1.xml"
    hed_schema = hed.schema.load_schema(local_hed_xml)
    issues = hed_schema.check_compliance()
    print(hed.get_printable_issue_string(issues))

    # this should produce fairly minimal issues.
    local_hed_xml = "data/HED8.0.0-alpha.1.xml"
    issues = hed_schema.check_compliance()
    print(hed.get_printable_issue_string(issues))
