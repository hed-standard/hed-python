"""Allows output of HedSchema objects as .json format"""

import json
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.schema.schema_io import json_constants, df_constants
from hed.schema.schema_io.schema2base import Schema2Base


class Schema2JSON(Schema2Base):
    """Convert HedSchema to JSON format."""

    def __init__(self):
        super().__init__()
        self.output = None

    # =========================================
    # Required baseclass functions
    # =========================================
    def _initialize_output(self):
        """Initialize the output dictionary."""
        self.output = {}

    def _output_header(self, attributes):
        """Output the header attributes.

        Parameters:
            attributes (dict): Header attributes to output
        """
        # Output all header attributes to preserve xmlns:xsi, xsi:noNamespaceSchemaLocation, etc.
        for key, value in attributes.items():
            self.output[key] = value

    def _output_prologue(self, prologue):
        """Output the prologue.

        Parameters:
            prologue (str): Prologue text
        """
        if prologue:
            self.output[json_constants.PROLOGUE_KEY] = prologue

    def _output_annotations(self, hed_schema):
        """Output annotations (not implemented for JSON base format)."""
        pass

    def _output_extras(self, hed_schema):
        """Output extra sections like sources, prefixes, external annotations.

        Parameters:
            hed_schema (HedSchema): The schema being output
        """
        self._output_sources(hed_schema)
        self._output_prefixes(hed_schema)
        self._output_external_annotations(hed_schema)

    def _output_sources(self, hed_schema):
        """Output sources section.

        Parameters:
            hed_schema (HedSchema): The schema being output
        """
        sources = hed_schema.get_extras(df_constants.SOURCES_KEY)
        if sources is None or sources.empty:
            return

        sources_list = []
        for _, row in sources.iterrows():
            sources_list.append(
                {
                    "name": row[df_constants.source],
                    "link": row[df_constants.link],
                    json_constants.DESCRIPTION_KEY: row[df_constants.description],
                }
            )

        self.output[json_constants.SOURCES_KEY] = sources_list

    def _output_prefixes(self, hed_schema):
        """Output prefixes section.

        Parameters:
            hed_schema (HedSchema): The schema being output
        """
        prefixes = hed_schema.get_extras(df_constants.PREFIXES_KEY)
        if prefixes is None or prefixes.empty:
            return

        prefixes_list = []
        for _, row in prefixes.iterrows():
            prefixes_list.append(
                {
                    "name": row[df_constants.prefix],
                    "namespace": row[df_constants.namespace],
                    json_constants.DESCRIPTION_KEY: row[df_constants.description],
                }
            )

        self.output[json_constants.PREFIXES_KEY] = prefixes_list

    def _output_external_annotations(self, hed_schema):
        """Output external annotations section.

        Parameters:
            hed_schema (HedSchema): The schema being output
        """
        externals = hed_schema.get_extras(df_constants.EXTERNAL_ANNOTATION_KEY)
        if externals is None or externals.empty:
            return

        externals_list = []
        for _, row in externals.iterrows():
            externals_list.append(
                {
                    "name": row[df_constants.prefix],
                    "id": row[df_constants.id],
                    "iri": row[df_constants.iri],
                    json_constants.DESCRIPTION_KEY: row[df_constants.description],
                }
            )

        self.output[json_constants.EXTERNAL_ANNOTATIONS_KEY] = externals_list

    def _output_epilogue(self, epilogue):
        """Output the epilogue.

        Parameters:
            epilogue (str): Epilogue text
        """
        if epilogue:
            self.output[json_constants.EPILOGUE_KEY] = epilogue

    def _output_footer(self):
        """Finalize output (nothing needed for JSON)."""
        pass

    def _start_section(self, key_class):
        """Start a new section in the output.

        Parameters:
            key_class (HedSectionKey): The section type

        Returns:
            dict: The section dictionary
        """
        section_key = json_constants.SECTION_KEYS.get(key_class)
        if section_key:
            self.output[section_key] = {}
            return self.output[section_key]
        return {}

    def _end_tag_section(self):
        """Finalize the tags section (nothing needed for JSON)."""
        pass

    def _end_units_section(self):
        """Finalize the units section (nothing needed for JSON)."""
        pass

    def _end_section(self, section_key):
        """Finalize a section (nothing needed for JSON).

        Parameters:
            section_key (HedSectionKey): The section key
        """
        pass

    def _output_units(self, unit_classes):
        """Output units as separate sections for JSON format.

        Overrides base class to create two separate sections:
        1. units: All units with their attributes (SIUnit, unitSymbol, etc.)
        2. unit_classes: Unit classes with lists of units they contain

        Parameters:
            unit_classes: The unit classes section from the schema
        """
        # Create the units section - all units with their attributes
        units_section = self._start_section(HedSectionKey.Units)

        # Collect all units from all unit classes
        for unit_class_entry in unit_classes.values():
            if self._should_skip(unit_class_entry):
                continue

            for unit_entry in unit_class_entry.units.values():
                if self._should_skip(unit_entry):
                    continue

                # Write unit with its attributes
                unit_data = {
                    json_constants.DESCRIPTION_KEY: unit_entry.description,  # Use None directly, not ""
                }

                # Add unit-specific attributes
                for attr_name, attr_value in unit_entry.attributes.items():
                    # Skip attributes that should be disallowed (like inLibrary when saving unmerged)
                    if self._attribute_disallowed(attr_name):
                        continue
                    # Convert boolean attributes
                    if isinstance(attr_value, bool) or attr_value in (True, False, "true", "false"):
                        unit_data[attr_name] = bool(attr_value)
                    # Convert comma-separated strings to lists for multi-value attributes
                    elif isinstance(attr_value, str) and "," in attr_value:
                        unit_data[attr_name] = [v.strip() for v in attr_value.split(",") if v.strip()]
                    else:
                        unit_data[attr_name] = attr_value

                units_section[unit_entry.name] = unit_data

        # Create the unit_classes section - just references to units
        unit_classes_section = self._start_section(HedSectionKey.UnitClasses)

        for unit_class_entry in unit_classes.values():
            if self._should_skip(unit_class_entry):
                # Check if has lib units
                has_lib_unit = any(unit.attributes.get(HedKey.InLibrary) for unit in unit_class_entry.units.values())
                if not self._save_lib or not has_lib_unit:
                    continue

            # Use existing method which now writes just the unit names list
            self._write_entry(unit_class_entry, unit_classes_section, include_props=True)

        self._end_units_section()

    def _write_tag_entry(self, tag_entry, parent_node, level=0):
        """Write a tag entry to the output.

        Parameters:
            tag_entry (HedTagEntry): The tag entry to write
            parent_node (dict): Parent node dictionary (ignored for JSON flat structure)
            level (int): Nesting level (unused in JSON)

        Returns:
            dict: The created tag node
        """
        # Get the tags section
        tags_section = self.output[json_constants.TAGS_KEY]

        # For placeholder tags (e.g., "Age/#"), add to the base tag's placeholder key
        if tag_entry.name.endswith("/#"):
            # This is a takes-value placeholder tag
            # Get the base tag name (without "/#")
            base_name = tag_entry.name[:-2]
            base_short_name = tag_entry.short_tag_name

            # Check if we already have an entry for the base tag
            if base_short_name in tags_section:
                # Add placeholder data to existing base tag entry
                placeholder_data = {}

                # Add placeholder description
                if tag_entry.description:
                    placeholder_data["description"] = tag_entry.description

                # Add placeholder-specific attributes (unitClass, valueClass, hedId, deprecatedFrom, takesValue)
                placeholder_attrs = self._get_placeholder_attributes(tag_entry)
                if placeholder_attrs:
                    placeholder_data.update(placeholder_attrs)

                tags_section[base_short_name][json_constants.PLACEHOLDER_KEY] = placeholder_data
                return tags_section[base_short_name]
            else:
                # Base tag hasn't been encountered yet, create entry with placeholder
                # Filter out any children from the placeholder (shouldn't have any normally)
                children_names = []
                if tag_entry.children:
                    for child in tag_entry.children.values():
                        if tag_entry.takes_value_child_entry and child is tag_entry.takes_value_child_entry:
                            continue
                        children_names.append(child.short_tag_name)

                placeholder_data = {}
                # Add placeholder description
                if tag_entry.description:
                    placeholder_data["description"] = tag_entry.description

                placeholder_attrs = self._get_placeholder_attributes(tag_entry)
                if placeholder_attrs:
                    placeholder_data.update(placeholder_attrs)

                tag_data = {
                    json_constants.SHORT_FORM_KEY: base_short_name,
                    json_constants.LONG_FORM_KEY: base_name,
                    json_constants.DESCRIPTION_KEY: None,  # Base tag description will be set when base tag is processed
                    json_constants.PARENT_KEY: tag_entry.parent.short_tag_name if tag_entry.parent else None,
                    json_constants.CHILDREN_KEY: children_names,
                    json_constants.ATTRIBUTES_KEY: {},  # Base tag attributes will be added later
                    json_constants.PLACEHOLDER_KEY: placeholder_data,
                }
                tags_section[base_short_name] = tag_data
                return tag_data
        else:
            # Regular tag (not a placeholder)
            # Filter out the takes-value child from the children list
            children_names = []
            if tag_entry.children:
                for child in tag_entry.children.values():
                    # Skip the takes-value placeholder child
                    if tag_entry.takes_value_child_entry and child is tag_entry.takes_value_child_entry:
                        continue
                    children_names.append(child.short_tag_name)

            # Check if this tag has a takes-value child (e.g., "Age/#")
            has_takes_value_child = tag_entry.takes_value_child_entry is not None

            if tag_entry.short_tag_name in tags_section:
                # Entry already exists (from encountering the placeholder first)
                # Update with the base tag information
                existing_entry = tags_section[tag_entry.short_tag_name]
                existing_entry[json_constants.LONG_FORM_KEY] = tag_entry.name
                existing_entry[json_constants.DESCRIPTION_KEY] = tag_entry.description or ""
                existing_entry[json_constants.PARENT_KEY] = tag_entry.parent.short_tag_name if tag_entry.parent else None
                existing_entry[json_constants.CHILDREN_KEY] = children_names
                # Set base tag attributes - include ALL attributes on the base tag
                all_attrs, explicit_attrs = self._get_tag_attributes(tag_entry)
                existing_entry[json_constants.ATTRIBUTES_KEY] = all_attrs
                existing_entry[json_constants.EXPLICIT_ATTRIBUTES_KEY] = explicit_attrs
                return existing_entry
            else:
                # New entry
                all_attrs, explicit_attrs = self._get_tag_attributes(tag_entry)
                tag_data = {
                    json_constants.SHORT_FORM_KEY: tag_entry.short_tag_name,
                    json_constants.LONG_FORM_KEY: tag_entry.name,
                    json_constants.DESCRIPTION_KEY: tag_entry.description,  # Use None directly, not ""
                    json_constants.PARENT_KEY: tag_entry.parent.short_tag_name if tag_entry.parent else None,
                    json_constants.CHILDREN_KEY: children_names,
                    json_constants.ATTRIBUTES_KEY: all_attrs,
                    json_constants.EXPLICIT_ATTRIBUTES_KEY: explicit_attrs,
                }

                # Add placeholder key if this tag has a takes-value child
                # (the placeholder entry will be processed later and will populate this)
                if has_takes_value_child:
                    tag_data[json_constants.PLACEHOLDER_KEY] = {}

                tags_section[tag_entry.short_tag_name] = tag_data
                return tag_data

    def _get_tag_attributes(self, tag_entry, exclude_takes_value_if_placeholder=True):
        """Extract tag attributes into dictionaries.

        Parameters:
            tag_entry (HedTagEntry): The tag entry
            exclude_takes_value_if_placeholder (bool): If True and tag has a placeholder child,
                                                       don't include takesValue in parent attributes

        Returns:
            tuple: (all_attributes_dict, explicit_attributes_dict)
                - all_attributes: All effective attributes (explicit + inherited)
                - explicit_attributes: Only attributes explicitly set on this tag
        """

        # Helper to get list values from a source dict
        def get_list_value(attr_key, source_dict):
            value = source_dict.get(attr_key)
            if value is None:
                return []
            if isinstance(value, list):
                return value
            # Comma-separated string
            return [v.strip() for v in value.split(",") if v.strip()]

        # Helper to get boolean attribute value from a source dict
        def get_bool_attribute(attr_key, source_dict):
            if attr_key not in source_dict:
                return False
            value = source_dict[attr_key]
            # If it's stored as string "True" or "true", keep it as string for XML compatibility
            if isinstance(value, str) and value.lower() in ("true", "false"):
                return value
            # Otherwise return as boolean
            return bool(value)

        # Helper to build attributes dict, omitting false booleans and empty values
        def build_attributes_dict(source_dict, include_takes_value):
            attrs = {}

            # Boolean attributes - only include if true
            bool_attrs = [
                ("extensionAllowed", HedKey.ExtensionAllowed),
                ("requireChild", HedKey.RequireChild),
                ("unique", HedKey.Unique),
                ("reserved", HedKey.Reserved),
                ("tagGroup", HedKey.TagGroup),
                ("topLevelTagGroup", HedKey.TopLevelTagGroup),
                ("recommended", HedKey.Recommended),
                ("required", HedKey.Required),
            ]

            for json_name, hed_key in bool_attrs:
                value = get_bool_attribute(hed_key, source_dict)
                if value:  # Only include if true
                    attrs[json_name] = value

            # takesValue - only if appropriate
            if include_takes_value:
                value = get_bool_attribute(HedKey.TakesValue, source_dict)
                if value:
                    attrs["takesValue"] = value

            # List attributes - only include if non-empty
            suggested_tag = get_list_value(HedKey.SuggestedTag, source_dict)
            if suggested_tag:
                attrs["suggestedTag"] = suggested_tag

            related_tag = get_list_value(HedKey.RelatedTag, source_dict)
            if related_tag:
                attrs["relatedTag"] = related_tag

            value_class = get_list_value(HedKey.ValueClass, source_dict)
            if value_class:
                attrs["valueClass"] = value_class

            unit_class = get_list_value(HedKey.UnitClass, source_dict)
            if unit_class:
                attrs["unitClass"] = unit_class

            # Single value attributes
            default_units = source_dict.get(HedKey.DefaultUnits)
            if default_units:
                attrs["defaultUnits"] = default_units

            return attrs

        # Check if this tag has a placeholder child - if so, takesValue belongs to the child
        has_placeholder_child = tag_entry.takes_value_child_entry is not None
        include_takes_value = not (exclude_takes_value_if_placeholder and has_placeholder_child)

        # Build attributes dict from inherited_attributes (all effective values)
        all_attributes = build_attributes_dict(tag_entry.inherited_attributes, include_takes_value)

        # Build explicit attributes dict from attributes (only explicit values)
        explicit_attributes = build_attributes_dict(tag_entry.attributes, include_takes_value)

        # Add annotation attributes (non-inheritable) - these are always explicit
        # Add hedId if present
        hed_id = tag_entry.attributes.get(HedKey.HedID)
        if hed_id:
            all_attributes["hedId"] = hed_id
            explicit_attributes["hedId"] = hed_id

        # Add rooted if present
        rooted = tag_entry.attributes.get(HedKey.Rooted)
        if rooted:
            all_attributes["rooted"] = rooted
            explicit_attributes["rooted"] = rooted

        # Add deprecatedFrom if present
        deprecated = tag_entry.attributes.get(HedKey.DeprecatedFrom)
        if deprecated:
            all_attributes["deprecatedFrom"] = deprecated
            explicit_attributes["deprecatedFrom"] = deprecated

        # Add inLibrary if present and not disallowed (depends on save_merged setting)
        in_library = tag_entry.attributes.get(HedKey.InLibrary)
        if in_library and not self._attribute_disallowed(HedKey.InLibrary):
            all_attributes["inLibrary"] = in_library
            explicit_attributes["inLibrary"] = in_library

        # Add any other custom attributes not in our known list (e.g., 'annotation')
        known_attrs = {
            HedKey.ExtensionAllowed,
            HedKey.TakesValue,
            HedKey.RequireChild,
            HedKey.Unique,
            HedKey.Reserved,
            HedKey.TagGroup,
            HedKey.TopLevelTagGroup,
            HedKey.Recommended,
            HedKey.Required,
            HedKey.SuggestedTag,
            HedKey.RelatedTag,
            HedKey.ValueClass,
            HedKey.UnitClass,
            HedKey.DefaultUnits,
            HedKey.HedID,
            HedKey.Rooted,
            HedKey.DeprecatedFrom,
            HedKey.InLibrary,
        }
        # Add custom attributes from inherited_attributes to all_attributes
        for attr_name, attr_value in tag_entry.inherited_attributes.items():
            if attr_name not in known_attrs and not self._attribute_disallowed(attr_name):
                # Convert comma-separated strings to lists for multi-value attributes
                if isinstance(attr_value, str) and "," in attr_value:
                    all_attributes[attr_name] = [v.strip() for v in attr_value.split(",") if v.strip()]
                else:
                    all_attributes[attr_name] = attr_value

        # Add custom attributes from explicit attributes to explicit_attributes
        for attr_name, attr_value in tag_entry.attributes.items():
            if attr_name not in known_attrs and not self._attribute_disallowed(attr_name):
                # Convert comma-separated strings to lists for multi-value attributes
                if isinstance(attr_value, str) and "," in attr_value:
                    explicit_attributes[attr_name] = [v.strip() for v in attr_value.split(",") if v.strip()]
                else:
                    explicit_attributes[attr_name] = attr_value

        return all_attributes, explicit_attributes

    def _get_placeholder_attributes(self, placeholder_entry):
        """Extract placeholder-specific attributes (unitClass, valueClass, hedId, deprecatedFrom).

        Parameters:
            placeholder_entry (HedTagEntry): The placeholder tag entry (ends with /#)

        Returns:
            dict: Placeholder attributes dictionary
        """

        # Helper to get list values
        def get_list_value(attr_key):
            value = placeholder_entry.attributes.get(attr_key)
            if value is None:
                return []
            if isinstance(value, list):
                return value
            # Comma-separated string
            return [v.strip() for v in value.split(",") if v.strip()]

        placeholder_attrs = {}

        # Get takesValue - preserve string "true"/"True" if that's how it's stored
        if placeholder_entry.has_attribute(HedKey.TakesValue):
            value = placeholder_entry.attributes[HedKey.TakesValue]
            # If it's stored as string "True" or "true", keep it as string for XML compatibility
            if isinstance(value, str) and value.lower() in ("true", "false"):
                placeholder_attrs["takesValue"] = value
            else:
                placeholder_attrs["takesValue"] = True

        # Get unitClass and valueClass
        unit_class = get_list_value(HedKey.UnitClass)
        if unit_class:
            placeholder_attrs["unitClass"] = unit_class

        value_class = get_list_value(HedKey.ValueClass)
        if value_class:
            placeholder_attrs["valueClass"] = value_class

        # Get hedId if present (placeholder has its own hedId)
        hed_id = placeholder_entry.has_attribute(HedKey.HedID, return_value=True)
        if hed_id:
            placeholder_attrs["hedId"] = hed_id

        # Get deprecatedFrom if present
        deprecated = placeholder_entry.has_attribute(HedKey.DeprecatedFrom, return_value=True)
        if deprecated:
            placeholder_attrs["deprecatedFrom"] = deprecated

        # Get inLibrary if present and not disallowed
        in_library = placeholder_entry.has_attribute(HedKey.InLibrary, return_value=True)
        if in_library and not self._attribute_disallowed(HedKey.InLibrary):
            placeholder_attrs["inLibrary"] = in_library

        # Add any other custom attributes not in our known list (e.g., 'annotation')
        known_attrs = {
            HedKey.TakesValue,
            HedKey.UnitClass,
            HedKey.ValueClass,
            HedKey.HedID,
            HedKey.DeprecatedFrom,
            HedKey.InLibrary,
        }
        for attr_name, attr_value in placeholder_entry.attributes.items():
            if attr_name not in known_attrs and not self._attribute_disallowed(attr_name):
                # Convert comma-separated strings to lists for multi-value attributes
                if isinstance(attr_value, str) and "," in attr_value:
                    placeholder_attrs[attr_name] = [v.strip() for v in attr_value.split(",") if v.strip()]
                else:
                    placeholder_attrs[attr_name] = attr_value

        return placeholder_attrs

    def _write_entry(self, entry, parent_node, include_props=True):
        """Write a schema entry (unit class, value class, etc.) to the output.

        Parameters:
            entry (HedSchemaEntry): The entry to write
            parent_node (dict): Parent node dictionary
            include_props (bool): Whether to include properties

        Returns:
            dict: The created entry node
        """
        entry_data = {
            json_constants.DESCRIPTION_KEY: entry.description,  # Use None directly, not ""
        }

        # Add hedId if present (common to all entry types)
        hed_id = entry.has_attribute(HedKey.HedID, return_value=True)
        if hed_id:
            entry_data["hedId"] = hed_id

        # Add inLibrary if present and not disallowed (depends on save_merged setting)
        in_library = entry.has_attribute(HedKey.InLibrary, return_value=True)
        if in_library and not self._attribute_disallowed(HedKey.InLibrary):
            entry_data["inLibrary"] = in_library

        # Add attributes based on entry type
        if entry.section_key == HedSectionKey.UnitClasses:
            self._add_unit_class_data(entry, entry_data)
        elif entry.section_key == HedSectionKey.ValueClasses:
            self._add_value_class_data(entry, entry_data)
        elif entry.section_key == HedSectionKey.UnitModifiers:
            self._add_unit_modifier_data(entry, entry_data)
        elif entry.section_key in [HedSectionKey.Attributes, HedSectionKey.Properties]:
            self._add_schema_attribute_data(entry, entry_data)

        parent_node[entry.name] = entry_data
        return entry_data

    def _add_unit_class_data(self, entry, entry_data):
        """Add unit class specific data.

        Parameters:
            entry (HedSchemaEntry): The unit class entry
            entry_data (dict): The data dictionary to populate
        """
        # Add units list (just the names - full unit data is in separate units section)
        units_list = []
        if hasattr(entry, "units") and entry.units:
            for unit in entry.units.values():
                units_list.append(unit.name)
        entry_data[json_constants.UNITS_LIST_KEY] = units_list

        # Add default units
        default_units = entry.has_attribute(HedKey.DefaultUnits, return_value=True)
        if default_units:
            entry_data[json_constants.DEFAULT_UNITS_KEY] = default_units

    def _add_value_class_data(self, entry, entry_data):
        """Add value class specific data.

        Parameters:
            entry (HedSchemaEntry): The value class entry
            entry_data (dict): The data dictionary to populate
        """
        # Add allowed characters
        allowed_chars_value = entry.attributes.get(HedKey.AllowedCharacter)
        if allowed_chars_value:
            if isinstance(allowed_chars_value, list):
                allowed_chars = allowed_chars_value
            else:
                # Comma-separated string
                allowed_chars = [v.strip() for v in allowed_chars_value.split(",") if v.strip()]
            entry_data[json_constants.ALLOWED_CHARACTERS_KEY] = allowed_chars

        # Add any other attributes that aren't in the known list
        known_value_class_attrs = {HedKey.AllowedCharacter, HedKey.HedID, HedKey.InLibrary}
        for attr_name, attr_value in entry.attributes.items():
            if attr_name not in known_value_class_attrs and not self._attribute_disallowed(attr_name):
                # Convert comma-separated strings to lists for multi-value attributes
                if isinstance(attr_value, str) and "," in attr_value:
                    entry_data[attr_name] = [v.strip() for v in attr_value.split(",") if v.strip()]
                else:
                    entry_data[attr_name] = attr_value

    def _add_unit_modifier_data(self, entry, entry_data):
        """Add unit modifier specific data.

        Parameters:
            entry (HedSchemaEntry): The unit modifier entry
            entry_data (dict): The data dictionary to populate
        """
        # Add conversion factor
        conversion_factor = entry.has_attribute(HedKey.ConversionFactor, return_value=True)
        if conversion_factor:
            entry_data["conversionFactor"] = conversion_factor

        # Add SI unit modifier
        si_modifier = entry.has_attribute(HedKey.SIUnitModifier, return_value=True)
        if si_modifier:
            entry_data["SIUnitModifier"] = si_modifier

        # Add SI unit symbol modifier
        si_symbol = entry.has_attribute(HedKey.SIUnitSymbolModifier, return_value=True)
        if si_symbol:
            entry_data["SIUnitSymbolModifier"] = si_symbol

        # Add any other attributes that aren't in the known list
        known_modifier_attrs = {
            HedKey.ConversionFactor,
            HedKey.SIUnitModifier,
            HedKey.SIUnitSymbolModifier,
            HedKey.HedID,
            HedKey.InLibrary,
        }
        for attr_name, attr_value in entry.attributes.items():
            if attr_name not in known_modifier_attrs and not self._attribute_disallowed(attr_name):
                # Convert comma-separated strings to lists for multi-value attributes
                if isinstance(attr_value, str) and "," in attr_value:
                    entry_data[attr_name] = [v.strip() for v in attr_value.split(",") if v.strip()]
                else:
                    entry_data[attr_name] = attr_value

    def _add_schema_attribute_data(self, entry, entry_data):
        """Add schema attribute/property specific data.

        Parameters:
            entry (HedSchemaEntry): The attribute/property entry
            entry_data (dict): The data dictionary to populate
        """
        # Add all attributes from the entry (except description which is already added, and disallowed ones)
        for attr_name in entry.attributes:
            if attr_name not in [json_constants.DESCRIPTION_KEY, HedKey.HedID, HedKey.InLibrary]:
                if not self._attribute_disallowed(attr_name):
                    value = entry.attributes[attr_name]
                    # Convert comma-separated strings to lists for multi-value attributes
                    if isinstance(value, str) and "," in value:
                        entry_data[attr_name] = [v.strip() for v in value.split(",") if v.strip()]
                    else:
                        entry_data[attr_name] = value

    def to_json_string(self, indent=2):
        """Convert the output to a JSON string.

        Parameters:
            indent (int): Number of spaces for indentation

        Returns:
            str: JSON string representation
        """
        return json.dumps(self.output, indent=indent, ensure_ascii=False)
