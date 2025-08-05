from hed.schema.schema_io.ontology_util import get_library_data
from hed.schema.schema_io.df_util import remove_prefix
from semantic_version import Version
from hed.schema.hed_schema_io import load_schema_version
from hed.schema.hed_cache import get_hed_versions
from hed.schema.hed_schema_constants import HedKey
from hed.errors.error_types import SchemaAttributeErrors
from hed.errors.error_reporter import ErrorHandler


class HedIDValidator:
    """Support class to validate hedIds in schemas"""
    def __init__(self, hed_schema):
        """Support class to validate hedIds in schemas

        Parameters:
            hed_schema(HedSchemaBase): The schema we're validating.
            It uses this to derive the version number(s) of the previous schema.
        """
        self.hed_schema = hed_schema
        self._previous_schemas = {}

        versions = self.hed_schema.version_number.split(",")
        libraries = self.hed_schema.library.split(",")

        prev_versions = {}
        self.library_data = {}
        for version, library in zip(versions, libraries):
            prev_version = self._get_previous_version(version, library)
            if prev_version:
                prev_versions[library] = prev_version
            library_data = get_library_data(library)
            if library_data:
                self.library_data[library] = library_data

        # Add the standard schema if we have a with_standard
        if "" not in prev_versions and self.hed_schema.with_standard:
            prev_version = self._get_previous_version(self.hed_schema.with_standard, "")
            if prev_version:
                prev_versions[""] = prev_version
            library_data = get_library_data("")
            if library_data:
                self.library_data[""] = get_library_data("")

        if prev_versions:
            self._previous_schemas = {library: load_schema_version(full_version) for library, full_version in
                                      prev_versions.items()}

    @staticmethod
    def _get_previous_version(version, library):
        current_version = Version(version)
        all_schema_versions = get_hed_versions(library_name=library)
        for old_version in all_schema_versions:
            if Version(old_version) < current_version:
                prev_version = old_version
                if library:
                    prev_version = f"{library}_{prev_version}"
                return prev_version

    def verify_tag_id(self, hed_schema, tag_entry, attribute_name):
        """Validates the hedID attribute values

           This follows the template from schema_attribute_validators.py

        Parameters:
            hed_schema (HedSchema): The schema to use for validation
            tag_entry (HedSchemaEntry): The schema entry for this tag.
            attribute_name (str): The name of this attribute.

        Returns:
            issues(list): A list of issues from validating this attribute.
        """
        # todo: If you have a way to know the schema should have 100% ids, you could check for that and flag missing
        new_id = tag_entry.attributes.get(attribute_name, "")
        old_id = None
        tag_library = tag_entry.has_attribute(HedKey.InLibrary, return_value=True)
        if not tag_library:
            tag_library = ""

        previous_schema = self._previous_schemas.get(tag_library)
        if previous_schema:
            old_entry = previous_schema.get_tag_entry(tag_entry.name, key_class=tag_entry.section_key)
            if old_entry:
                old_id = old_entry.attributes.get(HedKey.HedID)

        if old_id:
            try:
                old_id = int(remove_prefix(old_id, "HED_"))
            except ValueError:
                # Just silently ignore invalid old_id values(this shouldn't happen)
                pass
        if new_id:
            try:
                new_id = int(remove_prefix(new_id, "HED_"))
            except ValueError:
                return ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_HED_ID_INVALID, tag_entry.name, new_id)
        # Nothing to verify
        if new_id is None and old_id is None:
            return []

        issues = []
        if old_id and old_id != new_id:
            issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_HED_ID_INVALID, tag_entry.name, new_id,
                                                old_id=old_id)

        library_data = self.library_data.get(tag_library)
        if library_data and new_id is not None:
            starting_id, ending_id = library_data["id_range"]
            if new_id < starting_id or new_id > ending_id:
                issues += ErrorHandler.format_error(SchemaAttributeErrors.SCHEMA_HED_ID_INVALID, tag_entry.name,
                                                    new_id, valid_min=starting_id, valid_max=ending_id)

        return issues
