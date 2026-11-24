"""Schema compliance: attributes on a schema property, the comma in the prologue, and error severities.

Issues #1511 (specification 3.1.4.8), #1505 (Appendix B SCHEMA_CHARACTER_INVALID d) and #1515 (Appendix B
SCHEMA_CHARACTER_INVALID and SCHEMA_ATTRIBUTE_VALUE_INVALID are errors).
"""

import unittest

from hed.errors import ErrorSeverity
from hed.schema import from_string

PROPERTY_SCHEMA = """HED version="1.1.0" library="score"
'''Prologue'''
!# start schema
'''BaseTag'''
!# end schema
'''Unit classes'''
'''Unit modifiers'''
'''Value classes'''
'''Schema attributes'''
{attributes}* deprecatedFrom {{elementProperty, stringRange}}
* hedId {{elementProperty, stringRange}}
* extensionAllowed {{boolRange}}
'''Properties'''
{prop}
* elementProperty
* stringRange
* boolRange
'''Epilogue'''
!# end hed
"""

LIBRARY_SCHEMA = """HED version="1.0.0" library="testlib" withStandard="8.5.0" unmerged="true"
'''Prologue'''
{prologue}
!# start schema
{tag}
!# end schema
'''Unit classes'''
'''Unit modifiers'''
'''Value classes'''
'''Schema attributes'''
'''Properties'''
'''Epilogue'''
{epilogue}
!# end hed
"""


def compliance(text):
    """Return (code, severity) of each issue, without the prerelease warning of a test library."""
    schema = from_string(text, schema_format=".mediawiki")
    return sorted(
        (issue["code"], issue["severity"])
        for issue in schema.check_compliance()
        if issue["code"] != "SCHEMA_PRERELEASE_VERSION_USED"
    )


def property_schema(prop, attributes=""):
    return PROPERTY_SCHEMA.format(prop=prop, attributes=attributes)


def library_schema(prologue="P.", epilogue="E.", tag="'''Tag-one'''"):
    return LIBRARY_SCHEMA.format(prologue=prologue, epilogue=epilogue, tag=tag)


class TestSchemaPropertyAttributes(unittest.TestCase):
    INVALID = [("SCHEMA_ATTRIBUTE_INVALID", ErrorSeverity.ERROR)]

    def test_deprecated_from_on_a_property_is_attribute_invalid(self):
        for label, attributes in [
            ("unused", ""),
            ("used by a live attribute", "* myAttribute {myProperty}\n"),
            ("used by a deprecated attribute", "* myAttribute {myProperty, deprecatedFrom=1.0.0}\n"),
        ]:
            with self.subTest(label):
                text = property_schema("* myProperty {deprecatedFrom=1.0.0}", attributes)
                self.assertEqual(compliance(text), self.INVALID)

    def test_other_attributes_on_a_property(self):
        self.assertEqual(compliance(property_schema("* myProperty {extensionAllowed}")), self.INVALID)
        self.assertEqual(compliance(property_schema("* myProperty {madeUp}")), self.INVALID)
        self.assertEqual(compliance(property_schema("* myProperty {hedId=HED_0040799}")), [])
        self.assertEqual(compliance(property_schema("* myProperty")), [])

    def test_the_attribute_still_loads_and_is_written_back(self):
        schema = from_string(property_schema("* myProperty {deprecatedFrom=1.0.0}"), schema_format=".mediawiki")
        self.assertEqual(schema.properties["myProperty"].attributes.get("deprecatedFrom"), "1.0.0")
        for text in (schema.get_as_mediawiki_string(), schema.get_as_xml_string(), schema.get_as_json_string()):
            self.assertIn("deprecatedFrom", text.split("myProperty", 1)[1][:200])


class TestPrologueComma(unittest.TestCase):
    def test_a_comma_is_allowed_in_the_prologue_and_epilogue(self):
        self.assertEqual(compliance(library_schema(prologue="A, B.")), [])
        self.assertEqual(compliance(library_schema(epilogue="A, B.")), [])

    def test_another_character_is_still_invalid(self):
        self.assertEqual(
            compliance(library_schema(prologue="A [B].")),
            [("SCHEMA_CHARACTER_INVALID", ErrorSeverity.ERROR)] * 2,
        )


class TestSchemaErrorSeverity(unittest.TestCase):
    def test_a_bad_character_in_a_tag_is_an_error(self):
        self.assertEqual(
            compliance(library_schema(tag="'''Tag$one'''")), [("SCHEMA_CHARACTER_INVALID", ErrorSeverity.ERROR)]
        )

    def test_a_unit_class_on_a_non_placeholder_is_an_error(self):
        self.assertEqual(
            compliance(library_schema(tag="'''Tag-one''' {unitClass=timeUnits}")),
            [("SCHEMA_ATTRIBUTE_VALUE_INVALID", ErrorSeverity.ERROR)],
        )


if __name__ == "__main__":
    unittest.main()
