import os
import pandas as pd
from hed.schema.hed_schema_file import from_string
from hed.util.event_file_input import EventFileInput
from hed.validator.hed_validator import HedValidator
from hed.schema.hed_schema_file import load_schema
from hed.util.column_def_group import ColumnDefGroup
from hed.util.error_reporter import get_printable_issue_string

if __name__ == '__main__':
    #schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
    with open(schema_path, "r") as myfile:
        schema_string = myfile.read()
    hed_schema = from_string(schema_string)

    print("to here")