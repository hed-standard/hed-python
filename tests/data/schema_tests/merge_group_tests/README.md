# Merge group test schemas

Test-only library schemas for the schema merge-group tests
(`tests/schema/test_schema_merge.py`), copied from hed-tests
`json_test_data/test_schemas/<library>/hedxml_unmerged/` at hed-tests commit
bde8a9a, plus the two vendored standard schemas (`HED8.4.0.xml`,
`HED8.5.0.xml`) from that repository's `hedxml/` folder so that loading is
hermetic. The libraries are in UNMERGED form and use the cache-convention
file names, so this folder can be passed as `xml_folder` to
`load_schema_version`. See the hed-tests README in that folder for what each
library version probes; the `.mediawiki` sources there are the source of
truth and are regenerated with `src/scripts/convert_test_schemas.py`.
