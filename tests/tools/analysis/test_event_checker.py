import unittest
from hed.errors.error_types import TagQualityErrors
from hed.schema import load_schema_version
from hed.models.hed_string import HedString
from hed.tools.analysis.event_checker import EventChecker


class TestEventChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hed_schema = load_schema_version('8.3.0')

    def check_issues(self, hed_string, expected_code=None, line_number=0):
        hed_obj = HedString(hed_string, hed_schema=self.hed_schema)
        checker = EventChecker(hed_obj, line_number)
        if expected_code is None:
            self.assertEqual(checker.issues, [])
        else:
            self.assertTrue(checker.issues)
            self.assertEqual(checker.issues[0]["code"], expected_code)

    def test_no_event_tag(self):
        self.check_issues('Action, (Participant-response, Red)', TagQualityErrors.MISSING_EVENT_TYPE)

    def test_event_without_task_role(self):
        hed_strings = ['Sensory-event, (Red, Blue)', '((Agent-action, Red))']
        for s in hed_strings:
            with self.subTest(s=s):
                self.check_issues(s, TagQualityErrors.MISSING_TASK_ROLE)

    def test_event_with_task_role(self):
        hed_strings = [
            '(Sensory-event, Visual-presentation, (Experimental-stimulus, Blue, Green))',
            '((Agent-action, Participant-response, Red, Jump))'
        ]
        for s in hed_strings:
            with self.subTest(s=s):
                self.check_issues(s)

    def test_event_missing_sensory_presentation(self):
        self.check_issues('(Sensory-event, Experimental-stimulus)', TagQualityErrors.MISSING_SENSORY_PRESENTATION)

    def test_event_with_sensory_presentation(self):
        self.check_issues('(Sensory-event, Experimental-stimulus, Auditory-presentation)')

    def test_event_missing_action_tag(self):
        self.check_issues('(Agent-action, Participant-response)', TagQualityErrors.MISSING_ACTION_TAG)

    def test_non_task_event_tag_no_task_role(self):
        # Should not raise missing task role for non-task event
        self.check_issues('(Data-feature, Blue)')

    def test_improperly_grouped_event_tags(self):
        hed_strings = ['Sensory-event, (Red, Blue), Experiment-control',
                       '((Sensory-event, (Red, Blue), Experiment-control))']
        for s in hed_strings:
            with self.subTest(s=s):
                self.check_issues(s, TagQualityErrors.IMPROPER_EVENT_GROUPS)

    def test_nested_group_with_event_and_task_role(self):
        hed_strings = ['Sensory-event, Visual-presentation, ((Experimental-stimulus, Red))', '(Experiment-control, Incidental)']
        for s in hed_strings:
            with self.subTest(s=s):
                self.check_issues(s)

    def test_empty_hed_string(self):
        checker = EventChecker(None, 6)
        self.assertEqual(checker.issues, [])

    def test_flat_event_with_task_role(self):
        self.check_issues('Agent-action, Participant-response, Red, Jump')

    def test_task_role_without_event(self):
        self.check_issues('(Experimental-stimulus, Green)', TagQualityErrors.MISSING_EVENT_TYPE)

    def test_multiple_event_tags_mixed_grouping(self):
        self.check_issues('Sensory-event, (Agent-action, Instructional)', TagQualityErrors.IMPROPER_EVENT_GROUPS)

    def test_empty_nested_group(self):
        self.check_issues('(())', TagQualityErrors.MISSING_EVENT_TYPE)

    def test_multiple_properly_grouped_events(self):
        hed_string = '((Sensory-event, Experimental-stimulus, Visual-presentation)), ((Agent-action, Participant-response, Press))'
        self.check_issues(hed_string)

if __name__ == '__main__':
    unittest.main()