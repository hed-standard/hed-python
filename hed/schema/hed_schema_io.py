"""Utilities for loading and outputting HED schema."""

from __future__ import annotations

import functools
import json
import os
import warnings
from collections import defaultdict
from urllib.error import URLError

from hed.errors.exceptions import HedExceptions, HedFileError
from hed.schema import hed_cache
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.schema.schema_header_util import validate_version_string
from hed.schema.schema_io import schema_util
from hed.schema.schema_io.df2schema import SchemaLoaderDF
from hed.schema.schema_io.json2schema import SchemaLoaderJSON
from hed.schema.schema_io.schema_merge import GroupSpec, merge_group, resolve_group
from hed.schema.schema_io.wiki2schema import SchemaLoaderWiki
from hed.schema.schema_io.xml2schema import SchemaLoaderXML

MAX_MEMORY_CACHE = 40


def load_schema_version(xml_version=None, xml_folder=None) -> HedSchema | HedSchemaGroup:
    """Return a HedSchema or HedSchemaGroup extracted from xml_version

    Parameters:
        xml_version (str or list): List or str specifying which official HED schemas to use.
                                           A json str format is also supported,
                                           based on the output of HedSchema.get_formatted_version
                                           Basic format: `[schema_namespace:][library_name_]X.Y.Z`.
        xml_folder (str): Path to a folder containing schema.

    Returns:
        Union[HedSchema, HedSchemaGroup]: The schema or schema group extracted.

    Raises:
        HedFileError: The xml_version is not valid.
        HedFileError: The specified version cannot be found or loaded.
        HedFileError: Other fatal errors loading the schema (These are unlikely if you are not editing them locally).
        HedFileError: The prefix is invalid.
    """
    # Check if we start and end with a square bracket, or double quote. This might be valid json
    if xml_version and isinstance(xml_version, str) and ((xml_version[0], xml_version[-1]) in [("[", "]"), ('"', '"')]):
        try:
            xml_version = json.loads(xml_version)
        except json.decoder.JSONDecodeError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), xml_version) from e
    if xml_version and isinstance(xml_version, list):
        xml_versions = parse_version_list(xml_version)
        schemas = [
            _load_schema_version(xml_version=version, xml_folder=xml_folder) for version in xml_versions.values()
        ]
        if len(schemas) == 1:
            return schemas[0]

        name = ",".join([schema.version for schema in schemas])
        return HedSchemaGroup(schemas, name=name)
    else:
        return _load_schema_version(xml_version=xml_version, xml_folder=xml_folder)


def load_schema(hed_path, schema_namespace=None, schema=None, name=None, xml_folder=None) -> HedSchema:
    """Load a schema from the given file or URL path.

    Parameters:
        hed_path (str): A filepath or url to open a schema from.
            If loading a TSV file, this should be a single filename where:
            Template: basename.tsv, where files are named basename_Struct.tsv, basename_Tag.tsv, etc.
            Alternatively, you can point to a directory containing the .tsv files.
        schema_namespace (str or None): The name_prefix all tags in this schema will accept.
        schema (HedSchema or None): Deprecated; removal scheduled for 2.0.0. A HED schema to parse
            this file into (it must be a with-standard schema with the same value). Combine
            schemas with a version list in load_schema_version instead.
        name (str or None): User supplied identifier for this schema
        xml_folder (str or None): Folder searched first for the standard schema partner of an
            unmerged partnered library; the normal cache is used when the partner is not there.

    Returns:
        HedSchema: The loaded schema. An unmerged partnered library is returned combined with its
            standard schema partner.

    Raises:
        HedFileError: Empty path passed.
        HedFileError: Unknown extension.
        HedFileError: Any fatal issues when loading the schema.

    """
    if not hed_path:
        raise HedFileError(
            HedExceptions.FILE_NOT_FOUND, "Empty file path passed to HedSchema.load_file", filename=hed_path
        )

    is_url = hed_cache._check_if_url(hed_path)
    if is_url:
        try:
            file_as_string = schema_util.url_to_string(hed_path)
        except URLError as e:
            raise HedFileError(HedExceptions.URL_ERROR, str(e), hed_path) from e
        return from_string(
            file_as_string,
            schema_format=os.path.splitext(hed_path.lower())[1],
            schema_namespace=schema_namespace,
            schema=schema,
            name=name,
            xml_folder=xml_folder,
        )

    # The URL branch above returns through from_string, which warns once itself.
    _warn_if_schema_parameter(schema)
    lower_path = hed_path.lower()
    if lower_path.endswith(".tsv") or os.path.isdir(hed_path):
        if schema is not None:
            raise HedFileError(
                HedExceptions.INVALID_HED_FORMAT,
                "Cannot pass a schema to merge into spreadsheet loading currently.",
                filename=name,
            )
        loader = SchemaLoaderDF(hed_path, None, name=name or "")
    elif lower_path.endswith((".xml", ".mediawiki", ".json")):
        loader = _open_schema_loader(os.path.splitext(lower_path)[1], filename=hed_path, schema=schema, name=name)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=hed_path)

    hed_schema = _finish_load(loader, xml_folder)
    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)

    return hed_schema


def from_string(
    schema_string, schema_format=".xml", schema_namespace=None, schema=None, name=None, xml_folder=None
) -> HedSchema:
    """Create a schema from the given string.

    Parameters:
        schema_string (str): An XML or MEDIAWIKI file as a single long string
        schema_format (str):         The schema format of the source schema string.
            Allowed normal values: .mediawiki, .xml, .json
        schema_namespace (str, None):  The name_prefix all tags in this schema will accept.
        schema (HedSchema or None): Deprecated; removal scheduled for 2.0.0. A HED schema to parse
            this file into (it must be a with-standard schema with the same value). Combine
            schemas with a version list in load_schema_version instead.
        name (str or None): User supplied identifier for this schema
        xml_folder (str or None): Folder searched first for the standard schema partner of an
            unmerged partnered library; the normal cache is used when the partner is not there.

    Returns:
        HedSchema: The loaded schema. An unmerged partnered library is returned combined with its
            standard schema partner.

    :raises HedFileError:
        - If empty string or invalid extension is passed.
        - Other fatal formatting issues with file

    Notes:
        - The loading is determined by file type.

    """
    if not schema_string:
        raise HedFileError(HedExceptions.BAD_PARAMETERS, "Empty string passed to HedSchema.from_string", filename=name)

    _warn_if_schema_parameter(schema)
    if isinstance(schema_string, str):
        # Replace carriage returns with new lines since this might not be done by the caller
        schema_string = schema_string.replace("\r\n", "\n")

    loader = _open_schema_loader(schema_format, schema_as_string=schema_string, schema=schema, name=name)
    hed_schema = _finish_load(loader, xml_folder)
    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)
    return hed_schema


def from_dataframes(schema_data, schema_namespace=None, name=None) -> HedSchema:
    """Create a schema from the given string.

    Parameters:
        schema_data (dict of str or None): A dict of DF_SUFFIXES:file_as_string_or_df
                              Should have an entry for all values of DF_SUFFIXES.
        schema_namespace (str, None):  The name_prefix all tags in this schema will accept.
        name (str or None): User supplied identifier for this schema

    Returns:
        HedSchema:  The loaded schema.

    Raises:
        HedFileError: If empty/invalid parameters.
        Exception: Other fatal I/O or formatting issues.

    Notes:
        - The loading is determined by file type.

    """
    if not schema_data or not isinstance(schema_data, dict):
        raise HedFileError(
            HedExceptions.BAD_PARAMETERS, "Empty or non dict value passed to HedSchema.from_dataframes", filename=name
        )

    loader = SchemaLoaderDF(None, schema_data, name=name or "")
    hed_schema = _finish_load(loader, None)

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)

    return hed_schema


def _warn_if_schema_parameter(schema):
    """Warn once per call site that the schema= parameter is deprecated (removal scheduled for 2.0.0)."""
    if schema is not None:
        warnings.warn(
            "The schema= parameter of load_schema and from_string is deprecated and will be removed in "
            "hedtools 2.0.0; combine schemas with a version list in load_schema_version instead.",
            DeprecationWarning,
            stacklevel=3,
        )


def _open_schema_loader(schema_format, filename=None, schema_as_string=None, schema=None, name=None):
    """Construct the loader for a format; construction reads only the header attributes.

    Parameters:
        schema_format (str): ".xml", ".mediawiki" or ".json" (a file extension).
        filename (str or None): Path to load from, or None when loading from a string.
        schema_as_string (str or None): The whole file as a string, or None when loading from a file.
        schema (HedSchema or None): Existing schema to append into (deprecated path).
        name (str or None): User supplied identifier.

    Returns:
        SchemaLoader: A loader whose ``.schema`` carries the header attributes; call ``_load()``
            to parse the body.

    Raises:
        HedFileError: INVALID_EXTENSION for any other format.
    """
    loaders = {".xml": SchemaLoaderXML, ".mediawiki": SchemaLoaderWiki, ".json": SchemaLoaderJSON}
    for extension, loader_class in loaders.items():
        if schema_format.endswith(extension):
            return loader_class(filename, schema_as_string, schema, None, name or "")
    raise HedFileError(
        HedExceptions.INVALID_EXTENSION, f"Unknown schema extension {schema_format}", filename=filename or name
    )


def _finish_load(loader, xml_folder):
    """Parse a header-read loader into a complete schema, combining an unmerged library with its partner.

    Loaders return exactly what a file declares; for an unmerged partnered library that is the
    library's own elements only. Such a file is the one-member merge group: the partner is loaded
    once through the cache and copied, and the library is inserted into that copy (spec 3.1.2.2).
    Standard schemas, unpartnered libraries, merged library files, and appends into an existing
    schema are simply parsed.

    Parameters:
        loader (SchemaLoader): A constructed loader (header attributes read, body not yet parsed).
        xml_folder (str or None): Folder searched first for the partner; falls back to the cache.

    Returns:
        HedSchema: The complete schema.

    Raises:
        HedFileError: SCHEMA_LIBRARY_INVALID if the partner cannot be loaded.
    """
    header = loader.schema
    if loader.appending_to_schema or not header.with_standard or header.merged:
        return loader._load()
    spec = GroupSpec(partner=header.with_standard, members=[loader], base=None, name=loader.name)
    return merge_group(spec, functools.partial(_load_partner, xml_folder=xml_folder))


def _load_partner(with_standard, xml_folder=None):
    """Load a standard schema partner: from xml_folder if present there, else from the cache.

    Parameters:
        with_standard (str): The standard schema version.
        xml_folder (str or None): Folder to search first.

    Returns:
        HedSchema: The shared cached standard schema (callers must copy before modifying).

    Raises:
        HedFileError: SCHEMA_LIBRARY_INVALID wrapping the underlying failure.
    """
    try:
        return _load_schema_version(xml_version=with_standard, xml_folder=xml_folder)
    except HedFileError as e:
        error = e
        if xml_folder and e.code == HedExceptions.FILE_NOT_FOUND:
            try:
                return _load_schema_version(xml_version=with_standard, xml_folder=None)
            except HedFileError as e2:
                error = e2
        raise HedFileError(
            HedExceptions.SCHEMA_LIBRARY_INVALID,
            message=f"Cannot load withStandard schema '{with_standard}'",
            filename=error.filename,
        ) from error


# If this is actually used, we could easily add other versions/update this one
def get_hed_xml_version(xml_file_path) -> str:
    """Get the version number from a HED XML file.

    Parameters:
        xml_file_path (str): The path to a HED XML file.

    Returns:
        str: The version number of the HED XML file.

    :raises HedFileError:
        - There is an issue loading the schema
    """
    parser = SchemaLoaderXML(xml_file_path)
    return parser.schema.version


def parse_version_list(xml_version_list) -> dict:
    """Takes a list of xml versions and returns a dictionary split by prefix

        e.g. ["score", "testlib"] will return {"": "score, testlib"}
        e.g. ["score", "testlib", "ol:otherlib"] will return {"": "score, testlib", "ol:": "otherlib"}

    Parameters:
        xml_version_list (list): List of str specifying which HED schemas to use

    Returns:
        dict: A dictionary of version strings split by prefix.
    """
    out_versions = defaultdict(list)
    for version in xml_version_list:
        schema_namespace = ""
        if version and ":" in version:
            schema_namespace, _, version = version.partition(":")

        if not isinstance(version, str):
            raise HedFileError(
                HedExceptions.SCHEMA_VERSION_INVALID,
                f"Must specify schema version by number, found no version on {xml_version_list} schema.",
                filename=None,
            )
        # Duplicate versions in one merge group are ignored (spec 3.1.2.4).
        if version not in out_versions[schema_namespace]:
            out_versions[schema_namespace].append(version)

    out_versions = {
        key: ",".join(value) if not key else f"{key}:" + ",".join(value) for key, value in out_versions.items()
    }

    return out_versions


@functools.lru_cache(maxsize=MAX_MEMORY_CACHE)
def _load_schema_version(xml_version=None, xml_folder=None):
    """Return specified version

    Parameters:
        xml_version (str): HED version format string. Expected format: '[schema_namespace:][library_name_]X.Y.Z'
                           Further versions can be added comma separated after the version number/library name.
                           e.g. "lib:library_x.y.z,otherlibrary_x.y.z" loads "library" and "otherlibrary" into "lib:"
                           The schema namespace must be the same and not repeated if loading multiple merged schemas.

        xml_folder (str): Path to a folder containing schema.

    Returns:
        HedSchema: The requested HedSchema object.

    Raises:
        HedFileError: The xml_version is not valid.
        HedFileError: The specified version cannot be found or loaded.
        HedFileError: SCHEMA_LOAD_FAILED - the versions in the namespace cannot be combined (spec 3.1.2.4).
        HedFileError: Other fatal errors loading the schema (These are unlikely if you are not editing them locally).
        HedFileError: The prefix is invalid.
    """
    schema_namespace = ""
    name = xml_version
    if xml_version:
        if ":" in xml_version:
            schema_namespace, _, xml_version = xml_version.partition(":")

    if xml_version:
        xml_versions = xml_version.split(",")
    # Add a blank entry to generate an error if we have no xml version
    else:
        xml_versions = [""]

    if len(xml_versions) == 1:
        return _load_schema_version_sub(xml_versions[0], schema_namespace, xml_folder=xml_folder, name=name)

    # A merge group: read every header first, decide the rules and the load order, then parse.
    loaders = [
        _open_schema_loader(".xml", filename=_resolve_version_path(version, xml_folder), name=name)
        for version in xml_versions
    ]
    spec = resolve_group(loaders, name=name)
    hed_schema = merge_group(spec, functools.partial(_load_partner, xml_folder=xml_folder))
    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace)
    return hed_schema


def _load_schema_version_sub(xml_version, schema_namespace="", xml_folder=None, schema=None, name=""):
    """Return specified version (single version only for this one).

    Parameters:
        xml_version (str): HED version format string. Expected format: '[library_name_]X.Y.Z'.
                           If empty, the latest released standard schema version from the cache is used.
        schema_namespace (str): The prefix this will have
        xml_folder (str): Path to a folder containing schema
        schema (HedSchema or None): A HED schema to merge this new file into.
        name (str): User supplied identifier for this schema

    Returns:
        HedSchema: The requested HedSchema object.

    Raises:
        HedFileError: For the following issues:
        - The xml_version is not valid.
        - The specified version cannot be found or loaded
        - Other fatal errors loading the schema (These are unlikely if you are not editing them locally)
        - The prefix is invalid
    """
    hed_file_path = _resolve_version_path(xml_version, xml_folder)
    return load_schema(
        hed_file_path, schema_namespace=schema_namespace, schema=schema, name=name, xml_folder=xml_folder
    )


def _resolve_version_path(xml_version, xml_folder=None):
    """Return the path of the cached (or xml_folder) file for one version string.

    Parameters:
        xml_version (str): '[library_name_]X.Y.Z'; empty means the latest released standard version.
        xml_folder (str or None): Folder to search instead of the cache.

    Returns:
        str: Path to the schema file.

    Raises:
        HedFileError: SCHEMA_VERSION_INVALID for a malformed version, FILE_NOT_FOUND when no file exists,
            BAD_PARAMETERS when no version is given and the cache is empty.
    """
    if not xml_version:
        versions = hed_cache.get_hed_versions(xml_folder, check_prerelease=False)
        if isinstance(versions, list) and versions:
            xml_version = versions[0]
        else:
            raise HedFileError(
                HedExceptions.BAD_PARAMETERS,
                "No version specified and no HED standard schema versions found in cache. "
                "Run hed.schema.cache_xml_versions() or install hedtools to populate the cache.",
                "",
            )

    # Parse library name from version string before validation
    library_name = ""
    version_to_validate = xml_version
    if "_" in xml_version:
        library_name, _, version_to_validate = xml_version.partition("_")

    # Validate the version string format
    validation_error = validate_version_string(version_to_validate)
    if validation_error:
        raise HedFileError(
            HedExceptions.SCHEMA_VERSION_INVALID,
            f"Invalid version format '{version_to_validate}': {validation_error}",
            xml_version,
        )

    hed_file_path = hed_cache.get_hed_version_path(
        version_to_validate,
        library_name=library_name,
        local_hed_directory=xml_folder,
    )

    if hed_file_path:
        return hed_file_path

    library_string = f"for library '{library_name}'" if library_name else ""
    known_versions = hed_cache.get_hed_versions(
        xml_folder, library_name=library_name if library_name else "all", check_prerelease=True
    )
    raise HedFileError(
        HedExceptions.FILE_NOT_FOUND,
        f"HED version {library_string}: '{version_to_validate}' not found. Check {hed_cache.get_cache_directory(xml_folder)} for cache or https://github.com/hed-standard/hed-schemas/tree/main/library_schemas. "
        f"Known versions {library_string}: {known_versions}.",
        "",
    )
