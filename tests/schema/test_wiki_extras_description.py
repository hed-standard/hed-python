"""A comma in the description of a MediaWiki Sources, Prefixes, or External annotations row (issue #1516).

The value of ``description`` runs from ``description=`` to the end of the row and may contain commas; the row is
split at commas only before the description pair (HED specification Appendix A.2.5.7). A piece before the
description pair that is not a ``name=value`` pair is WIKI_DELIMITERS_INVALID e.
"""

import unittest

from hed.errors.exceptions import HedExceptions, HedFileError
from hed.schema import from_string, load_schema_version
from hed.schema.schema_io import df_constants
from hed.schema.schema_io.wiki2schema import SchemaLoaderWiki

STANDARD_WIKI = """HED version="8.9.0"
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
'''External annotations'''
!# end hed
"""

LIBRARY_WIKI = STANDARD_WIKI.replace(
    'HED version="8.9.0"', 'HED version="1.0.0" library="testlib" withStandard="8.5.0" unmerged="true"'
)


def _row(description, link="https://x.org"):
    return f"* <nowiki>source=Mine,link={link},description={description}</nowiki>"


def _mine(schema):
    sources = schema.get_extras(df_constants.SOURCES_KEY)
    return sources[sources[df_constants.source] == "Mine"].to_dict("records")


class TestParseStarString(unittest.TestCase):
    def test_description_without_comma(self):
        result = SchemaLoaderWiki.parse_star_string("* source=Mine,link=https://x.org,description=General definitions.")
        self.assertEqual(result, {"source": "Mine", "link": "https://x.org", "description": "General definitions."})

    def test_description_with_comma(self):
        result = SchemaLoaderWiki.parse_star_string(
            "* source=Mine,link=https://x.org,description=Definitions, and more."
        )
        self.assertEqual(result["description"], "Definitions, and more.")
        self.assertEqual(len(result), 3)

    def test_description_with_comma_and_equals(self):
        result = SchemaLoaderWiki.parse_star_string(
            "* source=Mine,link=https://x.org,description=Definitions, see a=b."
        )
        self.assertEqual(result, {"source": "Mine", "link": "https://x.org", "description": "Definitions, see a=b."})

    def test_attribute_block_kept(self):
        result = SchemaLoaderWiki.parse_star_string(
            "* {inLibrary=lang} source=GOLD,link=http://purl.org/linguistics/gold,description=Linguistics, general."
        )
        self.assertEqual(result["inLibrary"], "lang")
        self.assertEqual(result["description"], "Linguistics, general.")

    def test_unpaired_pieces(self):
        self.assertEqual(
            SchemaLoaderWiki.find_unpaired_pieces("* source=Mine,link=https://x.org/a,b,description=D."), ["b"]
        )
        self.assertEqual(
            SchemaLoaderWiki.find_unpaired_pieces("* source=Mine,link=https://x.org,description=D, e."), []
        )
        self.assertEqual(SchemaLoaderWiki.find_unpaired_pieces("* {inLibrary=lang} source=M,description=D, e."), [])


class TestWikiExtrasDescriptionLoad(unittest.TestCase):
    def test_standard_rows(self):
        for description in ("General definitions.", "Definitions, and more.", "Definitions, see a=b."):
            with self.subTest(description=description):
                schema = from_string(STANDARD_WIKI.format(sources=_row(description)), schema_format=".mediawiki")
                self.assertEqual(
                    _mine(schema), [{"source": "Mine", "link": "https://x.org", "description": description}]
                )

    def test_unmerged_library_rows(self):
        # Before the fix, "Definitions, see a=b." raised KeyError while merging with the partner's Sources.
        for description in ("General definitions.", "Definitions, and more.", "Definitions, see a=b."):
            with self.subTest(description=description):
                schema = from_string(LIBRARY_WIKI.format(sources=_row(description)), schema_format=".mediawiki")
                rows = _mine(schema)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["description"], description)
                self.assertEqual(rows[0][df_constants.in_library], "testlib")
                self.assertEqual(
                    list(schema.get_extras(df_constants.SOURCES_KEY).columns),
                    [*df_constants.source_columns, df_constants.in_library],
                )

    def test_comma_in_link_is_fatal(self):
        text = STANDARD_WIKI.format(sources=_row("Bad.", link="https://x.org/a,b"))
        with self.assertRaises(HedFileError) as context:
            from_string(text, schema_format=".mediawiki")
        self.assertEqual(context.exception.code, HedExceptions.WIKI_DELIMITERS_INVALID)
        self.assertIn("['b']", context.exception.issues[0]["message"])


class TestWikiExtrasDescriptionRoundTrip(unittest.TestCase):
    def test_xml_to_mediawiki_and_back(self):
        # HedSchema.__eq__ does not compare the extras, so they are compared directly.
        schema = load_schema_version("8.5.0").get_as_xml_string()
        original = from_string(schema, schema_format=".xml")
        sources = original.get_extras(df_constants.SOURCES_KEY)
        sources.loc[sources.index[0], df_constants.description] = "Definitions, with a comma, and a=b."

        wiki = original.get_as_mediawiki_string()
        self.assertIn("description=Definitions, with a comma, and a=b.", wiki)
        from_wiki = from_string(wiki, schema_format=".mediawiki")
        back = from_string(from_wiki.get_as_xml_string(), schema_format=".xml")
        for reloaded in (from_wiki, back):
            reloaded_sources = reloaded.get_extras(df_constants.SOURCES_KEY)
            self.assertEqual(
                reloaded_sources[df_constants.source_columns].to_dict("records"),
                sources[df_constants.source_columns].to_dict("records"),
            )


if __name__ == "__main__":
    unittest.main()
