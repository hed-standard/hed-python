from tests.test_translation_hed import TestHed


class HedStrings(TestHed):
    def test_invalid_characters(self):
        invalidString1 = '/Attribute/Object side/Left,/Participant/Effect{/Body part/Arm'
    #     invalidString2 = '/Attribute/Object side/Left,/Participant/Effect}/Body part/Arm'
    #     invalidString3 = '/Attribute/Object side/Left,/Participant/Effect[/Body part/Arm'
    #     invalidString4 = '/Attribute/Object side/Left,/Participant/Effect]/Body part/Arm'
    #     issues1 =
