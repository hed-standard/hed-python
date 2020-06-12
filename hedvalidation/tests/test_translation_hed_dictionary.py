import unittest
import os

from hedvalidator.hed_string_delimiter import HedStringDelimiter
from hedvalidator.hed_input_reader import HedInputReader
from hedvalidator.error_reporter import report_error_type
from hedvalidator.warning_reporter import report_warning_type
from hedvalidator.tag_validator import TagValidator
from hedvalidator.hed_dictionary import HedDictionary
from tests.test_translation_hed import TestHed

local_hed_schema_file ='tests/data/HED.xml'
local_hed_schema_version = 'v1.6.0-restruct'
class RemoteHedSchemas(TestHed):
    def test_load_from_central_git_repo(self):
        remote_hed_schema_file = '7.0.4'
