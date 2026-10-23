# Release 1.3.0 October 23, 2026

This release implements HED specification 4.0.0 (reserved tags, column names and padded values, tag-extension rules, value-text and character sets, BIDS date-times, compound units) and bundles HED 8.5.0. Many annotations that passed under 1.2.0 now give errors, and tabular validation reports issues differently: read the upgrade notes first. Runtime dependencies and supported Python versions (3.10 and later) are unchanged.

## Upgrade notes

These changes can alter validation results or break code written against 1.2.0.

- **Tabular validation runs in stages and stops at the first stage with an error.** A file's column names are checked first, then its sidecar, then each column's distinct values, then each distinct `HED`-column string, and only then the assembled rows (group-level, onset and temporal checks). Warnings never stop the run. A file whose sidecar has errors now reports only the sidecar's issues, once each, rather than once per row; fix them and run again to see later checks.
- **A bad value is reported once, not once per row.** An issue found in a column value or a `HED`-column string is reported at the first row that holds it, with a new `row_count` key giving the number of rows. Code that counts issues will see much smaller numbers.
- **`SpreadsheetValidator.validate` has a new signature:** `validate(source, sidecar=None, extra_def_dicts=None, name=None, error_handler=None, row_offset=None, validate_sidecar=True)`. The second positional argument is now the sidecar; passing a definition dictionary there raises `TypeError`.
- **New errors for annotations that used to pass.** In particular: a repeated, padded or blank column name and a padded value in an annotated column (`TABULAR_INVALID`); a padded sidecar key (`SIDECAR_INVALID`); an extension term with no letter such as `Item/Blech/3` (`TAG_EXTENSION_INVALID`); `#` after an extension in a sidecar (`PLACEHOLDER_INVALID`); `(Delay/3 s)` without an inner group (`TEMPORAL_TAG_ERROR`); a double quote anywhere in a HED string (`CHARACTER_INVALID`); a date-time that is not a BIDS Datetime or not a real date (`VALUE_INVALID`); unit names in the wrong case such as `Milliseconds` (`UNITS_INVALID`). Details below.
- **`NaN` in a TSV file is a value, not a missing cell.** Only an empty cell and `n/a` are missing. `NaN`, `NA`, `NULL`, `None` and the other pandas default NA strings are now validated like any other value.
- **Column names are used exactly as written.** They are never trimmed, and a sidecar key or column selector must match a column name exactly. A blank column name no longer raises `HedFileError` when the file is loaded; validation reports it as `TABULAR_INVALID`. Text files are read without CSV quoting, so a double quote is an ordinary character.
- **Changed error codes.** `SchemaAttributeErrors.SCHEMA_MISSING_EXTRA_VALUE` is now an alias whose value is the string `"SCHEMA_MISSING_EXTRA"`, so code comparing issue codes to the literal `"SCHEMA_MISSING_EXTRA_VALUE"` must change. The warnings `SCHEMA_ANNOTATION_PREFIX_MISSING`, `SCHEMA_ANNOTATION_EXTERNAL_MISSING` and `SCHEMA_ANNOTATION_SOURCE_MISSING` are replaced by `SCHEMA_ANNOTATION_INVALID`. A tilde is `CHARACTER_INVALID` instead of `TILDES_UNSUPPORTED`. Extending a reserved tag (`Onset/Blah`) is `TAG_EXTENSION_INVALID` instead of `TEMPORAL_TAG_ERROR`. A schema listed twice in one merge group fails with `SCHEMA_LOAD_FAILED` instead of `SCHEMA_LIBRARY_INVALID`.
- **`Sidecar.validate` no longer reports `REQUIRED_TAG_MISSING`**, because a sidecar string is only part of a row. The check runs on the assembled row.
- **Removed functions and data files** are listed under "Removed" below.

## New features

### Schemas

- HED 8.5.0 is bundled, with the libraries score 1.2.0, score 2.2.0 and lang 1.2.0, so they load offline. `load_schema_version()` with no version now loads 8.5.0. The bundled partnered libraries (lang 1.0.0 to 1.2.0, score 1.1.0 to 2.2.0) are stored unmerged, which shrinks the package; they load the same as the merged releases.
- Schema merge groups follow HED specification 3.1.2.4. `load_schema_version` resolves each namespace of a version list as a merge group: all libraries must share one standard partner, an unpartnered library must be alone in its namespace, and the partner standard version may be listed beside its libraries. The rules are checked from the schema headers before any file is parsed, and the standard schema is loaded at most once per group. Libraries in one group may declare the same element if the declarations agree; it carries a comma-separated `inLibrary` value. The merged schema's Sources, Prefixes and External annotations combine every library's rows with the partner's.
- `load_schema` and `from_string` take a new `xml_folder` argument, searched first for the standard partner of an unmerged partnered library.
- `HedSchema.unmerged_libraries`: the libraries in a schema that were loaded from an unmerged file.
- `anyUnits` (HED 8.5.0, `Quantity/#`): the placeholder accepts a unit from any unit class, listed or derived; a listed unit wins over a derived form (`dB` is the decibel). `value_as_default_unit` converts to the default unit of the class that matched.
- `HedTag.default_unit` resolves a `defaultUnits` value that is a derived form of a listed unit (such as `mA` in HED 8.5.0) to the unit it derives from.

### Validation

- Public staged-validation methods on `SpreadsheetValidator`: `validate_column_names`, `validate_column_structure`, `validate_value_column`, `validate_categorical_column`, `validate_padded_values`, `validate_hed_column` (with `full_string=` for callers that never assemble rows) and `validate_assembled`. `SpreadsheetValidator(hed_schema, def_dicts=None)` takes definitions for these calls.
- The `ColumnSource` protocol (`hed.models.column_source`): validation reads a table through `column_names()`, `distinct_values()`, `column_mapper()` and `as_base_input()`, so tables other than files (for example NWB tables through ndx-hed) get the same checks. `BaseInput` implements it; `ListColumnSource` wraps plain lists; `hed.models.distinct_values` builds the value-to-rows map; `check_column_names` applies the column-name rules.
- `BaseInput.validate`, `TabularInput.validate` and `SpreadsheetValidator.validate` take `validate_sidecar=` (skip a sidecar you already validated) and `row_offset=` (`0` reports 0-based data rows; the default is still 1-based file lines counting the header).
- `row_count` on issues; `get_printable_issue_string` and `get_printable_issue_string_html` add `[first of N rows with this value]` when N > 1.
- `HedValidator.run_full_string_checks(hed_string, *, required_tags=True, unique_tags=True)` can skip the row-wide checks when validating part of a row.
- New read-only properties `BaseInput.duplicate_columns`, `BaseInput.padded_columns` and `BaseInput.blank_columns`. Repeated names are read from the raw header, before pandas renames the second copy.
- One character table shared with the specification: `hed/validator/data/character_sets.json`, read by `hed.validator.util.character_sets` (`CharacterSets.load()`, `code_point()`). From standard schema 8.5.0, and in libraries partnered with 8.5.0 or later, a value class's `allowedCharacter` declaration defines its characters; earlier schemas use the file's per-class defaults.
- The `value-text` character set: from standard schema 8.5.0, a textClass value (`Description/#`, `Label/#`, `Parameter-value/#`, ...) may not contain `(`, `)`, `#` or `~` (`CHARACTER_INVALID`).
- `CHARACTER_INVALID` and `VALUE_INVALID` messages name the character, its code point, its index and the allowed set, and the issues carry new `char_set` and `code_point` keys.

### Schema tools

- Schema compliance (`check_compliance`, `hedpy schema validate`):
  - New error `SCHEMA_RESERVED_INVALID`: a standard schema must define the reserved tags with their required attributes, and a reserved tag may have no child other than `#`.
  - New `SCHEMA_LIBRARY_INVALID` reasons: an unmerged partnered library may not declare a Properties section (j); a merged one's must equal its partner's (k); no library element may carry `reserved` (l), define a tag with a reserved name (m), or root a node under a reserved tag (n).
  - A unit already accepted as an SI-modified or plural form of another unit of its class (`uV` beside `V`) is `SCHEMA_DUPLICATE_NODE`, for standard schemas 8.5.0 and later and the libraries partnered with them.
  - Unit class rules: a `#` with more than one `unitClass`, or with a `unitClass` but not `valueClass=numericClass` (8.5.0 and later), is `SCHEMA_ATTRIBUTE_VALUE_INVALID`; `anyUnits` may list no units or `defaultUnits`; one unit string derived by two classes is `SCHEMA_DUPLICATE_NODE`.
- `hed_validate_schemas --require-ids` and `hedpy schema validate --require-ids` list every element without a hedId and fail; `hed_validate_schemas` accepts `.json` schema files; `hedpy schema add-ids` works (it crashed with an argument error in 1.2.0).
- `hedpy schema convert` (`hed_update_schemas`) drops a spreadsheet row whose element is gone from the schema when its hedId is listed under `retired_ids` in hed-schemas `library_data.json`, and never reassigns a retired hedId. New helper `hed.schema.schema_io.hed_id_util.remove_retired_rows`.
- `SchemaComparer`: a removed unit the newer schema still derives is reported as Patch with the derivation (`Unit uV removed from electricPotentialUnits; still derivable as u + V`); for a partnered library, changes are marked with `origin` and the partner's changes are printed in a separate `From the partner standard schema` block; a prologue or epilogue change lists the removed and added lines; `compare_differences` takes `use_markdown=` (default True) and its markdown follows the hed-schemas `PRERELEASE_CHANGES.md` layout.

### Other tools

- `hed.tools.util.data_util.remove_rows_by_value(df, value, column_list=None)` returns a new dataframe without the rows where any of the columns holds `value`, keeping the original index.

## Changed

### Validation rules (HED specification 4.0.0)

- Reserved tags are validated from the `reserved_tags.json` file the specification publishes, for every standard schema from 8.0.0. A reserved tag may not be extended (`Onset/Blah`, `Onset/#`: `TAG_EXTENSION_INVALID`); a `Delay` group needs its inner group (`(Delay/3 s)`: `TEMPORAL_TAG_ERROR`); `Delay` and `Duration` need a value in every schema version (`TAG_REQUIRES_CHILD`); only `#` may follow a definition name (`DEFINITION_INVALID`); a `Def` may not sit at the top level of a `Duration` or `Delay` group (`TEMPORAL_TAG_ERROR`); a `{column}` reference may not appear in a `Definition` or `Event-context` group. A content error in a reserved group carries the reserved tag's own code.
- An extension term must contain at least one letter (3.2.5 rule 6): `Item/Blech/3`, `Item/1-2`, `Item/_` and, from 8.3.0, a non-ASCII term with no letter are `TAG_EXTENSION_INVALID`, reported at the term; `Item/Blech/1red` and `Item/3D-printout` stay valid. The rule applies to every schema version, so `Clock-face/08:30` under a schema before 8.3.0 (where `Clock-face` takes no value) is now an error.
- `#` after an extension (`Item/#`, `Item/Blech/#`) is `PLACEHOLDER_INVALID` in a sidecar too; 1.2.0 accepted it there.
- Tag extensions may contain non-ASCII characters from the `nonascii` set (code 160 and above).
- Date-time values follow the BIDS Datetime format, `YYYY-MM-DDThh:mm:ss[.ffffff][Z|+hh:mm|-hh:mm]`, and the date must exist (`2026-02-31` is `VALUE_INVALID`). 1.2.0 accepted `2026-13-45T99:99:99`.
- A double quote is `CHARACTER_INVALID` anywhere in a HED string. Control characters (codes 0-31 and 127-159) are forbidden in every schema version; other non-ASCII characters such as a no-break space are accepted in text values from 8.3.0.
- A placeholder with no value class (`URL/#`, `DOI/#`, `UUID/#`, ...) is checked against `value-text`, so `DOI/10.1000/abc?x=1` is now valid.
- A definition repeated with identical contents is accepted; different contents are still `DEFINITION_INVALID`.
- `Def-expand` contents are compared without regard to the order of tags and groups.

### Tabular files and sidecars

- `TABULAR_INVALID` is reported for a column name that is repeated, padded (begins or ends with whitespace) or blank, and for a padded value in a column the sidecar annotates with HED. Column-name errors stop validation before the sidecar is checked; a padded value is reported once per column at its first row. The `HED` and `onset` columns are not checked for padded values.
- `SIDECAR_INVALID` is reported for a padded top-level sidecar key and for a padded key under `"HED"` in a categorical entry.
- Excel header cells and DataFrame column labels are converted to text at load: a whole number becomes `"1"`, and None or NaN becomes `""` (a blank name).
- `BaseInput.assemble` (and `dataframe_a`, `series_a`, `series_filtered`, `EventManager`) raises `HedFileError` (`BAD_COLUMN_NAMES`) for a table with a padded, blank or repeated column name instead of assembling it wrongly.
- A value column referenced by `{column}` is checked in every row, and a value that would break the HED string it is substituted into (`a(b`, `a~b`, `a#b`) is rejected at the value stage.
- In a file with an `onset` column, a `Delay` or `Duration` value that cannot be converted to its default unit is `TEMPORAL_TAG_ERROR`; an invalid `Delay` unit used to raise `TypeError`. Under 8.0.0, whose time units have no conversion factors, a value in seconds is taken as it is. `split_delay_tags` and `TemporalEvent` raise `HedFileError` naming the tag instead of computing a wrong onset.
- Rows with equal onsets keep their file order when a table is sorted by onset, so an issue in rows sharing an onset is reported at the first of them.
- `Sidecar.validate`, `TabularInput.validate` and `SpreadsheetValidator.validate` add a file-name context only when a name is given (`name=""` suppresses it), so callers validating non-file tables can supply their own context.
- `BidsFileGroup` validates each merged sidecar once and skips a data file whose merged sidecar has errors, unless its header has a bad column name; `hedpy validate tabular` no longer validates the sidecar twice. Directories are walked in sorted order on every OS.

### Units

- Unit names are case-sensitive, like symbols and modifiers: `Time-value/5 milliseconds` is valid, while `Milliseconds`, `MS` and `UV` are `UNITS_INVALID`. Unit names may be pluralized; symbols may not.
- Compound SI units (`m-per-s`, `m-per-s^2`, `m^3`, `mol-per-L`) take one SI modifier on each component: `Speed/3 cm-per-us` is now valid, and conversions are computed per component (`mm^3` converts to 1e-9 m^3; 1.2.0 gave 1e-3).
- `HedTag.value_as_default_unit` returns None when the value is not numeric, the unit is not valid, or the unit has no `conversionFactor` (it used to return the bare number).

### Schemas

- Schema writers (MediaWiki, XML, JSON) always write the Sources, Prefixes and External annotations sections, empty when the schema has none.
- The annotation-attribute check uses one warning, `SCHEMA_ANNOTATION_INVALID`, with four reasons, and runs only on standard schemas 8.5.0 and later and the libraries partnered with them. A `dc:source` value may cite a Sources row by a URL under the row's link.
- Two different versions of one schema in a merge group, or a library that is incompatible with another in the group, fail with `SCHEMA_LOAD_FAILED`, one issue per problem; this replaces `SCHEMA_DUPLICATE_NAMES`.
- A library that redeclares a unit class of its partner may only add units to it; a redeclaration with a description is `SCHEMA_LIBRARY_INVALID`.
- An unpartnered library's entries no longer get the `inLibrary` attribute when loaded.
- The library hedId registry (`library_data.json`) is fetched from hed-schemas first, falling back to the cached and packaged copies only when GitHub is unreachable.
- Schema tools write a partnered library's prerelease JSON unmerged; `hed_add_ids` fails with a message when there is no prerelease TSV set; a missing or exhausted hedId range raises `HedFileError` instead of `IndexError`.

### API

- `CharRexValidator` and `UnitValueValidator` take a `hed_schema=` argument; `UnitValueValidator.report_value_errors` is an instance method with `allowed_names=` and `rule_failures=`.

## Bug fixes

- A schema version bundled with hedtools now always loads from the bundled file, and a cache populated by an older hedtools receives the newly bundled schemas (HED 8.5.0, lang 1.2.0, score 1.2.0 and 2.2.0). Before, a stale or prerelease copy left in the cache, such as an 8.5.0 prerelease downloaded with 1.2.0, was loaded instead of the release, and `load_schema_version()` with no version could resolve to an older version. A folder passed as `xml_folder` is still used as it is.
- `conversionFactor` values written with a caret (`10^-15` in HED 8.0.0 to 8.2.0 and score 1.2.0) are read as powers; they were read as `10e-15`, ten times too large (`Duration/1 fs` on 8.2.0 converted to 1e-14 s).
- `TabularSummary` no longer doubles the categorical row and file counts on each update (present since 0.9.0).
- hedtools no longer triggers the pandas 3.1 `Pandas4Warning` deprecations (`inplace=`, filling text into numeric columns in `KeyMap.remap`, adding a column with `.at`) that were printed when validating a table with an `onset` column.
- Loading a JSON file that is not a HED schema raises `HedFileError` (`INVALID_HED_FORMAT`) naming the file, instead of a misleading header error or an `AttributeError`.
- Validators no longer leave a file-name context on a caller's `ErrorHandler` after an early return.
- `get_printable_issue_string(..., add_link=True)` prints the documentation link.
- `SchemaComparer` output is in a stable, sorted order.
- A `CHARACTER_INVALID` in a `Def/` or `Def-expand/` value reports the index within the tag as written.
- A text stream that cannot report its position can be loaded as a tabular input.
- The `INVALID_COLUMN_REF` message no longer ends with a stray quote.

## Deprecations

All are scheduled for removal in hedtools 2.0.0 and raise `DeprecationWarning`.

- The `schema=` parameter of `load_schema` and `from_string` (parsing a file into an existing schema): use a version list in `load_schema_version`.
- `SchemaAttributeErrors.SCHEMA_MISSING_EXTRA_VALUE`: use `SCHEMA_MISSING_EXTRA` (the value is already `"SCHEMA_MISSING_EXTRA"`).
- The `def_dicts=` parameter of `SpreadsheetValidator.validate`: use `extra_def_dicts=`.
- The `value_validators=` parameter of `UnitValueValidator`: it has no effect.
- The `allow_blank_names=` parameter of `BaseInput` and of `ColumnMapper.check_for_mapping_issues`: it is ignored.
- `ColumnMapper.check_for_blank_names`: validation reports blank names as `TABULAR_INVALID`.
- `hed.tools.util.data_util.delete_rows_by_column`: use `remove_rows_by_value`, which returns a new dataframe.

## Removed

- Error codes `SCHEMA_ANNOTATION_PREFIX_MISSING`, `SCHEMA_ANNOTATION_EXTERNAL_MISSING` and `SCHEMA_ANNOTATION_SOURCE_MISSING` (now `SCHEMA_ANNOTATION_INVALID`) and `HedExceptions.SCHEMA_DUPLICATE_NAMES` (now `SCHEMA_LOAD_FAILED`).
- Validation no longer issues `HED_BLANK_COLUMN` (the constant remains defined).
- From `hed.validator.util.class_util`: `is_date_time_value_class`, `is_name_value_class`, `is_numeric_value_class`, `is_text_value_class`, `is_clock_face_time`, `find_invalid_positions`, `UnitValueValidator.validate_value_class_type` and the constants `DATE_TIME_VALUE_CLASS`, `NUMERIC_VALUE_CLASS`, `TEXT_VALUE_CLASS`, `NAME_VALUE_CLASS`, `DIGIT_OR_POUND_EXPRESSION`.
- The `CharValidator` attributes `DEFAULT_ALLOWED_PLACEHOLDER_CHARS`, `TAG_ALLOWED_CHARS`, `INVALID_STRING_CHARS`, `INVALID_STRING_CHARS_PLACEHOLDERS` and `CLASS_REX_FILENAME`; `PANDAS_COLUMN_PREFIX_TO_IGNORE` from `hed.models.column_mapper` and `hed.validator.spreadsheet_validator`.
- Package data files `hed/validator/data/class_regex.json` (replaced by `character_sets.json`) and `reservedTags.json` (replaced by `reserved_tags.json`).
- The `benchmarks/` directory; the benchmark harness lives in [hed-benchmarks](https://github.com/hed-standard/hed-benchmarks).

## Testing

- The specification tests run against hed-tests 54f137e (reserved tags, column names, padded values, extension rules), with no skipped cases.
- The unit tests no longer use the testlib library or vendored copies of released schemas: they load the bundled schemas and the hed-tests test schemas.
- New tests for staged validation, column sources, value-text and character sets, merge groups, reserved tags, the hedId tools, and HED 8.5.0 units; a deprecation registry (`tests/test_deprecations.py`) fails when a scheduled removal is overdue.
- CI adds a job with the minimum supported pandas (2.2.3, Python 3.10).

## Internal and documentation

- Ruff uses the standard rule set plus isort, pyupgrade and pandas-vet PD002 (no `inplace=True`); code reformatted, no behavior change.
- `reserved_tags.json` and `character_sets.json` are verbatim copies of the specification's files; CI workflows fail when they drift.
- The user guide covers staged tabular validation and `row_count`, schema merge groups, and the schema release steps (`--set-ids`, `--require-ids`, `add-ids`).
- Repository layout, contributor and assistant instructions standardized; the documentation chat widget renamed and moved.

# Release 1.2.0 July 18, 2026

## New features

### `get_available_hed_versions()` — list schema versions on GitHub without downloading them

A new public function, `get_available_hed_versions()`, lists the HED schema versions available on GitHub *without* fetching any schema file's actual XML content. It is the live-from-GitHub counterpart to `get_hed_versions()` (which reports only what is already bundled or cached locally, with no network calls) and a far cheaper alternative to `cache_xml_versions()` (which downloads every discovered version's full content). The intended use is populating a version-picker in a UI or web service and then fetching only the one version the user selects via `load_schema_version()`.

```python
from hed.schema import get_available_hed_versions, load_schema_version

choices = get_available_hed_versions()  # ['8.4.0', '8.3.0', ...] — listing calls only
if choices:  # empty if GitHub is unreachable or rate-limited
    schema = load_schema_version(choices[0])  # this is the step that downloads schema content
```

- Exported from `hed/schema/__init__.py` alongside the existing cache functions.
- Supports `library_name=None` (standard schema only, the default), `library_name="all"` (returns a `{library_name: [versions]}` dict), and a specific library name (restricted to that one library's folder). A `check_prerelease` flag optionally includes prerelease folders.
- Degrades gracefully: any URL that can't be reached yields an empty result rather than raising, so it is safe on an unattended user-facing path.

### Repo-level manifest fast path for version discovery

`get_available_hed_versions()` now resolves versions from a single repository-level manifest instead of crawling GitHub's REST API directory listings whenever possible. hed-schemas publishes one `schema_versions.json` at its repository root listing every version (released, prerelease, and deprecated) for the standard schema and each library, with each XML file's git blob SHA. hedtools reads that one file from the raw/CDN host (`raw.githubusercontent.com`) in a single fetch — which is **not** subject to GitHub's REST API rate limit (60 requests/hour unauthenticated, where even conditional 304s count against the cap).

- A new internal module, `hed/schema/schema_version_manifest.py`, parses the manifest. It is deliberately I/O-light and independent of `hed_cache` (the network fetch is performed by the caller via the existing ETag-aware helper), and is not part of the public API.
- The manifest fetch is itself ETag-aware and time-throttled (`cache_time_threshold`, default 60s), so repeated calls cost at most one conditional request per interval — and it reads from the raw/CDN host, which is not metered by GitHub's REST API rate limit.
- Used only for the canonical hed-schemas URLs. Any custom/forked URL set, or any failure (host unreachable, malformed JSON, or an unrecognized `manifest_format_version`), transparently falls through to the REST API crawl below, so behavior is never worse than before.
- Deprecated versions are recorded in the manifest so the static HED schema browser can display them, but hedtools never lists or loads deprecated schemas through this path — matching the REST crawl's skipping of the `deprecated` folder.

### ETag-cached REST API fallback

When the manifest fast path is unavailable (a custom/forked URL set, or any fetch/parse failure), `get_available_hed_versions()` falls back to crawling GitHub's REST API directory listings, backed by a small on-disk cache in `hed/schema/hed_cache.py` with two tiers of throttling so a frequently-polling caller still doesn't trip GitHub's rate limits:

- **Time-based reuse** — a URL checked within `cache_time_threshold` seconds (default 60) is reused with no network call at all.
- **ETag conditional requests** — otherwise a conditional GET (`If-None-Match`) is made; a `304 Not Modified` reuses the stored body and, for authenticated requests, does not count against GitHub's primary rate limit. Results are persisted in a small on-disk metadata file (`available_versions_cache.json`) in the cache folder, holding only directory-listing JSON — never schema content.

Recorded failures are never shielded from retry by a large threshold, so a transient network/rate-limit error is retried within `AVAILABLE_VERSIONS_TIME_THRESHOLD` (60s) rather than being held for the full threshold.

### On-demand single-version download

`get_hed_version_path()` now downloads only the single requested version when it is absent from the local cache, rather than bulk-downloading the entire catalog. A new internal helper, `_download_schema_version()`, resolves the version from the manifest (a single CDN fetch) when possible and otherwise from a REST listing of just the relevant library, then downloads only that one XML file — using SHA comparison so a file whose content is unchanged on GitHub is never re-fetched.

- `cache_xml_versions()` remains the way to pre-populate the entire catalog (e.g. for an offline/air-gapped environment) and now seeds the bundled schemas first, so the cache is usable even if the subsequent GitHub download fails.
- Local lookups (including `get_hed_version_path()`) already consider the bundled schemas that ship with hedtools, so those versions never require a network call.

### `make_url_request()` supports conditional-request headers

`schema_util.make_url_request()` gained an `extra_headers` argument so callers can add headers such as `If-None-Match`. Its docstring now documents that a `304 Not Modified` surfaces as an `HTTPError` the caller must interpret. Existing calls are unaffected (the argument is optional).

## Testing

- Added tests in `tests/schema/test_hed_schema_io.py` covering `get_available_hed_versions()`: listing without downloading, result caching, conditional requests after `force_refresh`, skipping unneeded URLs, graceful degradation on malformed responses and corrupted cache entries, and failure-entry retry despite a large threshold.
- Added a regression test in `tests/validator/test_hed_validator.py` (`test_severity_enum_not_string_github_hedit_161`) confirming that validation issue `severity` is the `ErrorSeverity` enum, not a string — verifying downstream code can correctly filter by `ErrorSeverity.ERROR` (Annotation-Garden/HEDit#161).
- `test_get_hed_versions_includes_bundled_score`: new always-runs (no-network) test in `tests/schema/test_hed_schema_io.py` asserting that the `score` library schemas bundled in `hed/schema/schema_data/` are always locally available via `get_hed_versions()`.
- The new network-dependent tests in `tests/schema/test_hed_schema_io.py` call `self.skipTest()` when GitHub is unreachable or rate-limited rather than failing with an assertion error. `test_get_available_hed_versions_lists_without_downloading` additionally handles the specific case where the library API endpoint is independently rate-limited while the standard-schema endpoint succeeds: it marks `score_available = False` and skips only the score-specific assertions rather than skipping the entire test.
- Added `tests/schema/test_schema_version_manifest.py` covering the manifest module: format-version gating (`is_supported`), the list/dict shapes returned by `available_versions()` (standard schema keyed as `None`, `"all"`, and a single library), prerelease inclusion, `find_version_info()` download-info resolution, and the exclusion of deprecated versions from both listing and loading.
- Added tests in `tests/schema/test_hed_schema_io.py` for the on-demand download path: re-seeding when the cache directory holds only non-schema files, `cache_xml_versions()` seeding bundled schemas when the GitHub download fails, `get_hed_version_path()` fetching only the one requested version, and the `deprecated` folder (both a top-level library folder and a subfolder within `hedxml/`) never being fetched.
- Added a regression guard in `tests/schema/test_schema_validator_hed_id.py` confirming `HedIDValidator._get_previous_version()` draws from the full manifest version list, not just the local cache (`testlib` 2.0.0 → `testlib_1.0.2`).
- Updated the `spec_tests/test_hed_cache.py` auto-download test to use a non-bundled `testlib` version, so it exercises the real on-demand GitHub download and asserts that only the single requested file (not the whole catalog) is fetched.
- Made `spec_tests/test_hed_cache.py::test_cache_again` deterministic: it now stamps a fresh cache timestamp before re-calling `cache_xml_versions()`, so the "throttled, returns -1" assertion no longer flakes when the setup download is rate-limited on an unauthenticated CI runner (the throttle timestamp is written only on a successful refresh).

## Bug fixes

### `HedIDValidator` skipped versions released after the cache was last populated

`HedIDValidator._get_previous_version()` determined a schema's previous version from only the local cache (`get_hed_versions()`), so a version released after the cache was last populated could be silently skipped — a failure that surfaced on a fresh CI runner. It now uses the manifest-based listing (`get_available_hed_versions()`) as the authoritative source, falling back to the local cache when the network is unavailable.

- `hed/schema/schema_validation/hed_id_validator.py`: `_get_previous_version()` prefers the manifest listing and normalizes the standard schema's library name to `None`.

### `get_hed_versions()` re-seeded the cache only when the directory was completely empty

`get_hed_versions()` re-seeded the bundled schemas only when the cache directory listing was entirely empty (`if not hed_files:`), so a directory containing only non-schema files (lock files, the listing-cache JSON, etc.) would return no versions. It now re-seeds whenever no version-matching schema file is present.

- `hed/schema/hed_cache.py`: the guard now checks `version_pattern` matches rather than mere directory non-emptiness, and re-lists the directory after seeding.

### `CacheLock` never acquired its portalocker lock; failed refresh stamped throttle timestamp

`CacheLock.__enter__` constructed a `portalocker.Lock` object but never called `.acquire()`, so every "locked" cache section ran without mutual exclusion and the `LockException` handler was unreachable dead code. `CacheLock.__exit__` also wrote the throttle timestamp unconditionally, so a failed cache refresh (network error, rate limit) blocked all retries for the full threshold period (default 30 minutes) — compounding the offline/HPC impact of any transient failure.

- `hed/schema/hed_cache_lock.py`: added `self.cache_lock.acquire()` after `portalocker.Lock()` so the lock is actually held and `LockException` is reachable; guarded `_write_last_cached_time` with `exc_type is None` so only a successful refresh stamps the throttle; added a defensive `if self.cache_lock is not None:` guard on `release()`.

## Documentation

- Expanded `docs/user_guide.md` with guidance on listing available versions and the lazy-download workflow.
- Updated the `hed.schema` module docstring to document `get_available_hed_versions()` and clarify the trade-offs between it, `get_hed_versions()`, and `cache_xml_versions()`.
- Documented the `HedFileError` (`RequiredColumnsMissing`) raised by `df_to_hed()` in `hed/tools/analysis/annotation_util.py` when required columns are absent (behavior unchanged; docstring now records it).
- Cleaned up `RELEASE_GUIDE.md`: replaced version-specific examples with `<version>`/`<date>` placeholders, removed Black-specific and Copilot-specific references, and corrected `git add .` to `git add <files>`.
- Added `.envrc` (direnv) to `.gitignore` for per-checkout local environment variables such as a GitHub token.

## CI/CD

- Bumped `astral-sh/setup-uv` from 8.2.0 to 8.3.2 across all workflows.
- Bumped `qltysh/qlty-action/coverage` from 2.2.1 to 2.3.0.
- Bumped `lycheeverse/lychee-action` from 2.8.0 to 2.9.0.
- Updated the `spec_tests/hed-schemas` and `spec_tests/hed-tests` submodules to their latest commits.

# Release 1.1.1 July 7, 2026

## Bug fixes

### KeyMap crash under pandas 3.0 with certain hash-key combinations

`KeyMap._remap()` (used by `hed.tools` remap utilities and by `table-remodeler`'s `RemapColumnsOp`) builds a `pandas.Series` from a dict whose keys are Python `hash()` values of row contents. pandas 3.0's `Series._init_dict()` tries to detect an evenly spaced integer range in dict keys by subtracting adjacent keys; when two hash keys have opposite sign and near-maximal magnitude, that subtraction silently overflows `int64`, corrupting the resulting `Index` (collapsing it to length 0) and raising `ValueError: Length of values (N) does not match length of index (0)`. 1.1.0 already addressed the pandas 3.0 breaking changes known at the time, but this code path only surfaces with particular hash-value combinations and wasn't caught by that pass.

- `hed/tools/analysis/key_map.py`: the lookup `Index` is now built explicitly with `dtype="object"`, and the per-row hash `Series` is likewise kept as `dtype=object`, so pandas' numeric range-detection fast path is never invoked for these hash-based lookups.
- Added `tests/tools/analysis/test_key_map.py::test_remap_extreme_magnitude_hash_keys`, which patches `get_row_hash` to force the exact pathological key pair deterministically, plus five other new `KeyMap` tests covering numeric keys as integers, as strings, with `n/a` values, multi-key cascades, and a 100-entry dictionary.

### Missing `inLibrary` attribute on merged library-schema extras

`HedSchema.save_as_dataframes()` unconditionally overwrote its computed output with `self.extras` whenever a schema had extras, even when the caller requested a merged save, discarding the serializer's correctly computed `in_library` values. `merge_extras_dataframes()` could also lose the `in_library` marking on entries duplicated between a library and its standard schema, depending on `drop_duplicates()` ordering. Both are fixed, completing the merged-extras support across all schema formats:

- `hed/schema/hed_schema.py`: the extras override in `save_as_dataframes()` is now skipped when `save_merged=True`, preserving the serializer's own merged output; the internal `in_library` bookkeeping column is stripped before non-merged saves since it is metadata, not schema content.
- `hed/schema/schema_io/df_util.py`: `merge_extras_dataframes()` now explicitly prefers the library version (which carries `in_library`) for entries that exist in both library and standard extras, using an indicator merge to find standard-only rows.
- Updated `df2schema.py`, `json2schema.py`, `xml2schema.py`, `wiki2schema.py`, `schema2json.py`, `schema2xml.py`, `schema2wiki.py`, `schema2df.py`, `schema2base.py`, `base2schema.py`, the `df_constants.py`/`json_constants.py`/`xml_constants.py` constant modules, and `schema_comparer.py` for consistency.
- Added comprehensive round-trip coverage in `tests/schema/test_schema_extras_comprehensive.py` and related schema I/O tests.

### `get_hed_versions()` returned every library for an unrecognized name

`hed_cache.get_hed_versions(library_name=...)` fell through to returning the entire dict of every cached library's versions when given a name that matched nothing. `library_name="all"` now has its own explicit branch, and any other unrecognized name correctly returns `[]`.

## Packaging

- Removed ~28,800 lines of dev/test-only `HED_testlib_*.xml` schemas that were being bundled into the installed `hed/schema/schema_data/` package directory; these are used only by hedtools' own test suite, not real published HED libraries, and had no effect on any documented API.
- Added `typeguard>=4.5.2` as an explicit dependency in `pyproject.toml`.

## Testing

- Six new `KeyMap` pandas-3 regression tests (see above).
- Comprehensive schema-extras round-trip tests across DataFrame, JSON, XML, and MediaWiki formats.
- Loosened an overly strict dtype assertion on the `in_library` column in `test_schema_extras_comprehensive.py` so it tolerates a broader range of pandas versions.
- Test fixtures switched from `testlib_1.0.2` to `testlib_2.1.0` to avoid extra schema-cache network loading during CI.

## CI/CD

- Removed the `claude-code-review.yml` and `claude.yml` GitHub Actions workflows.
- Bumped `actions/checkout` (to 6.0.3, then 7.0.0), `astral-sh/setup-uv` (to 8.1.0, then 8.2.0), and `qltysh/qlty-action` to 2.2.1.
- Bumped `anthropics/claude-code-action` repeatedly from 1.0.104 through 1.0.133.
- Updated `spec_tests/hed-schemas` and `spec_tests/hed-tests` submodules.

# Release 1.1.0 April 19, 2026

## New features

### Search engine performance improvements

`ExpressionAnd`, `ExpressionOr`, and `ExpressionNegation` in `query_expressions.py` now use set-based deduplication instead of O(n²) list scanning, giving a significant speedup for queries that produce many intermediate results. Supporting this, `SearchResult` gains `__eq__` and `__hash__` methods so instances can be stored in sets and dicts. `QueryHandler._expr_has_wildcard()` replaces the fragile `"?" in str(interior)` string check with a proper recursive AST walk, eliminating false positives on queries whose string representations happen to contain a literal `?`.

### `StringQueryHandler` and `schema_lookup` (internal / experimental)

Two new internal modules support schema-free HED search:

- `hed/models/string_search.py` — `StringQueryHandler` subclasses `QueryHandler` and accepts a raw HED string instead of a parsed `HedString`, enabling query evaluation without loading a schema. `StringNode` duck-types `HedGroup`/`HedTag` so that existing `Expression` subclasses evaluate against it without modification.
- `hed/models/schema_lookup.py` — `generate_schema_lookup(schema)` builds a compact `{short_tag: tag_terms}` dict from a loaded schema that can be passed to `StringQueryHandler.search()` to enable ancestor-aware matching on short-form strings. `save_schema_lookup()` / `load_schema_lookup()` persist the table as JSON for offline use.

These modules are not part of the public API and may change in future releases.

### `HedGroup` find-method documentation clarified

Docstrings for `find_tags`, `find_wildcard_tags`, `find_exact_tags`, and `find_tags_with_term` now document the exact comparison property each method uses (`short_base_tag`, `short_tag`, `HedTag.__eq__`, and `tag_terms` respectively) and explain the rationale for that choice.

### Search benchmarks

A new `benchmarks/` directory provides reproducible performance benchmarking tools: `search_benchmark.py` measures throughput across query types and string sizes, `data_generator.py` synthesizes realistic HED strings, and `report.py` generates Markdown and PNG reports. Pre-computed results are stored under `benchmarks/results/` and benchmark figures under `docs/_static/images/`.

### Search documentation

A new `docs/search_details.md` page covers all three HED search implementations (`basic_search`, `QueryHandler`, and `StringQueryHandler`): design trade-offs, query language reference, and measured performance characteristics with benchmark figures.

### Pandas 3.0 compatibility

All pandas 3.0 breaking changes have been addressed, and the pandas version constraint in `pyproject.toml` has been updated from `<3.0.0` to `<4.0.0`:

- **Copy-on-Write (CoW)**: Chained `df[col][mask] = ...` assignments in `df_util.py` replaced with `df.loc[mask, col] = ...` to prevent silent no-ops and the new `ChainedAssignmentError`.
- **`drop()` API**: Removed redundant `axis=1` argument when `columns=` is already specified in `data_util.py` (the two arguments conflict in pandas 3.0).
- **NaN handling in schema loading**: `df2schema.py`, `df_util.py`, and `hed_id_util.py` now check `isinstance(value, str)` before calling string methods such as `.strip()` and `.startswith()`, preventing `AttributeError` when empty cells are `float` NaN rather than `""`.
- **StringDtype in `_merge_dataframes`**: Fillna logic updated in `schema_io/df_util.py` to use `pd.api.types.is_numeric_dtype()` instead of `dtype == "object"`, correctly handling pandas 3.0 `StringDtype` columns.
- **Float64 column FutureWarning**: `assign_hed_ids_section` in `hed_id_util.py` now casts all-NaN hedId columns from `float64` to `object` before assigning string values, eliminating a pandas deprecation warning.
- Added `tests/test_pandas3_compat.py` with 27 targeted tests covering all of the above fixes.

### Filename filter for `extract bids-sidecar`

`hedpy extract bids-sidecar` and the underlying `hed_extract_bids_sidecar` script now accept a `--filter` / `-fl` option. Only files whose name contains the filter string are included in the sidecar extraction. Example:

```bash
hedpy extract bids-sidecar /path/to/dataset --filter sub-01
```

### `BidsFileGroup.get_task_names()`

`BidsFileGroup` now exposes a `get_task_names()` method that returns a sorted list of unique task names (the `xxxx` portion of `task-xxxx` BIDS entities) found across all sidecar and data files in the group.

### `TabularSummary` deduplicates `skip_cols`

`TabularSummary.__init__` now deduplicates the `skip_cols` list using `dict.fromkeys`, preserving order. Passing the same column name more than once no longer produces duplicate entries in `skip_cols` or in the `"Skip columns"` field of the summary metadata output. Functional behaviour (which columns are skipped) is unchanged.

## Documentation

- Removed `{index}` placeholder annotations from `README.md` and `examples/README.md`.

## CI/CD

- Bumped `actions/configure-pages` from 5 to 6.
- Bumped `astral-sh/setup-uv` from v7 to v8.0.0.
- Updated `anthropics/claude-code-action` to v1.0.97.
- Pinned all GitHub Actions steps to full SHA hashes for supply-chain security.
- Updated `spec_tests/hed-examples`, `spec_tests/hed-schemas`, and `spec_tests/hed-tests` submodules.

# Release 1.0.0 March 27, 2026

This is a major release with breaking changes. It removes several subsystems that are no longer part of the core `hedtools` package, completes the schema library-extras support across all schema formats, and cleans up the public API.

## Breaking changes

### Removed remodeling tools

The entire `hed/tools/remodeling/` subsystem (dispatcher, operations, backup manager, and CLI entry points `run_remodel` / `run_remodel_backup` / `run_remodel_restore`) has been removed (issue #1180). Remodeling functionality is now maintained as a separate repository: [table-remodeler](https://github.com/hed-standard/table-remodeler):

### Removed visualization code

`hed/tools/visualization/` (`TagWordCloud`, `word_cloud_util`) and the `wordcloud` dependency have been removed. Visualization is maintained in the separate `hedvis` package in repository [hed-vis](https://github.com/hed-standard/hed-vis)

### Removed ontology utilities

`ontology_util.py` and the associated `create_ontology.py` script have been removed (issue #1177) and are now in the [hed-ontology](https://github.com/hed-standard/hed-ontology) HED ID management is now handled by the new `hed/schema/schema_io/hed_id_util.py` module.

### Removed `sequence_map.py`

`hed/tools/analysis/sequence_map.py` has been moved to the `hedvis` package in the [hed-vis](https://github.com/hed-standard/hed-vis) and is no longer part of `hedtools`.

### Removed `HedLogger`

The `HedLogger` logging class has been removed from `hed/errors/`. Use Python's standard `logging` module instead.

### Removed `check_prerelease` parameter from schema loading API

The `check_prerelease` flag has been removed from all public schema-loading functions (`load_schema_version()`, `load_schema()`, `from_string()`, `from_dataframes()`) and all `SchemaLoader` subclasses. Prerelease schemas are now found automatically whenever they are present in the local cache — no flag is needed.

### `check_warnings` renamed to `check_for_warnings`

`ErrorReporter.check_warnings()` has been renamed to `check_for_warnings()` for API consistency.

### Removed `versionner` dependency

Version management has migrated fully to `setuptools-scm`. The `versionner` tool and its configuration have been removed (issue #1181). `hed/_version.py` continues to be auto-generated — do not edit it manually.

## Schema enhancements

### Library schema extras (`inLibrary`) fully supported across all formats

Extra (non-standard) sections in library schemas, marked with `inLibrary`, now round-trip correctly through all three schema file formats:

- **XML**: `inLibrary` attribute written and read for all extra node types.
- **JSON/DataFrame**: `in_library` column propagated through all extra section tables.
- **MediaWiki**: `inLibrary` tags serialized and parsed in extra sections.

Comprehensive roundtrip test suites have been added for each format.

### Consistent `inLibrary` / `in_library` naming

A naming inconsistency between the XML attribute name (`inLibrary`) and the internal DataFrame column name (`in_library`) has been resolved. All internal representations now use `in_library`; serialization to XML uses `inLibrary` as required by the schema specification.

### Prerelease schemas found automatically

When a requested version is present only in the prerelease cache, it is now loaded without any additional flags. The previous `check_prerelease=True` requirement has been eliminated throughout the stack.

### Prerelease library schemas can use their prerelease standard partner

A prerelease library schema that has `withStandard` set may now load against its matching prerelease standard partner instead of requiring a released standard schema.

### Auto-download missing schemas from GitHub

`get_hed_version_path()` now automatically fetches a schema from GitHub when the requested version is absent from the default local cache directory.

### Default schema version resolved dynamically

The default schema version is derived at runtime from the highest released version in the cache rather than being hardcoded in the source. New schema releases no longer require a code change.

### Consistent line-ending handling

CRLF/LF differences in schema files are now normalized on read and write, preventing spurious diffs and test failures on Windows.

### Fixed empty schema DataFrame sections

Writing a schema to DataFrame format no longer fails when a section (e.g., unit modifiers) is empty.

### Fixed loading of early TSV-format schemas

Schemas stored in older TSV formats that predate the current DataFrame layout now load correctly.

### Removed unverified `omn:` columns from TSV format

Columns prefixed with `omn:` that were written but never populated have been removed from the TSV/DataFrame schema format.

### Schema error vs warning strategy revised

The `ErrorReporter` now distinguishes schema-level errors from warnings more precisely. `check_for_warnings()` (formerly `check_warnings()`) returns only genuine warning-level issues; schema structural errors are always reported as errors regardless of warning-filter settings.

### Schema compliance tests check only latest versions

Spec-test compliance checking has been refactored to validate only the latest released version of each schema, reducing test time and avoiding failures from already-superseded versions.

## Bug fixes

- Fixed a race condition in schema-version auto-detection when multiple processes access the cache simultaneously.
- Fixed duplicate HED ID detection — `check_duplicate_hed_ids()` now correctly tracks already-seen IDs across all schema sections.
- Verified all built-in error messages are unique (no two distinct error codes share the same message text).
- Normalized error message punctuation: sentence-ending periods are followed by one space (was inconsistently one or two).
- Fixed extension capitalization check in schema attribute validation.
- Removed stray debug `print` statements from the schema loading path.

## CI/CD and developer tooling

### Migrated GitHub Actions to `uv`

All CI workflows now use the `astral-sh/setup-uv` action and `uv` for environment creation and package installation. `pip`-based setup has been removed. The `black` formatter has been eliminated; `ruff format` handles all code formatting.

### Updated GitHub Actions versions

- `actions/checkout`: v4 → **v6**
- `astral-sh/setup-uv`: v5 → **v7**
- Added `cache-dependency-glob` to all `setup-uv` steps for correct cache invalidation.

### Replaced `codespell` with `typos`

Spell checking in CI now uses [`typos`](https://github.com/crate-ci/typos). Configuration has been consolidated into `pyproject.toml`; the separate `.codespellrc` file has been removed. The `tests/` directory and generated/binary file types are excluded from spell checking.

### Added Claude Code Review and PR Assistant workflows

Two new GitHub Actions workflows provide automated AI code review on pull requests:

- `claude_code_review.yaml` — posts inline review comments via the `gh` CLI.
- `claude_pr_assistant.yaml` — responds to `/review` commands in PR comments.

Bot-authored PRs are excluded from automated review to prevent feedback loops.

### Added project context files for AI assistants

- `.github/copilot-instructions.md` — VS Code Copilot context (now tracked in the repository).
- `CLAUDE.md` and `.rules/` — Claude Code project context and coding rules.

### Consolidated tool configuration

- Ruff options updated; submodule directories excluded from linting.
- `lychee.toml` updated to use plain URL format (replaced `{meta}` tags removed in newer lychee releases).
- `pyproject.toml` is now the single source of truth for spell-check word lists.

# Release 0.9.0 January 22, 2026

The main purpose of this release is to clean up the CLI for the hedtools and to improve the documentation in preparation for release of 1.0.0, which will be a breaking release.

## Major changes

### Command-line interface (CLI) overhaul

**Complete CLI redesign with Git-Style commands**

- Introduced unified `hedpy` command-line interface with git-style subcommand structure
- Replaced legacy standalone scripts with organized command groups: `validate`, `schema`, `extract`
- Added comprehensive help system with detailed command documentation
- Implemented click-option-group for organized command options

**New commands:**

- `hedpy validate bids-dataset` - BIDS dataset validation
- `hedpy validate string` - HED string validation
- `hedpy validate sidecar` - JSON sidecar validation
- `hedpy validate tabular` - TSV file validation
- `hedpy schema validate` - Schema file validation
- `hedpy schema convert` - Schema format conversion
- `hedpy schema add-ids` - HED ID management
- `hedpy extract bids-sidecar` - Sidecar template extraction
- `hedpy extract tabular-summary` - Tabular file summarization

**Enhanced output options:**

- Multiple output formats: text, json, json_pp (pretty-printed JSON with metadata)
- Configurable error limiting per error type
- File-based and per-error error counting options
- Comprehensive logging configuration with file output support

### Documentation improvements

**Major documentation restructuring**

- Complete rewrite of user guide with comprehensive examples and workflows
- Added detailed Jupyter notebook documentation section
- Created extensive CLI documentation with command examples
- Improved API reference organization with clearer section headers
- Enhanced introduction page with quick start examples
- Added troubleshooting section with common issues and solutions
- Updated the RELEASE_GUIDE to better reflect current release process

**New documentation features:**

- Sidebar quick links for easy navigation
- Custom CSS styling for improved readability
- Dark mode support with proper color theming
- Brand customization with project logo and name
- Better code block formatting and syntax highlighting
- Comprehensive examples for all major workflows

### Jupyter notebook examples

**New example notebooks (examples/ directory)**

- `extract_json_template.ipynb` - Generate JSON sidecar templates
- `find_event_combinations.ipynb` - Find unique value combinations
- `merge_spreadsheet_into_sidecar.ipynb` - Merge edited annotations
- `sidecar_to_spreadsheet.ipynb` - Convert JSON to spreadsheet format
- `summarize_events.ipynb` - Summarize event file contents
- `validate_bids_dataset.ipynb` - Validate BIDS datasets
- `validate_bids_dataset_with_libraries.ipynb` - Validate with library schemas
- `validate_bids_datasets.ipynb` - Batch validate multiple datasets
- `validate_bids_dataset_nondefault. ipynb` - Non-standard validation scenarios

**Notebook infrastructure:**

- Added comprehensive README for notebooks with usage instructions
- Created optional dependencies group for Jupyter support
- Added notebook testing framework for validation

### Core functionality enhancements

**Validation improvements:**

- Enhanced placeholder validation with units (e.g., "# m-per-s^2")
- Fixed unit class validation for placeholders with units
- Improved error reporting with better categorization
- Added support for --no-log option to disable all logging

**TabularSummary Enhancements:**

- Added categorical limit feature to prevent memory issues with high-cardinality columns
- Implemented overflow column tracking for truncated summaries
- Added categorical counts metadata (total values and file counts)
- Improved summary statistics and reporting

**Schema processing:**

- Enhanced schema validation error messages with specification links
- Fixed schema attribute inheritance handling
- Improved JSON schema format support
- Updated conversion factor validation

### Script and utility improvements

**New scripts:**

- `hed/scripts/validate_hed_string.py` - Standalone HED string validation
- `hed/scripts/validate_hed_sidecar.py` - Standalone sidecar validation
- `hed/scripts/validate_hed_tabular.py` - Standalone tabular file validation
- `hed/scripts/extract_tabular_summary.py` - Non-BIDS tabular summarization
- `hed/scripts/script_utils.py` - Shared utility functions for scripts

**Script utilities:**

- Centralized logging setup across all scripts
- Standardized validation result formatting
- Consistent error handling and reporting
- Improved argument parsing with organized option groups

### Dependencies and requirements

**Updated Dependencies:**

- Added `click-option-group>=0.5.0` for CLI option organization
- Updated `wordcloud` from 1.9.4 to 1.9.5
- Updated `black` to >=26.1.0 with Jupyter support
- Added `mdformat>=0.7.0` and `mdformat-myst>=0.1.5` for markdown formatting
- Updated Sphinx and documentation dependencies

**New Optional Dependency Groups:**

- `examples` - Jupyter notebook support (jupyter, notebook, nbformat, ipykernel)
- Updated `docs` group with version constraints
- Enhanced `dev` group with markdown formatting tools

### Testing enhancements

**Schema test data:**

- Added extensive JSON test data for schema validation
- New test files for schema attribute validation
- Tests for conversion factors, HED IDs, unit classes, value classes
- Tests for character validation and deprecation handling
- Tests for library schema attributes

**Test organization:**

- Improved test structure with categorized error cases
- Added common causes and correction strategies to test metadata
- Enhanced test documentation with specification references
- Moved JSON test references from the hed-specification repository to the hed-tests repository

### Documentation files

**Updated documentation:**

- Comprehensive CHANGELOG.md updates
- Enhanced CONTRIBUTING.md with detailed workflows
- Improved README. md with better examples and structure
- Updated RELEASE_GUIDE.md with detailed release procedures

**Configuration files:**

- Added `.lycheeignore` for link checker exclusions
- Added `lychee.toml` for link validation configuration
- Enhanced `.gitignore` with additional patterns
- Updated workflow configurations for GitHub Actions

## GitHub actions and CI/CD

### Workflow updates

**Enhanced CI pipeline:**

- Updated cache actions from v4 to v5 across all workflows
- Changed default branch references from `develop` to `main`
- Renamed and reorganized workflow files (. yml → .yaml)
- Improved Sphinx documentation build workflow

**New workflows:**

- `links. yaml` - Lychee link checker for documentation (weekly schedule)
- `mdformat.yaml` - Markdown formatting validation
- `notebook_tests.yaml` - Jupyter notebook validation
- `ruff.yaml` - Python linting with Ruff

**Workflow improvements:**

- Updated codespell workflow to use main branch
- Enhanced documentation deployment workflow
- Added proper artifact handling for GitHub Pages
- Improved test isolation and parallel execution

## File organization and structure

### Repository structure changes

**Removed:**

- Removed `spec_tests/hed-specification` submodule (replaced with hed-tests)
- Removed remodeling CLI commands (moved to separate repository)

**Added:**

- New `examples/` directory with Jupyter notebooks and README
- New `hed/scripts/script_utils.py` for shared utilities
- New validation scripts for string, sidecar, and tabular files
- New extract script for non-BIDS tabular summaries

**Updated:**

- Moved documentation assets from `docs/assets/` to `docs/_static/`
- Enhanced documentation structure with better organization
- Improved test data organization in spec_tests/

### Code quality and formatting

**Black formatting:**

- Applied Black code formatter across entire codebase
- Updated Black configuration for Python 3.14 support
- Enhanced exclusion patterns for auto-generated files

**Ruff linting:**

- Added comprehensive Ruff configuration
- Implemented linting rules for code quality
- Added automated linting in CI pipeline

**Markdown formatting:**

- Added mdformat for consistent markdown styling
- Configured myst-parser support
- Automated markdown checking in CI

## Bug fixes and minor improvements

### Schema handling

- Fixed MediaWiki → MEDIAWIKI naming consistency
- Improved schema format detection and conversion
- Enhanced schema attribute validation
- Fixed inheritance handling for schema attributes

### Validation

- Fixed unit validation for placeholders with units
- Improved error message clarity and documentation links
- Fixed definition extraction from sidecars
- Enhanced sidecar validation error reporting

### Error reporting

- Updated documentation link format in error messages
- Improved error categorization and grouping
- Added error iteration utility (`iter_errors`)
- Enhanced printable issue formatting

### Miscellaneous

- Fixed various typos and formatting issues
- Improved code comments and docstrings
- Enhanced type hints and error handling
- Cleaned up deprecated code patterns

## Breaking changes

**CLI command changes:**

- Legacy commands are now deprecated (still work but show warnings)
- Recommended migration to new `hedpy` command structure
- Some command-line argument names have changed for consistency

**Python version:**

- Minimum Python version remains 3.10
- Added support for Python 3.14

## Migration guide

### CLI Migration

```bash
# Old (deprecated)
validate_bids /path/to/dataset

# New (recommended)
hedpy validate bids-dataset /path/to/dataset
```

### Script Imports

```python
# Validation functions remain unchanged
from hed import HedString, load_schema_version, BidsDataset

# New utility imports available
from hed.errors import iter_errors
from hed.scripts.script_utils import format_validation_results
```

# Release 0.8.1 December 9, 2025

The primary purpose of this release was to correct the JSON format for HED schemas so that it would accurately distinguish between inherited and non-inherited attributes. The documentation layout was also improved with quick links.

## Highlights

- HED schema JSON export is now cleaner: empty list attributes are omitted instead of written as empty arrays, with stronger tests around inheritance and round-trip behavior.
- Default HED XML schema version bumped to **8.4.0**, so helper functions pick up the latest standard without extra configuration.
- Sphinx docs get a polished Furo theme setup, project logo, sidebar quick links, dark-mode fixes, and a proper GitHub repo icon.
- CI updated to use `actions/checkout@v6` via Dependabot

## What’s Changed

### Schema & JSON I/O

- **Omit empty list attributes in schema JSON** Updated `build_attributes_dict` in `schema2json.py` so list-valued attributes like `suggestedTag`, `relatedTag`, `valueClass`, and `unitClass` are only written when non-empty, instead of always being present as `[]`. This produces a more compact JSON representation and avoids ambiguous “empty list means nothing” cases.

- **Stronger JSON format tests** Refined tests in `test_json_explicit_attributes.py` and `test_schema_format_roundtrip.py` to assert that:

  - Tags without `relatedTag` / `valueClass` / `unitClass` simply do not have those keys in `attributes`.
  - Any list attributes that *are* present must be non-empty.
  - A full 8.4.0 schema is saved as JSON and scanned to ensure no empty list attributes sneak into the output.

- **Schema comparison & round-trip robustness** Extended round-trip tests for JSON schema export/import so that schema comparison is aligned with the new “omit empty lists” behavior and no longer relies on placeholder empty arrays.

- **Default XML schema → 8.4.0** Updated the default XML schema version used by helper utilities to `8.4.0` (from 8.3.0). This ensures `load_schema_version()` and similar functions resolve to the current standard HED schema by default.

### Documentation & Site

- **Furo theme configuration and versioning** Updated `docs/conf.py` to:

  - Set `release = "0.8.0"` for the docs.
  - Use the Furo theme with `html_static_path = ["_static"]`.
  - Register extra assets: `custom.css` and `gh_icon_fix.js`.
  - Attach a project logo via `html_logo`.

- **Sidebar quick links** Added a new `quicklinks.html` sidebar template and wired it into `html_sidebars` so all pages include a “Quick links” section pointing to HED homepage, resources, schema browser, specification, and online tools.

- **Dark-mode & header polish** Extended `custom.css` and the new `gh_icon_fix.js` helper to:

  - Make the sidebar search box readable in dark mode (background, placeholder, and icon colors).
  - Hide the raw “view source” / “edit this page” links in the header.
  - Replace them with a single GitHub icon button that points to the repo root and works in both light and dark themes.

- **Minor formatting clean-ups**\
  Small documentation/test formatting adjustments, including updating tests to load schema version 8.4.0 and aligning text with the new JSON behavior.

### CI / Tooling

- **GitHub Actions: `actions/checkout` v6**\
  Dependabot PR **#1155** updates all workflows to use `actions/checkout@v6` instead of v5, pulling in the latest upstream improvements (including Node.js 24 support and updated credential handling).

# Release 0.8.0 November 18, 2025

- **Unified CLI Interface**: Added `hedpy` command-line tool with git-like subcommand structure.
  - Main command: `hedpy` with subcommands for all HED operations.
  - Subcommands organized by category: `hedpy validate-bids`, `hedpy remodel run`, `hedpy schema validate`, etc.
  - Prevents CLI namespace collisions with other tools (e.g., `validate_bids` → `hedpy validate-bids`).
  - Legacy commands still available for backward compatibility but deprecated.
  - Built with `click` framework for better CLI user experience.
  - Added comprehensive help text: `hedpy --help`, `hedpy COMMAND --help`.
  - **CLI Parameter Fidelity**: All CLI wrapper commands now correctly match original script parameters (38+ parameter fixes across 7 commands).
    - Fixed `validate-bids`: Added missing suffixes, output format, error control, and print options.
    - Fixed `remodel` commands: Corrected argument names, added missing parameters, fixed option conflicts.
    - Fixed `schema` commands: Corrected positional vs option argument structures for add-ids and create-ontology.
    - Added comprehensive test suite (`tests/test_cli_parameter_parity.py`) to verify CLI parameters match original parsers.
- **JSON Schema Format Support**: Added comprehensive JSON format support for HED schemas alongside existing XML, MEDIAWIKI, and TSV formats.
  - Implemented `SchemaLoaderJSON` class for loading JSON schemas (`hed/schema/schema_io/json2schema.py`).
  - Implemented `Schema2JSON` class for exporting schemas to JSON (`hed/schema/schema_io/schema2json.py`).
  - Added JSON constants and key mappings (`hed/schema/schema_io/json_constants.py`).
  - Added `save_as_json()` and `get_as_json_string()` methods to HedSchema class.
  - JSON format uses flat tag structure with hierarchy metadata for easier programmatic access.
  - Separate units section in JSON format for improved AI/tool accessibility.
  - Placeholder structure for takes-value tags with proper attribute inheritance.
  - Full roundtrip validation ensures JSON format produces identical validation results to XML/MEDIAWIKI.
- **New BIDS Sidecar Extraction Tool**: Added `hed_extract_bids_sidecar` command-line script for extracting sidecar templates from BIDS datasets.
  - Configurable value columns and skip columns for flexible template generation.
  - Comprehensive logging support with file output and verbosity control.
  - Integrated with BidsDataset and TabularSummary classes for robust extraction.
- **Schema Validation Enhancements**: Extended schema validation to include JSON format in roundtrip testing.
  - Updated `hed_script_util.py` to validate all 4 schema formats (XML, MEDIAWIKI, TSV, JSON).
  - Updated schema conversion script to automatically generate JSON format alongside other formats.
- **Python Version Requirements**: Minimum Python version raised to 3.10 (dropped 3.9 support).
- **Documentation Improvements**: Added comprehensive Google-style docstrings to all functions in `hed_script_util.py`.
- **Configuration Updates**:
  - Added `status` directory to Black exclude list in `pyproject.toml` for development scripts.
  - Updated matplotlib dependency to 3.10.7.
- **Specification Tests**: Updated hed-specification submodule to latest version for improved test coverage.

# Release 0.7.1 October 13, 2025

- Added official support for Python 3.13 (tested in CI workflows).
- Applied Black code formatter to entire codebase for consistent code style (148 files reformatted).
- Added Black to development dependencies (`pip install -e .[dev]`) and GitHub Actions CI workflow.
- Created `.github/workflows/black.yaml` for automated code formatting checks on all PRs and pushes.
- Migrated from flake8 to ruff for linting and code quality checks (faster, more comprehensive).
- Applied code corrections throughout codebase as suggested by ruff linter.
- Removed `.flake8` configuration file in favor of ruff configuration in pyproject.toml.
- Removed unneeded parameters from validator functions for cleaner API.
- Added TYPE_CHECKING imports to avoid circular import issues in type annotations.
- Changed sentinel value name from `_UNSET` to `_SENTINEL` in bids_dataset.py for clarity.
- Enhanced coverage workflow configuration for improved CI/CD reliability.
  - Changed ci_cov.yaml to only run on main branch (not all branches).
  - Updated Python version from 3.12 to 3.10 for coverage tests.
  - Configured qlty.toml for proper coverage reporting with relative paths.
  - Updated .coveragerc to remove explicit source specification.
- Added `pip install -e .[test]` to all GitHub Actions workflows (ci.yaml, ci_windows.yaml, spec_tests.yaml).
- Enhanced CONTRIBUTING.md with Black and ruff usage guidelines and code quality tools section.
- Updated README.md with "Code Formatting with Black" section including Windows-specific workarounds.
- Updated RELEASE_GUIDE.md to include code quality checks (Black, ruff, codespell) as pre-release step.
- Configured Black in pyproject.toml with 127 character line length matching existing ruff configuration.

# Release 0.7.0 October 2, 2025

- Added comprehensive logging infrastructure with configurable log levels and file output to validation tools.
- Enhanced validate_bids script with improved error reporting and filtering capabilities.
- Added error code counting and filtering by count/file in ErrorHandler.
- Improved validation output formatting with version tracking in JSON output.
- Added comprehensive CONTRIBUTING.md with development guidelines and best practices.
- Enhanced README.md with better documentation structure and examples.
- Improved user guide documentation with clearer installation and usage instructions.
- Fixed typos and improved code documentation throughout the codebase.
- Enhanced Windows compatibility with normalized path handling in tests.
- Updated pyproject.toml with improved metadata and dependencies.

# Release 0.6.0 August 7, 2024

- Added MATLAB integration support with improved function visibility in __init__.py.
- Enhanced ontology creation and validation with better handling of equivalent classes.
- Improved schema scripts with migration from hed-schemas repository.
- Added DataFrame loading/saving optimizations and folder-based operations.
- Enhanced HED ID validation with more robust checks.
- Improved sidecar and tabular input utilities with new helper functions.
- Added support for empty tabular files and whitespace-only files.
- Enhanced annotation utilities for better MATLAB compatibility.
- Improved matplotlib compatibility and updated color map access.
- Fixed various bugs in spreadsheet handling and schema loading.
- Updated dependencies and improved Python 3.7+ compatibility.
- Improved code quality with better type handling and error messages.

# Release 0.5.0

- Added JSON schema specification of remodeling commands.
- Added support for schema that are specified by .tsv files.
- Added support for embedding schema in an ontology.
- Added WordCloud visualizations.
- Added handling of event context and events of temporal extent.

# Release 0.4.0 October 27, 2023

- Refactored the model classes to be based on DataFrame.
- Added additional command line options for remodeling tools.
- Restructured summaries for better reporting.
- Minor refactoring to reduce code complexity.
- Finalized and automated SPEC tests.
- Improvements to GitHub automation -- including adding CodeSpell.
- Improvements to API-Docs.

# Release 0.3.1 July 3, 2023

- Pinned the version of the pydantic and inflect libraries due to conflict.
- Reorganized JSON output of remodeling summaries so that all of consistent form.
- Fixed summarize_hed_tags_op so that tags were correctly categorized for output.
- Minor refactoring to reduce code complexity.
- BaseInput and Sidecar now raise HedFileError if input could not be read.

# Release 0.3.0 June 20, 2023

- Introduction of partnered schema.
- Improved error handling for schema validation.
- Support of Inset tags.
- Support of curly brace notation in sidecars.
- Expanded remodeling functionality.
- Refactoring of models to rely on DataFrames.
- Expanded unit tests in conjunction with specification tests.

# Release 0.2.0 February 14, 2023

- First release of the HED remodeling tools.
- Reorganization of branches to reflect stages of development.
- Updating of schema cache with local copies.
- Improved schema validation and error messages.
- First pass at search and summarization.

# Release 0.1.0 June 20, 2022

- First release on PyPI
