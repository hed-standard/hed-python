from hed.schema.hed_schema_constants import HedKey
from hed.schema.hed_schema_entry import HedTagEntry


class HedTag:
    """ A single HED tag.

    Notes:
        - HedTag is a smart class in that it keeps track of its original value and positioning
          as well as pointers to the relevant HED schema information, if relevant.

    """

    def __init__(self, hed_string, span=None, hed_schema=None):
        """ Creates a HedTag.

        Parameters:
            hed_string (str): Source hed string for this tag.
            span  (int, int): The start and end indexes of the tag in the hed_string.
            hed_schema (HedSchema or None): A convenience parameter for calculating canonical forms on creation.

        Notes:
            - This does not produce issues and is used primarily for testing.

        """
        self._hed_string = hed_string
        if span is None:
            span = (0, len(hed_string))
        # This is the span into the original hed string for this tag
        self.span = span

        # If this is present, use this as the org tag for most purposes.  This is generally only filled out
        # if the tag has a name_prefix added, or is an expanded def.
        self._tag = None

        self._schema_prefix = self._get_schema_prefix(self.org_tag)

        # This is the schema this tag was converted to.
        self._schema = None
        self._schema_entry = None

        self._extension_value = ""
        self._parent = None

        if hed_schema:
            self.convert_to_canonical_forms(hed_schema)

    @property
    def schema_prefix(self):
        """ Library prefix for this tag if one exists.

        Returns:
            prefix (str): The library prefix, including the colon.

        """
        return self._schema_prefix

    @property
    def short_tag(self):
        """ Short form including value or extension.

        Returns:
            short_tag (str): The short form of the tag, including value or extension.

         Note:
             Only valid after calling convert_to_canonical_forms

        """
        if self._schema_entry:
            return f"{self._schema_prefix}{self._schema_entry.short_tag_name}{self._extension_value}"

        return str(self)

    @property
    def base_tag(self):
        """ Long form without value or extension.

        Returns:
            base_tag (str): The long form of the tag, without value or extension.

        Notes:
            - Only valid after calling convert_to_canonical_forms.

        """
        if self._schema_entry:
            return self._schema_entry.long_tag_name
        return str(self)

    @property
    def short_base_tag(self):
        """ Short form without value or extension

        Returns:
            base_tag (str): The short non-extension port of a tag.

        Notes:
            - ParentNodes/Def/DefName would return just "Def".

        """
        if self._schema_entry:
            return self._schema_entry.short_tag_name
        return str(self)

    @short_base_tag.setter
    def short_base_tag(self, new_tag_val):
        """ Change base tag, leaving extension or value.

        Parameters:
            new_tag_val (str): The new short_base_tag for this tag.

        Raises:
            ValueError: If tags cannot unidentified.

        Note:
            - Generally this is used to swap def to def-expand.
        """
        if self._schema_entry:
            if self._schema:
                tag_entry = self._schema.get_tag_entry(new_tag_val, schema_prefix=self.schema_prefix)
            else:
                tag_entry, remainder = HedTagEntry.get_fake_tag_entry(new_tag_val, [new_tag_val.lower()])

            self._schema_entry = tag_entry
        else:
            raise ValueError("Cannot set unidentified tags")

    @property
    def org_base_tag(self):
        """ Original form without value or extension.

        Returns:
            base_tag (str): The original form of the tag, without value or extension.

        Notes:
            - Warning: This could be empty if the original tag had a name_prefix prepended.
            e.g. a column where "Label/" is prepended, thus the column value has zero base portion.

            - Only valid after calling convert_to_canonical_forms.

        """
        if self._schema_entry:
            extension_len = len(self._extension_value)
            if not extension_len:
                return self.tag

            org_len = len(self.tag)
            if org_len == extension_len:
                return ""

            return self.tag[:org_len - extension_len]
        return str(self)

    def tag_modified(self):
        """ Return true if tag has been modified from original.

        Returns:
            bool: Return True if the tag is modified.

        Notes:
            - Modifications can include adding a column name_prefix.

        """
        return bool(self._tag)

    @property
    def tag(self):
        """ Returns the tag.

            Returns the original tag if no user form set.

        Returns:
            tag (str): The custom set user form of the tag.

        """
        if self._tag:
            return self._tag

        return self.org_tag

    @tag.setter
    def tag(self, new_tag_val):
        """ Allow you to overwrite the tag output text.

        Parameters:
            new_tag_val (str): New (implicitly long form) of tag to set.

        Notes:
            - Primarily used to add prefixes from column metadata to tags.
            - Only valid before calling convert_to_canonical_forms.

        """

        if self._schema_entry:
            raise ValueError("Can only edit tags before calculating canonical forms. " +
                             "This could be updated to instead remove computed forms.")
        self._tag = new_tag_val

    @property
    def extension_or_value_portion(self):
        """ Get the extension or value of tag

            Generally this is just the portion after the last slash.
            Returns an empty string if no extension or value.

        Returns:
            str: The tag name.

        Notes:
            - This tag must have been computed first.

        """
        if self._extension_value:
            return self._extension_value[1:]

        return ""

    @property
    def long_tag(self):
        """ Long form including value or extension.

        Returns:
            str: The long form of this tag.

        """
        if self._schema_entry:
            return f"{self._schema_prefix}{self._schema_entry.long_tag_name}{self._extension_value}"
        return str(self)

    @property
    def org_tag(self):
        """ Return the original unmodified tag.

        Returns:
            str: The original unmodified tag.

        """
        return self._hed_string[self.span[0]:self.span[1]]

    @property
    def tag_terms(self):
        """ Return a tuple of all the terms in this tag Lowercase.

        Returns:
            tag_terms (str): Tuple of terms or empty tuple for unidentified tag.

        Notes:
            - Does not include any extension.

        """
        if self._schema_entry:
            return self._schema_entry.tag_terms

        # TODO: Potentially remove this.  It's just a quick hack for testing
        return tuple(str(self).lower())

    def __str__(self):
        """ Convert this HedTag to a string.

        Returns:
            str: The original tag if we haven't set a new tag.(e.g. short to long).

        """
        if self._schema_entry:
            return self.short_tag

        if self._tag:
            return self._tag

        return self._hed_string[self.span[0]:self.span[1]]

    def add_prefix_if_needed(self, required_prefix):
        """ Add a prefix to this tag *unless* already formatted.

        Parameters:
            required_prefix (str): The full name_prefix to add if not present.

        Notes:
            - This means we verify the tag does not have the required name_prefix, or any partial name_prefix.

        Examples:
            Required: KnownTag1/KnownTag2

            Case 1: KnownTag1/KnownTag2/ColumnValue
                Will not be changed, has name_prefix already.

            Case 2: KnownTag2/ColumnValue
                Will not be changed, has partial name_prefix already.

            Case 3: ColumnValue
                Prefix will be added.

        """

        checking_prefix = required_prefix
        while checking_prefix:
            if self.lower().startswith(checking_prefix.lower()):
                return
            slash_index = checking_prefix.find("/") + 1
            if slash_index == 0:
                break
            checking_prefix = checking_prefix[slash_index:]
        self.tag = required_prefix + self.org_tag

    def lower(self):
        """ Convenience function, equivalent to str(self).lower(). """
        return str(self).lower()

    def convert_to_canonical_forms(self, hed_schema):
        """ Update internal state based on schema.

        Parameters:
            hed_schema (HedSchema or HedSchemaGroup): The schema to use to validate this tag

        Returns:
            list:  A list of issues found during conversion. Each element is a dictionary.

        """
        if not hed_schema:
            return self._convert_key_tags_to_canonical_form()

        tag_entry, remainder, tag_issues = hed_schema.find_tag_entry(self, self.schema_prefix)
        self._schema_entry = tag_entry
        self._schema = hed_schema
        if self._schema_entry:
            if remainder:
                self._extension_value = remainder

        return tag_issues

    def get_stripped_unit_value(self):
        """ Return the extension portion without units.

        Returns:
            stripped_unit_value (str): The extension portion with the units removed.
            unit (str or None): None if no valid unit found.

        Examples:
            'Duration/3 ms' will return '3'

        """
        tag_unit_classes = self.unit_classes
        stripped_value, unit = self._get_tag_units_portion(tag_unit_classes)
        if stripped_value:
            return stripped_value, unit

        return self.extension_or_value_portion, None

    @property
    def unit_classes(self):
        """ Return a dict of all the unit classes this tag accepts.

        Returns:
            unit_classes (dict):  A dict of unit classes this tag accepts.

        Notes:
            - Returns empty dict if this is not a unit class tag.
            - The dictionary has unit name as the key and HedSchemaEntry as value.

        """
        if self._schema_entry:
            return self._schema_entry.unit_classes
        return {}

    @property
    def value_classes(self):
        """ Return a dict of all the value classes this tag accepts.

        Returns:
            dict: A dictionary of HedSchemaEntry value classes this tag accepts.

        Notes:
            - Returns empty dict if this is not a value class.
            - The dictionary has unit name as the key and HedSchemaEntry as value.

        """
        if self._schema_entry:
            return self._schema_entry.value_classes
        return {}

    @property
    def attributes(self):
        """ Return a dict of all the attributes this tag has.

            Returns empty dict if this is not a value tag.

        Returns:
            dict: A dict of attributes this tag has.

        Notes:
            - Returns empty dict if this is not a unit class tag.
            - The dictionary has unit name as the key and HedSchemaEntry as value.

        """
        if self._schema_entry:
            return self._schema_entry.attributes
        return {}

    def tag_exists_in_schema(self):
        """ Get the schema entry for this tag.

        Returns:
            bool: True if this tag exists.

        Notes:
            - This does NOT assure this is a valid tag.
        """
        return bool(self._schema_entry)

    def is_takes_value_tag(self):
        """ Return true if this is a takes value tag.

        Returns:
            bool: True if this is a takes value tag.

        """
        if self._schema_entry:
            return self._schema_entry.has_attribute(HedKey.TakesValue)
        return False

    def is_unit_class_tag(self):
        """ Return true if this is a unit class tag.

        Returns:
            bool: True if this is a unit class tag.

        """
        if self._schema_entry:
            return bool(self._schema_entry.unit_classes)
        return False

    def is_value_class_tag(self):
        """ Return true if this is a value class tag.

        Returns:
            bool:  True if this is a a tag with a value class.

        """
        if self._schema_entry:
            return bool(self._schema_entry.value_classes)
        return False

    def is_basic_tag(self):
        """  Return True if a known tag with no extension or value.

        Returns:
            bool:  True if this is a known tag without extension or value.

        """
        return bool(self._schema_entry and not self.extension_or_value_portion)

    def has_attribute(self, attribute):
        """ Return true if this is an attribute this tag has.

        Parameters:
            attribute (str): Name of the attribute.

        Returns:
            bool: True if this tag has the attribute.

        """
        if self._schema_entry:
            return self._schema_entry.has_attribute(attribute)
        return False

    def is_extension_allowed_tag(self):
        """ Check if tag has 'extensionAllowed' attribute.

            Recursively checks parent tag entries for the attribute as well.

        Returns:
            bool: True if the tag has the 'extensionAllowed' attribute. False, if otherwise.

        """
        if self.is_takes_value_tag():
            return False

        if self._schema_entry:
            return self._schema_entry.any_parent_has_attribute(HedKey.ExtensionAllowed)
        return False

    def get_tag_unit_class_units(self):
        """ Get the unit class units associated with a particular tag.

        Returns:
            list: A list containing the unit class units associated with a particular tag or an empty list.

        """
        units = []
        unit_classes = self.unit_classes
        for unit_class_entry in unit_classes.values():
            units += unit_class_entry.unit_class_units.keys()

        return units

    def get_unit_class_default_unit(self):
        """ Get the default unit class unit for this tag.

        Returns:
            str: The default unit class unit associated with the specific tag or an empty string.

        """
        default_unit = ''
        unit_classes = self.unit_classes.values()
        if unit_classes:
            first_unit_class_entry = list(unit_classes)[0]
            default_unit = first_unit_class_entry.has_attribute(HedKey.DefaultUnits, return_value=True)

        return default_unit

    def base_tag_has_attribute(self, tag_attribute):
        """ Check to see if the tag has a specific attribute.

        Parameters:
            tag_attribute (str): A tag attribute.

        Returns:
            bool: True if the tag has the specified attribute. False, if otherwise.

        """
        if not self._schema_entry:
            return False

        return self._schema_entry.base_tag_has_attribute(tag_attribute)

    def any_parent_has_attribute(self, attribute):
        """ Check if the tag or any of its parents has the attribute.

        Parameters:
            attribute (str): The name of the attribute to check for.

        Returns:
            bool: True if the tag has the given attribute. False, if otherwise.

        """
        if self._schema_entry:
            return self._schema_entry.any_parent_has_attribute(attribute=attribute)

    def _convert_key_tags_to_canonical_form(self):
        """ Find the canonical form for basic known tags.

        Returns:
            list: Always return an empty list.

        Notes:
            -  This is used for such as definition and def when no schema present

        """
        tags_to_identify = ["onset", "definition", "offset", "def-expand", "def"]
        tag_entry, remainder = HedTagEntry.get_fake_tag_entry(str(self), tags_to_identify)
        if tag_entry:
            self._schema_entry = tag_entry
            self._schema = None
            self._extension_value = remainder

        return []

    def _get_schema_prefix(self, org_tag):
        """ Finds the library prefix for the tag.

        Parameters:
            org_tag (str): A string representing a tag.

        Returns:
            str: Library prefix string or empty.

        """
        first_slash = org_tag.find("/")
        first_colon = org_tag.find(":")

        if first_colon != -1:
            if first_slash != -1 and first_colon > first_slash:
                return ""

            return org_tag[:first_colon + 1]
        return ""

    def _get_tag_units_portion(self, tag_unit_classes):
        """ Check that this string has valid units and remove them.

        Parameters:
            tag_unit_classes (dict): Dictionary of valid UnitClassEntry objects for this tag.

        Returns:
            stripped_value (str): The value with the units removed.

        """
        value, _, units = self.extension_or_value_portion.rpartition(" ")
        if not units:
            return None, None

        for unit_class_entry in tag_unit_classes.values():
            all_valid_unit_permutations = unit_class_entry.derivative_units

            possible_match = self._find_modifier_unit_entry(units, all_valid_unit_permutations)
            if possible_match and not possible_match.has_attribute(HedKey.UnitPrefix):
                return value, units

            # Repeat the above, but as a prefix
            possible_match = self._find_modifier_unit_entry(value, all_valid_unit_permutations)
            if possible_match and possible_match.has_attribute(HedKey.UnitPrefix):
                return units, value

        return None, None

    @staticmethod
    def _find_modifier_unit_entry(units, all_valid_unit_permutations):
        possible_match = all_valid_unit_permutations.get(units)
        if not possible_match or not possible_match.has_attribute(HedKey.UnitSymbol):
            possible_match = all_valid_unit_permutations.get(units.lower())
            if possible_match and possible_match.has_attribute(HedKey.UnitSymbol):
                possible_match = None

        return possible_match

    def replace_placeholder(self, placeholder_value):
        """ If tag has a placeholder character(#), replace with value.

        Parameters:
            placeholder_value (str): Value to replace placeholder with.

        """
        if "#" in self.org_tag:
            if self._schema_entry:
                self._extension_value = self._extension_value.replace("#", placeholder_value)
            else:
                self._tag = self.tag.replace("#", placeholder_value)

    def __hash__(self):
        if self._schema_entry:
            return hash(
                self._schema_prefix + self._schema_entry.short_tag_name.lower() + self._extension_value.lower())
        else:
            return hash(self.lower())

    def __eq__(self, other):
        if self is other:
            return True

        if isinstance(other, str):
            return self.lower() == other

        if not isinstance(other, HedTag):
            return False

        if self.short_tag.lower() == other.short_tag.lower():
            return True

        if self.org_tag.lower() == other.org_tag.lower():
            return True
        return False
