# Merge group test schemas

Test-only library schemas for the schema merge-group tests
(`tests/schema/test_schema_merge.py`), copied from hed-tests
`json_test_data/test_schemas/<library>/hedxml_unmerged/` at hed-tests commit
ccfb308. The libraries are in UNMERGED form and use the cache-convention file
names. Their partner standards (8.4.0 and 8.5.0) are not copied here: the tests
build a temporary `xml_folder` from this folder plus the copies bundled with
hedtools in `hed/schema/schema_data/` (`make_xml_folder` in
`tests/schema/schema_test_helpers.py`), so loading stays hermetic. When
re-copying from hed-tests, do not copy its `HED8.*.xml` standards back in. See the hed-tests README in that folder for what each
library version probes; the `.mediawiki` sources there are the source of
truth and are regenerated with `src/scripts/convert_test_schemas.py`.
