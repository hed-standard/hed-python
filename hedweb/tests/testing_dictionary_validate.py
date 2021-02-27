import os
import json
import os.path
from urllib.parse import urlparse
from shutil import move
from hed.validator.hed_validator import HedValidator
from hed.util.column_def_group import ColumnDefGroup
from hed.schema.hed_schema_file import load_schema
from hed.util.error_types import ErrorContext

if __name__ == '__main__':

    dir_path = os.path.dirname(os.path.realpath(__file__))
    local_hed_file1 = os.path.join(dir_path, 'data/HED7.1.2.xml')
    local_hed_file2 = os.path.join(dir_path, 'data/HED8.0.0-alpha.1.xml')
    json_file = os.path.join(dir_path, 'data/example_dictionary.json')

    # Example 1

    hed_schema = load_schema(local_hed_file1)
    json_dictionary = ColumnDefGroup(json_file)
    issues = json_dictionary.validate_entries(hed_schema)
    issue_list = []
    for issue in issues:
        code = issue.get('code', "")
        message = issue.get('message', "")
        column_name = issue.get(ErrorContext.SIDECAR_COLUMN_NAME, "")
        if column_name:
            column_name = column_name[0]
        key_name = issue.get(ErrorContext.SIDECAR_KEY_NAME, "")
        if key_name:
            key_name = key_name[0]
        hed_string = issue.get(ErrorContext.SIDECAR_HED_STRING, "")
        issue_dict = {"code": code, "message": message, "column_name": column_name,
                      "key_name": key_name, "hed_string": hed_string}
        issue_list.append(issue_dict)
    print(issue_list)