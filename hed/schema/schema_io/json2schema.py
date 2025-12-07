"""
This module is used to create a HedSchema object from a JSON file or string.
"""

import json
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.schema.schema_io import json_constants
from hed.schema.schema_io.base2schema import SchemaLoader


class SchemaLoaderJSON(SchemaLoader):
    """Loads JSON schemas from filenames or strings.

    Expected usage is SchemaLoaderJSON.load(filename)

    SchemaLoaderJSON(filename) will load just the header_attributes
    """

    def __init__(self, filename, schema_as_string=None, schema=None, file_format=None, name=""):
        """Initialize the JSON schema loader.

        Parameters:
            filename (str or None): A valid filepath or None
            schema_as_string (str or None): A full schema as text or None
            schema (HedSchema or None): A HED schema to merge this new file into
            file_format (str or None): Not used for JSON
            name (str or None): Optional user supplied identifier, by default uses filename
        """
        super().__init__(filename, schema_as_string, schema, file_format, name)
        self._json_data = None
        self._schema.source_format = ".json"

    def _open_file(self):
        """Parses a JSON file and returns the dictionary."""
        try:
            if self.filename:
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(self.schema_as_string)
            return data
        except json.JSONDecodeError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), self.name) from e
        except Exception as e:
            raise HedFileError(HedExceptions.FILE_NOT_FOUND, str(e), self.name) from e

    def _get_header_attributes(self, json_data):
        """Gets the schema attributes from the JSON root"""
        # Define the keys that are section keys (not header attributes)
        section_keys = {
            json_constants.TAGS_KEY,
            json_constants.UNITS_KEY,
            json_constants.UNIT_CLASSES_KEY,
            json_constants.UNIT_MODIFIERS_KEY,
            json_constants.VALUE_CLASSES_KEY,
            json_constants.SCHEMA_ATTRIBUTES_KEY,
            json_constants.PROPERTIES_KEY,
            json_constants.SOURCES_KEY,
            json_constants.PREFIXES_KEY,
            json_constants.EXTERNAL_ANNOTATIONS_KEY,
            json_constants.PROLOGUE_KEY,
            json_constants.EPILOGUE_KEY,
        }

        # Collect all top-level keys that aren't section keys as header attributes
        # This includes version, library, withStandard, unmerged, xmlns:xsi, xsi:noNamespaceSchemaLocation, etc.
        header_attrs = {}
        for key, value in json_data.items():
            if key not in section_keys:
                header_attrs[key] = value

        return header_attrs

    @staticmethod
    def _convert_to_internal_format(value):
        """Convert JSON values to internal schema format.

        Multi-value attributes are stored as arrays in JSON but as comma-separated strings internally.

        Parameters:
            value: The value to convert (could be array, string, bool, etc.)

        Returns:
            The converted value
        """
        # Convert arrays to comma-separated strings
        if isinstance(value, list):
            return ",".join(str(v) for v in value)
        return value

    def _parse_data(self):
        """Loads the schema data from the JSON dictionary."""
        self._json_data = self.input_data

        # Initialize unit entries dictionary for use by unit classes
        self._unit_entries = {}

        # Parse in the defined order
        # Units must be parsed before UnitClasses since unit classes reference units
        parse_order = {
            HedSectionKey.Properties: self._populate_properties,
            HedSectionKey.Attributes: self._populate_schema_attributes,
            HedSectionKey.UnitModifiers: self._populate_unit_modifiers,
            HedSectionKey.Units: self._populate_units,
            HedSectionKey.UnitClasses: self._populate_unit_classes,
            HedSectionKey.ValueClasses: self._populate_value_classes,
            HedSectionKey.Tags: self._populate_tags,
        }

        # Load prologue and epilogue
        self._schema.prologue = self._json_data.get(json_constants.PROLOGUE_KEY, "")
        self._schema.epilogue = self._json_data.get(json_constants.EPILOGUE_KEY, "")

        # Load extras
        self._load_extras()

        # Parse each section - initialize attributes before loading each section
        # This follows the same pattern as MediaWiki/XML loaders
        for section_key, parse_func in parse_order.items():
            self._schema._initialize_attributes(section_key)
            parse_func()

    def _populate_properties(self):
        """Populate the properties section."""
        if json_constants.PROPERTIES_KEY not in self._json_data:
            return

        self._schema._initialize_attributes(HedSectionKey.Properties)
        properties = self._json_data[json_constants.PROPERTIES_KEY]

        for prop_name, prop_data in properties.items():
            entry = self._create_property_entry(prop_name, prop_data)
            self._add_to_dict_base(entry, HedSectionKey.Properties)

    def _create_property_entry(self, prop_name, prop_data):
        """Create a property entry from JSON data.

        Parameters:
            prop_name (str): Property name
            prop_data (dict): Property attributes

        Returns:
            HedSchemaEntry: The created entry
        """
        entry = self._schema._create_tag_entry(prop_name, HedSectionKey.Properties)

        if json_constants.DESCRIPTION_KEY in prop_data:
            desc = prop_data[json_constants.DESCRIPTION_KEY]
            # Convert empty string back to None to match XML/MediaWiki behavior
            entry.description = desc if desc else None

        # Add any other attributes from the data
        for key, value in prop_data.items():
            if key != json_constants.DESCRIPTION_KEY:
                entry._set_attribute_value(key, self._convert_to_internal_format(value))

        return entry

    def _populate_schema_attributes(self):
        """Populate the schema attributes section."""
        if json_constants.SCHEMA_ATTRIBUTES_KEY not in self._json_data:
            return

        self._schema._initialize_attributes(HedSectionKey.Attributes)
        attributes = self._json_data[json_constants.SCHEMA_ATTRIBUTES_KEY]

        for attr_name, attr_data in attributes.items():
            entry = self._create_schema_attribute_entry(attr_name, attr_data)
            self._add_to_dict_base(entry, HedSectionKey.Attributes)

    def _create_schema_attribute_entry(self, attr_name, attr_data):
        """Create a schema attribute entry from JSON data.

        Parameters:
            attr_name (str): Attribute name
            attr_data (dict): Attribute properties

        Returns:
            HedSchemaEntry: The created entry
        """
        entry = self._schema._create_tag_entry(attr_name, HedSectionKey.Attributes)

        if json_constants.DESCRIPTION_KEY in attr_data:
            entry.description = attr_data[json_constants.DESCRIPTION_KEY]

        # Add domain and range properties
        for key, value in attr_data.items():
            if key != json_constants.DESCRIPTION_KEY:
                entry._set_attribute_value(key, self._convert_to_internal_format(value))

        return entry

    def _populate_unit_modifiers(self):
        """Populate the unit modifiers section."""
        if json_constants.UNIT_MODIFIERS_KEY not in self._json_data:
            return

        self._schema._initialize_attributes(HedSectionKey.UnitModifiers)
        unit_modifiers = self._json_data[json_constants.UNIT_MODIFIERS_KEY]

        for modifier_name, modifier_data in unit_modifiers.items():
            entry = self._create_unit_modifier_entry(modifier_name, modifier_data)
            self._add_to_dict_base(entry, HedSectionKey.UnitModifiers)

    def _create_unit_modifier_entry(self, modifier_name, modifier_data):
        """Create a unit modifier entry from JSON data.

        Parameters:
            modifier_name (str): Unit modifier name
            modifier_data (dict): Modifier attributes

        Returns:
            HedSchemaEntry: The created entry
        """
        entry = self._schema._create_tag_entry(modifier_name, HedSectionKey.UnitModifiers)

        if json_constants.DESCRIPTION_KEY in modifier_data:
            entry.description = modifier_data[json_constants.DESCRIPTION_KEY]

        # Add other attributes (conversion factor, SI unit modifier, etc.)
        for key, value in modifier_data.items():
            if key != json_constants.DESCRIPTION_KEY:
                entry._set_attribute_value(key, self._convert_to_internal_format(value))

        return entry

    def _populate_units(self):
        """Populate the units section from top-level units dictionary."""
        if json_constants.UNITS_KEY not in self._json_data:
            return

        units = self._json_data[json_constants.UNITS_KEY]

        # Populate the unit entries dictionary for use by unit classes
        for unit_name, unit_data in units.items():
            entry = self._create_unit_entry(unit_name, unit_data)
            self._add_to_dict_base(entry, HedSectionKey.Units)
            self._unit_entries[unit_name] = entry

    def _create_unit_entry(self, unit_name, unit_data):
        """Create a unit entry from JSON data.

        Parameters:
            unit_name (str): Unit name
            unit_data (dict): Unit attributes

        Returns:
            HedSchemaEntry: The created entry
        """
        entry = self._schema._create_tag_entry(unit_name, HedSectionKey.Units)

        if json_constants.DESCRIPTION_KEY in unit_data:
            entry.description = unit_data[json_constants.DESCRIPTION_KEY]

        # Add all attributes
        for key, value in unit_data.items():
            if key != json_constants.DESCRIPTION_KEY:
                entry._set_attribute_value(key, self._convert_to_internal_format(value))

        return entry

    def _populate_unit_classes(self):
        """Populate the unit classes section."""
        if json_constants.UNIT_CLASSES_KEY not in self._json_data:
            return

        unit_classes = self._json_data[json_constants.UNIT_CLASSES_KEY]

        for class_name, class_data in unit_classes.items():
            entry = self._create_unit_class_entry(class_name, class_data)
            self._add_to_dict_base(entry, HedSectionKey.UnitClasses)

    def _create_unit_class_entry(self, class_name, class_data):
        """Create a unit class entry from JSON data.

        Parameters:
            class_name (str): Unit class name
            class_data (dict): Class attributes

        Returns:
            HedSchemaEntry: The created entry
        """
        entry = self._schema._create_tag_entry(class_name, HedSectionKey.UnitClasses)

        if json_constants.DESCRIPTION_KEY in class_data:
            entry.description = class_data[json_constants.DESCRIPTION_KEY]

        # Add units from the units list - look them up in the pre-loaded _unit_entries
        if json_constants.UNITS_LIST_KEY in class_data:
            unit_names = class_data[json_constants.UNITS_LIST_KEY]
            for unit_name in unit_names:
                # Get the pre-loaded unit entry
                unit_entry = self._unit_entries.get(unit_name)
                if unit_entry:
                    entry.add_unit(unit_entry)
                else:
                    # Unit not found - might be old format or missing data
                    # Create a minimal unit entry
                    unit_entry = self._schema._create_tag_entry(unit_name, HedSectionKey.Units)
                    # Check for unit data as a sibling key (old format)
                    if unit_name in class_data and isinstance(class_data[unit_name], dict):
                        unit_data = class_data[unit_name]
                        if json_constants.DESCRIPTION_KEY in unit_data:
                            unit_entry.description = unit_data[json_constants.DESCRIPTION_KEY]
                        for attr_key, attr_value in unit_data.items():
                            if attr_key != json_constants.DESCRIPTION_KEY:
                                unit_entry._set_attribute_value(attr_key, self._convert_to_internal_format(attr_value))
                    entry.add_unit(unit_entry)
                    self._unit_entries[unit_name] = unit_entry

        # Add default units
        if json_constants.DEFAULT_UNITS_KEY in class_data:
            entry._set_attribute_value(
                HedKey.DefaultUnits, self._convert_to_internal_format(class_data[json_constants.DEFAULT_UNITS_KEY])
            )

        # Add any other attributes (exclude unit data if present)
        unit_names_set = set(class_data.get(json_constants.UNITS_LIST_KEY, []))
        for key, value in class_data.items():
            if (
                key not in [json_constants.DESCRIPTION_KEY, json_constants.UNITS_LIST_KEY, json_constants.DEFAULT_UNITS_KEY]
                and key not in unit_names_set
            ):
                entry._set_attribute_value(key, self._convert_to_internal_format(value))

        return entry

    def _populate_value_classes(self):
        """Populate the value classes section."""
        if json_constants.VALUE_CLASSES_KEY not in self._json_data:
            return

        value_classes = self._json_data[json_constants.VALUE_CLASSES_KEY]

        for class_name, class_data in value_classes.items():
            entry = self._create_value_class_entry(class_name, class_data)
            self._add_to_dict_base(entry, HedSectionKey.ValueClasses)

    def _create_value_class_entry(self, class_name, class_data):
        """Create a value class entry from JSON data.

        Parameters:
            class_name (str): Value class name
            class_data (dict): Class attributes

        Returns:
            HedSchemaEntry: The created entry
        """
        entry = self._schema._create_tag_entry(class_name, HedSectionKey.ValueClasses)

        if json_constants.DESCRIPTION_KEY in class_data:
            entry.description = class_data[json_constants.DESCRIPTION_KEY]

        # Add allowed characters (join multiple values with commas)
        if json_constants.ALLOWED_CHARACTERS_KEY in class_data:
            char_types = class_data[json_constants.ALLOWED_CHARACTERS_KEY]
            if isinstance(char_types, list):
                allowed_char_value = ",".join(char_types)
            else:
                allowed_char_value = char_types
            entry._set_attribute_value(HedKey.AllowedCharacter, allowed_char_value)

        # Add any other attributes
        for key, value in class_data.items():
            if key not in [json_constants.DESCRIPTION_KEY, json_constants.ALLOWED_CHARACTERS_KEY]:
                entry._set_attribute_value(key, self._convert_to_internal_format(value))

        return entry

    def _populate_tags(self):
        """Populate the tags section by building the hierarchy."""
        if json_constants.TAGS_KEY not in self._json_data:
            return

        tags_data = self._json_data[json_constants.TAGS_KEY]

        # Tags are keyed by short_form in JSON
        # If a tag has a placeholder key, we need to create both the base tag and the /#placeholder
        for short_form, tag_data in tags_data.items():
            long_form = tag_data.get(json_constants.LONG_FORM_KEY, short_form)
            has_placeholder = json_constants.PLACEHOLDER_KEY in tag_data

            # Create the base tag entry
            entry = self._create_tag_entry(long_form, tag_data, is_takes_value_placeholder=False)
            self._add_to_dict_base(entry, HedSectionKey.Tags)

            # If this tag has a placeholder, create the placeholder tag
            if has_placeholder:
                placeholder_name = long_form + "/#"
                placeholder_entry = self._create_tag_entry(placeholder_name, tag_data, is_takes_value_placeholder=True)
                self._add_to_dict_base(placeholder_entry, HedSectionKey.Tags)

    def _create_tag_entry(self, long_form, tag_data, is_takes_value_placeholder=False):
        """Create a tag entry from JSON data.

        Parameters:
            long_form (str): Full tag path (e.g., "Event/Action/Move" or "Property/Agent-property/Agent-trait/Age/#")
            tag_data (dict): Tag attributes and metadata
            is_takes_value_placeholder (bool): If True, this is the /#  placeholder tag

        Returns:
            HedTagEntry: The created tag entry
        """
        # Use the long_form (full path) as the entry name - this is critical!
        # The schema internals rely on the full path for proper hierarchy
        entry = self._schema._create_tag_entry(long_form, HedSectionKey.Tags)

        # Set description (only on base tag, not placeholder)
        if not is_takes_value_placeholder and json_constants.DESCRIPTION_KEY in tag_data:
            entry.description = tag_data[json_constants.DESCRIPTION_KEY]

        # Set attributes based on whether this is a placeholder or base tag
        if is_takes_value_placeholder:
            # For placeholder tags, get attributes from the placeholder key
            if json_constants.PLACEHOLDER_KEY in tag_data:
                placeholder_attrs = tag_data[json_constants.PLACEHOLDER_KEY]

                # Set placeholder description if present
                if "description" in placeholder_attrs:
                    entry.description = placeholder_attrs["description"]

                # Set other attributes
                for attr_name, attr_value in placeholder_attrs.items():
                    if attr_name != "description":  # Skip description, already handled
                        self._set_tag_attribute(entry, attr_name, attr_value)
        else:
            # For base tags, prefer explicitAttributes if present (new format)
            # Otherwise fall back to attributes (old format for backwards compatibility)
            attrs_to_set = tag_data.get(json_constants.EXPLICIT_ATTRIBUTES_KEY)
            if attrs_to_set is None:
                # Old format without explicitAttributes - use attributes
                attrs_to_set = tag_data.get(json_constants.ATTRIBUTES_KEY, {})

            for attr_name, attr_value in attrs_to_set.items():
                self._set_tag_attribute(entry, attr_name, attr_value)

        return entry

    def _set_tag_attribute(self, entry, attr_name, attr_value):
        """Set an attribute on a tag entry.

        Parameters:
            entry (HedTagEntry): The tag entry
            attr_name (str): Attribute name
            attr_value: Attribute value (bool, str, or list)
        """
        # Map JSON attribute names to HedKey constants
        attr_map = {
            "extensionAllowed": HedKey.ExtensionAllowed,
            "takesValue": HedKey.TakesValue,
            "requireChild": HedKey.RequireChild,
            "unique": HedKey.Unique,
            "reserved": HedKey.Reserved,
            "tagGroup": HedKey.TagGroup,
            "topLevelTagGroup": HedKey.TopLevelTagGroup,
            "recommended": HedKey.Recommended,
            "required": HedKey.Required,
            "suggestedTag": HedKey.SuggestedTag,
            "relatedTag": HedKey.RelatedTag,
            "valueClass": HedKey.ValueClass,
            "unitClass": HedKey.UnitClass,
            "defaultUnits": HedKey.DefaultUnits,
            "hedId": HedKey.HedID,
            "rooted": HedKey.Rooted,
            "deprecatedFrom": HedKey.DeprecatedFrom,
        }

        hed_key = attr_map.get(attr_name)
        if not hed_key:
            # Unknown attribute, store with conversion (arrays to comma-separated strings)
            entry._set_attribute_value(attr_name, self._convert_to_internal_format(attr_value))
            return

        # Handle boolean attributes
        if isinstance(attr_value, bool):
            if attr_value:  # Only set if True
                entry._set_attribute_value(hed_key, True)
        # Handle list attributes (join with commas)
        elif isinstance(attr_value, list):
            if attr_value:  # Skip empty lists
                value_str = ",".join(str(v) for v in attr_value if v)
                if value_str:
                    entry._set_attribute_value(hed_key, value_str)
        # Handle single value attributes
        elif attr_value:
            entry._set_attribute_value(hed_key, attr_value)

    def _load_extras(self):
        """Load extra sections like sources, prefixes, and external annotations."""
        from hed.schema.schema_io import df_constants
        import pandas as pd

        self._schema.extras = {}

        # Load sources - always create DataFrame even if empty to match XML/MediaWiki behavior
        sources_list = []
        if json_constants.SOURCES_KEY in self._json_data:
            sources_data = self._json_data[json_constants.SOURCES_KEY]
            for source_data in sources_data:
                sources_list.append(
                    {
                        df_constants.source: source_data.get("name", ""),
                        df_constants.link: source_data.get("link", ""),
                        df_constants.description: source_data.get(json_constants.DESCRIPTION_KEY, ""),
                    }
                )
        self._schema.extras[df_constants.SOURCES_KEY] = pd.DataFrame(sources_list, columns=df_constants.source_columns)

        # Load prefixes - always create DataFrame even if empty
        prefixes_list = []
        if json_constants.PREFIXES_KEY in self._json_data:
            prefixes_data = self._json_data[json_constants.PREFIXES_KEY]
            for prefix_data in prefixes_data:
                prefixes_list.append(
                    {
                        df_constants.prefix: prefix_data.get("name", ""),
                        df_constants.namespace: prefix_data.get("namespace", ""),
                        df_constants.description: prefix_data.get(json_constants.DESCRIPTION_KEY, ""),
                    }
                )
        self._schema.extras[df_constants.PREFIXES_KEY] = pd.DataFrame(prefixes_list, columns=df_constants.prefix_columns)

        # Load external annotations - always create DataFrame even if empty
        externals_list = []
        if json_constants.EXTERNAL_ANNOTATIONS_KEY in self._json_data:
            externals_data = self._json_data[json_constants.EXTERNAL_ANNOTATIONS_KEY]
            for external_data in externals_data:
                externals_list.append(
                    {
                        df_constants.prefix: external_data.get("name", ""),
                        df_constants.id: external_data.get("id", ""),
                        df_constants.iri: external_data.get("iri", ""),
                        df_constants.description: external_data.get(json_constants.DESCRIPTION_KEY, ""),
                    }
                )
        self._schema.extras[df_constants.EXTERNAL_ANNOTATION_KEY] = pd.DataFrame(
            externals_list, columns=df_constants.external_annotation_columns
        )
