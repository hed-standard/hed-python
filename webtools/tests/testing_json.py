import os
import hed
from hed.models import EventsInput
from hed.schema.hed_schema_file import load_schema
from hed.validator.hed_validator import HedValidator
from hed.models import ColumnDefGroup
from hed.util.error_reporter import get_printable_issue_string

if __name__ == '__main__':
    str = open('D:/temp.txt', 'r').read()
    json_dictionary = ColumnDefGroup(json_string=str)
    print(str)