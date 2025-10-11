from hed.models import HedString
import unittest
from hed import load_schema_version
import copy


class TestHedStrings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.4.0")

    def validator_scalar(self, test_strings, expected_results, test_function):
        for test_key in test_strings:
            test_result = test_function(test_strings[test_key])
            expected_result = expected_results[test_key]
            self.assertEqual(test_result, expected_result, test_strings[test_key])

    def validator_list(self, test_strings, expected_results, test_function):
        for test_key in test_strings:
            test_result = test_function(test_strings[test_key])
            expected_result = expected_results[test_key]
            self.assertCountEqual(test_result, expected_result, test_strings[test_key])


class TestHedString(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.0.0")
        pass

    def test_constructor(self):
        test_strings = {
            "normal": "Tag1,Tag2",
            "normalParen": "(Tag1,Tag2)",
            "normalDoubleParen": "(Tag1,Tag2,(Tag3,Tag4))",
            "extraOpeningParen": "((Tag1,Tag2,(Tag3,Tag4))",
            "extra2OpeningParen": "(((Tag1,Tag2,(Tag3,Tag4))",
            "extraClosingParen": "(Tag1,Tag2,(Tag3,Tag4)))",
            "extra2ClosingParen": "(Tag1,Tag2,(Tag3,Tag4))))",
        }
        expected_result = {
            "normal": True,
            "normalParen": True,
            "normalDoubleParen": True,
            "extraOpeningParen": False,
            "extra2OpeningParen": False,
            "extraClosingParen": False,
            "extra2ClosingParen": False,
        }

        # Just make sure it doesn't crash while parsing super invalid strings.
        for name, string in test_strings.items():
            hed_string = HedString(string, self.schema)

            self.assertEqual(bool(hed_string), expected_result[name])
            if bool(hed_string):
                _ = hed_string.get_all_groups()
                _ = hed_string.get_all_tags()


class HedTagLists(TestHedStrings):
    def test_type(self):
        hed_string = "Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple"
        result = HedString.split_into_groups(hed_string, self.schema)
        self.assertIsInstance(result, list)

    def test_top_level_tags(self):
        hed_string = "Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple"
        result = HedString.split_into_groups(hed_string, self.schema)
        tags_as_strings = [str(tag) for tag in result]
        self.assertCountEqual(
            tags_as_strings,
            ["Event/Category/Experimental stimulus", "Item/Object/Vehicle/Train", "Attribute/Visual/Color/Purple"],
        )

    def test_group_tags(self):
        hed_string = (
            "/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),"
            "/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px "
        )
        string_obj = HedString(hed_string, self.schema)
        tags_as_strings = [str(tag) for tag in string_obj.children]
        self.assertCountEqual(
            tags_as_strings,
            [
                "/Action/Reach/To touch",
                "(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)",
                "/Attribute/Location/Screen/Top/70 px",
                "/Attribute/Location/Screen/Left/23 px",
            ],
        )

    def test_square_brackets_in_string(self):
        # just verifying this parses, square brackets do not validate
        hed_string = "[test_ref], Event/Sensory-event, Participant, ([test_ref2], Event)"
        string_obj = HedString(hed_string, self.schema)
        tags_as_strings = [str(tag) for tag in string_obj.children]
        self.assertCountEqual(tags_as_strings, ["[test_ref]", "Sensory-event", "Participant", "([test_ref2],Event)"])

    # Potentially restore some similar behavior later if desired.
    # We no longer automatically remove things like quotes.
    # def test_double_quotes(self):
    #     double_quote_string = 'Event/Category/Experimental stimulus,"Item/Object/Vehicle/Train",' \
    #                           'Attribute/Visual/Color/Purple '
    #     normal_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
    #     double_quote_result = HedString.split_into_groups(double_quote_string)
    #     normal_result = HedString.split_into_groups(normal_string)
    #     self.assertEqual(double_quote_result, normal_result)

    def test_blanks(self):
        test_strings = {
            "doubleTilde": "/Item/Object/Vehicle/Car~~/Attribute/Object control/Perturb",
            "doubleComma": "/Item/Object/Vehicle/Car,,/Attribute/Object control/Perturb",
            "doubleInvalidCharacter": "/Item/Object/Vehicle/Car[]/Attribute/Object control/Perturb",
            "trailingBlank": "/Item/Object/Vehicle/Car,/Attribute/Object control/Perturb,",
        }
        expected_list = [
            "/Item/Object/Vehicle/Car",
            "/Attribute/Object control/Perturb",
        ]
        expected_results = {
            "doubleTilde": [
                "/Item/Object/Vehicle/Car~~/Attribute/Object control/Perturb",
            ],
            "doubleComma": expected_list,
            "doubleInvalidCharacter": ["/Item/Object/Vehicle/Car[]/Attribute/Object control/Perturb"],
            "trailingBlank": expected_list,
        }

        def test_function(string):
            return [str(child) for child in HedString.split_into_groups(string, self.schema)]

        self.validator_list(test_strings, expected_results, test_function)


class ProcessedHedTags(TestHedStrings):
    def test_parsed_tags(self):
        hed_string = (
            "/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),"
            "/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px "
        )
        parsed_string = HedString(hed_string, self.schema)
        self.assertCountEqual(
            [str(tag) for tag in parsed_string.get_all_tags()],
            [
                "/Action/Reach/To touch",
                "/Attribute/Object side/Left",
                "/Participant/Effect/Body part/Arm",
                "/Attribute/Location/Screen/Top/70 px",
                "/Attribute/Location/Screen/Left/23 px",
            ],
        )
        self.assertCountEqual(
            [str(group) for group in parsed_string.get_all_groups()],
            [
                "/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),"
                "/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px",
                "(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)",
            ],
        )


class TestHedStringUtil(unittest.TestCase):
    def compare_split_results(self, test_strings, expected_results):
        for test_key in test_strings:
            test_string = test_strings[test_key]
            expected_result = expected_results[test_key]
            actual_results = HedString.split_hed_string(test_string)
            decoded_results = [test_string[start:end] for (is_tag, (start, end)) in actual_results]
            self.assertEqual(decoded_results, expected_result)

    def test_split_hed_string(self):
        test_strings = {
            "single": "Event",
            "double": "Event, Event/Extension",
            "singleAndGroup": "Event/Extension, (Event/Extension2, Event/Extension3)",
            "singleAndGroupWithBlank": "Event/Extension, (Event, ,Event/Extension3)",
            "manyParens": "Event/Extension,(((Event/Extension2, )(Event)",
            "manyParensEndingSpace": "Event/Extension,(((Event/Extension2, )(Event) ",
            "manyParensOpeningSpace": " Event/Extension,(((Event/Extension2, )(Event)",
            "manyParensBothSpace": " Event/Extension,(((Event/Extension2, )(Event ",
            "manyClosingParens": "Event/Extension, (Event/Extension2, ))(Event)",
        }
        expected_results = {
            "single": ["Event"],
            "double": ["Event", ", ", "Event/Extension"],
            "singleAndGroup": ["Event/Extension", ", ", "(", "Event/Extension2", ", ", "Event/Extension3", ")"],
            "singleAndGroupWithBlank": ["Event/Extension", ", ", "(", "Event", ", ", ",", "Event/Extension3", ")"],
            "manyParens": ["Event/Extension", ",", "(", "(", "(", "Event/Extension2", ", ", ")", "(", "Event", ")"],
            "manyParensEndingSpace": [
                "Event/Extension",
                ",",
                "(",
                "(",
                "(",
                "Event/Extension2",
                ", ",
                ")",
                "(",
                "Event",
                ") ",
            ],
            "manyParensOpeningSpace": [
                " ",
                "Event/Extension",
                ",",
                "(",
                "(",
                "(",
                "Event/Extension2",
                ", ",
                ")",
                "(",
                "Event",
                ")",
            ],
            "manyParensBothSpace": [
                " ",
                "Event/Extension",
                ",",
                "(",
                "(",
                "(",
                "Event/Extension2",
                ", ",
                ")",
                "(",
                "Event",
                " ",
            ],
            "manyClosingParens": ["Event/Extension", ", ", "(", "Event/Extension2", ", ", ")", ")", "(", "Event", ")"],
        }

        self.compare_split_results(test_strings, expected_results)


class TestHedStringShrinkDefs(unittest.TestCase):
    hed_schema = load_schema_version("8.0.0")

    def test_shrink_defs(self):
        test_strings = {
            1: "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2)),Event",
            2: "Event, ((Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2)),Event)",
            # this one shouldn't change as it doesn't have a parent
            3: "Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2),Event",
            # This one is an obviously invalid def, but still shrinks
            4: "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2), ThisDefIsInvalid),Event",
        }

        expected_results = {
            1: "Def/TestDefPlaceholder/2471,Event",
            2: "Event,(Def/TestDefPlaceholder/2471,Event)",
            3: "Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2),Event",
            4: "Def/TestDefPlaceholder/2471,Event",
        }

        for key, test_string in test_strings.items():
            hed_string = HedString(test_string, hed_schema=self.hed_schema)
            hed_string.shrink_defs()
            self.assertEqual(str(hed_string), expected_results[key])


class TestFromHedStrings(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema_version("8.1.0")
        self.hed_strings = [
            HedString("Event", self.schema),
            HedString("Action", self.schema),
            HedString("Age/20", self.schema),
            HedString("Item", self.schema),
        ]

    def test_from_hed_strings(self):
        combined_hed_string = HedString.from_hed_strings(self.hed_strings)

        # Test that the combined HED string is as expected
        self.assertEqual(combined_hed_string._hed_string, "Event,Action,Age/20,Item")

        # Test that the schema of the combined HED string is the same as the first HED string
        self.assertEqual(combined_hed_string._schema, self.schema)

        # Test that the contents of the combined HED string is the concatenation of the contents of all HED strings
        expected_contents = [child for hed_string in self.hed_strings for child in hed_string.children]
        self.assertEqual(combined_hed_string.children, expected_contents)

        # Test that the _from_strings attribute of the combined HED string is the list of original HED strings
        self.assertEqual(combined_hed_string._from_strings, self.hed_strings)

    def test_empty_hed_strings_list(self):
        with self.assertRaises(TypeError):
            HedString.from_hed_strings([])

    def test_none_hed_strings_list(self):
        with self.assertRaises(TypeError):
            HedString.from_hed_strings(None)

    def test_complex_hed_strings(self):
        complex_hed_strings = [
            HedString("Event,Action", self.schema),
            HedString("Age/20,Hand", self.schema),
            HedString("Item,(Leg, Nose)", self.schema),
        ]

        combined_hed_string = HedString.from_hed_strings(complex_hed_strings)

        # Test that the combined HED string is as expected
        self.assertEqual(combined_hed_string._hed_string, "Event,Action,Age/20,Hand,Item,(Leg, Nose)")

        # Test that the schema of the combined HED string is the same as the first HED string
        self.assertEqual(combined_hed_string._schema, self.schema)

        # Test that the contents of the combined HED string is the concatenation of the contents of all HED strings
        expected_contents = [child for hed_string in complex_hed_strings for child in hed_string.children]
        self.assertEqual(combined_hed_string.children, expected_contents)

        # Test that the _from_strings attribute of the combined HED string is the list of original HED strings
        self.assertEqual(combined_hed_string._from_strings, complex_hed_strings)

    def _verify_copied_string(self, original_hed_string):
        # Make a deepcopy of the original HedString
        copied_hed_string = copy.deepcopy(original_hed_string)

        # The copied HedString should not be the same object as the original
        self.assertNotEqual(id(original_hed_string), id(copied_hed_string))

        # The copied HedString should have the same _hed_string as the original
        self.assertEqual(copied_hed_string._hed_string, original_hed_string._hed_string)

        # The _children attribute of copied HedString should not be the same object as the original
        self.assertNotEqual(id(original_hed_string.children), id(copied_hed_string.children))

        # The _children attribute of copied HedString should have the same contents as the original
        self.assertEqual(copied_hed_string.children, original_hed_string.children)

        # The parent of each child in copied_hed_string._children should point to copied_hed_string
        for child in copied_hed_string.children:
            self.assertEqual(child._parent, copied_hed_string)

        # The _original_children and _from_strings attributes should also be deep copied
        self.assertNotEqual(id(original_hed_string._original_children), id(copied_hed_string._original_children))
        self.assertEqual(copied_hed_string._original_children, original_hed_string._original_children)
        if original_hed_string._from_strings:
            self.assertNotEqual(id(original_hed_string._from_strings), id(copied_hed_string._from_strings))
            self.assertEqual(copied_hed_string._from_strings, original_hed_string._from_strings)

    def test_deepcopy(self):
        original_hed_string = HedString("Event,Action", self.schema)

        self._verify_copied_string(original_hed_string)
        complex_hed_strings = [
            HedString("Event,Action", self.schema),
            HedString("Age/20,Hand", self.schema),
            HedString("Item,(Leg, Nose)", self.schema),
        ]

        combined_hed_string = HedString.from_hed_strings(complex_hed_strings)

        self._verify_copied_string(combined_hed_string)
