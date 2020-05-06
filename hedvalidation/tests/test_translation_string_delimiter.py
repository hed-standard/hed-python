import unittest
import os

from hedvalidation.hed_string_delimiter import HedStringDelimiter
from hedvalidation.hed_input_reader import HedInputReader
from hedvalidation.error_reporter import report_error_type
from hedvalidation.warning_reporter import report_warning_type
from hedvalidation.tag_validator import TagValidator
from hedvalidation.hed_dictionary import HedDictionary
from tests.test_translation_hed import TestHed

class HedStrings(TestHed):
    def test_invalid_characters(self):
        invalidString1 = '/Attribute/Object side/Left,/Participant/Effect{/Body part/Arm'
    #     invalidString2 = '/Attribute/Object side/Left,/Participant/Effect}/Body part/Arm'
    #     invalidString3 = '/Attribute/Object side/Left,/Participant/Effect[/Body part/Arm'
    #     invalidString4 = '/Attribute/Object side/Left,/Participant/Effect]/Body part/Arm'
    #     issues1 =