"""Schema compliance: property attributes, the prologue comma, error severities and repeated extras rows.

Issues #1511 (specification 3.1.4.8), #1505 (Appendix B SCHEMA_CHARACTER_INVALID d), #1515 (Appendix B
SCHEMA_CHARACTER_INVALID and SCHEMA_ATTRIBUTE_VALUE_INVALID are errors) and #1504 (Appendix B
SCHEMA_LIBRARY_INVALID h).
"""

import os
import unittest

import hed
from hed.errors import ErrorSeverity
from hed.schema import from_string, load_schema

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


EXTRAS_SCHEMA = """HED version="1.0.0" library="testlib" withStandard="{standard}" unmerged="true"
'''Prologue'''
P.
!# start schema
'''Tag-one'''
!# end schema
'''Unit classes'''
'''Unit modifiers'''
'''Value classes'''
'''Schema attributes'''
'''Properties'''
'''Epilogue'''
E.
'''Sources'''
{sources}
'''Prefixes'''
{prefixes}
'''External annotations'''
!# end hed
"""
REPEATED_SOURCE = "* <nowiki>source=Original,link=https://www.hedtags.org,description=Not the partner's text.</nowiki>"
REPEATED_PREFIX = "* <nowiki>prefix=dc:,namespace=http://purl.org/dc/elements/1.1/,description=Repeat.</nowiki>"
NEW_SOURCE = "* <nowiki>source=Mine,link=https://www.hedtags.org,description=A row of its own.</nowiki>"


def extras_codes(standard, sources="", prefixes=""):
    text = EXTRAS_SCHEMA.format(standard=standard, sources=sources, prefixes=prefixes)
    return compliance(text)


class TestUnmergedLibraryExtrasKeys(unittest.TestCase):
    INVALID = [("SCHEMA_LIBRARY_INVALID", ErrorSeverity.ERROR)]

    def test_a_row_with_the_key_of_a_partner_row_is_invalid(self):
        self.assertEqual(extras_codes("8.5.0", sources=REPEATED_SOURCE), self.INVALID)
        self.assertEqual(extras_codes("8.5.0", prefixes=REPEATED_PREFIX), self.INVALID)
        self.assertEqual(extras_codes("8.4.0", prefixes=REPEATED_PREFIX), self.INVALID)

    def test_a_row_of_its_own_is_valid(self):
        self.assertEqual(extras_codes("8.5.0", sources=NEW_SOURCE), [])

    def test_the_released_libraries_that_repeat_partner_rows_load_but_are_not_compliant(self):
        data = os.path.join(os.path.dirname(hed.__file__), "schema", "schema_data")
        for name in ("HED_lang_1.1.0.xml", "HED_score_2.1.0.xml"):
            with self.subTest(name=name):
                codes = [issue["code"] for issue in load_schema(os.path.join(data, name)).check_compliance()]
                self.assertIn("SCHEMA_LIBRARY_INVALID", codes)

    def test_the_other_bundled_libraries_are_compliant(self):
        data = os.path.join(os.path.dirname(hed.__file__), "schema", "schema_data")
        for name in ("HED_lang_1.2.0.xml", "HED_score_2.2.0.xml"):
            with self.subTest(name=name):
                codes = [issue["code"] for issue in load_schema(os.path.join(data, name)).check_compliance()]
                self.assertNotIn("SCHEMA_LIBRARY_INVALID", codes)


class TestUnmergedSaveDropsPartnerRows(unittest.TestCase):
    def unmerged_rows(self, schema):
        """Return the Sources and Prefixes keys written by an unmerged mediawiki save."""
        text = schema.get_as_mediawiki_string(save_merged=False)
        return [
            line.split(",", 1)[0][len("* <nowiki>") :] for line in text.splitlines() if line.startswith("* <nowiki>")
        ]

    def test_a_merged_round_trip_writes_only_the_library_rows(self):
        library = from_string(EXTRAS_SCHEMA.format(standard="8.5.0", sources=NEW_SOURCE, prefixes=""), ".mediawiki")
        merged = from_string(library.get_as_xml_string(save_merged=True), schema_format=".xml")
        self.assertIn("prefix=dc:", merged.get_as_mediawiki_string(save_merged=True))
        self.assertEqual(self.unmerged_rows(merged), ["source=Mine"])

    def test_a_repeated_partner_row_is_not_written_back(self):
        text = EXTRAS_SCHEMA.format(standard="8.5.0", sources=REPEATED_SOURCE + "\n" + NEW_SOURCE, prefixes="")
        self.assertEqual(self.unmerged_rows(from_string(text, ".mediawiki")), ["source=Mine"])

    def test_a_released_library_saved_unmerged_is_compliant(self):
        data = os.path.join(os.path.dirname(hed.__file__), "schema", "schema_data")
        released = load_schema(os.path.join(data, "HED_score_2.1.0.xml"))  # repeats 30 partner rows
        resaved = from_string(released.get_as_mediawiki_string(save_merged=False), schema_format=".mediawiki")
        codes = [issue["code"] for issue in resaved.check_compliance()]
        self.assertNotIn("SCHEMA_LIBRARY_INVALID", codes)
        self.assertIn("Beniczky ea 2013", resaved.get_as_mediawiki_string(save_merged=False))


if __name__ == "__main__":
    unittest.main()
