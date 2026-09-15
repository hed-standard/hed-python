# Empty extras sections fixtures

The mouse 1.0.0 library (partnered with HED 8.5.0, unmerged) adds no
Sources, Prefixes, or External annotations of its own. These fixtures pin the
reader and writer behavior for the three extras sections
(`tests/schema/test_schema_extras_comprehensive.py`,
`tests/schema/test_schema_format_roundtrip.py`, `tests/schema/test_schema_compare.py`).

- `no_sections/` - files that omit the three sections, as hedtools wrote them
  before the sections were always written. `HED_mouse_1.0.0.mediawiki` is a copy
  of hed-schemas `library_schemas/mouse/prerelease/HED_mouse_1.0.0.mediawiki` at
  hed-schemas commit 909c5fa; the `.xml`, `.json`, and TSV folder were saved
  unmerged from that file with hedtools at hed-python commit 1f73c977 (the TSV
  folder then had its `_Sources.tsv`, `_Prefixes.tsv`, and
  `_AnnotationPropertyExternal.tsv` files removed).
- `empty_sections/` - the same schema saved unmerged in all four formats by
  hedtools after the change: the three sections are present and empty.

Regenerate with `.status/scratch/make_empty_extras_fixtures.py <subdir>` (a
throwaway script; the recipe above is the record) rather than editing by hand.
Loading these fixtures needs the HED 8.5.0 partner from the schema cache.
