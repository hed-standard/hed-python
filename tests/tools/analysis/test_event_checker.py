import unittest
from hed.errors.error_types import TagQualityErrors
from hed.schema import load_schema_version
from hed.models.hed_string import HedString
from hed.tools.analysis.event_checker import EventChecker


class TestEventChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hed_schema = load_schema_version('8.3.0')

    def test_no_event_tag(self):
        hed_strings = ['Action, (Participant-response, Red)']
        for hed_string in hed_strings:
            hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
            checker = EventChecker(hed_obj, 0)
            self.assertEqual(checker.issues[0]["code"], TagQualityErrors.MISSING_EVENT_TYPE)

    def test_event_without_task_role(self):
        hed_strings = ['Sensory-event, (Red, Blue)', '((Agent-action, Red))']
        for hed_string in hed_strings:
            hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
            checker = EventChecker(hed_obj, 2)
            self.assertEqual(checker.issues[0]["code"], TagQualityErrors.MISSING_TASK_ROLE)

    def test_event_with_task_role(self):
        hed_strings = ['(Sensory-event, (Experimental-stimulus, Blue, Green))',
                       '((Agent-action, Participant-response, Red))']
        for hed_string in hed_strings:
            hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
            checker = EventChecker(hed_obj, 2)
            self.assertEqual(checker.issues, [])

    def test_improperly_grouped_event_tags(self):
        hed_strings = ['Sensory-event, (Red, Blue), Experiment-control',
                       '((Sensory-event, (Red, Blue), Experiment-control))']
        for hed_string in hed_strings:
            hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
            checker = EventChecker(hed_obj, 2)
            self.assertEqual(checker.issues[0]["code"], TagQualityErrors.IMPROPER_TAG_GROUPING)

    def test_nested_group_with_event_and_task_role(self):
        hed_strings = ['Sensory-event, ((Experimental-stimulus, Red))', '(Experiment-control, Incidental)']
        for hed_string in hed_strings:
            hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
            checker = EventChecker(hed_obj, 5)
            self.assertEqual(checker.issues, [])

    def test_empty_hed_string(self):
        checker = EventChecker(None, 6)
        self.assertEqual(checker.issues, [])

    def test_flat_event_with_task_role(self):
        hed_string = 'Agent-action, Participant-response, Red'
        hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
        checker = EventChecker(hed_obj, 7)
        self.assertEqual(checker.issues, [])

    def test_task_role_without_event(self):
        hed_string = '(Experimental-stimulus, Green)'
        hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
        checker = EventChecker(hed_obj, 8)
        self.assertEqual(checker.issues[0]["code"], TagQualityErrors.MISSING_EVENT_TYPE)

    def test_multiple_event_tags_mixed_grouping(self):
        hed_string = 'Sensory-event, (Agent-action, Instructional)'
        hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
        checker = EventChecker(hed_obj, 9)
        self.assertEqual(checker.issues[0]["code"], TagQualityErrors.IMPROPER_TAG_GROUPING)

    def test_empty_nested_group(self):
        hed_string = '(())'
        hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
        checker = EventChecker(hed_obj, 10)
        self.assertEqual(checker.issues[0]["code"], TagQualityErrors.MISSING_EVENT_TYPE)

if __name__ == '__main__':
    unittest.main()