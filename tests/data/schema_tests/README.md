# Schema test data

Tests load released standard schemas from the copies bundled with hedtools in `hed/schema/schema_data/`, with
`load_schema_version("8.2.0")`, never from a copy here. A test that needs the file itself uses
`bundled_standard_path` in `tests/schema/schema_test_helpers.py`. A test that names a released standard inside
an `xml_folder` (a version string is looked up only in that folder) builds a temporary folder with
`make_xml_folder` in the same module. `load_schema_version` returns one shared cached object per version, so a
test that changes its schema works on a `copy.deepcopy`.

## Full standard schemas kept as files

Each is released 8.0.0 with a deliberate edit, so the bundle cannot replace it:

- `HED8.0.0_2_value_classes.xml` - a tag with two value classes (edge-case format roundtrip test).
- `unknown_attribute.xml` - attributes the schema does not define (edge-case format roundtrip test).
- `HED8.0.0_2_value_classes.mediawiki`, `unknown_attribute.mediawiki` - the MediaWiki sources of the two above;
  no test reads them.
- `../validator_tests/HED8.0.0_added_tests.mediawiki` - test additions for the validator tests (for example
  `Item/Currency-test`).

Everything else here is a small edited fixture or fragment (`added_prop*`, `duplicate_unit*`,
`prologue_tests/`, `wiki_tests/`, `prerelease/` stubs) or a test library (`merge_tests/`,
`merge_group_tests/`, `HED_test*`).
