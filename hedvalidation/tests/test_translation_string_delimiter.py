import unittest
import os

from hedvalidator.hed_string_delimiter import HedStringDelimiter
from hedvalidator.hed_input_reader import HedInputReader
from hedvalidator.error_reporter import report_error_type
from hedvalidator.warning_reporter import report_warning_type
from hedvalidator.tag_validator import TagValidator
from hedvalidator.hed_dictionary import HedDictionary
from tests.test_translation_hed import TestHed

class HedStrings(TestHed):
    def test_invalid_characters(self):
        invalidString1 = '/Attribute/Object side/Left,/Participant/Effect{/Body part/Arm'
    #     invalidString2 = '/Attribute/Object side/Left,/Participant/Effect}/Body part/Arm'
    #     invalidString3 = '/Attribute/Object side/Left,/Participant/Effect[/Body part/Arm'
    #     invalidString4 = '/Attribute/Object side/Left,/Participant/Effect]/Body part/Arm'
    #     issues1 =