import unittest


from hed.validator import tag_validator_util
from tests.validator.test_tag_validator import TestHed


class StringUtilityFunctions(TestHed):
    def test_clock_face_times(self):
        valid_test_strings = {
            'validPM': '23:52',
            'validMidnight': '00:55',
            'validHour': '11:00',
            'validSingleDigitHour': '08:30',
            'validSeconds': '19:33:47',
        }
        invalid_test_strings = {
            'invalidDate': '8/8/2019',
            'invalidHour': '25:11',
            'invalidSingleDigitHour': '8:30',
            'invalidMinute': '12:65',
            'invalidSecond': '15:45:82',
            'invalidTimeZone': '16:25:51+00:00',
            'invalidMilliseconds': '17:31:05.123',
            'invalidMicroseconds': '09:21:16.123456',
            'invalidDateTime': '2000-01-01T00:55:00',
            'invalidString': 'not a time',
        }
        for string in valid_test_strings.values():
            result = tag_validator_util.is_clock_face_time(string)
            self.assertEqual(result, True, string)
        for string in invalid_test_strings.values():
            result = tag_validator_util.is_clock_face_time(string)
            self.assertEqual(result, False, string)

    def test_date_times(self):
        valid_test_strings = {
            'validPM': '2000-01-01T23:52:00',
            'validMidnight': '2000-01-01T00:55:00',
            'validHour': '2000-01-01T11:00:00',
            'validSingleDigitHour': '2000-01-01T08:30:00',
            'validSeconds': '2000-01-01T19:33:47',
            'validMilliseconds': '2000-01-01T17:31:05.123',
            'validMicroseconds': '2000-01-01T09:21:16.123456',
        }
        invalid_test_strings = {
            'invalidDate': '8/8/2019',
            'invalidTime': '00:55:00',
            'invalidHour': '2000-01-01T25:11',
            'invalidSingleDigitHour': '2000-01-01T8:30',
            'invalidMinute': '2000-01-01T12:65',
            'invalidSecond': '2000-01-01T15:45:82',
            'invalidTimeZone': '2000-01-01T16:25:51+00:00',
            'invalidString': 'not a time',
        }
        for string in valid_test_strings.values():
            result = tag_validator_util.is_date_time(string)
            self.assertEqual(result, True, string)
        for string in invalid_test_strings.values():
            result = tag_validator_util.is_date_time(string)
            self.assertEqual(result, False, string)



if __name__ == '__main__':
    unittest.main()
